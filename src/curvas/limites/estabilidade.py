"""
Limite de estabilidade estática (UEL).

Com curva tabulada do fabricante: escala (Vt/Vt_ref)².
Sem curva: não vincula o envelope (retorna −∞) - modo mínimo analítico.
"""

from typing import Optional

from src.curvas.limites.escala_tensao import EscalarLimiteQPorTensaoQuadratica
from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.gerador import GeradorSincrono
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteEstabilidade(
    potencia_ativa: float,
    curva_estabilidade: Optional[TabelaCurva],
    gerador: GeradorSincrono,
    tensao_terminal: float,
    em_por_unidade: bool = True,
    tensao_referencia: float = 1.0,
) -> float:
    """
    Calcula o limite inferior de Q por estabilidade estática.

    Sem CSV de fabricante o limite não entra no envelope (modo mínimo).
    """
    del gerador, em_por_unidade  # usados só com curva / legado
    vt = tensao_terminal if tensao_terminal > 0 else 1.0
    vt_ref = tensao_referencia if tensao_referencia > 0 else 1.0

    if curva_estabilidade and curva_estabilidade.pontos:
        q_tab = InterpolarPorSegmentos(
            curva_estabilidade.obter_abscissas(),
            curva_estabilidade.obter_ordenadas(),
            potencia_ativa,
            curva_estabilidade.permitir_extrapolacao,
        )
        return EscalarLimiteQPorTensaoQuadratica(q_tab, vt, vt_ref)

    return float("-inf")
