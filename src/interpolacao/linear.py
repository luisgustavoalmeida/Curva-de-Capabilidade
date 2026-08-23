"""
Interpolação linear entre dois pontos.

Objetivo:
    Obter o valor de uma curva tabulada em um ponto intermediário.

Equação:
    y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)

Hipóteses:
    x1 != x2.

Referências:
    - BURDEN, R.L.; FAIRES, J.D. Numerical Analysis. Capítulo 3.
"""

from typing import Tuple


def InterpolarLinearmente(
    x: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:
    """
    Interpola linearmente y em função de x entre (x1,y1) e (x2,y2).

    Entradas:
        x: abscissa desejada
        x1, y1: primeiro ponto conhecido
        x2, y2: segundo ponto conhecido

    Saída:
        Valor interpolado de y.
    """
    if x1 == x2:
        raise ValueError("Abscissas iguais impedem interpolação linear.")
    proporcao = (x - x1) / (x2 - x1)
    return y1 + proporcao * (y2 - y1)


def ExtrapolarLinearmente(
    x: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:
    """
    Extrapola linearmente além dos limites da tabela.

    Limitação:
        Extrapolação pode produzir valores fisicamente inválidos.
        Deve ser habilitada explicitamente pelo chamador.
    """
    return InterpolarLinearmente(x, x1, y1, x2, y2)
