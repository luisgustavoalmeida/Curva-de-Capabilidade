"""
Limite do rotor por corrente de campo (sobre-excitação).

Referências:
    - KUNDUR, P. Power System Stability and Control. Seção 3.4.2.
    - IEEE Std 1110-2002: Field heating limit (over-excitation).
    - ONS BD Anatem: curva OEL em p.u.
"""

from typing import Optional

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.gerador import GeradorSincrono
from src.modelos.tabela_curva import TabelaCurva


def CalcularLimiteRotor(
    potencia_ativa: float,
    curva_rotor: Optional[TabelaCurva],
    gerador: GeradorSincrono,
    em_por_unidade: bool = True,
) -> float:
    """Calcula o limite superior de Q pela curva do rotor."""
    return CalcularLimiteSobreExcitacao(
        potencia_ativa, curva_rotor, gerador, em_por_unidade
    )


def CalcularLimiteSobreExcitacao(
    potencia_ativa: float,
    curva_sobre_excitacao: Optional[TabelaCurva],
    gerador: GeradorSincrono,
    em_por_unidade: bool = True,
) -> float:
    """
    Calcula limite de sobre-excitação (rotor).

    Entradas:
        potencia_ativa: P em p.u. (ou MW se em_por_unidade=False)
        curva_sobre_excitacao: tabela (P, Q) na mesma unidade
    """
    if curva_sobre_excitacao and curva_sobre_excitacao.pontos:
        return InterpolarPorSegmentos(
            curva_sobre_excitacao.obter_abscissas(),
            curva_sobre_excitacao.obter_ordenadas(),
            potencia_ativa,
            curva_sobre_excitacao.permitir_extrapolacao,
        )

    if em_por_unidade:
        return gerador.calcular_potencia_reativa_nominal_pu() * 1.15
    return gerador.calcular_potencia_reativa_nominal() * 1.15
