"""
Conversões em por unidade (p.u.).

Bases alinhadas à prática de curvas de capabilidade (ONS / IEEE / Kundur):

    Sn  - potência aparente nominal (MVA) → base de P, Q, S
    Vn  - tensão terminal nominal (kV)    → base de Vt
    In  - corrente de estator nominal (A) → base de Is
    If_FL - corrente de campo a plena carga (A) → base de If
    fn  - frequência nominal (Hz)         → base de f
    Hn  - queda nominal (m), hidráulica   → base de H

Equações:
    P_pu  = P_MW / Sn
    Q_pu  = Q_Mvar / Sn
    Vt_pu = V_kV / Vn
    Is_pu = Is_A / In
    If_pu = If_A / If_FL
    f_pu  = f_Hz / fn
    H_pu  = H_m / Hn

Referências:
    - ONS BD Anatem v1.6 - traçado operacional de curva de capabilidade.
    - IEEE Std 1110-2002: Guide for Synchronous Generator Modeling.
    - KUNDUR, P. Power System Stability and Control. Cap. 3.
    - FITZGERALD / KINGSLEY: corrente trifásica I = S/(√3 V).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.modelos.gerador import GeradorSincrono
    from src.modelos.turbina import Turbina


@dataclass
class BasesPorUnidade:
    """Bases do sistema para conversão em p.u. das entradas de campo."""

    potencia_aparente_base: float
    tensao_base: float
    corrente_estator_base: float = 0.0
    corrente_campo_base: float = 0.0
    frequencia_base: float = 60.0
    queda_base: float = 0.0

    def potencia_ativa_para_pu(self, potencia_ativa_mw: float) -> float:
        return potencia_ativa_mw / self.potencia_aparente_base

    def potencia_reativa_para_pu(self, potencia_reativa_mvar: float) -> float:
        return potencia_reativa_mvar / self.potencia_aparente_base

    def potencia_ativa_para_mw(self, potencia_ativa_pu: float) -> float:
        return potencia_ativa_pu * self.potencia_aparente_base

    def potencia_reativa_para_mvar(self, potencia_reativa_pu: float) -> float:
        return potencia_reativa_pu * self.potencia_aparente_base

    def tensao_para_pu(self, tensao_kv: float) -> float:
        return tensao_kv / self.tensao_base

    def tensao_para_kv(self, tensao_pu: float) -> float:
        return tensao_pu * self.tensao_base

    def corrente_estator_para_pu(self, corrente_a: float) -> float:
        if self.corrente_estator_base <= 0:
            return 0.0
        return corrente_a / self.corrente_estator_base

    def corrente_estator_para_a(self, corrente_pu: float) -> float:
        return corrente_pu * self.corrente_estator_base

    def corrente_campo_para_pu(self, corrente_a: float) -> float:
        if self.corrente_campo_base <= 0:
            return 0.0
        return corrente_a / self.corrente_campo_base

    def corrente_campo_para_a(self, corrente_pu: float) -> float:
        return corrente_pu * self.corrente_campo_base

    def frequencia_para_pu(self, frequencia_hz: float) -> float:
        if self.frequencia_base <= 0:
            return 0.0
        return frequencia_hz / self.frequencia_base

    def frequencia_para_hz(self, frequencia_pu: float) -> float:
        return frequencia_pu * self.frequencia_base

    def queda_para_pu(self, queda_m: float) -> float:
        if self.queda_base <= 0:
            return 0.0
        return queda_m / self.queda_base

    def queda_para_m(self, queda_pu: float) -> float:
        return queda_pu * self.queda_base

    def resumo_bases(self) -> dict:
        """Dicionário de bases para exibição / exportação."""
        return {
            "Sn_MVA": self.potencia_aparente_base,
            "Vn_kV": self.tensao_base,
            "In_A": self.corrente_estator_base,
            "If_FL_A": self.corrente_campo_base,
            "fn_Hz": self.frequencia_base,
            "Hn_m": self.queda_base,
        }


def CorrenteEstatorNominal(potencia_nominal_mva: float, tensao_nominal_kv: float) -> float:
    """Corrente de estator nominal trifásica em ampere."""
    return (potencia_nominal_mva * 1_000_000.0) / (
        math.sqrt(3.0) * tensao_nominal_kv * 1_000.0
    )


def CriarBasesDoGerador(
    potencia_nominal_mva: float,
    tensao_nominal_kv: float,
    corrente_campo_nominal_a: float = 0.0,
    frequencia_hz: float = 60.0,
    queda_nominal_m: float = 0.0,
    corrente_estator_nominal_a: float = 0.0,
) -> BasesPorUnidade:
    """Cria bases a partir dos dados nominais do gerador (e turbina, se houver)."""
    if potencia_nominal_mva <= 0:
        raise ValueError("Potência aparente base (Sn) deve ser positiva.")
    if tensao_nominal_kv <= 0:
        raise ValueError("Tensão base (Vn) deve ser positiva.")

    corrente_estator = corrente_estator_nominal_a
    if corrente_estator <= 0:
        corrente_estator = CorrenteEstatorNominal(
            potencia_nominal_mva, tensao_nominal_kv
        )
    elif corrente_estator < 100.0:
        # Dados de usina frequentemente em kA (ex.: 8,137 kA)
        corrente_estator *= 1000.0

    return BasesPorUnidade(
        potencia_aparente_base=potencia_nominal_mva,
        tensao_base=tensao_nominal_kv,
        corrente_estator_base=corrente_estator,
        corrente_campo_base=corrente_campo_nominal_a,
        frequencia_base=frequencia_hz,
        queda_base=queda_nominal_m,
    )


def CriarBasesCompletas(
    gerador: "GeradorSincrono",
    turbina: Optional["Turbina"] = None,
) -> BasesPorUnidade:
    """Cria bases completas a partir dos modelos Gerador e Turbina."""
    queda = turbina.queda_nominal if turbina is not None else 0.0
    return CriarBasesDoGerador(
        potencia_nominal_mva=gerador.potencia_nominal,
        tensao_nominal_kv=gerador.tensao_nominal,
        corrente_campo_nominal_a=gerador.corrente_campo_nominal,
        frequencia_hz=gerador.frequencia,
        queda_nominal_m=queda,
        corrente_estator_nominal_a=gerador.corrente_nominal,
    )
