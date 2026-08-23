"""
Definição de constantes, enumeradores e unidades padrão.

Objetivo:
    Centralizar identificadores de limites e tipos de equipamento
    utilizados em toda a biblioteca.

Referências:
    - KUNDUR, P. Power System Stability and Control. Capítulo 3.
    - IEC 60034-3: Rotating electrical machines - Synchronous generators.
"""

from enum import Enum


class NomeLimite(str, Enum):
    """Identificadores dos limites operacionais da curva de capabilidade."""

    ESTATOR = "LimiteEstator"
    ROTOR = "LimiteRotor"  # OEL de pico (OEL PK)
    SOBRE_EXCITACAO = "LimiteSobreExcitacao"  # OEL térmico contínuo (OEL TH)
    SUB_EXCITACAO = "LimiteSubExcitacao"  # MEL
    ESTABILIDADE = "LimiteEstabilidade"  # UEL ativo
    ESTABILIDADE_PRATICA = "LimiteEstabilidadePratica"
    TURBINA = "LimiteTurbina"  # legado / referência combinada
    PMEC_MAX = "LimitePmecMax"  # Pmec máxima configurada (curvas / máquina)
    QUEDA_UTIL = "LimiteQuedaUtil"  # Pmax pela queda útil (H)
    TURBINA_MAX = "LimiteTurbinaMax"  # Teto mecânico da turbina
    PMEC_MIN = "LimitePmecMin"  # Pmec mínima configurada
    TURBINA_MIN = "LimiteTurbinaMin"  # P mínima da turbina / legado
    SATURACAO = "LimiteSaturacao"  # Saliência polar (legado ONS)
    SATURACAO_MAGNETICA = "LimiteSaturacaoMagnetica"
    AQUECIMENTO_EXTREMO = "LimiteAquecimentoExtremoEstator"
    CORRENTE_CAMPO = "LimiteCorrenteCampo"  # IFD (referência)
    VOLTS_HERTZ = "LimiteVoltsHertz"  # V/Hz (sobrefluxo)


class TipoMaquina(str, Enum):
    """Tipo de máquina síncrona para a curva de capabilidade."""

    GERADOR = "Gerador"
    COMPENSADOR_SINCRONO = "CompensadorSincrono"


class TipoTurbina(str, Enum):
    """Tipos de turbina hidráulica suportados."""

    FRANCIS = "Francis"
    KAPLAN = "Kaplan"
    PELTON = "Pelton"
    AXIAL = "Axial"
    TERMICA = "Termica"


class UnidadesPadrao:
    """
    Unidades padrão utilizadas na biblioteca.

    Hipóteses:
        - Potências em megavoltampere (MVA) ou megawatt (MW) conforme contexto.
        - Tensões em quilovolt (kV).
        - Correntes em ampere (A).
        - Frequência em hertz (Hz).
        - Ângulos em graus para interface e radianos internamente quando necessário.
    """

    POTENCIA_APARENTE = "MVA"
    POTENCIA_ATIVA = "MW"
    POTENCIA_REATIVA = "Mvar"
    TENSAO = "kV"
    CORRENTE = "A"
    FREQUENCIA = "Hz"
    QUEDA = "m"
    VAZAO = "m3/s"
    CORRENTE_CAMPO = "A"
    ANGULO = "graus"
