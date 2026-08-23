"""
Ponto operacional do gerador.

Representa o estado instantâneo lido de campo (supervisório / Elipse)
para posicionar a máquina na curva de capabilidade P–Q.

Entradas de campo necessárias (literatura / prática profissional):

    | Grandeza              | Símbolo | Base p.u. | Papel                         |
    |-----------------------|---------|-----------|-------------------------------|
    | Potência ativa        | P       | Sn        | Coordenada Y do ponto         |
    | Potência reativa      | Q       | Sn        | Coordenada X do ponto         |
    | Tensão terminal       | Vt      | Vn        | Recalcula envelope (SCL/OEL)  |
    | Corrente de campo     | If      | If_FL     | Limite OEL / excitação        |
    | Corrente de estator   | Is      | In        | Verificação SCL (medida)      |
    | Frequência            | f       | fn        | V/Hz / subtensão de rede      |
    | Queda útil (hidro)    | H       | Hn        | Limite Pmec da turbina        |

Referências:
    - KUNDUR, Cap. 3 — diagrama de capabilidade e excitação.
    - IEEE Std 1110-2002 — modeling / capability curves.
    - ONS BD Anatem — traçado operacional com Vt e If.
    - IEC 60034-3 — curvas de capabilidade.
"""

from dataclasses import dataclass


@dataclass
class PontoOperacional:
    """
    Grandezas do ponto operacional atual.

    Armazenamento interno em unidades de engenharia (SI de usina):
        P [MW], Q [Mvar], Vt [kV], Is [A], If [A], f [Hz], H [m].

    A interface de simulação e tags Elipse preferem p.u.; a conversão
    é feita pelas BasesPorUnidade no motor do simulador.
    """

    potencia_ativa: float
    potencia_reativa: float
    tensao: float
    corrente_estator: float = 0.0
    corrente_campo: float = 0.0
    frequencia: float = 60.0
    queda: float = 0.0
