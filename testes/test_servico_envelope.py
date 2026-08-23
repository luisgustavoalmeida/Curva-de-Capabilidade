"""Testes do serviço de envelope dinâmico multi-UG."""

import json
from pathlib import Path

from src.servico.envelope_dinamico import (
    CarregarUnidades,
    ExecutarCiclo,
    ListarPastasUg,
    ProcessarUnidade,
    RodarServico,
)


RAIZ_DADOS = Path(__file__).resolve().parents[1] / "dados"


def test_listar_pastas_ug():
    pastas = ListarPastasUg(RAIZ_DADOS)
    nomes = {p.name for p in pastas}
    assert "usina" in nomes


def test_carregar_e_ciclo_uma_ug():
    unidades = CarregarUnidades(RAIZ_DADOS, apenas=["usina"])
    assert len(unidades) == 1
    assert unidades[0].id == "usina"
    resultados = ExecutarCiclo(unidades)
    assert len(resultados) == 1
    assert resultados[0].ok
    saida = unidades[0].diretorio / "exportacao_elipse"
    assert (saida / "CurvaCapabilidade_LimiteSuperior.csv").exists()
    assert (saida / "CurvaCapabilidade_LimiteInferior.csv").exists()


def test_campo_json_altera_ponto():
    unidades = CarregarUnidades(RAIZ_DADOS, apenas=["usina"])
    u = unidades[0]
    caminho = u.diretorio / "campo.json"
    original = caminho.read_text(encoding="utf-8")
    try:
        caminho.write_text(
            json.dumps(
                {
                    "EmPorUnidade": True,
                    "P": 0.2,
                    "Q": 0.1,
                    "Vt": 1.0,
                    "If": 1.0,
                    "f": 1.0,
                    "H": 1.0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        res = ProcessarUnidade(u)
        assert res.ok
        g = u.simulador.obter_grandezas_campo_pu()
        assert abs(g["P"] - 0.2) < 1e-6
        assert abs(g["Q"] - 0.1) < 1e-6
    finally:
        caminho.write_text(original, encoding="utf-8")


def test_rodar_servico_uma_vez():
    RodarServico(RAIZ_DADOS, apenas=["usina"], uma_vez=True)
