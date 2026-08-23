"""Testes das correções da revisão técnica (Pmec, OEL/Vt, OCC, SCL)."""

import math
from pathlib import Path

from src.constantes.grandezas import NomeLimite
from src.curvas.limites.analiticos_tensao import CalcularTensaoInternaPorCorrenteCampo
from src.curvas.limites.escala_tensao import (
    EscalarLimiteQPorTensao,
    EscalarLimiteQPorTensaoQuadratica,
)
from src.simulador.fabrica import CriarSimuladorDeDiretorio
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


def test_pmec_fora_marca_fora_da_curva():
    simulador = _criar_simulador()
    # P = 1.05 pu > Pmec_max = 0.9
    simulador.atualizar_ponto_operacional(
        potencia_ativa=1.05,
        potencia_reativa=0.0,
        tensao=1.0,
        corrente_campo=1.0,
        em_por_unidade=True,
    )
    resultado = simulador.verificar_capabilidade()
    assert resultado.dentro_da_curva is False
    assert resultado.limite_restritivo == NomeLimite.PMEC_MAX
    assert any("Pmec" in m for m in resultado.mensagens)


def test_scl_usa_imax_real():
    simulador = _criar_simulador()
    simulador.avaliador.configuracao.corrente_estator_maxima_pu = 0.85
    simulador.atualizar_ponto_operacional(
        potencia_ativa=0.2,
        potencia_reativa=0.1,
        tensao=1.0,
        corrente_estator=0.95,
        corrente_campo=1.0,
        em_por_unidade=True,
    )
    resultado = simulador.verificar_capabilidade()
    assert resultado.dentro_da_curva is False
    assert any("Imax=0.8500" in m for m in resultado.mensagens)


def test_oel_tabular_nao_descartado_com_vt_diferente():
    simulador = _criar_simulador()
    env_vt1 = simulador.avaliador.calcular_envelope(0.0, 1.0, 27.5, 1780.0)
    env_vt095 = simulador.avaliador.calcular_envelope(0.0, 0.95, 27.5, 1780.0)
    assert NomeLimite.SOBRE_EXCITACAO in env_vt095.limites_superiores
    # SCL encolhe com Vt; OEL em Vtâ‰ ref usa analÃ­tico (nÃ£o escala circular)
    assert env_vt095.limites_superiores[NomeLimite.ESTATOR] < env_vt1.limites_superiores[
        NomeLimite.ESTATOR
    ]
    assert env_vt095.regiao_valida and env_vt095.limite_superior_efetivo > 0.5


def test_escala_q_por_tensao_preserva_raio():
    q = EscalarLimiteQPorTensao(0.6, 0.0, 0.95, 1.0)
    assert abs(q - 0.6 * 0.95) < 1e-9
    q2 = EscalarLimiteQPorTensaoQuadratica(-0.5, 0.9, 1.0)
    assert abs(q2 - (-0.5 * 0.81)) < 1e-9
    # Fora do arco: nÃ£o vincula (evita muro em Q=0)
    assert EscalarLimiteQPorTensao(0.5, 0.8, 0.7, 1.0) == float("inf")
    assert EscalarLimiteQPorTensao(-0.5, 0.8, 0.7, 1.0) == float("-inf")


def test_vt_baixa_regiao_continua_sem_muro_q0():
    """Com Vt=0.7, Qsup > 0 atÃ© perto de S=Vt; sem parede artificial em Q=0."""
    simulador = _criar_simulador()
    for p in [i * 0.05 for i in range(14)]:  # 0 â€¦ 0.65
        env = simulador.avaliador.calcular_envelope(p, 0.7, 27.5, 1780.0)
        assert env.regiao_valida, f"P={p} deveria ser vÃ¡lido"
        assert env.limite_superior_efetivo > 0.05, (
            f"P={p}: Qsup={env.limite_superior_efetivo} (muro Q=0?)"
        )
        assert env.limite_inferior_efetivo < -0.05
    # P > VtÂ·Imax: sem regiÃ£o
    env_alto = simulador.avaliador.calcular_envelope(0.85, 0.7, 27.5, 1780.0)
    assert env_alto.regiao_valida is False


