"""Testes da corrente de estator (Is) no SCL e na verificaÃ§Ã£o."""

from pathlib import Path

from src.constantes.grandezas import NomeLimite
from src.matematica.eletrica import CorrenteEstatorPu
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


def test_is_calc_igual_s_sobre_vt():
    assert abs(CorrenteEstatorPu(0.5, 1.0) - 0.5) < 1e-9
    assert abs(CorrenteEstatorPu(0.35, 0.7) - 0.5) < 1e-9


def test_is_zero_sincroniza_com_pq_vt():
    s = _criar()
    s.atualizar_ponto_operacional(
        potencia_ativa=0.3,
        potencia_reativa=0.4,
        tensao=1.0,
        corrente_estator=0.0,
        em_por_unidade=True,
    )
    g = s.obter_grandezas_campo_pu()
    assert g["Is_origem"] == "calculada"
    assert abs(g["Is"] - g["Is_calc"]) < 1e-9
    assert abs(g["Is_calc"] - 0.5) < 1e-6  # S=0.5, Vt=1


def test_is_medida_acima_imax_marca_fora():
    s = _criar()
    s.atualizar_ponto_operacional(
        potencia_ativa=0.2,
        potencia_reativa=0.1,
        tensao=1.0,
        corrente_estator=1.05,
        corrente_campo=1.0,
        em_por_unidade=True,
    )
    res = s.verificar_capabilidade()
    assert res.dentro_da_curva is False
    assert res.limite_restritivo == NomeLimite.ESTATOR


def test_envelope_usa_imax_nao_is_operacao():
    s = _criar()
    s.avaliador.configuracao.corrente_estator_maxima_pu = 0.8
    env = s.avaliador.calcular_envelope(
        0.0, 1.0, 27.5, 1780.0, corrente_estator_maxima_pu=0.8
    )
    # Em P=0, SCL = Â±Imax = Â±0.8
    assert abs(env.limites_superiores[NomeLimite.ESTATOR] - 0.8) < 1e-6


def test_tracado_inclui_circulo_operacao_quando_is_menor_imax():
    s = _criar()
    s.atualizar_ponto_operacional(
        potencia_ativa=0.3,
        potencia_reativa=0.2,
        tensao=1.0,
        corrente_estator=0.0,
        em_por_unidade=True,
    )
    pontos = s.recalcular_curva()
    assert "CirculoPotenciaAparente" in pontos.curvas_individuais_superiores
    assert "CirculoOperacaoIs" in pontos.curvas_individuais_superiores
