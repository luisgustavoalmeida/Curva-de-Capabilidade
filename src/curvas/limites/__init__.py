"""
Cálculo dos limites individuais da curva de capabilidade.

Objetivo:
    Implementar cada limite operacional conforme referências de engenharia.

Referências:
    - KUNDUR, P. Power System Stability and Control. Seção 3.4.
    - IEEE Std 1110-2002: Capability curves.
    - IEC 60034-3: Synchronous generators - capability curves.
"""

from .estator import CalcularLimiteEstator
from .estator_tabulado import CalcularLimiteEstatorTabulado
from .analiticos_tensao import (
    CalcularLimiteEstatorPorTensao,
    CalcularLimiteCampoPorTensao,
    CalcularTensaoInternaPorCorrenteCampo,
    CalcularFatorCorrenteCampo,
    EstimarTensaoInternaMaxima,
)
from .rotor import CalcularLimiteRotor, CalcularLimiteSobreExcitacao
from .subexcitacao import CalcularLimiteSubExcitacao
from .estabilidade import CalcularLimiteEstabilidade
from .saliencia_polar import CalcularLimiteSalienciaPolar
from .saturacao import CalcularLimiteSaturacao
from .aquecimento_extremo import CalcularLimiteAquecimentoExtremoEstator
from .escala_tensao import EscalarLimiteQPorTensao, EscalarLimiteQPorTensaoQuadratica
from .turbina import (
    CalcularLimitePotenciaAtivaTurbina,
    CalcularPotenciaHidraulicaPorQueda,
    CalcularTetoPotenciaTurbina,
)
from .volts_hertz import (
    CalcularFatorDeratingVoltsHertz,
    CalcularRelacaoVoltsHertz,
    MargemVoltsHertzPercentual,
    VerificarVoltsHertz,
)

__all__ = [
    "CalcularLimiteEstator",
    "CalcularLimiteEstatorTabulado",
    "CalcularLimiteEstatorPorTensao",
    "CalcularLimiteCampoPorTensao",
    "CalcularTensaoInternaPorCorrenteCampo",
    "CalcularFatorCorrenteCampo",
    "EstimarTensaoInternaMaxima",
    "CalcularLimiteRotor",
    "CalcularLimiteSobreExcitacao",
    "CalcularLimiteSubExcitacao",
    "CalcularLimiteEstabilidade",
    "CalcularLimiteSalienciaPolar",
    "CalcularLimiteSaturacao",
    "CalcularLimiteAquecimentoExtremoEstator",
    "EscalarLimiteQPorTensao",
    "EscalarLimiteQPorTensaoQuadratica",
    "CalcularLimitePotenciaAtivaTurbina",
    "CalcularPotenciaHidraulicaPorQueda",
    "CalcularTetoPotenciaTurbina",
    "CalcularRelacaoVoltsHertz",
    "CalcularFatorDeratingVoltsHertz",
    "VerificarVoltsHertz",
    "MargemVoltsHertzPercentual",
]