def test_tracado_vt_baixa_capado_no_circulo_s():
    simulador = _criar_simulador()
    simulador.atualizar_ponto_operacional(tensao=0.7, em_por_unidade=True)
    pontos = simulador.recalcular_curva()
    assert max(pontos.potencias_ativas) < 0.70
    # Sem salto espÃºrio de Qsup no topo (bug do Ã¡pice Pâ‰ˆVt)
    for p, q in pontos.limite_superior:
        assert q <= math.sqrt(max(0.0, 0.49 - p * p)) + 1e-6
        if p < 0.68:
            assert q > 0.05, f"P={p} Qsup={q}"
    for p, q in pontos.limite_inferior:
        assert q >= -math.sqrt(max(0.0, 0.49 - p * p)) - 1e-6
    # Contorno contÃ­nuo: sem salto absurdo de Qsup
    qs = [q for _, q in pontos.limite_superior]
    assert max(qs) < 0.75
    assert all(abs(qs[i] - qs[i - 1]) < 0.2 for i in range(1, len(qs)))


def test_efd_modelo_occ_bipartido():
    # If_NL=907, If_FL=1780, Efd_rated=1.6
    efd_fl = CalcularTensaoInternaPorCorrenteCampo(1780, 1780, 1.6, 907)
    efd_nl = CalcularTensaoInternaPorCorrenteCampo(907, 1780, 1.6, 907)
    efd_baixo = CalcularTensaoInternaPorCorrenteCampo(453.5, 1780, 1.6, 907)
    assert abs(efd_fl - 1.6) < 1e-9
    assert abs(efd_nl - 1.0) < 1e-9
    assert abs(efd_baixo - 0.5) < 1e-9


def test_plot_mantem_scl_e_circulo():
    pontos = _criar_simulador().recalcular_curva()
    superiores = pontos.curvas_individuais_superiores
    assert "CirculoPotenciaAparente" in superiores
    assert "LimiteEstator" in superiores


def test_uel_escala_com_vt():
    simulador = _criar_simulador()
    env1 = simulador.avaliador.calcular_envelope(0.3, 1.0, 27.5, 1780.0)
    env09 = simulador.avaliador.calcular_envelope(0.3, 0.9, 27.5, 1780.0)
    q_uel_1 = env1.limites_inferiores[NomeLimite.ESTABILIDADE]
    q_uel_09 = env09.limites_inferiores[NomeLimite.ESTABILIDADE]
    assert abs(q_uel_09 - q_uel_1 * 0.81) < 1e-6


def test_aquecimento_extremo_plotado_como_referencia():
    simulador = _criar_simulador()
    # Sem curva de fabricante: referÃªncia analÃ­tica no plot, fora do envelope
    assert simulador.avaliador.configuracao.incluir_aquecimento_extremo_no_envelope is False
    env = simulador.avaliador.calcular_envelope(0.0, 1.0, 27.5, 1780.0)
    assert NomeLimite.AQUECIMENTO_EXTREMO in env.limites_inferiores
    # UEL continua restritivo no exemplo
    assert env.limite_inferior_restritivo == NomeLimite.ESTABILIDADE


def test_regiao_invalida_nao_colapsa():
    simulador = _criar_simulador()
    cfg = simulador.avaliador.configuracao
    cfg.incluir_aquecimento_extremo_no_envelope = True
    # Qinf forÃ§ado acima de Qsup tÃ­pico (~0.77 em P=0)
    cfg.q_aquecimento_extremo_vazio_pu = 0.95
    env = simulador.avaliador.calcular_envelope(0.0, 1.0, 27.5, 1780.0)
    assert env.limite_inferior_efetivo > env.limite_superior_efetivo
    assert env.regiao_valida is False
    # NÃ£o colapsa ao ponto mÃ©dio
    medio = 0.5 * (env.limite_superior_efetivo + env.limite_inferior_efetivo)
    assert abs(env.limite_superior_efetivo - medio) > 1e-6
    assert abs(env.limite_inferior_efetivo - medio) > 1e-6


def test_fabrica_exemplo_ainda_funciona():
    simulador = CriarSimuladorDeDiretorio(DIRETORIO)
    res = simulador.executar_simulacao_completa()
    assert "PontosCurva" in res
    assert res["ResultadoCapabilidade"].limite_superior_efetivo > 0
