"""Testes do limitador Volts/Hertz (V/Hz)."""

from pathlib import Path

from src.constantes.grandezas import NomeLimite
from src.curvas.limites.volts_hertz import (
    CalcularFatorDeratingVoltsHertz,
    CalcularRelacaoVoltsHertz,
    VerificarVoltsHertz,
)
from src.simulador.motor import SimuladorCapabilidade
from src.utilitarios.carregador import CarregadorDados


DIRETORIO = str(Path(__file__).resolve().parents[1] / "dados" / "usina")


def _criar():
    c = CarregadorDados(DIRETORIO)
    return SimuladorCapabilidade(
        c.carregar_gerador(),
        c.carregar_configuracao_curvas(),
        c.carregar_turbina(),
    )


def test_relacao_vhz_basica():
    assert abs(CalcularRelacaoVoltsHertz(1.0, 1.0) - 1.0) < 1e-9
    assert abs(CalcularRelacaoVoltsHertz(1.0, 0.95) - (1.0 / 0.95)) < 1e-9


def test_derating_quando_sobrefluxo():
    # Vt=1, f=0.95 â†’ V/Hzâ‰ˆ1.053 > 1.05 â†’ fator < 1
    fator = CalcularFatorDeratingVoltsHertz(1.0, 0.95, 1.05)
    assert fator < 1.0
    assert abs(fator - 1.05 / (1.0 / 0.95)) < 1e-9


def test_sem_derating_em_nominal():
    assert abs(CalcularFatorDeratingVoltsHertz(1.0, 1.0, 1.05) - 1.0) < 1e-9


def test_verificacao_vhz_violada():
    ok, vhz, _ = VerificarVoltsHertz(1.0, 0.95, 1.05)
    assert ok is False
    assert vhz > 1.05


def test_f_baixa_marca_fora_por_vhz():
    s = _criar()
    s.atualizar_ponto_operacional(
        potencia_ativa=0.3,
        potencia_reativa=0.2,
        tensao=1.0,
        corrente_campo=1.0,
        frequencia=0.95,
        em_por_unidade=True,
    )
    res = s.verificar_capabilidade()
    g = s.obter_grandezas_campo_pu()
    assert g["VHz"] > g["VHz_max"]
    assert res.dentro_da_curva is False
    assert res.limite_restritivo == NomeLimite.VOLTS_HERTZ


def test_f_nominal_ok_vhz():
    s = _criar()
    s.atualizar_ponto_operacional(
        potencia_ativa=0.3,
        potencia_reativa=0.2,
        tensao=1.0,
        corrente_campo=1.0,
        frequencia=1.0,
        em_por_unidade=True,
    )
    res = s.verificar_capabilidade()
    g = s.obter_grandezas_campo_pu()
    assert g["VHz_ok"] is True
    assert abs(g["VHz"] - 1.0) < 1e-6
    assert res.limite_restritivo != NomeLimite.VOLTS_HERTZ


def test_derating_reduz_oel_no_envelope():
    s = _criar()
    env_nom = s.avaliador.calcular_envelope(
        0.3, 1.0, 27.5, 1780.0, frequencia_pu=1.0
    )
    env_baixa = s.avaliador.calcular_envelope(
        0.3, 1.0, 27.5, 1780.0, frequencia_pu=0.90
    )
    assert env_baixa.fator_derating_volts_hertz < 1.0
    # Com f=0.90, V/Hzâ‰ˆ1.11 > 1.05 â†’ OEL deratado
    q_oel_nom = env_nom.limites_superiores.get(NomeLimite.SOBRE_EXCITACAO)
    q_oel_baixa = env_baixa.limites_superiores.get(NomeLimite.SOBRE_EXCITACAO)
    if q_oel_nom is not None and q_oel_baixa is not None:
        if q_oel_nom not in (float("inf"), float("-inf")):
            assert q_oel_baixa < q_oel_nom + 1e-9


def test_config_carrega_relacao_vhz():
    s = _criar()
    assert abs(s.avaliador.configuracao.relacao_volts_hertz_maxima_pu - 1.05) < 1e-9
    assert s.avaliador.configuracao.derating_oel_por_volts_hertz is True
