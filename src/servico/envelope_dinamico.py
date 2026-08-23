"""
Serviço de envelope dinâmico multi-UG.

Um único loop percorre todas as unidades (pastas em dados/ com gerador.json),
lê entradas de campo (campo.json), recalcula o envelope e grava CSVs
em exportacao_elipse/ para o Elipse E3 (só visual).

Entrada por UG (Elipse/OPC/script pode sobrescrever este arquivo):
    dados/<ug>/campo.json  → P, Q, Vt, If, f, H (pu ou SI)

Referências:
    - Arquitetura: 1 processo Python, N máquinas
    - documentacao/ELIPSE_E3.md
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.exportacao.elipse_e3 import ExportadorElipseE3
from src.simulador.fabrica import CriarSimuladorDeDiretorio
from src.simulador.motor import SimuladorCapabilidade


@dataclass
class UnidadeGeradora:
    """Uma máquina carregada no serviço."""

    id: str
    diretorio: Path
    simulador: SimuladorCapabilidade


@dataclass
class ResultadoCicloUg:
    id: str
    ok: bool
    mensagem: str = ""
    arquivos: Dict[str, str] = field(default_factory=dict)


def ListarPastasUg(diretorio_dados: str | Path) -> List[Path]:
    """
    Lista pastas de UG em dados/ (contêm gerador.json).

    Ignora arquivos soltos e pastas sem placa.
    """
    raiz = Path(diretorio_dados)
    if not raiz.is_dir():
        return []
    pastas: List[Path] = []
    for filho in sorted(raiz.iterdir()):
        if filho.is_dir() and (filho / "gerador.json").exists():
            pastas.append(filho)
    return pastas


def CarregarUnidades(
    diretorio_dados: str | Path,
    apenas: Optional[List[str]] = None,
) -> List[UnidadeGeradora]:
    """Carrega um SimuladorCapabilidade por pasta de UG."""
    unidades: List[UnidadeGeradora] = []
    for pasta in ListarPastasUg(diretorio_dados):
        if apenas and pasta.name not in apenas:
            continue
        simulador = CriarSimuladorDeDiretorio(str(pasta))
        unidades.append(
            UnidadeGeradora(
                id=pasta.name,
                diretorio=pasta,
                simulador=simulador,
            )
        )
    return unidades


def LerCampoJson(caminho: Path) -> Dict[str, Any]:
    """Lê campo.json ignorando chaves _* (comentários)."""
    if not caminho.exists():
        return {}
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    return {
        chave: valor
        for chave, valor in dados.items()
        if not str(chave).startswith("_")
    }


def AplicarCampoNaUnidade(unidade: UnidadeGeradora, campo: Dict[str, Any]) -> None:
    """
    Atualiza o ponto operacional a partir de campo.json.

    Chaves aceitas (pu se EmPorUnidade=true, senão SI):
        P, Q, Vt, If, Is, f, H
    """
    if not campo:
        return
    em_pu = bool(campo.get("EmPorUnidade", True))
    unidade.simulador.atualizar_ponto_operacional(
        potencia_ativa=_opcional_float(campo, "P"),
        potencia_reativa=_opcional_float(campo, "Q"),
        tensao=_opcional_float(campo, "Vt"),
        corrente_campo=_opcional_float(campo, "If"),
        corrente_estator=_opcional_float(campo, "Is"),
        frequencia=_opcional_float(campo, "f"),
        queda=_opcional_float(campo, "H"),
        em_por_unidade=em_pu,
    )


def ProcessarUnidade(unidade: UnidadeGeradora) -> ResultadoCicloUg:
    """Lê campo, recalcula envelope e exporta CSVs da UG."""
    try:
        campo = LerCampoJson(unidade.diretorio / "campo.json")
        AplicarCampoNaUnidade(unidade, campo)
        resultado = unidade.simulador.executar_simulacao_completa()
        saida = unidade.diretorio / "exportacao_elipse"
        exportador = ExportadorElipseE3(str(saida))
        arquivos = exportador.exportar_pontos_curva(resultado["PontosCurva"])
        exportador.exportar_resultado_operacional(
            resultado["PontoOperacional"],
            resultado["ResultadoCapabilidade"],
            grandezas_pu=resultado["GrandezasCampoPu"],
            bases=resultado["Bases"],
        )
        return ResultadoCicloUg(
            id=unidade.id,
            ok=True,
            mensagem="ok",
            arquivos=arquivos,
        )
    except Exception as erro:  # noqa: BLE001 — serviço não pode cair por 1 UG
        return ResultadoCicloUg(id=unidade.id, ok=False, mensagem=str(erro))


def ExecutarCiclo(unidades: List[UnidadeGeradora]) -> List[ResultadoCicloUg]:
    """Um passo do loop: percorre todas as UGs."""
    return [ProcessarUnidade(u) for u in unidades]


def RodarServico(
    diretorio_dados: str | Path,
    *,
    intervalo_s: float = 1.0,
    apenas: Optional[List[str]] = None,
    uma_vez: bool = False,
    max_ciclos: Optional[int] = None,
) -> None:
    """
    Loop principal do envelope dinâmico.

    uma_vez=True → um ciclo e encerra (útil em teste/CI).
    """
    unidades = CarregarUnidades(diretorio_dados, apenas=apenas)
    if not unidades:
        raise FileNotFoundError(
            f"Nenhuma UG encontrada em {diretorio_dados} "
            "(pastas com gerador.json)."
        )

    ids = ", ".join(u.id for u in unidades)
    print(f"Serviço envelope dinâmico — UGs: {ids}")
    print(f"Intervalo: {intervalo_s:.2f} s | saída: <ug>/exportacao_elipse/")

    ciclo = 0
    while True:
        ciclo += 1
        inicio = time.perf_counter()
        resultados = ExecutarCiclo(unidades)
        ok = sum(1 for r in resultados if r.ok)
        falhas = [r for r in resultados if not r.ok]
        decorrido = time.perf_counter() - inicio
        print(
            f"[ciclo {ciclo}] {ok}/{len(resultados)} UG ok "
            f"({decorrido:.2f} s)"
        )
        for falha in falhas:
            print(f"  ERRO {falha.id}: {falha.mensagem}")

        if uma_vez or (max_ciclos is not None and ciclo >= max_ciclos):
            break

        espera = max(0.0, intervalo_s - decorrido)
        time.sleep(espera)


def _opcional_float(dados: Dict[str, Any], chave: str) -> Optional[float]:
    if chave not in dados or dados[chave] is None or dados[chave] == "":
        return None
    return float(dados[chave])
