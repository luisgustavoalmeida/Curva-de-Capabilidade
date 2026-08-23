"""
Limite de potência ativa imposto pela turbina hidráulica.

A potência máxima disponível depende da queda útil:

    P = ρ · g · H · Q · η

Com vazão em regime semelhante (abertura constante):
    Q ∝ √H  ⇒  P_max(H) ≈ P_nom · (H/H_nom)^1,5 · (η/η_nom)

Quando existe curva hidráulica tabulada (H × P), utiliza-se interpolação.

Referências:
    - CHAUDHRY, M.H. Applied Hydraulic Transients.
    - IEC 60193: Hydraulic turbines - model acceptance tests.
    - Dados de colina / curva hidráulica do fabricante.
"""

from typing import Optional

from src.interpolacao.segmentos import InterpolarPorSegmentos
from src.modelos.turbina import Turbina

# Densidade da água e gravidade (SI)
DENSIDADE_AGUA = 1000.0  # kg/m³
ACELERACAO_GRAVIDADE = 9.81  # m/s²


def CalcularLimitePotenciaAtivaTurbina(
    turbina: Turbina,
    queda_atual: float,
    em_por_unidade: bool = False,
    potencia_aparente_base: float = 0.0,
) -> float:
    """
    Retorna a potência ativa máxima da turbina para a queda útil atual.

    Combina capacidade hidráulica (queda) com teto mecânico da turbina:
        P = min(P_hidráulica(H), P_teto_turbina)
    """
    queda = queda_atual if queda_atual > 0 else turbina.queda_nominal
    potencia_mw = _aplicar_tetos(turbina, _calcular_potencia_hidraulica_mw(turbina, queda))

    if em_por_unidade:
        if potencia_aparente_base <= 0:
            raise ValueError("Base Sn necessária para retorno em p.u.")
        return potencia_mw / potencia_aparente_base

    return potencia_mw


def CalcularPotenciaHidraulicaPorQueda(
    turbina: Turbina,
    queda_atual: float,
    em_por_unidade: bool = False,
    potencia_aparente_base: float = 0.0,
) -> float:
    """
    Potência disponível só pela queda útil (curva hidráulica ou afinidade).

    Não aplica o teto PotenciaMaxima da turbina - para plotar o limitador
    de queda separado do teto mecânico.
    """
    queda = queda_atual if queda_atual > 0 else turbina.queda_nominal
    potencia_mw = max(0.0, _calcular_potencia_hidraulica_mw(turbina, queda))

    if em_por_unidade:
        if potencia_aparente_base <= 0:
            raise ValueError("Base Sn necessária para retorno em p.u.")
        return potencia_mw / potencia_aparente_base

    return potencia_mw


def CalcularTetoPotenciaTurbina(
    turbina: Turbina,
    em_por_unidade: bool = False,
    potencia_aparente_base: float = 0.0,
) -> Optional[float]:
    """
    Teto mecânico configurado da turbina (PotenciaMaxima / PotenciaMaximaPu).

    Retorna None se não houver teto explícito.
    """
    if turbina.potencia_maxima > 0:
        potencia_mw = turbina.potencia_maxima
    elif turbina.potencia_maxima_pu > 0 and potencia_aparente_base > 0:
        potencia_mw = turbina.potencia_maxima_pu * potencia_aparente_base
    else:
        return None

    if em_por_unidade:
        if potencia_aparente_base <= 0:
            raise ValueError("Base Sn necessária para retorno em p.u.")
        return potencia_mw / potencia_aparente_base

    return potencia_mw


def _calcular_potencia_hidraulica_mw(turbina: Turbina, queda: float) -> float:
    """
    Potência hidráulica em MW (curva ou afinidade), sem teto mecânico.

    Com H ≤ Hn: usa a curva do fabricante quando existir.
    Com H > Hn: permite subir - max(curva, afinidade), pois tabelas
    costumam saturar no Pnom e não refletem H acima do nominal.
    """
    p_afinidade = CalcularPotenciaHidraulicaPorAfinidade(turbina, queda)

    if not (turbina.curva_hidraulica and turbina.curva_hidraulica.pontos):
        return p_afinidade

    p_curva = InterpolarPorSegmentos(
        turbina.curva_hidraulica.obter_abscissas(),
        turbina.curva_hidraulica.obter_ordenadas(),
        queda,
        turbina.curva_hidraulica.permitir_extrapolacao,
    )

    if turbina.queda_nominal > 0 and queda > turbina.queda_nominal + 1e-9:
        return max(p_curva, p_afinidade)

    return p_curva


def CalcularPotenciaHidraulicaPorAfinidade(
    turbina: Turbina,
    queda: float,
) -> float:
    """
    Estima P_max pela lei de afinidade hidráulica.

    Equação:
        P(H) = P_nom · (H/H_nom)^expoente · (η/η_nom)

    Expoente padrão:
        Francis / Kaplan: 1,5  (Q ∝ √H)
        Pelton / linear: 1,0   (se configurado)
    """
    if turbina.queda_nominal <= 0:
        raise ValueError("Queda nominal da turbina deve ser positiva.")

    razao_queda = queda / turbina.queda_nominal
    if razao_queda < 0:
        return 0.0

    expoente = turbina.expoente_queda
    rendimento_relativo = 1.0
    if turbina.curva_rendimento and turbina.curva_rendimento.pontos:
        rendimento = InterpolarPorSegmentos(
            turbina.curva_rendimento.obter_abscissas(),
            turbina.curva_rendimento.obter_ordenadas(),
            queda,
            turbina.curva_rendimento.permitir_extrapolacao,
        )
        if turbina.rendimento_nominal > 0:
            rendimento_relativo = rendimento / turbina.rendimento_nominal

    return turbina.potencia_nominal * (razao_queda**expoente) * rendimento_relativo


def CalcularPotenciaHidraulicaAbsoluta(
    queda: float,
    vazao: float,
    rendimento: float,
) -> float:
    """
    Calcula potência hidráulica absoluta.

    Equação: P[MW] = ρ · g · H · Q · η / 10^6
    """
    return (DENSIDADE_AGUA * ACELERACAO_GRAVIDADE * queda * vazao * rendimento) / 1_000_000.0


def _aplicar_tetos(turbina: Turbina, potencia: float) -> float:
    """Aplica teto de potência máxima configurada da turbina."""
    potencia = max(0.0, potencia)
    if turbina.potencia_maxima > 0:
        potencia = min(potencia, turbina.potencia_maxima)
    return potencia
