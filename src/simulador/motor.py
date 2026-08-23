"""
Motor do simulador de curva de capabilidade.

A curva é construída em p.u. sobre Sn.
As entradas de campo do ponto operacional são preferencialmente em p.u.
(padrão profissional ONS / IEEE / supervisórios).

Referências:
    - ONS BD Anatem v1.6.
    - KUNDUR, P. Power System Stability and Control.
    - IEEE Std 1110-2002.
"""

from typing import Optional

from src.constantes.grandezas import NomeLimite
from src.curvas.avaliador import AvaliadorCurvas, ConfiguracaoCurvas
from src.curvas.construtor import ConstrutorCurvaCapabilidade, PontosCurvaCapabilidade
from src.matematica.eletrica import (
    CorrenteEstator,
    CorrenteEstatorPu,
    FatorPotencia,
    MargemCorrenteEstatorPu,
    PotenciaAparente,
)
from src.curvas.limites.volts_hertz import (
    MargemVoltsHertzPercentual,
    VerificarVoltsHertz,
)
from src.matematica.por_unidade import BasesPorUnidade, CriarBasesCompletas
from src.modelos.gerador import GeradorSincrono
from src.modelos.ponto_operacional import PontoOperacional
from src.modelos.resultado_capabilidade import ResultadoCapabilidade
from src.modelos.turbina import Turbina


