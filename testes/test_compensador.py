"""Testes de compensador síncrono (P ≈ 0, sem turbina)."""

import json
import shutil
from pathlib import Path

from src.constantes.grandezas import TipoMaquina
from src.simulador.fabrica import CriarSimuladorDeDiretorio


DIRETORIO_USINA = str(Path(__file__).resolve().parents[1] / "dados" / "usina")


def _pasta_compensador(tmp_path: Path) -> str:
    """Cópia do template com TipoMaquina = CompensadorSincrono."""
    destino = tmp_path / "compensador"
    shutil.copytree(DIRETORIO_USINA, destino)
    exportacao = destino / "exportacao_elipse"
    if exportacao.exists():
        shutil.rmtree(exportacao)
    (destino / "turbina.json").unlink(missing_ok=True)
    (destino / "turbina_hidraulica.csv").unlink(missing_ok=True)

    gerador = json.loads((destino / "gerador.json").read_text(encoding="utf-8"))
    gerador["TipoMaquina"] = "CompensadorSincrono"
    gerador["Identificacao"] = "Compensador — teste"
    gerador["PotenciaAtivaNominal"] = 0.0
    gerador["FatorPotenciaNominal"] = 0.0
    gerador["PotenciaAtivaMaximaPu"] = 0.0
    gerador["PotenciaAtivaMaxima"] = 0.0
    (destino / "gerador.json").write_text(
        json.dumps(gerador, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    curvas = json.loads((destino / "curvas.json").read_text(encoding="utf-8"))
    curvas["PotenciaAtivaMaxima"] = 0.0
    curvas["PotenciaMecanicaMaximaPu"] = 0.0
    curvas["PotenciaMecanicaMinimaPu"] = 0.0
    (destino / "curvas.json").write_text(
        json.dumps(curvas, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return str(destino)


def test_carrega_tipo_compensador(tmp_path):
    simulador = CriarSimuladorDeDiretorio(_pasta_compensador(tmp_path))
    assert simulador.gerador.tipo_maquina == TipoMaquina.COMPENSADOR_SINCRONO
    assert simulador.gerador.eh_compensador()
    assert simulador.turbina is None
    assert abs(simulador.gerador.obter_potencia_ativa_maxima_pu()) < 1e-9


def test_carrega_tipo_gerador_exemplo():
    simulador = CriarSimuladorDeDiretorio(DIRETORIO_USINA)
    assert simulador.gerador.tipo_maquina == TipoMaquina.GERADOR
    assert not simulador.gerador.eh_compensador()
    assert simulador.turbina is not None


def test_tracado_compensador_em_p_zero(tmp_path):
    simulador = CriarSimuladorDeDiretorio(_pasta_compensador(tmp_path))
    simulador.recalcular_curva()
    pontos = simulador.pontos_curva
    assert pontos is not None
    assert abs(pontos.potencia_mecanica_maxima_pu) < 1e-9
    assert abs(pontos.potencia_mecanica_minima_pu) < 1e-9
    assert "EixoOperacaoCompensador" in pontos.curvas_individuais_superiores
    assert "CirculoPotenciaAparente" in pontos.curvas_individuais_superiores
    assert "LimiteTurbina" not in pontos.curvas_individuais_superiores
    assert "LimitePmecMax" not in pontos.curvas_individuais_superiores
    assert "LimiteQuedaUtil" not in pontos.curvas_individuais_superiores
    assert "LimiteTurbinaMax" not in pontos.curvas_individuais_superiores
    assert pontos.contorno_fechado
    for _, p in pontos.contorno_fechado:
        assert abs(p) <= 0.05


def test_simulacao_completa_compensador(tmp_path):
    simulador = CriarSimuladorDeDiretorio(_pasta_compensador(tmp_path))
    resultado = simulador.executar_simulacao_completa()
    ponto = resultado["PontoOperacional"]
    res = resultado["ResultadoCapabilidade"]
    g = resultado["GrandezasCampoPu"]
    assert abs(ponto.potencia_ativa) < 1e-6
    assert abs(g["P"]) < 1e-6
    assert res.limite_superior_efetivo > 0
    assert res.limite_inferior_efetivo < 0


def test_envelope_referencia_fora_de_pmec(tmp_path):
    """Curvas de referência do compensador varrem P > 0 sem Pmec."""
    simulador = CriarSimuladorDeDiretorio(_pasta_compensador(tmp_path))
    env_restrito = simulador.avaliador.calcular_envelope(
        0.5, 1.0, respeitar_limite_potencia_mecanica=True
    )
    env_ref = simulador.avaliador.calcular_envelope(
        0.5, 1.0, respeitar_limite_potencia_mecanica=False
    )
    assert abs(env_restrito.limite_superior_efetivo) < 1e-9
    assert env_ref.limite_superior_efetivo > 0.3
