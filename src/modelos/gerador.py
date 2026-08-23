"""
Modelo da máquina síncrona (gerador ou compensador).

Objetivo:
    Armazenar parâmetros elétricos e mecânicos para cálculo
    da curva de capabilidade.

Equações de referência:
    Velocidade síncrona: n_s = 120 * f / polos  [rpm]
    Reatâncias em pu convertidas conforme base da máquina.

Referências:
    - KUNDUR, P. Power System Stability and Control. Capítulo 3.
    - IEEE Std 1110-2002: Guide for Synchronous Generator Modeling.
    - IEC 60034-1: Rating and performance of rotating electrical machines.
"""

import math
from dataclasses import dataclass

from src.constantes.grandezas import TipoMaquina


@dataclass
class GeradorSincrono:
    """
    Parâmetros do gerador ou compensador síncrono.

    Unidades:
        Potências em MVA/MW/Mvar.
        Tensão em kV.
        Corrente em A.
        Frequência em Hz.
        Reatâncias em pu sobre base da máquina.
        Inércia H em segundos.
    """

    identificacao: str
    potencia_nominal: float
    potencia_ativa_nominal: float
    tensao_nominal: float
    corrente_nominal: float
    frequencia: float
    numero_polos: int
    reatancia_direta: float
    reatancia_quadratura: float
    reatancia_transitoria_direta: float
    reatancia_subtransitoria_direta: float
    resistencia_armadura: float
    constante_inercia: float
    corrente_campo_nominal: float
    corrente_campo_vazio: float = 0.0
    fator_potencia_nominal: float = 0.85
    potencia_ativa_maxima: float = 0.0
    potencia_ativa_maxima_pu: float = 0.0
    tipo_maquina: TipoMaquina = TipoMaquina.GERADOR
    descricao: str = ""
    referencia: str = "IEEE Std 1110-2002"

    def eh_compensador(self) -> bool:
        """True se a máquina opera como compensador síncrono (P ≈ 0)."""
        return self.tipo_maquina == TipoMaquina.COMPENSADOR_SINCRONO

    def obter_potencia_ativa_maxima_pu(self) -> float:
        """Retorna P máxima em p.u. sobre Sn."""
        if self.eh_compensador():
            return 0.0
        if self.potencia_ativa_maxima_pu > 0:
            return self.potencia_ativa_maxima_pu
        if self.potencia_ativa_maxima > 0 and self.potencia_nominal > 0:
            return self.potencia_ativa_maxima / self.potencia_nominal
        return self.fator_potencia_nominal

    def calcular_potencia_reativa_nominal_pu(self) -> float:
        """
        Calcula Qn em p.u. sobre Sn.

        Equação: Qn_pu = sqrt(1 - FPN²)
        Compensador: referência Q ≈ 1 pu (sem P nominal).
        """
        if self.eh_compensador():
            return 1.0
        return math.sqrt(max(0.0, 1.0 - self.fator_potencia_nominal**2))

    def calcular_velocidade_sincrona(self) -> float:
        """
        Calcula a velocidade síncrona em rpm.

        Equação: n_s = 120 * f / polos
        """
        if self.numero_polos <= 0:
            raise ValueError("Número de polos deve ser positivo.")
        return 120.0 * self.frequencia / self.numero_polos

    def calcular_potencia_reativa_nominal(self) -> float:
        """
        Calcula potência reativa nominal.

        Gerador: Qn = Pn * tan(arccos(fp))
        Compensador: Qn ≈ Sn (troca reativa plena).
        """
        if self.eh_compensador():
            return self.potencia_nominal
        angulo = math.acos(self.fator_potencia_nominal)
        return self.potencia_ativa_nominal * math.tan(angulo)
