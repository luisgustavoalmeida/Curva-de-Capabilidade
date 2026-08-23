"""
Resultado da verificação de capabilidade.

Objetivo:
    Consolidar limites, margens e ponto restritivo.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.constantes.grandezas import NomeLimite


@dataclass
class ResultadoCapabilidade:
    """
    Resultado completo da análise de capabilidade.

    Atributos:
        dentro_da_curva: indica se o ponto está na região permitida
        margem_operacional: menor distância normalizada aos limites (%)
        limite_restritivo: limite mais próximo do ponto operacional
        limites_superiores: dicionário limite -> Q máximo em P atual
        limites_inferiores: dicionário limite -> Q mínimo em P atual
        limite_superior_efetivo: menor Q superior entre todos os limites
        limite_inferior_efetivo: maior Q inferior entre todos os limites
        mensagens: mensagens descritivas para interface
    """

    dentro_da_curva: bool
    margem_operacional: float
    limite_restritivo: Optional[NomeLimite]
    limites_superiores: Dict[NomeLimite, float] = field(default_factory=dict)
    limites_inferiores: Dict[NomeLimite, float] = field(default_factory=dict)
    limite_superior_efetivo: float = 0.0
    limite_inferior_efetivo: float = 0.0
    mensagens: List[str] = field(default_factory=list)
    potencia_aparente: float = 0.0
    fator_potencia: float = 0.0
    distancias_limites: Dict[NomeLimite, float] = field(default_factory=dict)
