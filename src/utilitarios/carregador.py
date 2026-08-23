"""
Carregador de dados externos JSON e CSV.

Objetivo:
    Carregar parâmetros do gerador, turbina e curvas de arquivos externos,
    permitindo reutilização da biblioteca sem alterar código-fonte.

Hipóteses:
    Arquivos CSV possuem cabeçalho com colunas PotenciaAtiva e PotenciaReativa
    ou Abscissa e Ordenada.

Referências:
    - Estrutura de dados de fabricantes conforme IEEE Std 1110-2002.
"""

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.constantes.grandezas import TipoMaquina, TipoTurbina
from src.curvas.avaliador import ConfiguracaoCurvas
from src.modelos.gerador import GeradorSincrono
from src.modelos.tabela_curva import TabelaCurva
from src.modelos.turbina import Turbina


class CarregadorDados:
    """Carrega dados de configuração de um diretório de projeto."""

    def __init__(self, diretorio_dados: str):
        self.diretorio = Path(diretorio_dados)

    def carregar_gerador(self, nome_arquivo: str = "gerador.json") -> GeradorSincrono:
        """Carrega parâmetros do gerador ou compensador síncrono."""
        dados = _carregar_json(self.diretorio / nome_arquivo)

        tipo_texto = str(dados.get("TipoMaquina", "Gerador"))
        try:
            tipo_maquina = TipoMaquina(tipo_texto)
        except ValueError:
            tipo_maquina = TipoMaquina.GERADOR

        return GeradorSincrono(
            identificacao=dados["Identificacao"],
            potencia_nominal=float(dados["PotenciaNominal"]),
            potencia_ativa_nominal=float(dados.get("PotenciaAtivaNominal", 0.0)),
            tensao_nominal=float(dados["TensaoNominal"]),
            corrente_nominal=float(dados["CorrenteNominal"]),
            frequencia=float(dados["Frequencia"]),
            numero_polos=int(dados["NumeroPolos"]),
            reatancia_direta=float(dados["ReatanciaDireta"]),
            reatancia_quadratura=float(dados["ReatanciaQuadratura"]),
            reatancia_transitoria_direta=float(dados["ReatanciaTransitoriaDireta"]),
            reatancia_subtransitoria_direta=float(dados["ReatanciaSubtransitoriaDireta"]),
            resistencia_armadura=float(dados["ResistenciaArmadura"]),
            constante_inercia=float(dados["ConstanteInercia"]),
            corrente_campo_nominal=float(dados["CorrenteCampoNominal"]),
            corrente_campo_vazio=float(dados.get("CorrenteCampoVazio", 0.0)),
            fator_potencia_nominal=float(dados.get("FatorPotenciaNominal", 0.0 if tipo_maquina == TipoMaquina.COMPENSADOR_SINCRONO else 0.85)),
            potencia_ativa_maxima=float(dados.get("PotenciaAtivaMaxima", 0.0)),
            potencia_ativa_maxima_pu=float(dados.get("PotenciaAtivaMaximaPu", 0.0)),
            tipo_maquina=tipo_maquina,
            descricao=dados.get("Descricao", ""),
            referencia=dados.get("Referencia", "IEEE Std 1110-2002"),
        )

    def carregar_turbina(
        self, nome_arquivo: str = "turbina.json"
    ) -> Optional[Turbina]:
        """
        Carrega parâmetros da turbina, se o arquivo existir.

        Compensadores síncronos tipicamente não possuem turbina — retorna None.
        """
        caminho = self.diretorio / nome_arquivo
        if not caminho.exists():
            return None

        dados = _carregar_json(caminho)

        curva_hidraulica = None
        if "ArquivoCurvaHidraulica" in dados and dados["ArquivoCurvaHidraulica"]:
            caminho_hid = self.diretorio / str(dados["ArquivoCurvaHidraulica"])
            if caminho_hid.exists():
                curva_hidraulica = self.carregar_curva_csv(
                    dados["ArquivoCurvaHidraulica"],
                    nome="CurvaHidraulica",
                    unidade_x="m",
                    unidade_y="MW",
                )

        curva_rendimento = None
        if "ArquivoCurvaRendimento" in dados and dados["ArquivoCurvaRendimento"]:
            caminho_rend = self.diretorio / str(dados["ArquivoCurvaRendimento"])
            if caminho_rend.exists():
                curva_rendimento = self.carregar_curva_csv(
                    dados["ArquivoCurvaRendimento"],
                    nome="CurvaRendimento",
                    unidade_x="m",
                    unidade_y="pu",
                )

        tipo = dados["Tipo"]
        expoente_padrao = 1.5
        if tipo in ("Pelton", "Termica"):
            expoente_padrao = 1.0

        return Turbina(
            identificacao=dados["Identificacao"],
            tipo=TipoTurbina(tipo),
            potencia_nominal=float(dados["PotenciaNominal"]),
            queda_nominal=float(dados["QuedaNominal"]),
            vazao_nominal=float(dados["VazaoNominal"]),
            rendimento_nominal=float(dados["RendimentoNominal"]),
            abertura_distribuidor=float(dados.get("AberturaDistribuidor", 100.0)),
            potencia_minima=float(dados.get("PotenciaMinima", 0.0)),
            potencia_maxima=float(dados.get("PotenciaMaxima", 0.0)),
            potencia_maxima_pu=float(dados.get("PotenciaMaximaPu", 0.0)),
            expoente_queda=float(dados.get("ExpoenteQueda", expoente_padrao)),
            curva_hidraulica=curva_hidraulica,
            curva_rendimento=curva_rendimento,
            descricao=dados.get("Descricao", ""),
            referencia=dados.get("Referencia", ""),
        )

    def carregar_curva_csv(
        self,
        nome_arquivo: str,
        nome: str,
        unidade_x: str = "pu",
        unidade_y: str = "pu",
        permitir_extrapolacao: bool = False,
        referencia: str = "",
    ) -> TabelaCurva:
        """
        Carrega curva tabulada de arquivo CSV.

        Formatos aceitos:
            - PotenciaAtivaPu, PotenciaReativaPu  (ONS / p.u.)
            - PotenciaReativaPu, PotenciaAtivaPu  (gráfico ONS)
            - PotenciaAtiva, PotenciaReativa      (MW / Mvar)

        Internamente a tabela fica ordenada por P (abscissa) com Q (ordenada).
        """
        caminho = self.diretorio / nome_arquivo
        pontos: List[Tuple[float, float]] = []

        with _abrir_csv_sem_comentarios(caminho) as arquivo:
            leitor = csv.DictReader(arquivo)
            colunas = leitor.fieldnames or []

            formato_grafico_pu = (
                "PotenciaReativaPu" in colunas and "PotenciaAtivaPu" in colunas
            )

            for linha in leitor:
                if formato_grafico_pu:
                    # CSV no formato gráfico ONS: Q, P → converter para (P, Q)
                    potencia_reativa = float(linha["PotenciaReativaPu"])
                    potencia_ativa = float(linha["PotenciaAtivaPu"])
                else:
                    potencia_ativa = float(
                        _obter_valor_coluna(
                            linha,
                            ["PotenciaAtivaPu", "PotenciaAtiva", "Abscissa", "Queda", "X"],
                        )
                    )
                    potencia_reativa = float(
                        _obter_valor_coluna(
                            linha,
                            [
                                "PotenciaReativaPu",
                                "PotenciaReativa",
                                "Potencia",
                                "Ordenada",
                                "Rendimento",
                                "Y",
                            ],
                        )
                    )
                pontos.append((potencia_ativa, potencia_reativa))

        pontos.sort(key=lambda p: p[0])
        pontos = _remover_duplicatas_abscissa(pontos)
        return TabelaCurva(
            nome=nome,
            unidade_x=unidade_x,
            unidade_y=unidade_y,
            pontos=pontos,
            permitir_extrapolacao=permitir_extrapolacao,
            referencia=referencia,
        )

    def carregar_configuracao_curvas(
        self,
        nome_arquivo: str = "curvas.json",
    ) -> ConfiguracaoCurvas:
        """Carrega configuração de todas as curvas do projeto."""
        dados = _carregar_json(self.diretorio / nome_arquivo)

        configuracao = ConfiguracaoCurvas(
            potencia_aparente_maxima=float(dados.get("PotenciaAparenteMaxima", 1.0)),
            potencia_ativa_maxima=float(
                dados.get("PotenciaMecanicaMaximaPu", dados.get("PotenciaAtivaMaxima", 0.9))
            ),
            potencia_mecanica_maxima_pu=float(
                dados.get("PotenciaMecanicaMaximaPu", dados.get("PotenciaAtivaMaxima", 0.9))
            ),
            potencia_mecanica_minima_pu=float(dados.get("PotenciaMecanicaMinimaPu", 0.0)),
            corrente_estator_maxima_pu=float(
                dados.get(
                    "CorrenteEstatorMaximaPu",
                    dados.get("PotenciaAparenteMaxima", 1.0),
                )
            ),
            relacao_volts_hertz_maxima_pu=float(
                dados.get("RelacaoVoltsHertzMaximaPu", 1.05)
            ),
            relacao_volts_hertz_minima_pu=float(
                dados.get("RelacaoVoltsHertzMinimaPu", 0.0)
            ),
            derating_oel_por_volts_hertz=bool(
                dados.get("DeratingOelPorVoltsHertz", True)
            ),
            tensao_referencia_curvas=float(dados.get("TensaoReferenciaCurvas", 1.0)),
            unidade=str(dados.get("Unidade", "pu")),
            base_potencia_aparente=float(dados.get("BasePotenciaAparente", 0.0)),
            incluir_saliencia_no_envelope=bool(
                dados.get("IncluirSalienciaNoEnvelope", False)
            ),
        )

        unidade_eixo = "pu" if configuracao.unidade == "pu" else "MW"

        mapa_curvas = {
            "ArquivoRotor": ("curva_rotor", "LimiteRotor"),
            "ArquivoSobreExcitacao": ("curva_sobre_excitacao", "LimiteSobreExcitacao"),
            "ArquivoSubExcitacao": ("curva_mel", "MEL"),
            "ArquivoEstabilidade": ("curva_estabilidade", "UEL"),
            "ArquivoEstabilidadePratica": ("curva_estabilidade_pratica", "EstabilidadePratica"),
            # Legado ONS: ArquivoSaturacao = saliência polar
            "ArquivoSaturacao": ("curva_saliencia_polar", "SalienciaPolar"),
            "ArquivoSalienciaPolar": ("curva_saliencia_polar", "SalienciaPolar"),
            "ArquivoSaturacaoMagnetica": ("curva_saturacao", "SaturacaoMagnetica"),
            "ArquivoEstator": ("curva_estator_tabulada", "EstatorSCL"),
            "ArquivoCorrenteCampo": ("curva_corrente_campo", "IFD"),
            "ArquivoCurvaV": ("curva_v", "CurvaV_OCC"),
            "ArquivoAquecimentoExtremo": (
                "curva_aquecimento_extremo",
                "AquecimentoExtremoEstator",
            ),
        }

        for chave_arquivo, (atributo, nome_curva) in mapa_curvas.items():
            if chave_arquivo not in dados or not dados[chave_arquivo]:
                continue
            caminho_csv = self.diretorio / str(dados[chave_arquivo])
            if not caminho_csv.exists():
                # CSV opcional: sem arquivo usa só limites analíticos
                continue
            curva = self.carregar_curva_csv(
                dados[chave_arquivo],
                nome=nome_curva,
                unidade_x=unidade_eixo,
                unidade_y="pu" if configuracao.unidade == "pu" else "Mvar",
                permitir_extrapolacao=dados.get("PermitirExtrapolacao", False),
                referencia=dados.get("Referencia", "Fabricante / IEEE 1110"),
            )
            setattr(configuracao, atributo, curva)

        if "IncluirAquecimentoExtremoNoEnvelope" in dados:
            configuracao.incluir_aquecimento_extremo_no_envelope = bool(
                dados["IncluirAquecimentoExtremoNoEnvelope"]
            )
        if "IncluirSaturacaoMagneticaNoEnvelope" in dados:
            configuracao.incluir_saturacao_magnetica_no_envelope = bool(
                dados["IncluirSaturacaoMagneticaNoEnvelope"]
            )
        if "QAquecimentoExtremoVazioPu" in dados:
            configuracao.q_aquecimento_extremo_vazio_pu = float(
                dados["QAquecimentoExtremoVazioPu"]
            )

        # Compatibilidade: subexcitação = MEL; rotor = OEL pico
        if configuracao.curva_mel and not configuracao.curva_sub_excitacao:
            configuracao.curva_sub_excitacao = configuracao.curva_mel
        if configuracao.curva_rotor and not configuracao.curva_oel_pico:
            configuracao.curva_oel_pico = configuracao.curva_rotor

        return configuracao


