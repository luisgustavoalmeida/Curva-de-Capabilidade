"""
Modelo da turbina.

Objetivo:
    Representar limites hidráulicos que restringem a potência ativa
    do conjunto turbina-gerador em função da queda útil.

Referências:
    - CHAUDHRY, M.H. Applied Hydraulic Transients.
    - IEC 60193: Hydraulic turbines.
"""

from dataclasses import dataclass
from typing import Optional

from src.constantes.grandezas import TipoTurbina
from src.modelos.tabela_curva import TabelaCurva


@dataclass
class Turbina:
    """
    Parâmetros da turbina associada ao gerador.

    Unidades:
        Potência em MW.
        Queda em metros.
        Vazão em m³/s.
        Abertura do distribuidor em percentual.
        Expoente da queda: 1,5 (Francis/Kaplan) ou 1,0 (aproximação linear).
    """

    identificacao: str
    tipo: TipoTurbina
    potencia_nominal: float
    queda_nominal: float
    vazao_nominal: float
    rendimento_nominal: float
    abertura_distribuidor: float = 100.0
    potencia_minima: float = 0.0
    potencia_maxima: float = 0.0
    potencia_maxima_pu: float = 0.0
    expoente_queda: float = 1.5
    curva_hidraulica: Optional[TabelaCurva] = None
    curva_rendimento: Optional[TabelaCurva] = None
    descricao: str = ""
    referencia: str = ""

    def obter_limite_potencia_ativa(self) -> float:
        """Retorna o teto de potência ativa configurado (MW)."""
        if self.potencia_maxima > 0:
            return self.potencia_maxima
        return self.potencia_nominal
