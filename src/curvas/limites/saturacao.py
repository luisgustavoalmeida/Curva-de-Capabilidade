"""
Limite de saturação magnética do gerador.

Objetivo:
    Considerar efeitos de saturação que reduzem a capacidade de Q
    (tipicamente no lado sobre-excitado) em altas tensões / excitação.

Referências:
    - IEEE Std 1110-2002: Saturation effects on capability.
    - FITZGERALD, A.E. Electric Machinery. Curvas de saturação.
"""

from typing import Optional

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteSaturacao(
    potencia_ativa: float,
    curva_saturacao: Optional[TabelaCurva],
) -> float:
    """
    Calcula limite superior de Q por saturação magnética (p.u. ou Mvar).

    Entrada:
        potencia_ativa: P na mesma base da curva
        curva_saturacao: tabela (P, Q_saturacao)

    Saída:
        Limite superior de Q, ou +inf se não houver curva.
    """
    if curva_saturacao and curva_saturacao.pontos:
        return InterpolarPorSegmentos(
            curva_saturacao.obter_abscissas(),
            curva_saturacao.obter_ordenadas(),
            potencia_ativa,
            curva_saturacao.permitir_extrapolacao,
        )
    return float("inf")
