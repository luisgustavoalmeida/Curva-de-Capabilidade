"""
Tabela parametrizada de curva.

Objetivo:
    Representar curvas de fabricante carregadas de arquivos externos.

Hipóteses:
    Pontos ordenados por abscissa crescente.

Referências:
    - IEEE Std 1110-2002: Capability curves from manufacturer data.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class TabelaCurva:
    """
    Estrutura de uma curva tabulada.

    Atributos:
        nome: identificação da curva
        unidade_x: unidade da abscissa (ex.: MW)
        unidade_y: unidade da ordenada (ex.: Mvar)
        pontos: lista de tuplas (x, y)
        permitir_extrapolacao: habilita extrapolação linear
        referencia: referência bibliográfica ou de fabricante
    """

    nome: str
    unidade_x: str
    unidade_y: str
    pontos: List[Tuple[float, float]] = field(default_factory=list)
    permitir_extrapolacao: bool = False
    referencia: str = ""

    def obter_abscissas(self) -> List[float]:
        """Retorna lista de abscissas."""
        return [ponto[0] for ponto in self.pontos]

    def obter_ordenadas(self) -> List[float]:
        """Retorna lista de ordenadas."""
        return [ponto[1] for ponto in self.pontos]

    def potencia_minima(self) -> float:
        """Retorna a menor abscissa da tabela."""
        if not self.pontos:
            raise ValueError("Tabela de curva sem pontos.")
        return self.pontos[0][0]

    def potencia_maxima(self) -> float:
        """Retorna a maior abscissa da tabela."""
        if not self.pontos:
            raise ValueError("Tabela de curva sem pontos.")
        return self.pontos[-1][0]
