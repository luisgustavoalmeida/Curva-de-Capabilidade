"""Testes de presenÃ§a dos limitadores no traÃ§ado / grÃ¡fico."""

import math
from pathlib import Path

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


def test_limitadores_superiores_completos():
    """ONS: OEL TH, OEL PK, cÃ­rculo S=Sn, IFD e Pmec Max."""
    pontos = _criar_simulador().recalcular_curva()
    superiores = pontos.curvas_individuais_superiores
    assert "LimiteSobreExcitacao" in superiores  # OEL TH
    assert "LimiteRotor" in superiores  # OEL PK
    assert "CirculoPotenciaAparente" in superiores  # S = Sn completo
    assert "LimiteCorrenteCampo" in superiores  # IFD
    assert "LimitePmecMax" in superiores  # Pmec mÃ¡quina
    assert "LimiteQuedaUtil" in superiores  # Pmax pela queda
    assert "LimiteTurbinaMax" in superiores  # teto turbina
    # OEL TH e OEL PK nÃ£o podem ser a mesma curva
    q_th = superiores["LimiteSobreExcitacao"][0][1]
    q_pk = superiores["LimiteRotor"][0][1]
    assert q_pk > q_th
    # SemicÃ­rculo S=Sn: extremos em Pâ‰ˆ0 com |Q|â‰ˆS
    circulo = superiores["CirculoPotenciaAparente"]
    assert abs(circulo[0][0]) < 1e-9  # Pâ‰ˆ0
    assert abs(circulo[0][1] - 1.0) < 1e-6  # Qâ‰ˆ+S
    assert abs(circulo[-1][0]) < 1e-9
    assert abs(circulo[-1][1] + 1.0) < 1e-6  # Qâ‰ˆâˆ’S
    # Retas horizontais de P: cada limitador separado
    pmec = superiores["LimitePmecMax"]
    assert abs(pmec[0][0] - pmec[1][0]) < 1e-9
    assert pmec[1][1] - pmec[0][1] > 1.5
    queda = superiores["LimiteQuedaUtil"]
    assert abs(queda[0][0] - queda[1][0]) < 1e-9
    assert queda[1][1] - queda[0][1] > 1.5
    # Limitadores Q(P) estendem alÃ©m da Pmec e tambÃ©m em P < 0
    oel_pk = superiores["LimiteRotor"]
    p_oel = [p[0] for p in oel_pk]
    assert min(p_oel) <= -0.20
    assert max(p_oel) >= 1.20
    assert max(p_oel) > pmec[0][0]
    # Reta do fator de potÃªncia nominal (origem â†’ ponto em SÂ·fp)
    assert "FatorPotenciaNominal" in superiores
    fp_reta = superiores["FatorPotenciaNominal"]
    assert fp_reta[0] == (0.0, 0.0)
    assert abs(fp_reta[-1][0] - 0.9) < 1e-6
    assert abs(fp_reta[-1][1] - math.sqrt(1.0 - 0.9**2)) < 1e-6


def test_limitadores_inferiores_completos():
    """UEL, MEL, UEL prÃ¡tico, saliÃªncia e end-iron (referÃªncia)."""
    pontos = _criar_simulador().recalcular_curva()
    inferiores = pontos.curvas_individuais_inferiores
    assert "LimiteEstabilidade" in inferiores
    assert "LimiteSubExcitacao" in inferiores
    assert "LimiteEstabilidadePratica" in inferiores
    assert "LimiteSaturacao" in inferiores  # referÃªncia (fora do envelope)
    assert "LimiteAquecimentoExtremoEstator" in inferiores
    assert "LimiteEstator" in inferiores  # SCL inferior

def test_envelope_nao_usa_oel_pk_em_regime_continuo():
    """Com If = If_FL, Qsup = min(OEL TH, SCL), sem prender no OEL PK."""
    simulador = _criar_simulador()
    env = simulador.avaliador.calcular_envelope(0.0, 1.0, 27.5, 1780.0)
    assert env.limite_superior_restritivo.value == "LimiteSobreExcitacao"
    assert abs(env.limites_superiores["LimiteSobreExcitacao"] - env.limite_superior_efetivo) < 1e-6
    assert env.limites_superiores["LimiteRotor"] > env.limite_superior_efetivo
