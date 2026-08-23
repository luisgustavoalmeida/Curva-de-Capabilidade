"""Biblioteca de interpolação para curvas tabuladas."""

from .linear import InterpolarLinearmente, ExtrapolarLinearmente
from .busca import PesquisaBinaria, BuscarIntervalo
from .segmentos import InterpolarPorSegmentos, AvaliarCurvaTabulada

__all__ = [
    "InterpolarLinearmente",
    "ExtrapolarLinearmente",
    "PesquisaBinaria",
    "BuscarIntervalo",
    "InterpolarPorSegmentos",
    "AvaliarCurvaTabulada",
]
