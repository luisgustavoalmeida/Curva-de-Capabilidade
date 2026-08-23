"""Testes das entradas de campo em p.u. para posiÃ§Ã£o na curva."""

from pathlib import Path

from src.matematica.por_unidade import CriarBasesCompletas, CriarBasesDoGerador
from src.simulador.motor import SimuladorCapabilidade
from src.utilitarios.carregador import CarregadorDados


DIRETORIO = str(Path(__file__).resolve().parents[1] / "dados" / "usina")


def _criar_simulador():
    carregador = CarregadorDados(DIRETORIO)
    return SimuladorCapabilidade(
        carregador.carregar_gerador(),
        carregador.carregar_configuracao_curvas(),
        carregador.carregar_turbina(),
    )


def test_bases_completas_usina():
    carregador = CarregadorDados(DIRETORIO)
    bases = CriarBasesCompletas(
        carregador.carregar_gerador(),
        carregador.carregar_turbina(),
    )
    assert abs(bases.potencia_aparente_base - 194.5) < 1e-6
    assert abs(bases.tensao_base - 13.8) < 1e-6
    assert abs(bases.corrente_campo_base - 1780.0) < 1e-6
    assert abs(bases.queda_base - 27.5) < 1e-6
    assert bases.corrente_estator_base > 8000.0  # ~8137 A


def test_atualizacao_em_por_unidade():
    simulador = _criar_simulador()
    simulador.atualizar_ponto_operacional(
        potencia_ativa=0.54,
        potencia_reativa=0.20,
        tensao=1.0,
        corrente_campo=1.0,
        corrente_estator=0.0,
        frequencia=1.0,
        queda=1.0,
        em_por_unidade=True,
    )
    g = simulador.obter_grandezas_campo_pu()
    assert abs(g["P"] - 0.54) < 1e-6
    assert abs(g["Q"] - 0.20) < 1e-6
    assert abs(g["Vt"] - 1.0) < 1e-6
    assert abs(g["If"] - 1.0) < 1e-6
    assert abs(g["f"] - 1.0) < 1e-6
    assert abs(g["H"] - 1.0) < 1e-6
    assert g["Is"] > 0  # calculada a partir de S, Vt
    assert abs(simulador.ponto_operacional.corrente_campo - 1780.0) < 1e-3
    assert abs(simulador.ponto_operacional.queda - 27.5) < 1e-6


def test_if_pu_restringe_envelope():
    simulador = _criar_simulador()
    simulador.atualizar_ponto_operacional(
        tensao=1.0, corrente_campo=1.0, queda=1.0, em_por_unidade=True
    )
    env_nom = simulador.avaliador.calcular_envelope(
        0.3, 1.0, simulador.ponto_operacional.queda, simulador.ponto_operacional.corrente_campo
    )
    simulador.atualizar_ponto_operacional(corrente_campo=0.6, em_por_unidade=True)
    env_baixa = simulador.avaliador.calcular_envelope(
        0.3, 1.0, simulador.ponto_operacional.queda, simulador.ponto_operacional.corrente_campo
    )
    assert env_baixa.limite_superior_efetivo < env_nom.limite_superior_efetivo


def test_h_pu_nao_altera_regiao_pmec():
    """Queda Ãºtil (H) Ã© referÃªncia: nÃ£o altera P mÃ¡ximo da regiÃ£o permitida."""
    simulador = _criar_simulador()
    simulador.atualizar_ponto_operacional(queda=1.0, em_por_unidade=True)
    p_nom = max(simulador.recalcular_curva().potencias_ativas)
    simulador.atualizar_ponto_operacional(queda=0.8, em_por_unidade=True)
    p_baixa = max(simulador.recalcular_curva().potencias_ativas)
    assert abs(p_baixa - p_nom) < 1e-6
    # TraÃ§o de referÃªncia se move com H
    ref_nom = simulador.avaliador.obter_limites_potencia_ativa_horizontais(
        simulador.ponto_operacional.queda
    )["LimiteQuedaUtil"]
    simulador.atualizar_ponto_operacional(queda=1.0, em_por_unidade=True)
    ref_alta = simulador.avaliador.obter_limites_potencia_ativa_horizontais(
        simulador.ponto_operacional.queda
    )["LimiteQuedaUtil"]
    assert ref_nom < ref_alta


def test_grandezas_campo_completas():
    simulador = _criar_simulador()
    g = simulador.obter_grandezas_campo_pu()
    for chave in ("P", "Q", "Vt", "If", "Is", "f", "H", "S", "fator_potencia"):
        assert chave in g


def test_criarbases_aceita_dois_argumentos():
    bases = CriarBasesDoGerador(194.5, 13.8)
    assert abs(bases.potencia_ativa_para_pu(175.05) - 0.9) < 1e-6
