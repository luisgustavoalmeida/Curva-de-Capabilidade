# Elipse E3 — scripts prontos (Curva de Capabilidade)

Pacote para o supervisório **plotar** a curva (Gráfico XY) e **enviar** as
grandezas de campo ao Python. O Python calcula o envelope; o Elipse desenha.

Visão geral do projeto: [`../README.md`](../README.md).

## Comece aqui

1. [`GUIA_IMPLEMENTACAO.md`](GUIA_IMPLEMENTACAO.md) — passo a passo completo
2. [`tags/CATALOGO_TAGS.md`](tags/CATALOGO_TAGS.md) — tags a criar
3. [`scripts/BibliotecaCompleta.vbs`](scripts/BibliotecaCompleta.vbs) — colar no E3
4. Arquitetura geral: [`../documentacao/COMUNICACAO_ELIPSE_PYTHON.md`](../documentacao/COMUNICACAO_ELIPSE_PYTHON.md)

## Responsabilidades

| Script | Direção | Função |
|--------|---------|--------|
| `01_EnviarCampoParaPython.vbs` | Elipse → Python | Grava `campo.json` (P, Q, Vt, If, f, H) |
| `02_LerCsvEAtualizarPlot.vbs` | Python → Elipse | Lê CSV, status, arrays do plot |
| `03_TimerCicloCompleto.vbs` | Ciclo | Timer chama envio + leitura |
| `00_Config.vbs` / `04_Utilitarios.vbs` | Base | Caminhos, UGs, helpers |

## Python (paralelo)

```powershell
python main.py servico --intervalo 1
```

## Plot

Chart XY no Elipse: X = Q, Y = P. Séries = CSV em `dados/<ug>/exportacao_elipse/`.  
**Não** use imagem gerada no Python.
