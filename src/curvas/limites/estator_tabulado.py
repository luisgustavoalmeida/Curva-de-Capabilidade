"""
Limite do estator por curva tabulada SCL (Stator Current Limit).

Objetivo:
    Aplicar limite de corrente do estator a partir da curva SCL do fabricante/ONS.

Referências:
    - ONS BD Anatem — traçado operacional / limite de estator tabulado.
    - IEEE Std 1110-2002: Stator current limit.
"""

from typing import Optional

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteEstatorTabulado(
    potencia_ativa: float,
    curva_estator: Optional[TabelaCurva],
) -> float:
    """
    Obtém Q máximo da curva SCL tabulada para um valor de P.

    Entrada:
        potencia_ativa: P em MW
        curva_estator: tabela (P, Q) da curva SCL

    Saída:
        Limite superior de Q em Mvar, ou valor alto se sem curva.
    """
    if not curva_estator or not curva_estator.pontos:
        return 9999.0

    if potencia_ativa > curva_estator.potencia_maxima():
        return 9999.0
    if potencia_ativa < curva_estator.potencia_minima():
        return 9999.0

    return InterpolarPorSegmentos(
        curva_estator.obter_abscissas(),
        curva_estator.obter_ordenadas(),
        potencia_ativa,
        curva_estator.permitir_extrapolacao,
    )
