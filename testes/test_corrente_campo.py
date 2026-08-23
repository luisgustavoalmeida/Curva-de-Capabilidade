"""Testes do efeito da corrente de campo (If) na curva de capabilidade."""

from pathlib import Path

from src.curvas.limites.analiticos_tensao import (
    CalcularFatorCorrenteCampo,
    CalcularTensaoInternaPorCorrenteCampo,
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


def test_fator_corrente_campo():
    assert CalcularFatorCorrenteCampo(0, 1780) == 1.0
    assert abs(CalcularFatorCorrenteCampo(890, 1780) - 0.5) < 1e-9
    assert abs(CalcularFatorCorrenteCampo(1780, 1780) - 1.0) < 1e-9


def test_efd_proporcional_a_if():
    """Modelo OCC bipartido: entreferro atÃ© If_NL; saturaÃ§Ã£o atÃ© If_FL."""
    efd_rated = CalcularTensaoInternaPorCorrenteCampo(1780, 1780, 1.6, 907)
    efd_nl = CalcularTensaoInternaPorCorrenteCampo(907, 1780, 1.6, 907)
    efd_meio_ag = CalcularTensaoInternaPorCorrenteCampo(453.5, 1780, 1.6, 907)
    assert abs(efd_rated - 1.6) < 1e-9
    assert abs(efd_nl - 1.0) < 1e-9
    assert abs(efd_meio_ag - 0.5) < 1e-9


def test_if_reduzida_restringe_q_superior():
    simulador = _criar_simulador()
    env_nominal = simulador.avaliador.calcular_envelope(
        0.3, 1.0, 27.5, corrente_campo=1780.0
    )
    env_reduzida = simulador.avaliador.calcular_envelope(
        0.3, 1.0, 27.5, corrente_campo=1200.0
    )
    assert env_reduzida.limite_superior_efetivo < env_nominal.limite_superior_efetivo


def test_curva_recalcula_com_corrente_campo():
    simulador = _criar_simulador()
    simulador.atualizar_ponto_operacional(corrente_campo=1780.0, queda=27.5)
    pontos_nom = simulador.recalcular_curva()
    q_nom = max(q for _, q in pontos_nom.limite_superior)

    simulador.atualizar_ponto_operacional(corrente_campo=1000.0)
    pontos_baixa = simulador.recalcular_curva()
    q_baixa = max(q for _, q in pontos_baixa.limite_superior)

    assert q_baixa < q_nom


def test_if_acima_nominal_expande_ate_oel_pico():
    """If > If_FL usa Efd elevado, limitado pelo OEL de pico (nÃ£o pelo contÃ­nuo)."""
    simulador = _criar_simulador()
    env_nominal = simulador.avaliador.calcular_envelope(
        0.3, 1.0, 27.5, corrente_campo=1780.0
    )
    env_elevada = simulador.avaliador.calcular_envelope(
        0.3, 1.0, 27.5, corrente_campo=2000.0
    )
    assert env_elevada.limite_superior_efetivo > env_nominal.limite_superior_efetivo
