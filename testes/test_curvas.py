"""Testes do traÃ§ado operacional em p.u. com Vt (conjunto usina)."""

from pathlib import Path

from src.curvas.limites.analiticos_tensao import (
    CalcularLimiteEstatorPorTensao,
    CalcularLimiteCampoPorTensao,
)
from src.curvas.limites.estator import CalcularLimiteEstator
from src.utilitarios.carregador import CarregadorDados
from src.simulador.motor import SimuladorCapabilidade
from src.matematica.por_unidade import CriarBasesDoGerador


DIRETORIO_EXEMPLO = str(
    Path(__file__).resolve().parents[1] / "dados" / "usina"
)


def _criar_simulador_exemplo():
    carregador = CarregadorDados(DIRETORIO_EXEMPLO)
    gerador = carregador.carregar_gerador()
    turbina = carregador.carregar_turbina()
    configuracao = carregador.carregar_configuracao_curvas()
    return SimuladorCapabilidade(gerador, configuracao, turbina)


def test_limite_estator_pu():
    inferior, superior = CalcularLimiteEstator(0.3, 1.0)
    assert superior > 0
    assert inferior == -superior
    assert abs(superior - 0.9539) < 0.01


def test_estator_depende_de_vt():
    _, q_vt1 = CalcularLimiteEstatorPorTensao(0.0, 1.0)
    _, q_vt095 = CalcularLimiteEstatorPorTensao(0.0, 0.95)
    assert abs(q_vt1 - 1.0) < 1e-9
    assert abs(q_vt095 - 0.95) < 1e-9
    assert q_vt095 < q_vt1


def test_campo_depende_de_vt():
    q1 = CalcularLimiteCampoPorTensao(0.0, 1.0, 0.8, 1.6)
    q095 = CalcularLimiteCampoPorTensao(0.0, 0.95, 0.8, 1.6)
    assert q1 > 0
    assert abs(q095 - q1) > 0.01


def test_bases_por_unidade():
    bases = CriarBasesDoGerador(194.5, 13.8)
    assert abs(bases.potencia_ativa_para_pu(175.05) - 0.9) < 1e-6


def test_carregamento_exemplo_tracado():
    carregador = CarregadorDados(DIRETORIO_EXEMPLO)
    gerador = carregador.carregar_gerador()
    assert abs(gerador.reatancia_direta - 0.8) < 1e-6
    assert "Sobradinho" in gerador.identificacao
    configuracao = carregador.carregar_configuracao_curvas()
    assert configuracao.unidade == "pu"
    assert abs(configuracao.potencia_mecanica_maxima_pu - 0.9) < 1e-6
    assert configuracao.curva_sobre_excitacao is not None
    assert configuracao.curva_estabilidade is not None


def test_envelope_ons_vt1_em_vazio():
    """Em P=0, Vt=1: Qsupâ‰ˆOEL(~0.74), Qinfâ‰ˆUEL(~-0.60)."""
    simulador = _criar_simulador_exemplo()
    env = simulador.avaliador.calcular_envelope(0.0, 1.0)
    assert 0.70 < env.limite_superior_efetivo < 0.80
    assert -0.65 < env.limite_inferior_efetivo < -0.55


def test_envelope_ons_vt1_em_pmec_max():
    """Em P=0.9, Vt=1: estator limita Qsupâ‰ˆ0.436."""
    simulador = _criar_simulador_exemplo()
    env = simulador.avaliador.calcular_envelope(0.9, 1.0)
    assert 0.40 < env.limite_superior_efetivo < 0.50
    assert env.limite_inferior_efetivo < 0


def test_vt_altera_envelope():
    simulador = _criar_simulador_exemplo()
    env1 = simulador.avaliador.calcular_envelope(0.5, 1.0)
    env095 = simulador.avaliador.calcular_envelope(0.5, 0.95)
    assert env095.limite_superior_efetivo != env1.limite_superior_efetivo


def test_simulador_tracado_completo():
    simulador = _criar_simulador_exemplo()
    resultado = simulador.executar_simulacao_completa()
    pontos = resultado["PontosCurva"]
    assert pontos.unidade == "pu"
    assert pontos.contorno_fechado
    assert max(pontos.potencias_ativas) <= 0.91
    potencias = [potencia for potencia, _ in pontos.limite_superior]
    assert potencias == sorted(potencias)


def test_contorno_fechado_sem_zigzag():
    simulador = _criar_simulador_exemplo()
    pontos = simulador.recalcular_curva(0.0, 0.9, 0.05)
    contorno = pontos.contorno_fechado
    assert len(contorno) > 10
    qs = [q for q, p in contorno]
    assert min(qs) > -1.0
    assert max(qs) < 1.1