def _carregar_json(caminho: Path) -> Dict[str, Any]:
    """Lê JSON ignorando chaves de comentário (iniciadas por _)."""
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    return {chave: valor for chave, valor in dados.items() if not str(chave).startswith("_")}


def _abrir_csv_sem_comentarios(caminho: Path):
    """Abre CSV ignorando linhas em branco e comentários (# ...)."""
    with open(caminho, "r", encoding="utf-8") as arquivo:
        linhas = [
            linha
            for linha in arquivo
            if linha.strip() and not linha.lstrip().startswith("#")
        ]
    return io.StringIO("".join(linhas))


def _obter_valor_coluna(linha: Dict[str, str], nomes_possiveis: List[str]) -> str:
    """Obtém valor de coluna com nomes alternativos."""
    for nome in nomes_possiveis:
        if nome in linha and linha[nome] != "":
            return linha[nome]
    raise KeyError(f"Coluna não encontrada. Esperado uma de: {nomes_possiveis}")


def _remover_duplicatas_abscissa(
    pontos: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """Remove abscissas duplicadas mantendo o último valor (planilha ONS)."""
    if not pontos:
        return pontos
    resultado = [pontos[0]]
    for potencia_ativa, potencia_reativa in pontos[1:]:
        if abs(potencia_ativa - resultado[-1][0]) < 1e-6:
            resultado[-1] = (potencia_ativa, potencia_reativa)
        else:
            resultado.append((potencia_ativa, potencia_reativa))
    return resultado
