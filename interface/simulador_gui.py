"""
Interface gráfica do simulador de curva de capabilidade.

Entradas de campo em p.u. (prática profissional ONS / IEEE / Elipse):
    P, Q, Vt, If, Is, f, H

Esta camada NÃO contém lógica de cálculo — consome o simulador.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import sys

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from src.exportacao.elipse_e3 import ExportadorElipseE3
from src.simulador.fabrica import CriarSimuladorDeDiretorio
from src.utilitarios.grafico import ConverterParaGrafico, PontoOperacionalParaGrafico


# Definição das entradas de campo necessárias (ordem de exibição)
ENTRADAS_CAMPO = (
    ("P", "P — Potência ativa (pu)", "Sn"),
    ("Q", "Q — Potência reativa (pu)", "Sn"),
    ("Vt", "Vt — Tensão terminal (pu)", "Vn"),
    ("If", "If — Corrente de campo (pu)", "If_FL"),
    ("Is", "Is — Corrente de estator (pu) [0 = S/Vt]", "In"),
    ("f", "f — Frequência (pu) [V/Hz = Vt/f]", "fn"),
    ("H", "H — Queda útil (pu)", "Hn"),
)


class InterfaceSimulador(tk.Tk):
    """Janela principal do simulador."""

    def __init__(self, diretorio_dados: str):
        super().__init__()
        self.geometry("1600x1000")
        self.minsize(1280, 800)
        self.diretorio_dados = diretorio_dados
        self._carregar_simulador()
        tipo = self.simulador.gerador.tipo_maquina.value
        self.title(
            f"Curva de Capabilidade — {self.simulador.gerador.identificacao} ({tipo})"
        )
        self._criar_widgets()
        self._atualizar_resultados()
        try:
            self.state("zoomed")
        except tk.TclError:
            pass

    def _carregar_simulador(self) -> None:
        self.simulador = CriarSimuladorDeDiretorio(self.diretorio_dados)
        self.simulador.recalcular_curva()

    def _criar_widgets(self) -> None:
        eh_compensador = self.simulador.gerador.eh_compensador()
        tem_turbina = self.simulador.turbina is not None

        titulo_painel = "Entradas de campo (p.u.)"
        if eh_compensador:
            titulo_painel += " — Compensador síncrono (P ≈ 0)"
        else:
            titulo_painel += " — posição na curva"

        painel_entrada = ttk.LabelFrame(self, text=titulo_painel)
        painel_entrada.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        bases = self.simulador.bases.resumo_bases()
        ttk.Label(
            painel_entrada,
            text=(
                f"Tipo: {self.simulador.gerador.tipo_maquina.value}\n"
                f"Bases: Sn={bases['Sn_MVA']:.1f} MVA | "
                f"Vn={bases['Vn_kV']:.2f} kV\n"
                f"In={bases['In_A']:.0f} A | "
                f"If_FL={bases['If_FL_A']:.0f} A\n"
                f"fn={bases['fn_Hz']:.0f} Hz"
                + (f" | Hn={bases['Hn_m']:.1f} m" if tem_turbina else "")
            ),
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=5, pady=6)

        ttk.Separator(painel_entrada, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

        grandezas = self.simulador.obter_grandezas_campo_pu()
        self.campos = {}
        for chave, rotulo, base_nome in ENTRADAS_CAMPO:
            if chave == "H" and (eh_compensador or not tem_turbina):
                continue
            rotulo_exibir = rotulo
            if chave == "P" and eh_compensador:
                rotulo_exibir = "P — Potência ativa (pu) [≈ 0]"
            ttk.Label(painel_entrada, text=f"{rotulo_exibir}  [base {base_nome}]").pack(
                anchor=tk.W, padx=5, pady=2
            )
            entrada = ttk.Entry(painel_entrada, width=18)
            valor = grandezas.get(chave, 0.0)
            entrada.insert(0, f"{valor:.4f}")
            if chave == "P" and eh_compensador:
                entrada.configure(state="readonly")
            entrada.pack(padx=5, pady=2)
            self.campos[chave] = entrada

        ttk.Label(
            painel_entrada,
            text=(
                "Is=0 → calcula Is=S/Vt | Is>0 → medida (SCL)\n"
                "Curva SCL usa Imax (capacidade), não Is de operação"
            ),
            font=("TkDefaultFont", 8),
        ).pack(anchor=tk.W, padx=5, pady=4)

        ttk.Button(
            painel_entrada, text="Recalcular", command=self._atualizar_resultados
        ).pack(pady=10, padx=5, fill=tk.X)

        ttk.Button(
            painel_entrada,
            text="Exportar para Elipse E3",
            command=self._exportar_elipse,
        ).pack(pady=5, padx=5, fill=tk.X)

        painel_resultado = ttk.LabelFrame(self, text="Resultados")
        painel_resultado.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.texto_resultado = tk.Text(painel_resultado, height=7, width=72)
        self.texto_resultado.pack(fill=tk.X, expand=False, padx=5, pady=5)

        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            self._plt = plt
            painel_grafico = ttk.Frame(painel_resultado)
            painel_grafico.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            self.figura = plt.Figure(figsize=(11.0, 7.5), dpi=100, layout="none")
            self.eixo = self.figura.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.figura, master=painel_grafico)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.matplotlib_disponivel = True
            self._atualizando_grafico = False
        except ImportError:
            self.matplotlib_disponivel = False
            self._plt = None
            self._atualizando_grafico = False

    def _ler_entradas(self) -> None:
        """Lê entradas de campo em p.u. e atualiza o simulador."""
        eh_compensador = self.simulador.gerador.eh_compensador()
        is_pu = float(self.campos["Is"].get())
        kwargs = {
            "potencia_ativa": 0.0 if eh_compensador else float(self.campos["P"].get()),
            "potencia_reativa": float(self.campos["Q"].get()),
            "tensao": float(self.campos["Vt"].get()),
            "corrente_campo": float(self.campos["If"].get()),
            "corrente_estator": is_pu if is_pu > 0 else None,
            "frequencia": float(self.campos["f"].get()),
            "em_por_unidade": True,
        }
        if "H" in self.campos:
            kwargs["queda"] = float(self.campos["H"].get())
        self.simulador.atualizar_ponto_operacional(**kwargs)
        if is_pu <= 0:
            self.simulador.ponto_operacional.corrente_estator = 0.0
            self.simulador._sincronizar_corrente_estator()

    def _atualizar_resultados(self) -> None:
        try:
            self._ler_entradas()
            resultado_simulacao = self.simulador.executar_simulacao_completa()
            resultado = resultado_simulacao["ResultadoCapabilidade"]
            ponto = resultado_simulacao["PontoOperacional"]
            pontos = resultado_simulacao["PontosCurva"]
            g = resultado_simulacao["GrandezasCampoPu"]
            bases = resultado_simulacao["Bases"]

            # Atualiza Is calculado no campo (feedback)
            self.campos["Is"].delete(0, tk.END)
            self.campos["Is"].insert(0, f"{g['Is']:.4f}")

            self.texto_resultado.delete("1.0", tk.END)
            unidade_limite = "pu" if pontos.unidade == "pu" else "Mvar"
            resumo = bases.resumo_bases()
            linhas = [
                "=== RESULTADO DA CAPABILIDADE ===",
                f"Unidade: {pontos.unidade} | Sn = {resumo['Sn_MVA']:.1f} MVA",
                f"Dentro da curva: {'SIM' if resultado.dentro_da_curva else 'NAO'}",
                f"Margem operacional: {resultado.margem_operacional:.2f} %",
                f"Limite restritivo: {resultado.limite_restritivo}",
                f"S = {g['S']:.4f} pu ({resultado.potencia_aparente:.2f} MVA)",
                f"fp = {g['fator_potencia']:.3f}",
                f"Qsup = {resultado.limite_superior_efetivo:.4f} {unidade_limite}",
                f"Qinf = {resultado.limite_inferior_efetivo:.4f} {unidade_limite}",
                f"P máxima (traçado): {max(pontos.potencias_ativas):.4f} pu",
                "",
                "=== ENTRADAS DE CAMPO (p.u.) ===",
                f"P  = {g['P']:.4f} pu  ({ponto.potencia_ativa:.2f} MW)",
                f"Q  = {g['Q']:.4f} pu  ({ponto.potencia_reativa:.2f} Mvar)",
                f"Vt = {g['Vt']:.4f} pu  ({ponto.tensao:.2f} kV)",
                f"If = {g['If']:.4f} pu  ({ponto.corrente_campo:.1f} A)  "
                f"[If_FL={resumo['If_FL_A']:.0f} A]",
                f"Is = {g['Is']:.4f} pu ({g['Is_origem']})  "
                f"[Is_calc={g['Is_calc']:.4f} | Imax={g['Imax']:.4f} | "
                f"margem={g['margem_Is']:.1f}%]",
                f"f  = {g['f']:.4f} pu  ({ponto.frequencia:.2f} Hz)",
                f"V/Hz = {g['VHz']:.4f} pu "
                f"[máx={g['VHz_max']:.4f} | margem={g['margem_VHz']:.1f}% | "
                f"{'OK' if g['VHz_ok'] else 'VIOLADO'}]",
            ]
            if "H" in self.campos:
                linhas.append(
                    f"H  = {g['H']:.4f} pu  ({ponto.queda:.2f} m)"
                )

            if resultado.mensagens:
                linhas.append("")
                linhas.append("=== MENSAGENS ===")
                linhas.extend(resultado.mensagens)

            self.texto_resultado.insert(tk.END, "\n".join(linhas))

            if self.matplotlib_disponivel:
                self._atualizar_grafico(pontos, g["P"], g["Q"])

        except Exception as erro:
            messagebox.showerror("Erro", str(erro))

    def _atualizar_grafico(
        self,
        pontos,
        potencia_ativa_pu: float,
        potencia_reativa_pu: float,
    ) -> None:
        if self._atualizando_grafico:
            return
        self._atualizando_grafico = True
        try:
            self._desenhar_grafico(pontos, potencia_ativa_pu, potencia_reativa_pu)
        finally:
            self._atualizando_grafico = False

    def _desenhar_grafico(
        self,
        pontos,
        potencia_ativa_pu: float,
        potencia_reativa_pu: float,
    ) -> None:
        # Recria o eixo a cada recálculo — evita figura “quebrada” no Tk
        self.figura.clear()
        self.eixo = self.figura.add_subplot(111)

        if pontos.contorno_fechado:
            coordenada_x = [item[0] for item in pontos.contorno_fechado]
            coordenada_y = [item[1] for item in pontos.contorno_fechado]
            coordenada_x.append(pontos.contorno_fechado[0][0])
            coordenada_y.append(pontos.contorno_fechado[0][1])
            self.eixo.fill(
                coordenada_x,
                coordenada_y,
                color="#C8E6C9",
                alpha=0.35,
                label="Região Permitida — área segura de operação",
            )
            self.eixo.plot(
                coordenada_x,
                coordenada_y,
                "g-",
                linewidth=1.5,
                label="Traçado Operacional — envelope efetivo",
            )

        cores_ref = {
            "LimiteSobreExcitacao": "#2E7D32",
            "LimiteRotor": "#AB47BC",
            "LimiteEstator": "#212121",
            "CirculoPotenciaAparente": "#212121",
            "CirculoOperacaoIs": "#616161",
            "LimiteEstabilidade": "#EF6C00",
            "LimiteEstabilidadePratica": "#FFA726",
            "LimiteSubExcitacao": "#7CB342",
            "LimiteSaturacao": "#00838F",
            "LimiteCorrenteCampo": "#5D4037",
            "LimiteTurbina": "#0D47A1",
            "LimitePmecMax": "#0D47A1",
            "LimiteQuedaUtil": "#0277BD",
            "LimiteTurbinaMax": "#01579B",
            "LimitePmecMin": "#90CAF9",
            "LimiteTurbinaMin": "#BBDEFB",
            "FatorPotenciaNominal": "#C62828",
            "EixoOperacaoCompensador": "#1565C0",
            "LimiteAquecimentoExtremoEstator": "#6A1B9A",
            "LimiteSaturacaoMagnetica": "#4527A0",
        }
        fp = getattr(pontos, "fator_potencia_nominal", 0.0) or (
            self.simulador.gerador.fator_potencia_nominal
        )
        rotulos = {
            "LimiteSobreExcitacao": "OEL TH — Limite térmico de sobre-excitação",
            "LimiteRotor": "OEL PK — Limite de pico de sobre-excitação",
            "LimiteEstator": "SCL — Limite efetivo de corrente do estator",
            "CirculoPotenciaAparente": "S = Vt·Imax — Limite SCL (capacidade)",
            "CirculoOperacaoIs": (
                f"S = Vt·Is — Operação atual (Is={getattr(pontos, 'corrente_estator_operacao_pu', 0):.3f})"
            ),
            "LimiteEstabilidade": "UEL — Limite de subexcitação / estabilidade",
            "LimiteEstabilidadePratica": "UEL Prático — Limite prático de estabilidade",
            "LimiteSubExcitacao": "MEL — Limitador de excitação mínima",
            "LimiteSaturacao": "Saliência polar — Limite por saliência do rotor",
            "LimiteSaturacaoMagnetica": "Saturação magnética — Limite de Q (OCC)",
            "LimiteAquecimentoExtremoEstator": (
                "End-iron — Aquecimento de extremo do estator"
            ),
            "LimiteCorrenteCampo": "IFD — Limite de corrente de campo",
            "LimitePmecMax": "Pmec Max — Limite da região permitida (P)",
            "LimiteQuedaUtil": "Queda útil — Referência P(H) [não limita a região]",
            "LimiteTurbinaMax": "Turbina Max — Referência teto da turbina",
            "LimitePmecMin": "Pmec Min — Limite inferior da região (P)",
            "LimiteTurbinaMin": "Turbina Min — Referência piso da turbina",
            "FatorPotenciaNominal": (
                f"fp = {fp:.2f} — Reta do fator de potência nominal"
            ),
            "EixoOperacaoCompensador": "P = 0 — Eixo de operação (compensador)",
        }
        estilos = {
            "LimitePmecMax": {"linewidth": 2.0, "linestyle": "-", "alpha": 1.0},
            "LimiteQuedaUtil": {"linewidth": 1.8, "linestyle": "--", "alpha": 0.95},
            "LimiteTurbinaMax": {"linewidth": 1.6, "linestyle": "-.", "alpha": 0.95},
            "LimitePmecMin": {"linewidth": 1.5, "linestyle": ":", "alpha": 0.9},
            "LimiteTurbinaMin": {"linewidth": 1.4, "linestyle": ":", "alpha": 0.85},
            "CirculoPotenciaAparente": {
                "linewidth": 1.8,
                "linestyle": "-",
                "alpha": 0.95,
            },
            "CirculoOperacaoIs": {
                "linewidth": 1.3,
                "linestyle": ":",
                "alpha": 0.9,
            },
            "FatorPotenciaNominal": {
                "linewidth": 1.6,
                "linestyle": "-.",
                "alpha": 1.0,
            },
            "EixoOperacaoCompensador": {
                "linewidth": 2.0,
                "linestyle": "-",
                "alpha": 1.0,
            },
        }
        for nome, serie in list(pontos.curvas_individuais_superiores.items()) + list(
            pontos.curvas_individuais_inferiores.items()
        ):
            if nome not in rotulos or not serie:
                continue
            grafico = ConverterParaGrafico(serie)
            estilo = estilos.get(
                nome, {"linewidth": 1.2, "linestyle": "--", "alpha": 0.9}
            )
            self.eixo.plot(
                [p[0] for p in grafico],
                [p[1] for p in grafico],
                color=cores_ref.get(nome, "#E53935"),
                label=rotulos[nome],
                **estilo,
            )

        coordenada_operacional = PontoOperacionalParaGrafico(
            potencia_ativa_pu,
            potencia_reativa_pu,
        )
        self.eixo.plot(
            coordenada_operacional[0],
            coordenada_operacional[1],
            "ko",
            markersize=9,
            markerfacecolor="yellow",
            markeredgewidth=1.5,
            label="Ponto Operacional — estado atual (P, Q)",
        )
        self.eixo.set_xlabel("Potência Reativa Q (p.u.)")
        self.eixo.set_ylabel("Potência Ativa P (p.u.)")
        base = pontos.base_potencia_aparente or self.simulador.gerador.potencia_nominal
        vt = getattr(pontos, "tensao_terminal_pu", 1.0)
        g = self.simulador.obter_grandezas_campo_pu()
        titulo_extra = f"Vt={vt:.2f} | If={g['If']:.2f}"
        if self.simulador.turbina is not None:
            titulo_extra += f" | H={g['H']:.2f}"
        if self.simulador.gerador.eh_compensador():
            titulo_extra += " | Compensador (P≈0)"
        self.eixo.set_title(
            f"Traçado Operacional - {self.simulador.gerador.identificacao}\n"
            f"Q×P (pu) | Sn={base:.1f} MVA | {titulo_extra}"
        )
        self.eixo.grid(True, alpha=0.3)
        self.eixo.axhline(0, color="gray", linewidth=0.5)
        self.eixo.axvline(0, color="gray", linewidth=0.5)

        self._aplicar_janela_circular(pontos)

        # Legenda à direita — libera altura do gráfico
        self.eixo.legend(
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            borderaxespad=0.0,
            fontsize=9,
            frameon=True,
            fancybox=False,
            edgecolor="#BDBDBD",
            handlelength=2.0,
            labelspacing=0.6,
        )
        self.figura.subplots_adjust(left=0.08, right=0.72, bottom=0.08, top=0.90)
        self.canvas.draw_idle()

    def _aplicar_janela_circular(self, pontos) -> None:
        """
        Janela do diagrama Q×P.

        Vertical (P): −0,25 … 1,25 (faixa útil do traçado).
        Horizontal (Q): cobre o círculo S=Sn.
        Aspecto equal ⇒ semicírculo geometricamente circular.
        """
        raio = getattr(pontos, "potencia_aparente_maxima_pu", 1.0) or 1.0
        margem = 0.12
        half_q = raio + margem
        self.eixo.set_xlim(-half_q, half_q)
        self.eixo.set_ylim(-0.25, 1.25)
        self.eixo.set_aspect("equal", adjustable="box")

    def _exportar_elipse(self) -> None:
        try:
            self._ler_entradas()
            resultado_simulacao = self.simulador.executar_simulacao_completa()
            diretorio_saida = str(Path(self.diretorio_dados) / "exportacao_elipse")
            exportador = ExportadorElipseE3(diretorio_saida)
            exportador.exportar_pontos_curva(resultado_simulacao["PontosCurva"])
            exportador.exportar_resultado_operacional(
                resultado_simulacao["PontoOperacional"],
                resultado_simulacao["ResultadoCapabilidade"],
                grandezas_pu=resultado_simulacao["GrandezasCampoPu"],
                bases=resultado_simulacao["Bases"],
            )
            exportador.gerar_instrucoes_grafico()
            from pathlib import Path as _Path
            exportador.copiar_scripts_elipse(_Path(__file__).resolve().parents[1])
            messagebox.showinfo(
                "Exportação",
                f"Séries visuais e scripts Elipse exportados para:\n{diretorio_saida}",
            )
        except Exception as erro:
            messagebox.showerror("Erro na exportação", str(erro))


def executar_interface(diretorio_dados: str) -> None:
    app = InterfaceSimulador(diretorio_dados)
    app.mainloop()


if __name__ == "__main__":
    diretorio = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(RAIZ_PROJETO / "dados" / "usina")
    )
    executar_interface(diretorio)
