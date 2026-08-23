"""
Limite de saliência polar (estabilidade prática).

Objetivo:
    Aplicar limite inferior de potência reativa pela curva de saliência polar.

Referências:
    - ONS BD Anatem - traçado operacional / saliência polar.
    - KUNDUR, P. Power System Stability and Control.
"""

from typing import Optional

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteSalienciaPolar(
    potencia_ativa: float,
    curva_saliencia_polar: Optional[TabelaCurva],
) -> float:
    """
    Calcula limite inferior de Q pela saliência polar.

    Saída:
        Limite inferior de Q em Mvar (tipicamente negativo).
    """
    if not curva_saliencia_polar or not curva_saliencia_polar.pontos:
        return -9999.0

    return InterpolarPorSegmentos(
        curva_saliencia_polar.obter_abscissas(),
        curva_saliencia_polar.obter_ordenadas(),
        potencia_ativa,
        curva_saliencia_polar.permitir_extrapolacao,
    )
