"""
Limite térmico do estator por potência aparente.

Objetivo:
    Determinar o limite superior e inferior de potência reativa imposto
    pela capacidade térmica do enrolamento do estator.

Equação:
    S_max² = P² + Q²
    Q_limite = sqrt(S_max² - P²)

Hipóteses:
    Limite circular de potência aparente em diagrama P-Q.
    Tensão nominal considerada constante para curva de capabilidade clássica.

Referências:
    - KUNDUR, P. Power System Stability and Control. Figura 3.15.
    - IEEE Std 1110-2002: Stator heating limit.
    - IEC 60034-3: Capability curve - stator end-region heating.
"""

from typing import Tuple

from src.matematica.funcoes_basicas import Quadrado, RaizQuadrada


def CalcularLimiteEstator(
    potencia_ativa: float,
    potencia_aparente_maxima: float,
) -> Tuple[float, float]:
    """
    Calcula os limites superior e inferior de Q pelo estator.

    Entradas:
        potencia_ativa: P em MW
        potencia_aparente_maxima: S_max em MVA

    Saídas:
        Tupla (limite_inferior, limite_superior) em Mvar.
        Para o limite clássico do estator, ambos são simétricos.
    """
    potencia_ativa_absoluta = abs(potencia_ativa)
    discriminante = Quadrado(potencia_aparente_maxima) - Quadrado(potencia_ativa_absoluta)

    if discriminante < 0:
        # P > Sn: limite do estator não se aplica neste ponto (Kundur / IEEE 1110)
        return (float("-inf"), float("inf"))

    limite = RaizQuadrada(discriminante)
    return (-limite, limite)
