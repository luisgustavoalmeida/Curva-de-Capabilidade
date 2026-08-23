"""
Funções matemáticas de grandezas elétricas.

Objetivo:
    Calcular grandezas fundamentais do gerador síncrono a partir de
    potência ativa, reativa e tensão.

Equações:
    Potência aparente: S = sqrt(P² + Q²)
    Corrente de estator (trifásico): I = S / (sqrt(3) * V)
    Fator de potência: cos(φ) = P / S
    Ângulo de potência: tan(φ) = Q / P

Hipóteses:
    Sistema trifásico equilibrado.
    Tensão de linha informada em kV.
    Potências em MVA/MW/Mvar.

Referências:
    - FITZGERALD, A.E.; KINGSLEY, C.; UMANS, S.D. Electric Machinery. Cap. 5.
    - IEEE Std 1110-2002: Guide for Synchronous Generator Modeling.
"""

import math

from .funcoes_basicas import Quadrado, RaizQuadrada


def PotenciaAparente(potencia_ativa: float, potencia_reativa: float) -> float:
    """
    Calcula a potência aparente a partir de P e Q.

    Equação: S = sqrt(P² + Q²)
    """
    return RaizQuadrada(Quadrado(potencia_ativa) + Quadrado(potencia_reativa))


def CorrenteEstator(
    potencia_aparente: float,
    tensao_linha: float,
) -> float:
    """
    Calcula a corrente de estator trifásica.

    Equação: I = S * 10^6 / (sqrt(3) * V * 10^3)
    Resultado em ampere quando S está em MVA e V em kV.
    """
    if tensao_linha <= 0:
        raise ValueError("Tensão de linha deve ser positiva.")
    return (potencia_aparente * 1_000_000.0) / (math.sqrt(3.0) * tensao_linha * 1_000.0)


def CorrenteEstatorPu(potencia_aparente_pu: float, tensao_terminal_pu: float) -> float:
    """
    Corrente de estator em p.u. (base In).

    Em p.u.: Is = S / Vt   (equivalente a I = S/(√3·V) nas bases Sn, Vn, In).
    """
    if tensao_terminal_pu <= 0:
        return 0.0
    return potencia_aparente_pu / tensao_terminal_pu


def MargemCorrenteEstatorPu(
    corrente_estator_pu: float,
    corrente_maxima_pu: float = 1.0,
) -> float:
    """Margem de corrente SCL em %: 100·(Imax − Is)/Imax."""
    if corrente_maxima_pu <= 0:
        return 0.0
    return max(0.0, 100.0 * (corrente_maxima_pu - corrente_estator_pu) / corrente_maxima_pu)


def FatorPotencia(potencia_ativa: float, potencia_aparente: float) -> float:
    """
    Calcula o fator de potência.

    Equação: cos(φ) = P / S
    """
    if potencia_aparente <= 0:
        raise ValueError("Potência aparente deve ser positiva.")
    return potencia_ativa / potencia_aparente


def PotenciaReativaPorFatorPotencia(
    potencia_ativa: float,
    fator_potencia: float,
    indutivo: bool = True,
) -> float:
    """
    Calcula Q a partir de P e fator de potência.

    Equação: Q = P * tan(arccos(fp))
    """
    if not 0 < fator_potencia <= 1:
        raise ValueError("Fator de potência deve estar no intervalo (0, 1].")
    angulo = math.acos(fator_potencia)
    potencia_reativa = potencia_ativa * math.tan(angulo)
    return potencia_reativa if indutivo else -potencia_reativa


def AnguloPorPotencias(potencia_ativa: float, potencia_reativa: float) -> float:
    """
    Calcula o ângulo de potência em graus.

    Equação: φ = arctan(Q / P)
    """
    if potencia_ativa == 0:
        return 90.0 if potencia_reativa > 0 else -90.0
    return math.degrees(math.atan(potencia_reativa / potencia_ativa))
