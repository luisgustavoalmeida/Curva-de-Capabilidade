"""
Construtor do traçado operacional em p.u.

Varre P de Pmec_Min a Pmec_Max e monta o contorno fechado Q × P.
Inclui referências geométricas clássicas (Kundur / IEEE 1110):
    - reta horizontal Pmec Max / Min
    - semicírculo de potência aparente nominal S = Vt·Imax
    - limitadores Q(P) estendidos além da faixa operacional (P < 0 e P > 1)
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.curvas.avaliador import AvaliadorCurvas, EnvelopeCapabilidade
from src.utilitarios.grafico import ConverterParaGrafico

# Faixa de P para plotar limitadores de referência (alinhada à janela da GUI)
P_REFERENCIA_MIN = -0.25
P_REFERENCIA_MAX = 1.25

# Chaves geométricas / Pmec - não são séries Q(P) do envelope
CHAVES_GEOMETRICAS = frozenset(
    {
        "CirculoPotenciaAparente",
        "CirculoOperacaoIs",
        "FatorPotenciaNominal",
        "EixoOperacaoCompensador",
        "LimitePmecMax",
        "LimiteQuedaUtil",
        "LimiteTurbinaMax",
        "LimitePmecMin",
        "LimiteTurbinaMin",
        "LimiteTurbina",
    }
)

@dataclass
class PontosCurvaCapabilidade:
    """Pontos do traçado operacional e curvas de referência (p.u.)."""

    potencias_ativas: List[float] = field(default_factory=list)
    limite_superior: List[Tuple[float, float]] = field(default_factory=list)
    limite_inferior: List[Tuple[float, float]] = field(default_factory=list)
    contorno_fechado: List[Tuple[float, float]] = field(default_factory=list)
    curvas_individuais_superiores: Dict[str, List[Tuple[float, float]]] = field(
        default_factory=dict
    )
    curvas_individuais_inferiores: Dict[str, List[Tuple[float, float]]] = field(
        default_factory=dict
    )
    unidade: str = "pu"
    base_potencia_aparente: float = 0.0
    tensao_terminal_pu: float = 1.0
    potencia_aparente_maxima_pu: float = 1.0
    potencia_mecanica_maxima_pu: float = 0.0
    potencia_mecanica_minima_pu: float = 0.0
    fator_potencia_nominal: float = 0.0
    corrente_estator_operacao_pu: float = 0.0
    corrente_estator_maxima_pu: float = 1.0


class ConstrutorCurvaCapabilidade:
    """Gera o traçado operacional completo da curva de capabilidade."""

    def __init__(self, avaliador: AvaliadorCurvas):
        self.avaliador = avaliador

    def gerar_pontos(
        self,
        potencia_minima: Optional[float] = None,
        potencia_maxima: Optional[float] = None,
        incremento: float = 0.01,
        tensao_terminal: float = 1.0,
        queda_atual: float = 0.0,
        corrente_campo: float = 0.0,
        corrente_estator_operacao_pu: float = 0.0,
        corrente_estator_maxima_pu: Optional[float] = None,
        frequencia_pu: float = 1.0,
    ) -> PontosCurvaCapabilidade:
        """
        Gera pontos do traçado operacional.

        Gerador: varre Pmec_Min → Pmec_Max.
        Compensador síncrono: região em P ≈ 0 + curvas de referência em P.
        """
        if incremento <= 0:
            raise ValueError("Incremento deve ser positivo.")

        if self.avaliador.gerador.eh_compensador():
            return self._gerar_pontos_compensador(
                incremento,
                tensao_terminal,
                corrente_campo,
                corrente_estator_operacao_pu,
                corrente_estator_maxima_pu,
                frequencia_pu,
            )

        p_min = (
            potencia_minima
            if potencia_minima is not None
            else self.avaliador.obter_potencia_ativa_minima()
        )
        p_max = (
            potencia_maxima
            if potencia_maxima is not None
            else self.avaliador.obter_potencia_ativa_maxima(queda_atual)
        )
        p_max = min(p_max, self.avaliador.obter_potencia_ativa_maxima(queda_atual))
        p_min = max(p_min, self.avaliador.obter_potencia_ativa_minima())

        if p_max < p_min:
            raise ValueError("Potência máxima menor que mínima.")

        imax = (
            corrente_estator_maxima_pu
            if corrente_estator_maxima_pu is not None and corrente_estator_maxima_pu > 0
            else self.avaliador.configuracao.corrente_estator_maxima_pu
        )
        if imax <= 0:
            imax = self.avaliador.configuracao.potencia_aparente_maxima
        if imax <= 0:
            imax = 1.0
        raio_aparente = tensao_terminal * imax

        # Traçado operacional: fica estritamente dentro do círculo S = Vt·Imax
        # (evita ápice singular P=Vt com Qsup espúrio por erro de ponto flutuante)
        p_max_pmec = p_max
        p_max = min(p_max, max(raio_aparente - 1e-4, 0.0))
        if p_max < p_min:
            if p_min > raio_aparente + 1e-9:
                p_min = 0.0
                p_max = 0.0
            else:
                p_max = p_min
                if p_max > raio_aparente - 1e-4:
                    p_max = max(raio_aparente - 1e-4, 0.0)
                    p_min = min(p_min, p_max)

        resultado = PontosCurvaCapabilidade(
            unidade=self.avaliador.configuracao.unidade,
            base_potencia_aparente=self.avaliador.configuracao.base_potencia_aparente,
            tensao_terminal_pu=tensao_terminal,
            potencia_aparente_maxima_pu=raio_aparente,
            potencia_mecanica_maxima_pu=p_max_pmec,
            potencia_mecanica_minima_pu=p_min,
            corrente_estator_operacao_pu=corrente_estator_operacao_pu,
            corrente_estator_maxima_pu=imax,
        )

        potencia_atual = p_min
        while potencia_atual <= p_max + 1e-9:
            envelope = self.avaliador.calcular_envelope(
                potencia_atual,
                tensao_terminal,
                queda_atual,
                corrente_campo,
                corrente_estator_maxima_pu=imax,
                frequencia_pu=frequencia_pu,
            )
            if envelope.regiao_valida:
                self._adicionar_ponto(
                    resultado, envelope, incluir_curvas_individuais=False
                )
            potencia_atual += incremento

        if p_max >= p_min:
            envelope = self.avaliador.calcular_envelope(
                p_max,
                tensao_terminal,
                queda_atual,
                corrente_campo,
                corrente_estator_maxima_pu=imax,
                frequencia_pu=frequencia_pu,
            )
            if envelope.regiao_valida:
                if (
                    not resultado.potencias_ativas
                    or abs(resultado.potencias_ativas[-1] - p_max) > 1e-6
                ):
                    self._adicionar_ponto(
                        resultado, envelope, incluir_curvas_individuais=False
                    )

        resultado.contorno_fechado = self._montar_contorno_fechado(resultado)
        self._adicionar_curvas_referencia_limitadores(
            resultado,
            incremento,
            tensao_terminal,
            queda_atual,
            corrente_campo,
            imax,
            frequencia_pu,
        )
        self._adicionar_retas_potencia_ativa(
            resultado, raio_aparente, queda_atual
        )
        self._adicionar_circulo_potencia_aparente(resultado, raio_aparente)
        self._adicionar_circulo_operacao_is(
            resultado, tensao_terminal, corrente_estator_operacao_pu
        )
        self._adicionar_reta_fator_potencia(resultado, raio_aparente)
        return resultado

    def _gerar_pontos_compensador(
        self,
        incremento: float,
        tensao_terminal: float,
        corrente_campo: float,
        corrente_estator_operacao_pu: float = 0.0,
        corrente_estator_maxima_pu: Optional[float] = None,
        frequencia_pu: float = 1.0,
    ) -> PontosCurvaCapabilidade:
        imax = (
            corrente_estator_maxima_pu
            if corrente_estator_maxima_pu is not None and corrente_estator_maxima_pu > 0
            else self.avaliador.configuracao.corrente_estator_maxima_pu
        )
        if imax <= 0:
            imax = self.avaliador.configuracao.potencia_aparente_maxima
        if imax <= 0:
            imax = 1.0
        raio_aparente = tensao_terminal * imax

        resultado = PontosCurvaCapabilidade(
            unidade=self.avaliador.configuracao.unidade,
            base_potencia_aparente=self.avaliador.configuracao.base_potencia_aparente,
            tensao_terminal_pu=tensao_terminal,
            potencia_aparente_maxima_pu=raio_aparente,
            potencia_mecanica_maxima_pu=0.0,
            potencia_mecanica_minima_pu=0.0,
            corrente_estator_operacao_pu=corrente_estator_operacao_pu,
            corrente_estator_maxima_pu=imax,
        )

        # Curvas de referência ao longo de P (plot além da região P≈0)
        self._adicionar_curvas_referencia_limitadores(
            resultado,
            incremento,
            tensao_terminal,
            0.0,
            corrente_campo,
            imax,
            frequencia_pu,
        )

        # Envelope operacional em P = 0
        envelope = self.avaliador.calcular_envelope(
            0.0,
            tensao_terminal,
            0.0,
            corrente_campo,
            respeitar_limite_potencia_mecanica=True,
            corrente_estator_maxima_pu=imax,
            frequencia_pu=frequencia_pu,
        )
        resultado.potencias_ativas = [0.0]
        resultado.limite_superior = [(0.0, envelope.limite_superior_efetivo)]
        resultado.limite_inferior = [(0.0, envelope.limite_inferior_efetivo)]

        q_sup = envelope.limite_superior_efetivo
        q_inf = envelope.limite_inferior_efetivo
        # Contorno: faixa estreita em torno de P = 0 (região permitida)
        espessura = 0.02
        resultado.contorno_fechado = [
            (q_inf, -espessura),
            (q_sup, -espessura),
            (q_sup, espessura),
            (q_inf, espessura),
        ]

        self._adicionar_circulo_potencia_aparente(resultado, raio_aparente)
        self._adicionar_circulo_operacao_is(
            resultado, tensao_terminal, corrente_estator_operacao_pu
        )
        # Eixo P = 0 (operação típica do compensador) - formato (P, Q)
        resultado.curvas_individuais_superiores["EixoOperacaoCompensador"] = [
            (0.0, -raio_aparente * 1.15),
            (0.0, raio_aparente * 1.15),
        ]
        return resultado

    def _adicionar_curvas_referencia_limitadores(
        self,
        resultado: PontosCurvaCapabilidade,
        incremento: float,
        tensao_terminal: float,
        queda_atual: float,
        corrente_campo: float,
        corrente_estator_maxima_pu: float,
        frequencia_pu: float,
    ) -> None:
        """
        Varre limitadores Q(P) na janela gráfica (−0,25 … 1,25 pu).

        Independente da Pmec: OEL PK, UEL, SCL etc. permanecem visíveis
        além da faixa operacional e também em P < 0.
        Não clipa ao círculo S (arco de campo pode ultrapassar S).
        """
        for dicionario in (
            resultado.curvas_individuais_superiores,
            resultado.curvas_individuais_inferiores,
        ):
            for chave in list(dicionario.keys()):
                if chave not in CHAVES_GEOMETRICAS:
                    del dicionario[chave]

        p_ref_min = P_REFERENCIA_MIN
        p_ref_max = P_REFERENCIA_MAX
        potencia_atual = p_ref_min
        while potencia_atual <= p_ref_max + 1e-9:
            envelope = self.avaliador.calcular_envelope(
                potencia_atual,
                tensao_terminal,
                queda_atual,
                corrente_campo,
                respeitar_limite_potencia_mecanica=False,
                corrente_estator_maxima_pu=corrente_estator_maxima_pu,
                frequencia_pu=frequencia_pu,
                modo_referencia=True,
            )
            self._acumular_limites_referencia(resultado, envelope)
            potencia_atual += incremento

    def _acumular_limites_referencia(
        self,
        resultado: PontosCurvaCapabilidade,
        envelope: EnvelopeCapabilidade,
    ) -> None:
        """Acumula Q(P) finitos dos limitadores individuais (sem clip em S)."""
        potencia = envelope.potencia_ativa
        for nome_limite, valor in envelope.limites_superiores.items():
            if valor in (float("inf"), float("-inf")) or abs(valor) > 1e4:
                continue
            chave = nome_limite.value
            if chave not in resultado.curvas_individuais_superiores:
                resultado.curvas_individuais_superiores[chave] = []
            resultado.curvas_individuais_superiores[chave].append((potencia, valor))

        for nome_limite, valor in envelope.limites_inferiores.items():
            if valor in (float("inf"), float("-inf")) or abs(valor) > 1e4:
                continue
            chave = nome_limite.value
            if chave not in resultado.curvas_individuais_inferiores:
                resultado.curvas_individuais_inferiores[chave] = []
            resultado.curvas_individuais_inferiores[chave].append((potencia, valor))

    def _adicionar_retas_potencia_ativa(
        self,
        resultado: PontosCurvaCapabilidade,
        raio_aparente: float,
        queda_atual: float = 0.0,
    ) -> None:
        """
        Retas horizontais de potência ativa.

        Restritivos (cortam a região permitida):
            LimitePmecMax / LimitePmecMin

        Referência (não cortam o envelope; H pode variar livremente):
            LimiteQuedaUtil, LimiteTurbinaMax, LimiteTurbinaMin

        Formato interno: (P, Q). Cruzam o diagrama de −S a +S.
        """
        q_span = max(raio_aparente, 1.0) * 1.15
        limites = self.avaliador.obter_limites_potencia_ativa_horizontais(queda_atual)

        chaves_max = (
            "LimitePmecMax",
            "LimiteQuedaUtil",
            "LimiteTurbinaMax",
        )
        chaves_min = (
            "LimitePmecMin",
            "LimiteTurbinaMin",
        )

        for chave in chaves_max:
            if chave not in limites:
                continue
            p_lim = limites[chave]
            resultado.curvas_individuais_superiores[chave] = [
                (p_lim, -q_span),
                (p_lim, q_span),
            ]

        for chave in chaves_min:
            if chave not in limites:
                continue
            p_lim = limites[chave]
            if p_lim <= 1e-9:
                continue
            resultado.curvas_individuais_inferiores[chave] = [
                (p_lim, -q_span),
                (p_lim, q_span),
            ]

    def _adicionar_reta_fator_potencia(
        self,
        resultado: PontosCurvaCapabilidade,
        raio_aparente: float,
    ) -> None:
        """
        Reta do fator de potência nominal (atrasado / sobre-excitado).

        Do origem ao ponto nominal sobre o círculo S:
            P = S · fp
            Q = S · sqrt(1 - fp²)
            Q = P · tan(arccos(fp))

        Referência: Kundur Cap. 3; IEEE Std 1110 - rated power factor line.
        Formato interno: (P, Q).
        """
        fp = self.avaliador.gerador.fator_potencia_nominal
        if raio_aparente <= 0 or not (0.0 < fp <= 1.0):
            return

        p_nominal = raio_aparente * fp
        q_nominal = raio_aparente * math.sqrt(max(0.0, 1.0 - fp * fp))
        resultado.curvas_individuais_superiores["FatorPotenciaNominal"] = [
            (0.0, 0.0),
            (p_nominal, q_nominal),
        ]
        # Guarda o fp para rótulo no gráfico
        resultado.fator_potencia_nominal = fp

    def _adicionar_circulo_potencia_aparente(
        self,
        resultado: PontosCurvaCapabilidade,
        raio_aparente: float,
    ) -> None:
        """
        Semicírculo completo de potência aparente nominal (SCL / Smax).

        Equação (Kundur / IEEE 1110), P ≥ 0:
            Q² + P² = S²    ⇒    Q = S·cos(θ), P = S·sin(θ), θ ∈ [0, π]

        Substitui os arcos parciais de LimiteEstator na plotagem.
        Formato interno: (P, Q).
        """
        if raio_aparente <= 0:
            return

        pontos_circulo: List[Tuple[float, float]] = []
        numero_pontos = 181
        for indice in range(numero_pontos):
            # θ = 0 → (P=0, Q=+S); θ = π/2 → (P=S, Q=0); θ = π → (P=0, Q=−S)
            angulo = math.pi * indice / (numero_pontos - 1)
            potencia_ativa = raio_aparente * math.sin(angulo)
            potencia_reativa = raio_aparente * math.cos(angulo)
            pontos_circulo.append((potencia_ativa, potencia_reativa))

        resultado.curvas_individuais_superiores["CirculoPotenciaAparente"] = (
            pontos_circulo
        )
        # Mantém LimiteEstator (SCL efetivo) + círculo S = Vt·Imax.

    def _adicionar_circulo_operacao_is(
        self,
        resultado: PontosCurvaCapabilidade,
        tensao_terminal: float,
        corrente_estator_pu: float,
    ) -> None:
        """
        Círculo de operação S = Vt·Is (corrente de estator atual).

        Compara o aquecimento atual com o limite S = Vt·Imax.
        """
        if tensao_terminal <= 0 or corrente_estator_pu <= 1e-6:
            return
        raio_op = tensao_terminal * corrente_estator_pu
        if raio_op <= 1e-9:
            return
        raio_cap = resultado.potencia_aparente_maxima_pu
        if abs(raio_op - raio_cap) < 0.02:
            return

        pontos: List[Tuple[float, float]] = []
        for indice in range(181):
            angulo = math.pi * indice / 180
            potencia_ativa = raio_op * math.sin(angulo)
            potencia_reativa = raio_op * math.cos(angulo)
            pontos.append((potencia_ativa, potencia_reativa))
        resultado.curvas_individuais_superiores["CirculoOperacaoIs"] = pontos
        resultado.corrente_estator_operacao_pu = corrente_estator_pu

    def _adicionar_ponto(
        self,
        resultado: PontosCurvaCapabilidade,
        envelope: EnvelopeCapabilidade,
        incluir_curvas_individuais: bool = True,
    ) -> None:
        potencia = envelope.potencia_ativa
        resultado.potencias_ativas.append(potencia)
        resultado.limite_superior.append((potencia, envelope.limite_superior_efetivo))
        resultado.limite_inferior.append((potencia, envelope.limite_inferior_efetivo))

        if not incluir_curvas_individuais:
            return

        raio = getattr(resultado, "potencia_aparente_maxima_pu", 0.0) or 0.0
        q_circ = 0.0
        if raio > 0 and abs(potencia) <= raio:
            q_circ = math.sqrt(max(0.0, raio * raio - potencia * potencia))

        for nome_limite, valor in envelope.limites_superiores.items():
            chave = nome_limite.value
            valor_plot = valor
            # Clipa referências ao círculo S (evita segmentos verticais fora de S=Vt)
            if q_circ > 0 and chave != "CirculoPotenciaAparente":
                valor_plot = min(valor, q_circ)
            if chave not in resultado.curvas_individuais_superiores:
                resultado.curvas_individuais_superiores[chave] = []
            resultado.curvas_individuais_superiores[chave].append((potencia, valor_plot))

        for nome_limite, valor in envelope.limites_inferiores.items():
            chave = nome_limite.value
            valor_plot = valor
            if q_circ > 0:
                valor_plot = max(valor, -q_circ)
            if chave not in resultado.curvas_individuais_inferiores:
                resultado.curvas_individuais_inferiores[chave] = []
            resultado.curvas_individuais_inferiores[chave].append((potencia, valor_plot))

    def _montar_contorno_fechado(
        self,
        resultado: PontosCurvaCapabilidade,
    ) -> List[Tuple[float, float]]:
        """
        Polígono fechado no plano Q × P:
            lado direito (Qsup) → teto Pmax → lado esquerdo (Qinf) revertido → base.
        """
        if not resultado.limite_superior or not resultado.limite_inferior:
            return []

        lado_direito = ConverterParaGrafico(resultado.limite_superior)
        lado_esquerdo = ConverterParaGrafico(resultado.limite_inferior)
        teto = [lado_direito[-1], lado_esquerdo[-1]]
        base = [lado_esquerdo[0], lado_direito[0]]
        return lado_direito + teto + list(reversed(lado_esquerdo)) + base
