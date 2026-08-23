"""Testes da conversÃ£o em por unidade e convenÃ§Ã£o grÃ¡fica."""

from src.matematica.por_unidade import CriarBasesDoGerador
from src.utilitarios.grafico import ConverterParaGrafico, PontoOperacionalParaGrafico


def test_converter_para_grafico():
    pontos_internos = [(0.5, 0.2), (0.8, -0.3)]
    pontos_grafico = ConverterParaGrafico(pontos_internos)
    assert pontos_grafico[0] == (0.2, 0.5)
    assert pontos_grafico[1] == (-0.3, 0.8)


def test_ponto_operacional_para_grafico():
    assert PontoOperacionalParaGrafico(0.72, 0.28) == (0.28, 0.72)


def test_conversao_pu_sn():
    bases = CriarBasesDoGerador(194.5, 13.8)
    assert abs(bases.potencia_reativa_para_pu(84.78058445186609) - 0.435889894354) < 1e-6
    assert abs(bases.tensao_para_pu(13.8) - 1.0) < 1e-9
