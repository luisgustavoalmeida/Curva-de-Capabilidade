"""
Escalonamento de limites tabulados com tensão terminal.

Dois modelos:

1) Circular (SCL / potência aparente - círculo em torno da origem):
       S_ref² = P² + Q_ref²
       S(Vt)  = S_ref · (Vt / Vt_ref)
       Q(Vt)  = sinal(Q_ref) · √(max(0, S(Vt)² − P²))
   Se S(Vt) < |P|, o arco não existe → limite não vincula (+inf / −inf).

2) Quadrático (UEL / estabilidade - margem ∝ V²/X, Kundur Cap. 5):
       Q(Vt) = Q_ref · (Vt / Vt_ref)²

NÃO usar escala circular em limites de campo (OEL): o centro do arco de
campo é −Vt²/Xd, não a origem. Nesses casos usar a fórmula analítica.

Referências:
    - ONS BD Anatem - curvas em tensão de referência.
    - IEEE Std 1110-2002 / Kundur Seção 3.4.
"""

import math


def EscalarLimiteQPorTensao(
    potencia_reativa_ref: float,
    potencia_ativa: float,
    tensao_terminal: float,
    tensao_referencia: float = 1.0,
) -> float:
    """
    Escala Q de limite circular (SCL) de Vt_ref para Vt atual.

    Se o ponto (P, Vt) fica fora do arco escalado, retorna +inf (limite
    superior) ou −inf (limite inferior) para NÃO vincular o envelope -
    nunca retorna 0 (que criaria muro artificial em Q=0).
    """
    if tensao_referencia <= 0:
        return potencia_reativa_ref
    if abs(tensao_terminal - tensao_referencia) < 1e-9:
        return potencia_reativa_ref

    s_ref = math.hypot(potencia_ativa, potencia_reativa_ref)
    s_novo = s_ref * (tensao_terminal / tensao_referencia)
    discriminante = s_novo * s_novo - potencia_ativa * potencia_ativa
    if discriminante < 0:
        return float("inf") if potencia_reativa_ref >= 0 else float("-inf")
    q_abs = math.sqrt(discriminante)
    return q_abs if potencia_reativa_ref >= 0 else -q_abs


def EscalarLimiteQPorTensaoQuadratica(
    potencia_reativa_ref: float,
    tensao_terminal: float,
    tensao_referencia: float = 1.0,
) -> float:
    """
    Escala Q proporcional a (Vt/Vt_ref)² - UEL / limites de estabilidade.
    """
    if tensao_referencia <= 0:
        return potencia_reativa_ref
    fator = (tensao_terminal / tensao_referencia) ** 2
    return potencia_reativa_ref * fator


def TensaoProximaDaReferencia(
    tensao_terminal: float,
    tensao_referencia: float,
    tolerancia: float = 1e-3,
) -> bool:
    """True se Vt ≈ Vt_ref (curva tabular do fabricante aplicável direto)."""
    return abs(tensao_terminal - tensao_referencia) <= tolerancia
