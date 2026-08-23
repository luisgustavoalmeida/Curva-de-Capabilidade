"""
Limite de aquecimento de extremo de estator (underexcited / leading PF).

Em máquinas salientes (hidro), o aquecimento das extremidades do núcleo
restringe a absorção de Q além do UEL/MEL genéricos (IEEE Std 1110).

Equação analítica simplificada (arco elíptico no lado capacitivo):
    Q_end(P) = Q0 · Vt · √(max(0, 1 − (P / (Vt · Pmax))²))
com Q0 < 0 (tipicamente −0,35 … −0,55 pu).

Referências:
    - IEEE Std 1110-2002: Stator end-region heating limit.
    - KUNDUR, P. Power System Stability and Control. Seção 3.4.
"""

import math
from typing import Optional

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteAquecimentoExtremoEstator(
    potencia_ativa: float,
    tensao_terminal: float = 1.0,
    curva: Optional[TabelaCurva] = None,
    q_em_vazio_pu: float = -0.45,
    potencia_maxima_arco_pu: float = 1.0,
) -> float:
    """
    Calcula Q mínimo por aquecimento de extremo de estator.

    Se houver curva tabulada, interpola; senão usa arco analítico.
    Retorna −inf se o limite não se aplica (fora do arco).
    """
    vt = tensao_terminal if tensao_terminal > 0 else 1.0

    if curva and curva.pontos:
        q_tab = InterpolarPorSegmentos(
            curva.obter_abscissas(),
            curva.obter_ordenadas(),
            potencia_ativa,
            curva.permitir_extrapolacao,
        )
        # Curva tipicamente em Vt_ref=1; escala linear em Vt (raio aparente)
        return q_tab * vt

    p_max = max(potencia_maxima_arco_pu * vt, 1e-9)
    razao = potencia_ativa / p_max
    if abs(razao) > 1.0:
        return float("-inf")
    return q_em_vazio_pu * vt * math.sqrt(max(0.0, 1.0 - razao * razao))