class SimuladorCapabilidade:
    """
    Simulador completo da curva de capabilidade.

    Entradas de campo (p.u.) para posicionar a máquina:
        P, Q, Vt, If, Is, f, H
    """

    def __init__(
        self,
        gerador: GeradorSincrono,
        configuracao_curvas: ConfiguracaoCurvas,
        turbina: Optional[Turbina] = None,
    ):
        self.gerador = gerador
        self.turbina = turbina
        self.avaliador = AvaliadorCurvas(gerador, configuracao_curvas, turbina)
        self.construtor = ConstrutorCurvaCapabilidade(self.avaliador)
        self.bases: BasesPorUnidade = CriarBasesCompletas(gerador, turbina)
        # Alinha bases do avaliador (Sn, Vn) com as bases completas
        self.avaliador.bases = self.bases

        self.ponto_operacional = PontoOperacional(
            potencia_ativa=(
                0.0
                if gerador.eh_compensador()
                else gerador.potencia_ativa_nominal * 0.6
            ),
            potencia_reativa=gerador.calcular_potencia_reativa_nominal() * (
                0.5 if gerador.eh_compensador() else 0.3
            ),
            tensao=gerador.tensao_nominal,
            corrente_campo=gerador.corrente_campo_nominal,
            frequencia=gerador.frequencia,
            queda=0.0 if gerador.eh_compensador() or turbina is None else turbina.queda_nominal,
        )
        self._sincronizar_corrente_estator()
        self.pontos_curva: Optional[PontosCurvaCapabilidade] = None
        self.incremento_padrao = 0.01
        # True se o operador informou Is medida (>0); False = Is sempre de S/Vt
        self._is_medida_informada = False

    def obter_imax_estator_pu(self) -> float:
        """Corrente máxima de estator (capacidade SCL) em p.u."""
        imax = self.avaliador.configuracao.corrente_estator_maxima_pu
        if imax <= 0:
            imax = self.avaliador.configuracao.potencia_aparente_maxima
        return imax if imax > 0 else 1.0

    def atualizar_ponto_operacional(
        self,
        potencia_ativa: Optional[float] = None,
        potencia_reativa: Optional[float] = None,
        tensao: Optional[float] = None,
        corrente_estator: Optional[float] = None,
        corrente_campo: Optional[float] = None,
        queda: Optional[float] = None,
        frequencia: Optional[float] = None,
        em_por_unidade: bool = False,
    ) -> None:
        """
        Atualiza grandezas do ponto operacional.

        Se em_por_unidade=True, interpreta entradas em p.u. nas bases:
            P,Q→Sn | Vt→Vn | If→If_FL | Is→In | f→fn | H→Hn
        Caso contrário, usa unidades de engenharia (MW, Mvar, kV, A, Hz, m).

        Is:
            ≤0 ou None → calcula Is = S/(√3·Vt) (ou S/Vt em p.u.)
            >0 → trata como medida de campo (verificação SCL)
        """
        b = self.bases
        if em_por_unidade:
            if potencia_ativa is not None:
                self.ponto_operacional.potencia_ativa = b.potencia_ativa_para_mw(
                    potencia_ativa
                )
            if potencia_reativa is not None:
                self.ponto_operacional.potencia_reativa = b.potencia_reativa_para_mvar(
                    potencia_reativa
                )
            if tensao is not None:
                self.ponto_operacional.tensao = b.tensao_para_kv(tensao)
            if corrente_campo is not None:
                self.ponto_operacional.corrente_campo = b.corrente_campo_para_a(
                    corrente_campo
                )
            if queda is not None:
                self.ponto_operacional.queda = b.queda_para_m(queda)
            if frequencia is not None:
                self.ponto_operacional.frequencia = b.frequencia_para_hz(frequencia)
            if corrente_estator is not None and corrente_estator > 0:
                self.ponto_operacional.corrente_estator = b.corrente_estator_para_a(
                    corrente_estator
                )
                self._is_medida_informada = True
            else:
                self._is_medida_informada = False
                self._sincronizar_corrente_estator()
        else:
            if potencia_ativa is not None:
                self.ponto_operacional.potencia_ativa = potencia_ativa
            if potencia_reativa is not None:
                self.ponto_operacional.potencia_reativa = potencia_reativa
            if tensao is not None:
                self.ponto_operacional.tensao = tensao
            if corrente_campo is not None:
                self.ponto_operacional.corrente_campo = corrente_campo
            if queda is not None:
                self.ponto_operacional.queda = queda
            if frequencia is not None:
                self.ponto_operacional.frequencia = frequencia
            if corrente_estator is not None and corrente_estator > 0:
                self.ponto_operacional.corrente_estator = corrente_estator
                self._is_medida_informada = True
            else:
                self._is_medida_informada = False
                self._sincronizar_corrente_estator()

        # Se P/Q/Vt mudaram com Is medida, mantém medida; senão recalcula
        if not self._is_medida_informada:
            self._sincronizar_corrente_estator()

    def _sincronizar_corrente_estator(self) -> None:
        """Calcula Is a partir de S e Vt (identidade elétrica)."""
        ponto = self.ponto_operacional
        s = PotenciaAparente(ponto.potencia_ativa, ponto.potencia_reativa)
        if ponto.tensao > 0 and s >= 0:
            ponto.corrente_estator = CorrenteEstator(s, ponto.tensao) if s > 0 else 0.0

    def obter_ponto_operacional_pu(self) -> tuple:
        """Retorna (P_pu, Q_pu, V_pu) - compatibilidade."""
        grandezas = self.obter_grandezas_campo_pu()
        return (grandezas["P"], grandezas["Q"], grandezas["Vt"])

    def obter_grandezas_campo_pu(self) -> dict:
        """
        Entradas de campo em p.u.

        Is_calc = S/Vt (sempre). Is = medida se informada, senão Is_calc.
        Imax = corrente máxima SCL (capacidade).
        """
        ponto = self.ponto_operacional
        b = self.bases
        p_pu = b.potencia_ativa_para_pu(ponto.potencia_ativa)
        q_pu = b.potencia_reativa_para_pu(ponto.potencia_reativa)
        vt_pu = b.tensao_para_pu(ponto.tensao)
        s_pu = PotenciaAparente(p_pu, q_pu)
        fp = FatorPotencia(p_pu, s_pu) if s_pu > 0 else 0.0
        is_calc = CorrenteEstatorPu(s_pu, vt_pu)
        is_armazenada = b.corrente_estator_para_pu(ponto.corrente_estator)
        if self._is_medida_informada and is_armazenada > 0:
            is_pu = is_armazenada
            is_origem = "medida"
        else:
            is_pu = is_calc
            is_origem = "calculada"
        imax = self.obter_imax_estator_pu()
        cfg = self.avaliador.configuracao
        vhz_max = cfg.relacao_volts_hertz_maxima_pu
        vhz_ok, vhz_pu, msg_vhz = VerificarVoltsHertz(
            vt_pu,
            b.frequencia_para_pu(ponto.frequencia),
            vhz_max,
            cfg.relacao_volts_hertz_minima_pu,
        )
        return {
            "P": p_pu,
            "Q": q_pu,
            "Vt": vt_pu,
            "If": b.corrente_campo_para_pu(ponto.corrente_campo),
            "Is": is_pu,
            "Is_calc": is_calc,
            "Is_origem": is_origem,
            "Imax": imax,
            "margem_Is": MargemCorrenteEstatorPu(is_pu, imax),
            "f": b.frequencia_para_pu(ponto.frequencia),
            "H": b.queda_para_pu(ponto.queda),
            "S": s_pu,
            "fator_potencia": fp,
            "VHz": vhz_pu,
            "VHz_max": vhz_max,
            "VHz_ok": vhz_ok,
            "margem_VHz": MargemVoltsHertzPercentual(
                vt_pu, b.frequencia_para_pu(ponto.frequencia), vhz_max
            ),
            "mensagem_VHz": msg_vhz,
        }

    def recalcular_curva(
        self,
        potencia_minima: Optional[float] = None,
        potencia_maxima: Optional[float] = None,
        incremento: Optional[float] = None,
    ) -> PontosCurvaCapabilidade:
        """Recalcula a curva com Vt, If, H e Imax do ponto / configuração."""
        potencia_min = potencia_minima if potencia_minima is not None else 0.0
        potencia_max = (
            potencia_maxima
            if potencia_maxima is not None
            else self.avaliador.obter_potencia_ativa_maxima(self.ponto_operacional.queda)
        )
        passo = incremento if incremento is not None else self.incremento_padrao

        grandezas = self.obter_grandezas_campo_pu()
        if self.avaliador.configuracao.unidade != "pu":
            tensao_terminal = self.ponto_operacional.tensao
        else:
            tensao_terminal = grandezas["Vt"]

        self.pontos_curva = self.construtor.gerar_pontos(
            potencia_min,
            potencia_max,
            passo,
            tensao_terminal,
            self.ponto_operacional.queda,
            self.ponto_operacional.corrente_campo,
            corrente_estator_operacao_pu=grandezas["Is"],
            corrente_estator_maxima_pu=grandezas["Imax"],
            frequencia_pu=grandezas["f"],
        )
        return self.pontos_curva

    def verificar_capabilidade(self) -> ResultadoCapabilidade:
        """Verifica se o ponto operacional está dentro da curva."""
        ponto = self.ponto_operacional
        if not self._is_medida_informada:
            self._sincronizar_corrente_estator()

        grandezas = self.obter_grandezas_campo_pu()
        potencia_ativa_pu = grandezas["P"]
        potencia_reativa_pu = grandezas["Q"]
        tensao_pu = grandezas["Vt"]
        is_pu = grandezas["Is"]
        is_calc = grandezas["Is_calc"]
        imax = grandezas["Imax"]
        s_pu = grandezas["S"]

        if self.avaliador.configuracao.unidade == "pu":
            potencia_ativa_calc = potencia_ativa_pu
            potencia_reativa_calc = potencia_reativa_pu
            tensao_calc = tensao_pu
            base_margem = 1.0
        else:
            potencia_ativa_calc = ponto.potencia_ativa
            potencia_reativa_calc = ponto.potencia_reativa
            tensao_calc = ponto.tensao
            base_margem = self.gerador.potencia_nominal

        # Envelope de capacidade: SCL com Imax; OEL deratado por V/Hz (f)
        envelope = self.avaliador.calcular_envelope(
            potencia_ativa_calc,
            tensao_calc,
            ponto.queda,
            ponto.corrente_campo,
            corrente_estator_maxima_pu=imax,
            frequencia_pu=grandezas["f"],
        )

        potencia_aparente = PotenciaAparente(
            ponto.potencia_ativa, ponto.potencia_reativa
        )
        fator_potencia = FatorPotencia(ponto.potencia_ativa, potencia_aparente)

        p_min = self.avaliador.obter_potencia_ativa_minima()
        p_max = self.avaliador.obter_potencia_ativa_maxima(ponto.queda)
        # P também limitado pelo círculo S = Vt·Imax
        p_max_scl = tensao_calc * imax if self.avaliador.configuracao.unidade == "pu" else (
            self.bases.potencia_ativa_para_mw(tensao_pu * imax)
        )
        potencia_mecanica_ok = (
            envelope.potencia_mecanica_ok
            and p_min - 1e-9 <= potencia_ativa_calc <= p_max + 1e-9
        )
        q_ok = (
            envelope.regiao_valida
            and envelope.limite_inferior_efetivo
            <= potencia_reativa_calc
            <= envelope.limite_superior_efetivo
        )
        # SCL: Is ≤ Imax  e  S ≤ Vt·Imax (equivalentes se Is = S/Vt)
        is_ok = is_pu <= imax + 1e-6
        s_ok = s_pu <= tensao_pu * imax + 1e-6
        scl_ok = is_ok and s_ok
        vhz_ok = bool(grandezas["VHz_ok"])

        dentro = potencia_mecanica_ok and q_ok and scl_ok and vhz_ok

        distancias = _calcular_distancias_limites(potencia_reativa_calc, envelope)
        if not potencia_mecanica_ok:
            margem = 0.0
            if potencia_ativa_calc > p_max + 1e-9:
                limite_restritivo = NomeLimite.PMEC_MAX
            elif potencia_ativa_calc < p_min - 1e-9:
                limite_restritivo = NomeLimite.PMEC_MIN
            else:
                limite_restritivo = NomeLimite.PMEC_MAX
        elif not vhz_ok:
            margem = 0.0
            limite_restritivo = NomeLimite.VOLTS_HERTZ
        elif not scl_ok:
            margem = 0.0
            limite_restritivo = NomeLimite.ESTATOR
        elif not envelope.regiao_valida:
            margem = 0.0
            limite_restritivo = envelope.limite_superior_restritivo
        else:
            margem = _calcular_margem_operacional(
                potencia_reativa_calc, envelope, base_margem
            )
            margem = min(margem, grandezas["margem_Is"], grandezas["margem_VHz"])
            limite_restritivo = _identificar_limite_restritivo(
                potencia_reativa_calc, envelope
            )

        resultado = ResultadoCapabilidade(
            dentro_da_curva=dentro,
            margem_operacional=margem,
            limite_restritivo=limite_restritivo,
            limites_superiores=envelope.limites_superiores,
            limites_inferiores=envelope.limites_inferiores,
            limite_superior_efetivo=envelope.limite_superior_efetivo,
            limite_inferior_efetivo=envelope.limite_inferior_efetivo,
            potencia_aparente=potencia_aparente,
            fator_potencia=fator_potencia,
            distancias_limites=distancias,
        )
        resultado.mensagens.append(
            "Campo (pu): "
            f"P={grandezas['P']:.4f}, Q={grandezas['Q']:.4f}, "
            f"Vt={grandezas['Vt']:.4f}, If={grandezas['If']:.4f}, "
            f"Is={grandezas['Is']:.4f} ({grandezas['Is_origem']}), "
            f"Imax={imax:.4f}, f={grandezas['f']:.4f}, "
            f"H={grandezas['H']:.4f}"
        )
        resultado.mensagens.append(
            f"SCL: Is_calc={is_calc:.4f} pu | S={s_pu:.4f} | "
            f"Vt·Imax={tensao_pu * imax:.4f} | margem Is={grandezas['margem_Is']:.1f} %"
        )
        resultado.mensagens.append(
            f"V/Hz: {grandezas['VHz']:.4f} pu "
            f"(máx={grandezas['VHz_max']:.4f}) | "
            f"margem={grandezas['margem_VHz']:.1f}% | "
            f"derating OEL={envelope.fator_derating_volts_hertz:.3f}"
        )
        if not vhz_ok and grandezas["mensagem_VHz"]:
            resultado.mensagens.append(grandezas["mensagem_VHz"])
        if (
            self._is_medida_informada
            and abs(is_pu - is_calc) > 0.02
        ):
            resultado.mensagens.append(
                f"Aviso: Is medida ({is_pu:.4f}) difere de S/Vt ({is_calc:.4f})."
            )
        if not envelope.regiao_valida and potencia_mecanica_ok:
            resultado.mensagens.append(
                "Envelope inválido: Qsup < Qinf (sem região permitida neste P)."
            )
        if not potencia_mecanica_ok:
            resultado.mensagens.append(
                f"P fora da faixa Pmec [{p_min:.4f}, {p_max:.4f}] pu "
                f"(SCL P≤{tensao_pu * imax:.4f})."
            )
        if not scl_ok:
            resultado.mensagens.append(
                f"SCL violado: Is={is_pu:.4f} pu > Imax={imax:.4f} pu "
                f"ou S > Vt·Imax."
            )
        if not dentro:
            resultado.mensagens.append(
                "Ponto operacional fora da região permitida da curva de capabilidade."
            )
        return resultado

    def executar_simulacao_completa(self) -> dict:
        """Executa recálculo da curva e verificação do ponto operacional."""
        pontos = self.recalcular_curva()
        resultado = self.verificar_capabilidade()
        return {
            "PontoOperacional": self.ponto_operacional,
            "PontoOperacionalPu": self.obter_ponto_operacional_pu(),
            "GrandezasCampoPu": self.obter_grandezas_campo_pu(),
            "ResultadoCapabilidade": resultado,
            "PontosCurva": pontos,
            "Bases": self.bases,
        }


