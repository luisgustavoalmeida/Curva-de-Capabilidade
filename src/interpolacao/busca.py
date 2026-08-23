"""
Pesquisa binária e localização de intervalo em tabelas ordenadas.

Objetivo:
    Localizar rapidamente o segmento de uma curva tabulada para interpolação.

Referências:
    - CORMEN, T.H. et al. Introduction to Algorithms. Capítulo 2.
"""

from typing import List, Tuple


def PesquisaBinaria(valores_x: List[float], valor_x: float) -> int:
    """
    Retorna o índice do maior valor <= valor_x na lista ordenada.

    Entrada:
        valores_x: lista crescente de abscissas
        valor_x: valor a localizar

    Saída:
        Índice do intervalo inferior.
    """
    if not valores_x:
        raise ValueError("Lista de abscissas vazia.")

    if valor_x <= valores_x[0]:
        return 0
    if valor_x >= valores_x[-1]:
        return len(valores_x) - 2

    inicio = 0
    fim = len(valores_x) - 1

    while inicio <= fim:
        meio = (inicio + fim) // 2
        if valores_x[meio] <= valor_x < valores_x[meio + 1]:
            return meio
        if valor_x < valores_x[meio]:
            fim = meio - 1
        else:
            inicio = meio + 1

    return len(valores_x) - 2


def BuscarIntervalo(
    valores_x: List[float],
    valor_x: float,
) -> Tuple[int, int]:
    """
    Retorna os índices (inferior, superior) do intervalo que contém valor_x.

    Saída:
        Tupla (indice_inferior, indice_superior).
    """
    indice_inferior = PesquisaBinaria(valores_x, valor_x)
    indice_superior = indice_inferior + 1
    if indice_superior >= len(valores_x):
        indice_superior = len(valores_x) - 1
        indice_inferior = indice_superior - 1
    return indice_inferior, indice_superior
