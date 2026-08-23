"""
Limites analíticos dependentes da tensão terminal (Vt) e corrente de campo (If).

Equações (Kundur / IEEE Std 1110 / ONS BD Anatem):

    Limite do estator:
        Q = ±sqrt((Vt·Imax)² - P²)

    Limite do campo / rotor:
        Q = -Vt²/Xd + sqrt( (Vt·Efd/Xd)² - P² )

    Relação corrente de campo → tensão interna (OCC / entreferro):
        Efd ≈ V_oc(If) via curva V, ou modelo bipartido com If_NL / If_FL

Referências:
    - KUNDUR, P. Power System Stability and Control. Seção 3.4.
    - IEEE Std 1110-2002: Capability curves / field current / OCC.
    - ONS BD Anatem: IFD_FL, IFD_NL, OEL.
"""

from typing import Optional, Tuple

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.matematica.funcoes_basicas import Quadrado, RaizQuadrada
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteEstatorPorTensao(
    potencia_ativa_pu: float,
    tensao_terminal_pu: float,
    corrente_estator_maxima_pu: float = 1.0,
) -> Tuple[float, float]:
    """
    Calcula limites de Q do estator em função de Vt.

    Equação: Q = ±sqrt( (Vt·Imax)² - P² )
    """
    if tensao_terminal_pu <= 0:
        raise ValueError("Tensão terminal deve ser positiva.")

    raio = tensao_terminal_pu * max(corrente_estator_maxima_pu, 0.0)
    discriminante = Quadrado(raio) - Quadrado(potencia_ativa_pu)

    if discriminante < 0:
        return (float("-inf"), float("inf"))

    limite = RaizQuadrada(discriminante)
    return (-limite, limite)


def CalcularLimiteCampoPorTensao(
    potencia_ativa_pu: float,
    tensao_terminal_pu: float,
    reatancia_direta_pu: float,
    tensao_interna_maxima_pu: float,
) -> float:
    """
    Calcula limite superior de Q pelo aquecimento do campo (OEL analítico).

    Equação:
        Q = -Vt²/Xd + sqrt( (Vt·Efd_max/Xd)² - P² )
    """
    if reatancia_direta_pu <= 0:
        raise ValueError("Reatância direta deve ser positiva.")
    if tensao_terminal_pu <= 0:
        raise ValueError("Tensão terminal deve ser positiva.")
    if tensao_interna_maxima_pu <= 0:
        return float("-inf")

    centro = -Quadrado(tensao_terminal_pu) / reatancia_direta_pu
    raio = (tensao_terminal_pu * tensao_interna_maxima_pu) / reatancia_direta_pu
    discriminante = Quadrado(raio) - Quadrado(potencia_ativa_pu)

    if discriminante < 0:
        return float("-inf")

    return centro + RaizQuadrada(discriminante)


def EstimarTensaoInternaMaxima(
    potencia_reativa_em_vazio_pu: float,
    tensao_terminal_pu: float,
    reatancia_direta_pu: float,
) -> float:
    """
    Estima Efd_max a partir do Q do limite de campo em P=0.

    Em P=0: Q = -Vt²/Xd + Vt·Efd/Xd
    Logo: Efd = Vt + Q·Xd/Vt
    """
    if tensao_terminal_pu <= 0 or reatancia_direta_pu <= 0:
        raise ValueError("Vt e Xd devem ser positivos.")
    return tensao_terminal_pu + (
        potencia_reativa_em_vazio_pu * reatancia_direta_pu / tensao_terminal_pu
    )


def CalcularTensaoInternaPorCorrenteCampo(
    corrente_campo: float,
    corrente_campo_nominal: float,
    tensao_interna_nominal_pu: float,
    corrente_campo_vazio: float = 0.0,
    curva_occ: Optional[TabelaCurva] = None,
) -> float:
    """
    Converte corrente de campo If em tensão interna Efd (p.u.).

    Prioridade (IEEE 1110):
        1) Curva V / OCC tabulada (abscissa=If A ou pu, ordenada=Efd/Vt pu)
        2) Modelo bipartido entreferro + saturação (If_NL, If_FL, Efd_rated)
        3) Proporcionalidade linear Efd_rated · (If/If_FL)

    Modelo bipartido:
        If ≤ If_NL  →  Efd = If / If_NL  (reta de entreferro)
        If_NL < If ≤ If_FL  →  interpola (1,0) → Efd_rated
        If > If_FL  →  Efd_rated · (If / If_FL)
    """
    if corrente_campo <= 0:
        return 0.0

    if curva_occ and curva_occ.pontos:
        return InterpolarPorSegmentos(
            curva_occ.obter_abscissas(),
            curva_occ.obter_ordenadas(),
            corrente_campo,
            curva_occ.permitir_extrapolacao,
        )

    if_nl = corrente_campo_vazio
    if_fl = corrente_campo_nominal
    efd_rated = tensao_interna_nominal_pu

    if if_nl > 0:
        efd_entreferro = corrente_campo / if_nl
        if if_fl > if_nl and efd_rated > 0:
            if corrente_campo <= if_nl:
                return efd_entreferro
            if corrente_campo <= if_fl:
                fracao = (corrente_campo - if_nl) / (if_fl - if_nl)
                return 1.0 + fracao * (efd_rated - 1.0)
            return efd_rated * (corrente_campo / if_fl)
        return efd_entreferro

    if if_fl > 0 and efd_rated > 0:
        return efd_rated * (corrente_campo / if_fl)

    return max(efd_rated, 0.0)


def CalcularFatorCorrenteCampo(
    corrente_campo: float,
    corrente_campo_nominal: float,
) -> float:
    """
    Fator If/If_FL para escalonar o limite de sobre-excitação.

    Se corrente_campo <= 0, retorna 1.0 (usa curva nominal de projeto).
    """
    if corrente_campo <= 0 or corrente_campo_nominal <= 0:
        return 1.0
    return corrente_campo / corrente_campo_nominal