def _calcular_distancias_limites(potencia_reativa: float, envelope) -> dict:
    distancias = {}
    for nome, valor in envelope.limites_superiores.items():
        distancias[nome] = valor - potencia_reativa
    for nome, valor in envelope.limites_inferiores.items():
        distancias[nome] = potencia_reativa - valor
    return distancias


def _calcular_margem_operacional(potencia_reativa, envelope, potencia_base: float) -> float:
    distancia_superior = envelope.limite_superior_efetivo - potencia_reativa
    distancia_inferior = potencia_reativa - envelope.limite_inferior_efetivo
    menor_distancia = min(distancia_superior, distancia_inferior)
    if potencia_base <= 0:
        potencia_base = 1.0
    margem = (menor_distancia / potencia_base) * 100.0
    return max(0.0, margem)


def _identificar_limite_restritivo(potencia_reativa, envelope) -> Optional[NomeLimite]:
    if potencia_reativa > envelope.limite_superior_efetivo:
        return envelope.limite_superior_restritivo
    if potencia_reativa < envelope.limite_inferior_efetivo:
        return envelope.limite_inferior_restritivo

    distancia_superior = envelope.limite_superior_efetivo - potencia_reativa
    distancia_inferior = potencia_reativa - envelope.limite_inferior_efetivo

    if distancia_superior <= distancia_inferior:
        return envelope.limite_superior_restritivo
    return envelope.limite_inferior_restritivo
