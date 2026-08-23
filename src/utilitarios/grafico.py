"""
Conversão de pontos para convenção gráfica da curva de capabilidade.

Convenção adotada (ONS BD Anatem / usinas brasileiras):
    Eixo horizontal (X): Potência Reativa Q (p.u.)
    Eixo vertical (Y):   Potência Ativa P (p.u.)
    Base: Sn (MVA)

Referências:
    - ONS BD Anatem v1.6 - traçado operacional de curva de capabilidade.
    - KUNDUR, P. Power System Stability and Control.
"""

from typing import List, Tuple


def ConverterParaGrafico(
    pontos_potencia_ativa_potencia_reativa: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """
    Converte lista (P, Q) interna para (Q, P) do gráfico.

    Entrada:
        pontos no formato (potencia_ativa, potencia_reativa) em p.u.

    Saída:
        pontos no formato (potencia_reativa, potencia_ativa) em p.u.
    """
    return [
        (potencia_reativa, potencia_ativa)
        for potencia_ativa, potencia_reativa in pontos_potencia_ativa_potencia_reativa
    ]


def PontoOperacionalParaGrafico(
    potencia_ativa: float,
    potencia_reativa: float,
) -> Tuple[float, float]:
    """Converte ponto operacional (P, Q) para coordenadas do gráfico (Q, P)."""
    return (potencia_reativa, potencia_ativa)
