"""
Limitador Volts/Hertz (V/Hz) - proteção contra sobrefluxo.

O fluxo magnético no núcleo é proporcional a Vt/f. Em p.u.:

    (V/Hz)_pu = Vt_pu / f_pu

Limite típico de excitação / AVR: 1,05 … 1,10 pu (IEEE / fabricantes).

Efeitos na capabilidade:
    - Verificação operacional: fora da curva se Vt/f > (V/Hz)_max
    - Derating do OEL: fator = min(1, (V/Hz)_max / (Vt/f))
      reduz Q sobre-excitado quando há sobrefluxo

Referências:
    - IEEE Std C37.102 / práticas de limitadores V/Hz em AVRs.
    - KUNDUR, P. Power System Stability and Control - overfluxing.
    - IEC 60034 - operação em frequência fora do nominal.
"""


def CalcularRelacaoVoltsHertz(
    tensao_terminal_pu: float,
    frequencia_pu: float,
) -> float:
    """Retorna Vt/f em p.u. Se f≤0, retorna +inf."""
    if frequencia_pu <= 1e-9:
        return float("inf")
    if tensao_terminal_pu < 0:
        return float("inf")
    return tensao_terminal_pu / frequencia_pu


def CalcularFatorDeratingVoltsHertz(
    tensao_terminal_pu: float,
    frequencia_pu: float,
    relacao_maxima_pu: float = 1.05,
) -> float:
    """
    Fator ∈ (0, 1] para derating de sobre-excitação.

    Se Vt/f ≤ limite → 1,0 (sem derating).
    Se Vt/f > limite → limite / (Vt/f) < 1.
    """
    if relacao_maxima_pu <= 0:
        return 1.0
    vhz = CalcularRelacaoVoltsHertz(tensao_terminal_pu, frequencia_pu)
    if vhz <= 0 or vhz == float("inf"):
        return 0.0
    if vhz <= relacao_maxima_pu + 1e-9:
        return 1.0
    return relacao_maxima_pu / vhz


def VerificarVoltsHertz(
    tensao_terminal_pu: float,
    frequencia_pu: float,
    relacao_maxima_pu: float = 1.05,
    relacao_minima_pu: float = 0.0,
) -> tuple:
    """
    Verifica se Vt/f está na faixa permitida.

    Retorno: (ok: bool, vhz_pu: float, mensagem: str)
    """
    vhz = CalcularRelacaoVoltsHertz(tensao_terminal_pu, frequencia_pu)
    if frequencia_pu <= 1e-9:
        return False, vhz, "Frequência nula ou inválida - V/Hz indefinido."
    if relacao_maxima_pu > 0 and vhz > relacao_maxima_pu + 1e-6:
        return (
            False,
            vhz,
            f"Sobrefluxo V/Hz={vhz:.4f} pu > máx={relacao_maxima_pu:.4f} pu.",
        )
    if relacao_minima_pu > 0 and vhz < relacao_minima_pu - 1e-6:
        return (
            False,
            vhz,
            f"Subfluxo V/Hz={vhz:.4f} pu < mín={relacao_minima_pu:.4f} pu.",
        )
    return True, vhz, ""


def MargemVoltsHertzPercentual(
    tensao_terminal_pu: float,
    frequencia_pu: float,
    relacao_maxima_pu: float = 1.05,
) -> float:
    """Margem até o teto V/Hz em %: 100·(máx − Vt/f)/máx."""
    if relacao_maxima_pu <= 0:
        return 0.0
    vhz = CalcularRelacaoVoltsHertz(tensao_terminal_pu, frequencia_pu)
    if vhz == float("inf"):
        return 0.0
    return max(0.0, 100.0 * (relacao_maxima_pu - vhz) / relacao_maxima_pu)
