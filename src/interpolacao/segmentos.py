"""
Interpolação por segmentos em curvas tabuladas.

Objetivo:
    Avaliar curvas de fabricante (rotor, estabilidade, turbina) a partir
    de tabelas externas CSV/JSON.

Referências:
    - IEEE Std 1110-2002: utilização de curvas de capabilidade tabuladas.
"""

from typing import List, Tuple

from .busca import BuscarIntervalo
from .linear import ExtrapolarLinearmente, InterpolarLinearmente


def InterpolarPorSegmentos(
    valores_x: List[float],
    valores_y: List[float],
    valor_x: float,
    permitir_extrapolacao: bool = False,
) -> float:
    """
    Interpola y(x) em uma tabela ordenada por segmentos lineares.

    Entradas:
        valores_x: abscissas crescentes (ex.: Potência Ativa)
        valores_y: ordenadas correspondentes (ex.: Potência Reativa limite)
        valor_x: ponto a avaliar
        permitir_extrapolacao: se False, limita aos extremos da tabela

    Saída:
        Valor interpolado de y.
    """
    if len(valores_x) != len(valores_y):
        raise ValueError("Tabelas X e Y devem possuir o mesmo tamanho.")
    if len(valores_x) < 2:
        raise ValueError("São necessários ao menos dois pontos na tabela.")

    if valor_x <= valores_x[0]:
        if permitir_extrapolacao:
            return ExtrapolarLinearmente(
                valor_x, valores_x[0], valores_y[0], valores_x[1], valores_y[1]
            )
        return valores_y[0]

    if valor_x >= valores_x[-1]:
        if permitir_extrapolacao:
            return ExtrapolarLinearmente(
                valor_x,
                valores_x[-2],
                valores_y[-2],
                valores_x[-1],
                valores_y[-1],
            )
        return valores_y[-1]

    indice_inferior, indice_superior = BuscarIntervalo(valores_x, valor_x)
    return InterpolarLinearmente(
        valor_x,
        valores_x[indice_inferior],
        valores_y[indice_inferior],
        valores_x[indice_superior],
        valores_y[indice_superior],
    )


def AvaliarCurvaTabulada(
    pontos: List[Tuple[float, float]],
    valor_x: float,
    permitir_extrapolacao: bool = False,
) -> float:
    """
    Avalia uma curva representada por lista de tuplas (x, y).
    """
    valores_x = [ponto[0] for ponto in pontos]
    valores_y = [ponto[1] for ponto in pontos]
    return InterpolarPorSegmentos(
        valores_x, valores_y, valor_x, permitir_extrapolacao
    )
