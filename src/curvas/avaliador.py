"""
Avaliador do traçado operacional da curva de capabilidade.

Composição alinhada ao traçado operacional (ONS BD Anatem / IEEE Std 1110):

    Pmec_Min ≤ P ≤ Pmec_Max
    Q_inf(P, Vt) ≤ Q ≤ Q_sup(P, Vt)

    Q_sup = min( OEL_TH(Vt, If), SCL/estator(Vt)[, saturação magnética] )
    Q_inf = max( UEL, MEL, estator_min(Vt)[, UEL prático][, saliência]
                 [, aquecimento extremo] )

    Dependência da tensão de barramento Vt e da corrente de campo If:
        Estator:  Q = ±sqrt((Vt·Imax)² - P²)
        Campo:    Q = -Vt²/Xd + sqrt((Vt·Efd(If)/Xd)² - P²)
        Efd(If) via OCC / If_NL (IEEE 1110)

Referências:
    - ONS BD Anatem v1.6 - Pmec Max, UEL ATIVO, Tensão.
    - KUNDUR, P. Power System Stability and Control. Seção 3.4.
    - IEEE Std 1110-2002.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from src.constantes.grandezas import NomeLimite
from src.curvas.limites.analiticos_tensao import (
    CalcularLimiteCampoPorTensao,
    CalcularLimiteEstatorPorTensao,
    CalcularFatorCorrenteCampo,
    CalcularTensaoInternaPorCorrenteCampo,
    EstimarTensaoInternaMaxima,
)
from src.curvas.limites.aquecimento_extremo import (
    CalcularLimiteAquecimentoExtremoEstator,
)
from src.curvas.limites.escala_tensao import (
    EscalarLimiteQPorTensao,
    EscalarLimiteQPorTensaoQuadratica,
    TensaoProximaDaReferencia,
)
from src.curvas.limites.estabilidade import CalcularLimiteEstabilidade
from src.curvas.limites.estator_tabulado import CalcularLimiteEstatorTabulado
from src.curvas.limites.rotor import CalcularLimiteSobreExcitacao
from src.curvas.limites.saliencia_polar import CalcularLimiteSalienciaPolar
from src.curvas.limites.saturacao import CalcularLimiteSaturacao
from src.curvas.limites.subexcitacao import CalcularLimiteSubExcitacao
from src.curvas.limites.turbina import (
    CalcularPotenciaHidraulicaPorQueda,
    CalcularTetoPotenciaTurbina,
)
from src.curvas.limites.volts_hertz import (
    CalcularFatorDeratingVoltsHertz,
    CalcularRelacaoVoltsHertz,
)
from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.matematica.por_unidade import BasesPorUnidade, CriarBasesDoGerador
from src.modelos.gerador import GeradorSincrono
from src.modelos.tabela_curva import TabelaCurva
from src.modelos.turbina import Turbina


@dataclass
class ConfiguracaoCurvas:
    """Configuração das curvas e do traçado operacional (p.u. sobre Sn)."""

    curva_rotor: Optional[TabelaCurva] = None
    curva_sobre_excitacao: Optional[TabelaCurva] = None
    curva_sub_excitacao: Optional[TabelaCurva] = None
    curva_estabilidade: Optional[TabelaCurva] = None
    curva_estabilidade_pratica: Optional[TabelaCurva] = None
    curva_saliencia_polar: Optional[TabelaCurva] = None
    curva_estator_tabulada: Optional[TabelaCurva] = None
    curva_mel: Optional[TabelaCurva] = None
    curva_oel_pico: Optional[TabelaCurva] = None
    curva_corrente_campo: Optional[TabelaCurva] = None
    curva_v: Optional[TabelaCurva] = None  # OCC: If → Efd
    curva_saturacao: Optional[TabelaCurva] = None  # saturação magnética (Qsup)
    curva_aquecimento_extremo: Optional[TabelaCurva] = None

    potencia_aparente_maxima: float = 1.0
    potencia_ativa_maxima: float = 0.9
    potencia_mecanica_maxima_pu: float = 0.9
    potencia_mecanica_minima_pu: float = 0.0
    corrente_estator_maxima_pu: float = 1.0  # Imax SCL (capacidade)
    tensao_referencia_curvas: float = 1.0
    # V/Hz (sobrefluxo): típico 1,05 pu (IEEE / AVR)
    relacao_volts_hertz_maxima_pu: float = 1.05
    relacao_volts_hertz_minima_pu: float = 0.0  # 0 = desliga piso
    derating_oel_por_volts_hertz: bool = True
    unidade: str = "pu"
    base_potencia_aparente: float = 0.0
    incluir_saliencia_no_envelope: bool = False
    incluir_aquecimento_extremo_no_envelope: Optional[bool] = None
    incluir_saturacao_magnetica_no_envelope: bool = True
    q_aquecimento_extremo_vazio_pu: float = -0.45


@dataclass
class EnvelopeCapabilidade:
    """Envelope de capabilidade em um valor de P (p.u.)."""

    potencia_ativa: float
    limite_superior_efetivo: float
    limite_inferior_efetivo: float
    limites_superiores: Dict[NomeLimite, float] = field(default_factory=dict)
    limites_inferiores: Dict[NomeLimite, float] = field(default_factory=dict)
    limite_superior_restritivo: Optional[NomeLimite] = None
    limite_inferior_restritivo: Optional[NomeLimite] = None
    tensao_terminal_pu: float = 1.0
    regiao_valida: bool = True
    potencia_mecanica_ok: bool = True
    frequencia_pu: float = 1.0
    relacao_volts_hertz_pu: float = 1.0
    fator_derating_volts_hertz: float = 1.0


class AvaliadorCurvas:
    """Avalia o traçado operacional completo com dependência de Vt."""

    def __init__(
        self,
        gerador: GeradorSincrono,
        configuracao: ConfiguracaoCurvas,
        turbina: Optional[Turbina] = None,
    ):
        self.gerador = gerador
        self.configuracao = configuracao
        self.turbina = turbina
        self.bases = CriarBasesDoGerador(
            gerador.potencia_nominal,
            gerador.tensao_nominal,
        )

        if configuracao.base_potencia_aparente <= 0:
            self.configuracao.base_potencia_aparente = gerador.potencia_nominal
        if configuracao.potencia_mecanica_maxima_pu <= 0 and not gerador.eh_compensador():
            self.configuracao.potencia_mecanica_maxima_pu = gerador.fator_potencia_nominal
        if configuracao.potencia_ativa_maxima <= 0:
            self.configuracao.potencia_ativa_maxima = (
                self.configuracao.potencia_mecanica_maxima_pu
            )
        if configuracao.potencia_aparente_maxima <= 0:
            self.configuracao.potencia_aparente_maxima = 1.0
        if configuracao.corrente_estator_maxima_pu <= 0:
            self.configuracao.corrente_estator_maxima_pu = (
                self.configuracao.potencia_aparente_maxima
            )
        if configuracao.incluir_aquecimento_extremo_no_envelope is None:
            # No envelope só com curva de fabricante; analítico fica como referência de plot
            self.configuracao.incluir_aquecimento_extremo_no_envelope = (
                configuracao.curva_aquecimento_extremo is not None
            )

        self._tensao_interna_maxima = self._estimar_efd_maxima()

    def _estimar_efd_maxima(self) -> float:
        """Estima Efd_max a partir da curva OEL em P=0 (Vt_ref)."""
        curva = self.configuracao.curva_sobre_excitacao or self.configuracao.curva_rotor
        vt_ref = self.configuracao.tensao_referencia_curvas
        xd = max(self.gerador.reatancia_direta, 0.1)

        if curva and curva.pontos:
            q_vazio = InterpolarPorSegmentos(
                curva.obter_abscissas(),
                curva.obter_ordenadas(),
                0.0,
                False,
            )
            return EstimarTensaoInternaMaxima(q_vazio, vt_ref, xd)
        return 1.6

    def obter_bases(self) -> BasesPorUnidade:
        return self.bases

    def obter_potencia_ativa_maxima(self, queda_atual: float = 0.0) -> float:
        """
        Retorna P máxima da região permitida em p.u.

        Apenas a Pmec máxima configurada restringe o envelope operacional.
        Queda útil e teto da turbina são referências de plotagem (não limitam).
        """
        del queda_atual  # H não impacta a região permitida
        return self.configuracao.potencia_mecanica_maxima_pu

    def obter_limites_potencia_ativa_horizontais(
        self, queda_atual: float = 0.0
    ) -> dict:
        """
        Retas horizontais de potência ativa no diagrama P–Q.

        Restritivos (definem a região permitida):
            LimitePmecMax / LimitePmecMin

        Referência (informativos; não cortam o envelope):
            LimiteQuedaUtil - P disponível pela H atual (pode ficar fora da região)
            LimiteTurbinaMax / LimiteTurbinaMin - tetos/pisos da turbina
        """
        sn = (
            self.configuracao.base_potencia_aparente
            or self.gerador.potencia_nominal
        )
        limites: dict = {}

        pmec_max = self.configuracao.potencia_mecanica_maxima_pu
        if pmec_max > 0:
            limites[NomeLimite.PMEC_MAX.value] = pmec_max

        pmec_min = self.configuracao.potencia_mecanica_minima_pu
        if pmec_min > 1e-9:
            limites[NomeLimite.PMEC_MIN.value] = pmec_min

        if self.turbina is None:
            return limites

        queda = queda_atual if queda_atual > 0 else self.turbina.queda_nominal
        limites[NomeLimite.QUEDA_UTIL.value] = CalcularPotenciaHidraulicaPorQueda(
            self.turbina,
            queda,
            em_por_unidade=True,
            potencia_aparente_base=sn,
        )

        teto = CalcularTetoPotenciaTurbina(
            self.turbina,
            em_por_unidade=True,
            potencia_aparente_base=sn,
        )
        if teto is not None and teto > 0:
            limites[NomeLimite.TURBINA_MAX.value] = teto

        if self.turbina.potencia_minima > 1e-9 and sn > 0:
            limites[NomeLimite.TURBINA_MIN.value] = self.turbina.potencia_minima / sn

        return limites

    def obter_potencia_ativa_minima(self) -> float:
        """P mínima da região permitida - só Pmec mínima configurada."""
        return self.configuracao.potencia_mecanica_minima_pu

    def calcular_envelope(
        self,
        potencia_ativa: float,
        tensao_terminal: float,
        queda_atual: float = 0.0,
        corrente_campo: float = 0.0,
        respeitar_limite_potencia_mecanica: bool = True,
        corrente_estator_maxima_pu: float = 1.0,
        frequencia_pu: float = 1.0,
        modo_referencia: bool = False,
    ) -> EnvelopeCapabilidade:
        """
        Calcula o envelope operacional de Q para P, Vt, If e f.

        frequencia_pu:
            Frequência em p.u. (fn). Usada no derating V/Hz do OEL.
        modo_referencia:
            Se True, calcula limites individuais mesmo fora de Pmec e do
            círculo S (para plotar OEL/UEL além da faixa operacional).
        """
        vt = tensao_terminal if tensao_terminal > 0 else 1.0
        f_pu = frequencia_pu if frequencia_pu > 1e-9 else 1.0
        vt_ref = self.configuracao.tensao_referencia_curvas
        vhz_max = self.configuracao.relacao_volts_hertz_maxima_pu
        fator_vhz = (
            CalcularFatorDeratingVoltsHertz(vt, f_pu, vhz_max)
            if self.configuracao.derating_oel_por_volts_hertz
            else 1.0
        )
        vhz_pu = CalcularRelacaoVoltsHertz(vt, f_pu)

        p_min = self.obter_potencia_ativa_minima()
        p_max = self.obter_potencia_ativa_maxima(queda_atual)
        pmec_ok = p_min - 1e-9 <= potencia_ativa <= p_max + 1e-9

        if not pmec_ok and respeitar_limite_potencia_mecanica and not modo_referencia:
            restritivo = (
                NomeLimite.PMEC_MAX
                if potencia_ativa > p_max + 1e-9
                else NomeLimite.PMEC_MIN
            )
            return EnvelopeCapabilidade(
                potencia_ativa=potencia_ativa,
                limite_superior_efetivo=0.0,
                limite_inferior_efetivo=0.0,
                limite_superior_restritivo=restritivo,
                limite_inferior_restritivo=restritivo,
                tensao_terminal_pu=vt,
                regiao_valida=False,
                potencia_mecanica_ok=False,
                frequencia_pu=f_pu,
                relacao_volts_hertz_pu=vhz_pu,
                fator_derating_volts_hertz=fator_vhz,
            )

        xd = max(self.gerador.reatancia_direta, 0.1)
        i_max = corrente_estator_maxima_pu if corrente_estator_maxima_pu > 0 else 1.0
        raio_estator = vt * i_max

        # P ≥ Vt·Imax: sem área operacional (ápice). Em modo referência continua
        # calculando OEL/UEL para plot além do círculo S.
        if potencia_ativa >= raio_estator - 1e-9 and not modo_referencia:
            no_apice = abs(potencia_ativa - raio_estator) <= 1e-6
            return EnvelopeCapabilidade(
                potencia_ativa=potencia_ativa,
                limite_superior_efetivo=0.0,
                limite_inferior_efetivo=0.0,
                limite_superior_restritivo=NomeLimite.ESTATOR,
                limite_inferior_restritivo=NomeLimite.ESTATOR,
                tensao_terminal_pu=vt,
                regiao_valida=no_apice,
                potencia_mecanica_ok=pmec_ok,
                frequencia_pu=f_pu,
                relacao_volts_hertz_pu=vhz_pu,
                fator_derating_volts_hertz=fator_vhz,
            )

        fator_campo = CalcularFatorCorrenteCampo(
            corrente_campo,
            self.gerador.corrente_campo_nominal,
        )
        efd_efetivo = CalcularTensaoInternaPorCorrenteCampo(
            corrente_campo if corrente_campo > 0 else self.gerador.corrente_campo_nominal,
            self.gerador.corrente_campo_nominal,
            self._tensao_interna_maxima,
            self.gerador.corrente_campo_vazio,
            curva_occ=self.configuracao.curva_v,
        )

        q_estator_min, q_estator_max = CalcularLimiteEstatorPorTensao(
            potencia_ativa, vt, i_max
        )

        # --- OEL TH: tabular só em Vt≈Vt_ref; fora disso usa analítico (Kundur) ---
        # Escala circular NÃO se aplica ao arco de campo (centro em −Vt²/Xd).
        q_oel_tab = CalcularLimiteSobreExcitacao(
            potencia_ativa,
            self.configuracao.curva_sobre_excitacao or self.configuracao.curva_rotor,
            self.gerador,
            em_por_unidade=True,
        )
        q_oel_analitico = CalcularLimiteCampoPorTensao(
            potencia_ativa, vt, xd, efd_efetivo
        )
        q_oel_th = self._combinar_oel_th(
            q_oel_tab, q_oel_analitico, vt, vt_ref, fator_campo
        )
        # Derating V/Hz no OEL (sobrefluxo reduz capacidade de sobre-excitação)
        if fator_vhz < 1.0 - 1e-9 and q_oel_th not in (float("inf"), float("-inf")):
            q_oel_th = q_oel_th * fator_vhz

        # OEL PK / IFD: tabulares em Vt_ref; em Vt≠Vt_ref só referência plotável
        # sem escala circular (evita Q=0 artificial).
        vt_ok_tab = TensaoProximaDaReferencia(vt, vt_ref)
        q_oel_pk = float("inf")
        if self.configuracao.curva_oel_pico and self.configuracao.curva_oel_pico.pontos:
            q_oel_pk_tab = CalcularLimiteSobreExcitacao(
                potencia_ativa,
                self.configuracao.curva_oel_pico,
                self.gerador,
                em_por_unidade=True,
            )
            if vt_ok_tab:
                q_oel_pk = q_oel_pk_tab
            elif q_oel_pk_tab not in (float("inf"), float("-inf")):
                q_oel_pk = (
                    max(q_oel_pk_tab, q_oel_analitico)
                    if q_oel_analitico > float("-inf")
                    else q_oel_pk_tab
                )
            if fator_vhz < 1.0 - 1e-9 and q_oel_pk < float("inf"):
                q_oel_pk = q_oel_pk * fator_vhz

        q_ifd = float("inf")
        if (
            self.configuracao.curva_corrente_campo
            and self.configuracao.curva_corrente_campo.pontos
        ):
            q_ifd_tab = CalcularLimiteSobreExcitacao(
                potencia_ativa,
                self.configuracao.curva_corrente_campo,
                self.gerador,
                em_por_unidade=True,
            )
            # IFD é referência de plot; em Vt≠ref usa valor tab sem forçar Q=0
            q_ifd = q_ifd_tab

        # SCL tabulado ∩ estator analítico (escala circular correta para SCL)
        q_scl = CalcularLimiteEstatorTabulado(
            potencia_ativa, self.configuracao.curva_estator_tabulada
        )
        if q_scl < 9000:
            q_scl_esc = EscalarLimiteQPorTensao(q_scl, potencia_ativa, vt, vt_ref)
            if q_scl_esc < float("inf"):
                q_estator_efetivo = min(q_estator_max, q_scl_esc)
            else:
                q_estator_efetivo = q_estator_max
        else:
            q_estator_efetivo = q_estator_max

        # Saturação magnética
        q_sat_mag = CalcularLimiteSaturacao(
            potencia_ativa, self.configuracao.curva_saturacao
        )
        if q_sat_mag < float("inf") and vt_ok_tab:
            pass  # mantém tab
        elif q_sat_mag < float("inf"):
            q_sat_mag = EscalarLimiteQPorTensaoQuadratica(q_sat_mag, vt, vt_ref)

        limites_superiores: Dict[NomeLimite, float] = {
            NomeLimite.ESTATOR: q_estator_efetivo,
            NomeLimite.SOBRE_EXCITACAO: q_oel_th,
        }
        if q_oel_pk not in (float("inf"), float("-inf")):
            limites_superiores[NomeLimite.ROTOR] = q_oel_pk
        if q_ifd not in (float("inf"), float("-inf")):
            limites_superiores[NomeLimite.CORRENTE_CAMPO] = q_ifd
        if q_sat_mag < float("inf"):
            limites_superiores[NomeLimite.SATURACAO_MAGNETICA] = q_sat_mag

        # UEL, MEL, UEL prático
        q_uel = CalcularLimiteEstabilidade(
            potencia_ativa,
            self.configuracao.curva_estabilidade,
            self.gerador,
            vt,
            em_por_unidade=True,
            tensao_referencia=vt_ref,
        )
        q_mel = CalcularLimiteSubExcitacao(
            potencia_ativa,
            self.configuracao.curva_mel or self.configuracao.curva_sub_excitacao,
            self.gerador,
            em_por_unidade=True,
        )
        # MEL: escala V² (não circular - evita muro em Q=0)
        if self.configuracao.curva_mel or self.configuracao.curva_sub_excitacao:
            q_mel = EscalarLimiteQPorTensaoQuadratica(q_mel, vt, vt_ref)

        limites_inferiores: Dict[NomeLimite, float] = {
            NomeLimite.ESTATOR: q_estator_min,
            NomeLimite.ESTABILIDADE: q_uel,
            NomeLimite.SUB_EXCITACAO: q_mel,
        }

        if (
            self.configuracao.curva_estabilidade_pratica
            and self.configuracao.curva_estabilidade_pratica.pontos
        ):
            q_pratica = CalcularLimiteEstabilidade(
                potencia_ativa,
                self.configuracao.curva_estabilidade_pratica,
                self.gerador,
                vt,
                em_por_unidade=True,
                tensao_referencia=vt_ref,
            )
            if q_pratica not in (float("inf"), float("-inf")):
                limites_inferiores[NomeLimite.ESTABILIDADE_PRATICA] = q_pratica

        if (
            self.configuracao.curva_saliencia_polar
            and self.configuracao.curva_saliencia_polar.pontos
        ):
            q_saliencia = CalcularLimiteSalienciaPolar(
                potencia_ativa, self.configuracao.curva_saliencia_polar
            )
            if q_saliencia > -9000:
                q_saliencia = EscalarLimiteQPorTensaoQuadratica(
                    q_saliencia, vt, vt_ref
                )
                limites_inferiores[NomeLimite.SATURACAO] = q_saliencia

        # Aquecimento extremo de estator (leading PF)
        q_extremo = CalcularLimiteAquecimentoExtremoEstator(
            potencia_ativa,
            vt,
            self.configuracao.curva_aquecimento_extremo,
            self.configuracao.q_aquecimento_extremo_vazio_pu,
        )
        if q_extremo > float("-inf"):
            limites_inferiores[NomeLimite.AQUECIMENTO_EXTREMO] = q_extremo

        limites_superiores = {
            k: v
            for k, v in limites_superiores.items()
            if v not in (float("inf"), float("-inf"))
        }
        limites_inferiores = {
            k: v
            for k, v in limites_inferiores.items()
            if v not in (float("inf"), float("-inf"))
        }

        # Envelope contínuo ONS / IEEE
        candidatos_sup = [NomeLimite.ESTATOR, NomeLimite.SOBRE_EXCITACAO]
        if fator_campo > 1.001 and NomeLimite.ROTOR in limites_superiores:
            candidatos_sup.append(NomeLimite.ROTOR)
        if (
            self.configuracao.incluir_saturacao_magnetica_no_envelope
            and NomeLimite.SATURACAO_MAGNETICA in limites_superiores
        ):
            candidatos_sup.append(NomeLimite.SATURACAO_MAGNETICA)

        limites_sup_envelope = {
            k: limites_superiores[k] for k in candidatos_sup if k in limites_superiores
        }
        if limites_sup_envelope:
            limite_superior_efetivo = min(limites_sup_envelope.values())
        else:
            limite_superior_efetivo = float("-inf")

        candidatos_inf = [
            NomeLimite.ESTATOR,
            NomeLimite.ESTABILIDADE,
            NomeLimite.SUB_EXCITACAO,
        ]
        if NomeLimite.ESTABILIDADE_PRATICA in limites_inferiores:
            candidatos_inf.append(NomeLimite.ESTABILIDADE_PRATICA)
        if (
            self.configuracao.incluir_saliencia_no_envelope
            and NomeLimite.SATURACAO in limites_inferiores
        ):
            candidatos_inf.append(NomeLimite.SATURACAO)
        if (
            self.configuracao.incluir_aquecimento_extremo_no_envelope
            and NomeLimite.AQUECIMENTO_EXTREMO in limites_inferiores
        ):
            candidatos_inf.append(NomeLimite.AQUECIMENTO_EXTREMO)

        limites_inf_envelope = {
            k: limites_inferiores[k] for k in candidatos_inf if k in limites_inferiores
        }
        if limites_inf_envelope:
            limite_inferior_efetivo = max(limites_inf_envelope.values())
        else:
            limite_inferior_efetivo = float("inf")

        # Clipagem dura ao círculo do estator (evita UEL/MEL/OEL fora de S=Vt·Imax)
        if q_estator_max < float("inf"):
            limite_superior_efetivo = min(limite_superior_efetivo, q_estator_max)
            limites_superiores[NomeLimite.ESTATOR] = q_estator_max
            limites_sup_envelope[NomeLimite.ESTATOR] = q_estator_max
        if q_estator_min > float("-inf"):
            limite_inferior_efetivo = max(limite_inferior_efetivo, q_estator_min)
            limites_inferiores[NomeLimite.ESTATOR] = q_estator_min
            limites_inf_envelope[NomeLimite.ESTATOR] = q_estator_min

        regiao_valida = limite_superior_efetivo >= limite_inferior_efetivo - 1e-9

        return EnvelopeCapabilidade(
            potencia_ativa=potencia_ativa,
            limite_superior_efetivo=limite_superior_efetivo,
            limite_inferior_efetivo=limite_inferior_efetivo,
            limites_superiores=limites_superiores,
            limites_inferiores=limites_inferiores,
            limite_superior_restritivo=_encontrar_limite_restritivo(
                limites_sup_envelope, limite_superior_efetivo, True
            ),
            limite_inferior_restritivo=_encontrar_limite_restritivo(
                limites_inf_envelope, limite_inferior_efetivo, False
            ),
            tensao_terminal_pu=vt,
            regiao_valida=regiao_valida,
            potencia_mecanica_ok=pmec_ok,
            frequencia_pu=f_pu,
            relacao_volts_hertz_pu=vhz_pu,
            fator_derating_volts_hertz=fator_vhz,
        )

    def _combinar_oel_th(
        self,
        q_oel_tab: float,
        q_oel_analitico: float,
        vt: float,
        vt_ref: float,
        fator_campo: float,
    ) -> float:
        """
        Combina OEL tabular com analítico Efd(If, Vt).

        - Vt ≈ Vt_ref e If ≤ If_FL: min(tab, analítico)
        - Vt ≠ Vt_ref: só analítico (física correta do arco de campo)
        - If > If_FL: analítico (curto prazo; PK no envelope via candidatos)
        """
        tem_tab = q_oel_tab not in (float("inf"), float("-inf")) and q_oel_tab < 9000
        tem_ana = q_oel_analitico > float("-inf")
        vt_ok = TensaoProximaDaReferencia(vt, vt_ref)

        if fator_campo > 1.001 and tem_ana:
            return q_oel_analitico

        if vt_ok and tem_tab and tem_ana:
            return min(q_oel_tab, q_oel_analitico)
        if vt_ok and tem_tab:
            return q_oel_tab
        if tem_ana:
            return q_oel_analitico
        if tem_tab:
            return q_oel_tab
        return float("inf")


def _encontrar_limite_restritivo(
    limites: Dict[NomeLimite, float],
    valor_efetivo: float,
    buscar_minimo: bool,
) -> Optional[NomeLimite]:
    tolerancia = 1e-6
    for nome_limite, valor_limite in limites.items():
        if abs(valor_limite - valor_efetivo) <= tolerancia:
            return nome_limite
    if not limites:
        return None
    if buscar_minimo:
        return min(limites, key=limites.get)
    return max(limites, key=limites.get)
