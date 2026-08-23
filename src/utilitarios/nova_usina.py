"""
Cria nova pasta de usina copiando o template `dados/usina`.

Fluxo: copie o template → edite valores nos JSON/CSV.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path


def CriarUsina(
    diretorio_pai: str | Path,
    nome_pasta: str,
    *,
    template: str | Path | None = None,
    identificacao: str | None = None,
) -> Path:
    """
    Copia `dados/usina` para `dados/<nome_pasta>`.

    Se `identificacao` for informada, atualiza só o campo Identificacao em gerador.json.
    """
    raiz = Path(diretorio_pai)
    destino = raiz / nome_pasta
    if destino.exists():
        raise FileExistsError(f"Pasta já existe: {destino}")

    origem = Path(template) if template else _template_padrao(raiz)
    if not origem.is_dir():
        raise FileNotFoundError(f"Template não encontrado: {origem}")

    shutil.copytree(origem, destino)

    # Não copiar pasta de exportação do template, se existir
    exportacao = destino / "exportacao_elipse"
    if exportacao.exists():
        shutil.rmtree(exportacao)

    if identificacao:
        caminho_gerador = destino / "gerador.json"
        dados = json.loads(caminho_gerador.read_text(encoding="utf-8"))
        dados["Identificacao"] = identificacao
        caminho_gerador.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return destino


def _template_padrao(diretorio_pai: Path) -> Path:
    """Resolve dados/usina a partir de dados/ ou da raiz do projeto."""
    candidato = diretorio_pai / "usina"
    if candidato.is_dir():
        return candidato
    return diretorio_pai.parent / "dados" / "usina"
