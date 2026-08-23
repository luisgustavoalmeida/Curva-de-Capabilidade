# Curva de Capabilidade

Biblioteca Python para o **traçado operacional P–Q** de máquinas síncronas — geradores e compensadores. Calcula a região permitida de operação, posiciona o ponto de campo e exporta o envelope para o supervisório **Elipse E3**.

O cálculo segue o traçado operacional em p.u. (base \(S_n\)) com dependência de \(V_t\) e \(I_f\), alinhado a **ONS BD Anatem**, **IEEE Std 1110**, **Kundur** e **IEC 60034-3**.

| | |
|---|---|
| Versão | 1.0.0 |
| Linguagem | Python 3.10+ |
| Entrada | JSON + CSV opcionais por unidade geradora |
| Saída | GUI, console, CSV para gráfico XY no Elipse E3 |

![Interface do simulador](Imagens/Imagem%20interface.png)

*Interface gráfica: entradas de campo em p.u., resultado da capabilidade e traçado operacional P–Q.*

---

## Índice

- [O que o projeto faz](#o-que-o-projeto-faz)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Começar rápido](#começar-rápido)
- [Comandos](#comandos)
- [Dados da usina](#dados-da-usina)
- [Envelope dinâmico e Elipse E3](#envelope-dinâmico-e-elipse-e3)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Documentação](#documentação)
- [Testes](#testes)
- [Referências](#referências)
- [Aviso](#aviso)
- [Licença](#licença)

---

## O que o projeto faz

Cada pasta em `dados/` com `gerador.json` é uma **unidade geradora (UG)**. O núcleo monta o envelope:

\[
P_{\mathrm{mec,min}} \le P \le P_{\mathrm{mec,max}}
\]
\[
Q_{\mathrm{sup}}(P) = \min\bigl(Q_{\mathrm{OEL\,TH}}(V_t,I_f),\; Q_{\mathrm{SCL}}(V_t)\bigr)
\]
\[
Q_{\mathrm{inf}}(P) = \max\bigl(Q_{\mathrm{UEL}},\; Q_{\mathrm{MEL}},\; Q_{\mathrm{estator,min}}(V_t),\; \ldots\bigr)
\]

O **Python calcula**. O **Elipse E3 só plota** (gráfico XY + ponto P–Q). Alarmes e proteções ficam fora deste escopo.

**Template de referência:** `dados/usina/` — dados de demonstração alinhados à UHE Sobradinho (\(S_n = 194{,}5\,\mathrm{MVA}\), FP \(0{,}9\)), validados nos testes.

---

## Funcionalidades

- Envelope operacional com SCL, OEL (térmico e de pico), UEL, MEL, V/Hz, Pmec e curvas de fabricante
- Gerador ou compensador síncrono (`TipoMaquina` em `gerador.json`)
- CSVs opcionais: sem arquivo, o envelope usa **SCL + OEL analíticos** + Pmec + V/Hz
- Interface gráfica (Tk) com entradas de campo em p.u.: \(P\), \(Q\), \(V_t\), \(I_f\), \(I_s\), \(f\), \(H\)
- Serviço contínuo multi-UG para o supervisório (`python main.py servico`)
- Exportação de séries CSV para gráfico XY no Elipse E3
- Scripts VBScript prontos em [`elipse_e3/`](elipse_e3/)

---

## Requisitos

- **Python 3.10 ou superior** (Tkinter incluso na instalação padrão do Windows)
- pip

Dependências (`requirements.txt`):

| Pacote | Uso |
|--------|-----|
| matplotlib ≥ 3.8 | Gráfico da interface |
| pytest ≥ 8.0 | Testes |

O núcleo de cálculo usa só a biblioteca padrão.

No Linux, instale o Tk se a GUI não abrir (`python3-tk` no Debian/Ubuntu).

---

## Instalação

```bash
git clone https://github.com/<usuario>/curva-de-capabilidade.git
cd curva-de-capabilidade
```

Prefira um nome de repositório **sem espaços** (`curva-de-capabilidade`).

Ambiente virtual (recomendado):

**Windows (PowerShell)**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Começar rápido

```powershell
# 1. Conferir o template
python main.py calcular --dados dados/usina

# 2. Abrir o simulador gráfico
python main.py
# ou
python main.py simulador --dados dados/usina

# 3. Criar uma usina nova a partir do template
python main.py nova-usina --pasta minha_usina --nome "Usina X"
# Edite dados/minha_usina/gerador.json, curvas.json e (se houver) turbina.json
python main.py simulador --dados dados/minha_usina
```

Chaves JSON que começam com `_` e linhas CSV que começam com `#` são **comentários** (ignoradas pelo programa).

---

## Comandos

| Comando | Função |
|---------|--------|
| `python main.py` | Abre o simulador com `dados/usina` |
| `python main.py simulador --dados <pasta>` | Interface gráfica da UG |
| `python main.py calcular --dados <pasta>` | Resultado no console (ponto, margem, limites) |
| `python main.py exportar --dados <pasta>` | Gera CSV + instruções em `<pasta>/exportacao_elipse/` |
| `python main.py nova-usina --pasta <nome> [--nome "..."]` | Copia o template para `dados/<nome>` |
| `python main.py servico` | Loop contínuo: lê `campo.json` e atualiza o envelope de todas as UGs |
| `python main.py servico --intervalo 1 --uma-vez` | Um ciclo (teste) |
| `python main.py servico --apenas usina,ug02` | Só as pastas indicadas |

Sem argumentos, `main.py` abre o simulador.

---

## Dados da usina

Cada pasta com `gerador.json` é uma UG. O serviço percorre todas as pastas em `dados/`.

```
dados/
  usina/           ← template (exemplo Sobradinho)
  <sua_usina>/     ← python main.py nova-usina --pasta sua_usina
```

| Arquivo | Obrigatório | Conteúdo |
|---------|-------------|----------|
| `gerador.json` | Sim | Placa + `TipoMaquina` (`Gerador` ou `CompensadorSincrono`) |
| `curvas.json` | Sim | Pmec, Imax, V/Hz; nomes dos CSVs (opcionais) |
| `turbina.json` | Não | Hidro (referência de queda). Omitir no compensador |
| `campo.json` | Não* | Entradas \(P, Q, V_t, I_f, f, H\) do serviço dinâmico |
| `*.csv` | Não | Curvas de fabricante (`Q` × `P` em p.u.) |

\*Necessário para o serviço atualizar o ponto operacional. Sem o arquivo, usa o ponto padrão do simulador.

Formato CSV: `PotenciaReativaPu,PotenciaAtivaPu`.

**Compensador síncrono:** `"TipoMaquina": "CompensadorSincrono"`, potências ativas = 0, remova `turbina.json`.

**Sem CSV:** envelope = SCL + OEL analíticos + Pmec + V/Hz. UEL/MEL só entram se houver curva tabulada.

Detalhes: [`dados/README.md`](dados/README.md) e [`dados/usina/README.md`](dados/usina/README.md).

---

## Envelope dinâmico e Elipse E3

O Python **não** gera imagem para o Elipse. O Elipse **não** recalcula OEL/UEL/MEL.

```
Elipse E3  --campo.json-->  python main.py servico  --CSV-->  Gráfico XY no E3
```

```powershell
# No servidor da usina (junto do Elipse), loop contínuo
python main.py servico --intervalo 1
```

| Direção | Arquivo | Conteúdo |
|---------|---------|----------|
| Elipse → Python | `dados/<ug>/campo.json` | \(P, Q, V_t, I_f, I_s, f, H\) |
| Python → Elipse | `dados/<ug>/exportacao_elipse/*.csv` | Envelope e limitadores (Q × P em p.u.) |

Scripts VBScript para colar no Studio: [`elipse_e3/`](elipse_e3/).

| Documento | Conteúdo |
|-----------|----------|
| [`elipse_e3/GUIA_IMPLEMENTACAO.md`](elipse_e3/GUIA_IMPLEMENTACAO.md) | Passo a passo no E3 |
| [`elipse_e3/tags/CATALOGO_TAGS.md`](elipse_e3/tags/CATALOGO_TAGS.md) | Tags a criar |
| [`documentacao/COMUNICACAO_ELIPSE_PYTHON.md`](documentacao/COMUNICACAO_ELIPSE_PYTHON.md) | Arquitetura, multi-UG, operação |

Eixo do gráfico XY: **X = Q**, **Y = P** (p.u.).

---

## Estrutura do repositório

```
.
├── main.py                 Ponto de entrada (CLI + GUI + serviço)
├── requirements.txt
├── LICENSE                 MIT
├── .github/workflows/      Testes automáticos (pytest)
├── src/                    Núcleo de cálculo (sem Tk)
│   ├── curvas/             Envelope, avaliador, limites (SCL, OEL, UEL, …)
│   ├── modelos/            Gerador, turbina, ponto, resultado
│   ├── matematica/         Grandezas elétricas e p.u.
│   ├── interpolacao/       Tabelas de fabricante
│   ├── simulador/          Motor e fábrica a partir da pasta da UG
│   ├── servico/            Loop multi-UG (campo.json → CSV)
│   ├── exportacao/         CSV + scripts para o Elipse E3
│   └── utilitarios/        Carga JSON/CSV, nova usina, gráfico
├── interface/              GUI Tk (não contém lógica de envelope)
├── dados/usina/            Template único (copie; não edite como produção)
├── elipse_e3/              Scripts VBS, tags e guia do supervisório
├── testes/                 pytest
└── documentacao/           Técnica, Elipse e comunicação
```

---

## Documentação

| Arquivo | Assunto |
|---------|---------|
| [`documentacao/TECNICA.md`](documentacao/TECNICA.md) | Equações, composição do envelope, entradas de campo |
| [`documentacao/COMUNICACAO_ELIPSE_PYTHON.md`](documentacao/COMUNICACAO_ELIPSE_PYTHON.md) | Serviço dinâmico, tags, multi-UG |
| [`documentacao/ELIPSE_E3.md`](documentacao/ELIPSE_E3.md) | Exportação estática e dinâmica |
| [`documentacao/modulos/matematica.md`](documentacao/modulos/matematica.md) | Funções elétricas básicas |
| [`elipse_e3/README.md`](elipse_e3/README.md) | Pacote de scripts do E3 |

---

## Testes

Na raiz do repositório, com o ambiente virtual ativo:

```bash
pytest
```

Os testes cobrem matemática, interpolação, limites (estator, campo, V/Hz, turbina), compensador, modo sem CSV, exportação e o serviço de envelope.

---

## Referências

- Kundur, P. *Power System Stability and Control*. McGraw-Hill, 1994 (cap. 3 e 5).
- IEEE Std 1110-2002 — *Guide for Synchronous Generator Modeling*.
- IEC 60034-3 — Máquinas síncronas.
- ONS — Banco de Dados Anatem (metodologia do traçado operacional).
- Fitzgerald, Kingsley, Umans — *Electric Machinery*.

---

## Aviso

Esta biblioteca é uma **ferramenta de engenharia e visualização**. Não substitui proteções, IEDs, limitadores de excitação em campo nem a lógica de alarme do supervisório. Valide placa, curvas de fabricante e ajustes antes de usar em operação.

Não entram no GitHub: `venv/`, caches, a planilha `.xlsm` local e a pasta gerada `exportacao_elipse/` (recriada com `python main.py exportar` ou `servico`).

No Elipse, ajuste `CAMINHO_RAIZ_DADOS` em `elipse_e3/scripts/00_Config.vbs` para a pasta `dados/` do clone neste servidor.

---
