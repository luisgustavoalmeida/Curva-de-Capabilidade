"""Testes de CSVs opcionais e cópia do template."""

import json
import shutil
from pathlib import Path

from src.constantes.grandezas import NomeLimite
from src.simulador.fabrica import CriarSimuladorDeDiretorio
from src.utilitarios.nova_usina import CriarUsina


DIRETORIO_USINA = Path(__file__).resolve().parents[1] / "dados" / "usina"


def _pasta_so_placa(tmp_path: Path) -> str:
    """Template sem CSVs de fabricante (só JSON de placa + limites analíticos)."""
    destino = tmp_path / "so_placa"
    shutil.copytree(DIRETORIO_USINA, destino)
    for csv in destino.glob("*.csv"):
        csv.unlink()
    curvas = json.loads((destino / "curvas.json").read_text(encoding="utf-8"))
    for chave in list(curvas):
        if chave.startswith("Arquivo"):
            del curvas[chave]
    (destino / "curvas.json").write_text(
        json.dumps(curvas, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (destino / "turbina.json").unlink(missing_ok=True)
    return str(destino)


def test_template_usina_carrega_com_csv():
    s = CriarSimuladorDeDiretorio(str(DIRETORIO_USINA))
    assert s.avaliador.configuracao.curva_sobre_excitacao is not None
    pontos = s.recalcular_curva()
    assert len(pontos.potencias_ativas) > 10


def test_sem_csv_envelope_scl_oel(tmp_path):
    s = CriarSimuladorDeDiretorio(_pasta_so_placa(tmp_path))
    assert s.avaliador.configuracao.curva_sobre_excitacao is None
    assert s.avaliador.configuracao.curva_estabilidade is None
    env = s.avaliador.calcular_envelope(0.0, 1.0)
    assert env.regiao_valida
    assert NomeLimite.ESTATOR in env.limites_superiores
    assert NomeLimite.SOBRE_EXCITACAO in env.limites_superiores
    assert env.limite_inferior_efetivo < 0
    assert abs(env.limite_inferior_efetivo + 1.0) < 0.05
    assert env.limite_superior_efetivo > 0.4


def test_criar_usina_copia_template(tmp_path):
    dest = CriarUsina(
        tmp_path,
        "teste_copia",
        template=DIRETORIO_USINA,
        identificacao="Teste Cópia",
    )
    assert (dest / "gerador.json").exists()
    assert (dest / "curvas.json").exists()
    assert list(dest.glob("*.csv"))
    dados = json.loads((dest / "gerador.json").read_text(encoding="utf-8"))
    assert dados["Identificacao"] == "Teste Cópia"
    s = CriarSimuladorDeDiretorio(str(dest))
    res = s.executar_simulacao_completa()
    assert res["PontosCurva"].potencias_ativas


def test_csv_apontado_mas_ausente_nao_quebra(tmp_path):
    dest = Path(_pasta_so_placa(tmp_path))
    curvas = json.loads((dest / "curvas.json").read_text(encoding="utf-8"))
    curvas["ArquivoEstabilidade"] = "estabilidade.csv"
    (dest / "curvas.json").write_text(
        json.dumps(curvas, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    s = CriarSimuladorDeDiretorio(str(dest))
    assert s.avaliador.configuracao.curva_estabilidade is None
    env = s.avaliador.calcular_envelope(0.3, 1.0, 0.0, 1000.0)
    assert env.regiao_valida
