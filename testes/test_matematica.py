"""Testes do mÃ³dulo matemÃ¡tica."""

import math
import pytest

from src.matematica.funcoes_basicas import (
    RaizQuadrada,
    Quadrado,
    Hipotenusa,
    Distancia,
    ConversaoGraus,
    ConversaoRadianos,
)
from src.matematica.eletrica import (
    PotenciaAparente,
    CorrenteEstator,
    FatorPotencia,
)


def test_raiz_quadrada():
    assert RaizQuadrada(9) == 3.0
    with pytest.raises(ValueError):
        RaizQuadrada(-1)


def test_quadrado():
    assert Quadrado(4) == 16.0


def test_hipotenusa():
    assert Hipotenusa(3, 4) == 5.0


def test_distancia():
    assert Distancia(0, 0, 3, 4) == 5.0


def test_conversao_angulos():
    assert abs(ConversaoGraus(math.pi) - 180.0) < 1e-9
    assert abs(ConversaoRadianos(180.0) - math.pi) < 1e-9


def test_potencia_aparente():
    # S = sqrt(PÂ² + QÂ²) - Fitzgerald & Kingsley
    assert abs(PotenciaAparente(3, 4) - 5.0) < 1e-9


def test_corrente_estator():
    corrente = CorrenteEstator(100.0, 13.8)
    assert corrente > 0


def test_fator_potencia():
    assert abs(FatorPotencia(80, 100) - 0.8) < 1e-9
