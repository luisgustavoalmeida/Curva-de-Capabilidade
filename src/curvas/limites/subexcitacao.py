"""
Limite de sub-excitação (MEL).

Com curva tabulada: interpolação Q(P).
Sem curva: não vincula o envelope (retorna −∞) — modo mínimo analítico.
"""

from typing import Optional

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.gerador import GeradorSincrono
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteSubExcitacao(
    potencia_ativa: float,
    curva_sub_excitacao: Optional[TabelaCurva],
    gerador: GeradorSincrono,
    em_por_unidade: bool = True,
) -> float:
    """
    Calcula o limite inferior de Q por sub-excitação.

    Sem CSV de fabricante o limite não entra no envelope (modo mínimo).
    """
    del gerador, em_por_unidade

    if curva_sub_excitacao and curva_sub_excitacao.pontos:
        return InterpolarPorSegmentos(
            curva_sub_excitacao.obter_abscissas(),
            curva_sub_excitacao.obter_ordenadas(),
            potencia_ativa,
            curva_sub_excitacao.permitir_extrapolacao,
        )

    return float("-inf")
