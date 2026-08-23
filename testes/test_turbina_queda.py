"""Testes da queda Ãºtil: referÃªncia no grÃ¡fico, sem limitar a regiÃ£o P."""

from pathlib import Path

from src.curvas.limites.turbina import (
    CalcularLimitePotenciaAtivaTurbina,
    CalcularPotenciaHidraulicaPorAfinidade,
)
from src.utilitarios.carregador import CarregadorDados
from src.simulador.motor import SimuladorCapabilidade


DIRETORIO = str(Path(__file__).resolve().parents[1] / "dados" / "usina")


def _criar_simulador():
    carregador = CarregadorDados(DIRETORIO)
    return SimuladorCapabilidade(
        carregador.carregar_gerador(),
        carregador.carregar_configuracao_curvas(),
        carregador.carregar_turbina(),
    )


def test_queda_reduz_potencia_por_afinidade():
    carregador = CarregadorDados(DIRETORIO)
    turbina = carregador.carregar_turbina()
    # Sem curva: usar afinidade isolada
    turbina.curva_hidraulica = None
    p_nom = CalcularPotenciaHidraulicaPorAfinidade(turbina, turbina.queda_nominal)
    p_baixa = CalcularPotenciaHidraulicaPorAfinidade(turbina, turbina.queda_nominal * 0.8)
    assert abs(p_nom - turbina.potencia_nominal) < 1e-6
    assert p_baixa < p_nom
    # (0.8)^1.5 â‰ˆ 0.7155
    assert abs(p_baixa / p_nom - (0.8**1.5)) < 1e-6


def test_queda_nao_altera_pmec_max_da_regiao():
    """H acima ou abaixo do nominal nÃ£o muda Pmax da regiÃ£o permitida."""
    simulador = _criar_simulador()
    p_nominal = simulador.avaliador.obter_potencia_ativa_maxima(27.5)
    p_baixa = simulador.avaliador.obter_potencia_ativa_maxima(22.0)
    p_alta = simulador.avaliador.obter_potencia_ativa_maxima(33.0)
    assert abs(p_nominal - p_baixa) < 1e-9
    assert abs(p_nominal - p_alta) < 1e-9
    assert abs(p_nominal - simulador.avaliador.configuracao.potencia_mecanica_maxima_pu) < 1e-9


def test_curva_regiao_independente_da_queda():
    """Envelope operacional (P) fixo; sÃ³ o traÃ§o de referÃªncia QuedaUtil se move."""
    simulador = _criar_simulador()
    simulador.atualizar_ponto_operacional(queda=27.5)
    pontos_nom = simulador.recalcular_curva()
    simulador.atualizar_ponto_operacional(queda=22.0)
    pontos_baixa = simulador.recalcular_curva()
    assert abs(max(pontos_baixa.potencias_ativas) - max(pontos_nom.potencias_ativas)) < 1e-6
    p_queda_nom = pontos_nom.curvas_individuais_superiores["LimiteQuedaUtil"][0][0]
    p_queda_baixa = pontos_baixa.curvas_individuais_superiores["LimiteQuedaUtil"][0][0]
    assert p_queda_baixa < p_queda_nom
    p_pmec_nom = pontos_nom.curvas_individuais_superiores["LimitePmecMax"][0][0]
    p_pmec_baixa = pontos_baixa.curvas_individuais_superiores["LimitePmecMax"][0][0]
    assert abs(p_pmec_nom - p_pmec_baixa) < 1e-9
    # Com H baixa, referÃªncia de queda fica Ã  esquerda da Pmec (nÃ£o corta a regiÃ£o)
    assert p_queda_baixa < p_pmec_baixa


def test_limites_p_horizontais_separados():
    simulador = _criar_simulador()
    limites = simulador.avaliador.obter_limites_potencia_ativa_horizontais(27.5)
    assert "LimitePmecMax" in limites
    assert "LimiteQuedaUtil" in limites
    assert "LimiteTurbinaMax" in limites
    assert limites["LimitePmecMax"] <= limites["LimiteTurbinaMax"] + 1e-6


def test_queda_acima_nominal_sobe_referencia():
    """Com H > 1 pu a linha de queda Ãºtil sobe (afinidade / curva)."""
    simulador = _criar_simulador()
    lim_nom = simulador.avaliador.obter_limites_potencia_ativa_horizontais(27.5)
    lim_alta = simulador.avaliador.obter_limites_potencia_ativa_horizontais(30.25)  # 1.1 pu
    assert lim_alta["LimiteQuedaUtil"] > lim_nom["LimiteQuedaUtil"]
    # RegiÃ£o permitida permanece na Pmec
    assert abs(
        simulador.avaliador.obter_potencia_ativa_maxima(30.25)
        - simulador.avaliador.obter_potencia_ativa_maxima(27.5)
    ) < 1e-9


def test_limite_turbina_com_curva_hidraulica():
    carregador = CarregadorDados(DIRETORIO)
    turbina = carregador.carregar_turbina()
    assert turbina.curva_hidraulica is not None
    p_27 = CalcularLimitePotenciaAtivaTurbina(turbina, 27.5)
    p_22 = CalcularLimitePotenciaAtivaTurbina(turbina, 22.0)
    assert p_22 < p_27
