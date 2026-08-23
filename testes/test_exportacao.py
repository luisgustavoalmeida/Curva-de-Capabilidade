"""Testes de exportação Elipse E3 (séries visuais)."""

from pathlib import Path
import tempfile

from src.exportacao.elipse_e3 import ExportadorElipseE3
from src.utilitarios.carregador import CarregadorDados
from src.simulador.motor import SimuladorCapabilidade


DIRETORIO_DADOS = str(
    Path(__file__).resolve().parents[1] / "dados" / "usina"
)


def test_exportacao_elipse():
    carregador = CarregadorDados(DIRETORIO_DADOS)
    gerador = carregador.carregar_gerador()
    turbina = carregador.carregar_turbina()
    configuracao = carregador.carregar_configuracao_curvas()

    simulador = SimuladorCapabilidade(gerador, configuracao, turbina)
    resultado = simulador.executar_simulacao_completa()

    with tempfile.TemporaryDirectory() as diretorio:
        exportador = ExportadorElipseE3(diretorio)
        arquivos = exportador.exportar_pontos_curva(resultado["PontosCurva"])
        assert "LimiteSuperior" in arquivos
        assert Path(arquivos["LimiteSuperior"]).exists()
        assert "LimiteInferior" in arquivos

        exportador.exportar_resultado_operacional(
            resultado["PontoOperacional"],
            resultado["ResultadoCapabilidade"],
            grandezas_pu=resultado["GrandezasCampoPu"],
            bases=resultado["Bases"],
        )
        csv_resultado = Path(diretorio) / "ResultadoOperacional.csv"
        texto = csv_resultado.read_text(encoding="utf-8")
        assert "P_pu," in texto
        assert "If_pu," in texto
        assert "Base_If_FL," in texto
        assert "DentroDaCurva" not in texto
        assert "MargemOperacional" not in texto

        instrucoes = exportador.gerar_instrucoes_grafico()
        texto_inst = Path(instrucoes).read_text(encoding="utf-8")
        assert "somente visual" in texto_inst.lower() or "só plota" in texto_inst.lower() or "plota" in texto_inst.lower()
        assert "elipse_e3" in texto_inst.lower() or "Chart XY" in texto_inst
        assert not (Path(diretorio) / "CurvaCapabilidade.vbs").exists()

        scripts = exportador.copiar_scripts_elipse(
            Path(__file__).resolve().parents[1]
        )
        assert (Path(scripts) / "scripts" / "BibliotecaCompleta.vbs").exists()
        assert (Path(scripts) / "GUIA_IMPLEMENTACAO.md").exists()

        csv_superior = Path(arquivos["LimiteSuperior"]).read_text(encoding="utf-8")
        primeira_linha_dados = csv_superior.strip().splitlines()[1]
        potencia_reativa, potencia_ativa = primeira_linha_dados.split(",")
        assert float(potencia_reativa) != float(potencia_ativa)
        assert csv_superior.startswith("PotenciaReativaPu,PotenciaAtivaPu")
        assert abs(float(potencia_ativa)) < 2.5  # valores em p.u.
