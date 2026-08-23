"""
Validador de dados de entrada.

Objetivo:
    Garantir consistência dos parâmetros antes do cálculo.
"""

from src.modelos.gerador import GeradorSincrono
from src.modelos.tabela_curva import TabelaCurva
from src.modelos.turbina import Turbina


class ValidadorDados:
    """Valida dados carregados de arquivos externos."""

    @staticmethod
    def validar_gerador(gerador: GeradorSincrono) -> None:
        """Valida parâmetros do gerador."""
        if gerador.potencia_nominal <= 0:
            raise ValueError("Potência nominal do gerador deve ser positiva.")
        if gerador.tensao_nominal <= 0:
            raise ValueError("Tensão nominal do gerador deve ser positiva.")
        if gerador.numero_polos <= 0:
            raise ValueError("Número de polos deve ser positivo.")

    @staticmethod
    def validar_turbina(turbina: Turbina) -> None:
        """Valida parâmetros da turbina."""
        if turbina.potencia_nominal <= 0:
            raise ValueError("Potência nominal da turbina deve ser positiva.")

    @staticmethod
    def validar_curva(curva: TabelaCurva) -> None:
        """Valida tabela de curva."""
        if len(curva.pontos) < 2:
            raise ValueError(f"Curva {curva.nome} deve possuir ao menos 2 pontos.")

        abscissas = curva.obter_abscissas()
        if abscissas != sorted(abscissas):
            raise ValueError(f"Curva {curva.nome}: abscissas devem ser crescentes.")
