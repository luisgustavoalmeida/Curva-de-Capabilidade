"""Testes do mÃ³dulo de interpolaÃ§Ã£o."""

from src.interpolacao.linear import InterpolarLinearmente
from src.interpolacao.busca import PesquisaBinaria, BuscarIntervalo
from src.interpolacao.segmentos import InterpolarPorSegmentos


def test_interpolacao_linear():
    resultado = InterpolarLinearmente(1.5, 1.0, 10.0, 2.0, 20.0)
    assert resultado == 15.0


def test_pesquisa_binaria():
    valores = [0, 10, 20, 30, 40]
    assert PesquisaBinaria(valores, 25) == 2


def test_buscar_intervalo():
    valores = [0, 10, 20, 30]
    inferior, superior = BuscarIntervalo(valores, 15)
    assert inferior == 1
    assert superior == 2


def test_interpolar_por_segmentos():
    x = [0, 10, 20]
    y = [0, 100, 200]
    assert InterpolarPorSegmentos(x, y, 5) == 50.0
    assert InterpolarPorSegmentos(x, y, 0) == 0.0
    assert InterpolarPorSegmentos(x, y, 20) == 200.0
