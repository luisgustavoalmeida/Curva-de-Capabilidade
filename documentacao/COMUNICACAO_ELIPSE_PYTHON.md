# Comunicação Elipse E3 ↔ Python — Curva de Capabilidade Dinâmica

Documento de implementação: como manter o Python rodando, como o Elipse entrega
grandezas de campo, como o Python devolve o envelope, e como diferenciar
unidades geradoras (UGs).

**Papéis**

| Sistema | Faz | Não faz |
|---------|-----|---------|
| **Python** | Calcula o envelopamento completo (SCL, OEL, UEL, MEL, Pmec, V/Hz…) e grava séries CSV | Não é o supervisório |
| **Elipse E3** | Lê tags de campo, escreve entradas para o Python, plota gráfico XY + ponto P–Q | Não recalcula OEL/UEL/MEL |

A curva no Elipse é **somente visual**. Alarmes e proteções, se existirem, ficam
fora deste escopo (proteções/IED ou lógica própria do E3).

**Scripts VBScript prontos (enviar campo + ler CSV + plot):** pasta do repositório
[`elipse_e3/`](../elipse_e3/) — comece por
[`elipse_e3/GUIA_IMPLEMENTACAO.md`](../elipse_e3/GUIA_IMPLEMENTACAO.md)
e cole [`BibliotecaCompleta.vbs`](../elipse_e3/scripts/BibliotecaCompleta.vbs) no Studio.

---

## 1. Visão geral da arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                    SERVIDOR DA USINA (Windows)                   │
│                                                                  │
│  ┌─────────────────────┐         ┌─────────────────────────────┐ │
│  │   Elipse E3         │         │  Serviço Python             │ │
│  │                     │  campo  │  python main.py servico     │ │
│  │  Tags UG01.P, Q…    │ ──────► │                             │ │
│  │  Tags UG02.P, Q…    │  .json  │  loop:                      │ │
│  │                     │         │    para cada UG:            │ │
│  │  Gráfico XY UG01    │ ◄────── │      ler campo.json         │ │
│  │  Gráfico XY UG02    │   CSV   │      recalcular envelope    │ │
│  │                     │         │      gravar exportacao_…    │ │
│  └─────────────────────┘         └─────────────────────────────┘ │
│                                                                  │
│  Disco compartilhado (mesmo PC ou pasta de rede):                │
│    C:\...\dados\ug01\campo.json                                  │
│    C:\...\dados\ug01\exportacao_elipse\*.csv                     │
│    C:\...\dados\ug02\campo.json                                  │
│    C:\...\dados\ug02\exportacao_elipse\*.csv                     │
└──────────────────────────────────────────────────────────────────┘
```

**Canal padrão desta biblioteca (já implementado):** arquivos em disco.

| Direção | Meio | Conteúdo |
|---------|------|----------|
| Elipse → Python | `dados/<ug>/campo.json` | P, Q, Vt, If, f, H (e opcional Is) |
| Python → Elipse | `dados/<ug>/exportacao_elipse/*.csv` | Envelope Qsup/Qinf + limitadores |

Evoluções possíveis (OPC UA, HTTP) estão na seção 8; o protocolo de *dados*
(quais grandezas, por UG) permanece o mesmo.

---

## 2. Como deixar o Python rodando

### 2.1 Onde rodar

| Local | Recomendação |
|-------|----------------|
| **Mesmo servidor do Elipse E3** | Preferencial (latência baixa, pasta local) |
| VM / servidor da usina sempre ligado | OK se a pasta `dados/` for acessível ao E3 |
| Notebook do engenheiro | Só para teste — não use em operação |

### 2.2 Comando do serviço

```powershell
cd <pasta-do-clone>
.\venv\Scripts\Activate.ps1

# Produção: loop contínuo, todas as UGs em dados/
python main.py servico --intervalo 1

# Teste: um ciclo e encerra
python main.py servico --uma-vez

# Só algumas UGs
python main.py servico --apenas ug01,ug02 --intervalo 1
```

- `--intervalo 1` → ciclo a cada ~1 segundo (ajuste 0,5…2 s conforme carga).
- O processo **não deve fechar**: enquanto ele roda, os CSVs são atualizados.

### 2.3 Manter o processo sempre ativo (Windows)

**Opção A — Agendador de Tarefas (simples)**

1. Abrir *Agendador de Tarefas* → Criar Tarefa.
2. Disparar: **Ao iniciar o computador** (e opcionalmente “Se a tarefa falhar, reiniciar”).
3. Ação: Iniciar programa  
   - Programa: `<pasta-do-clone>\venv\Scripts\python.exe`  
   - Argumentos: `main.py servico --intervalo 1`  
   - Iniciar em: `<pasta-do-clone>`
4. Configurar para executar mesmo com usuário deslogado (conta de serviço da usina).

**Opção B — Serviço Windows (NSSM ou similar)**

1. Instalar [NSSM](https://nssm.cc/).
2. `nssm install CurvaCapabilidade`
3. Path = `...\venv\Scripts\python.exe`
4. Arguments = `main.py servico --intervalo 1`
5. Startup directory = pasta do repositório
6. Iniciar o serviço e marcar *Automatic*.

**Opção C — Sessão RDP / console**

Deixar um PowerShell aberto com o comando — **não recomendado** em produção
(fecha se a sessão cair).

### 2.4 Verificação de saúde

- No console do serviço: linhas `[ciclo N] X/Y UG ok (t s)`.
- Se uma UG falhar: `ERRO ug01: …` — as outras continuam.
- Confirmar que os CSV em `exportacao_elipse/` mudam de *data de modificação*
  a cada ciclo (quando Vt/If/f ou o ponto mudam).

---

## 3. Como diferenciar as unidades geradoras

### 3.1 Regra de identificação

Cada UG é **uma pasta** sob `dados/`, com nome único:

```
dados/
  ug01/                 ← id da UG = "ug01"
    gerador.json        ← placa (obrigatório)
    curvas.json
    campo.json          ← entradas dinâmicas (Elipse escreve)
    exportacao_elipse/  ← saída do Python (Elipse lê)
  ug02/
    gerador.json
    campo.json
    exportacao_elipse/
  compensador_01/       ← outro id, TipoMaquina = CompensadorSincrono
```

- O **id da UG** = nome da pasta (`ug01`, `ug02`, …).
- O serviço lista automaticamente toda pasta que contém `gerador.json`.
- No Elipse, use o **mesmo id** no prefixo das tags e no nome da tela/gráfico.

### 3.2 Criar nova UG

```powershell
python main.py nova-usina --pasta ug01 --nome "UHE X - UG 01"
python main.py nova-usina --pasta ug02 --nome "UHE X - UG 02"
```

Depois edite `gerador.json` / `curvas.json` / CSVs de cada pasta (placa diferente).

### 3.3 Convenção de tags no Elipse (obrigatória para não misturar)

| UG | Tags de campo (exemplo) | Pasta Python | Gráfico |
|----|-------------------------|--------------|---------|
| UG 01 | `UG01.P`, `UG01.Q`, `UG01.Vt`, `UG01.If`, `UG01.f`, `UG01.H` | `dados/ug01/` | Tela / XY da UG 01 |
| UG 02 | `UG02.P`, `UG02.Q`, … | `dados/ug02/` | Tela / XY da UG 02 |

**Nunca** ligue o gráfico da UG 01 aos CSV de `dados/ug02/exportacao_elipse/`.

### 3.4 Mapeamento Elipse ↔ pasta

Documente na engenharia da usina uma tabela fixa:

| Nome operacional | Pasta `dados/` | Prefixo tag Elipse |
|------------------|----------------|--------------------|
| Unidade 01 | `ug01` | `UG01` |
| Unidade 02 | `ug02` | `UG02` |
| Compensador | `compensador_01` | `CS01` |

---

## 4. Como o Elipse entrega informações ao Python

### 4.1 Arquivo de entrada: `campo.json`

Caminho por UG:

```text
dados/<id_ug>/campo.json
```

Formato (p.u. recomendado):

```json
{
  "EmPorUnidade": true,
  "P": 0.54,
  "Q": 0.13,
  "Vt": 1.0,
  "If": 1.0,
  "Is": 0.0,
  "f": 1.0,
  "H": 1.0
}
```

| Campo | Significado | Base se `EmPorUnidade=true` | Se `false` (SI) |
|-------|-------------|-----------------------------|-----------------|
| `P` | Potência ativa | Sn (MVA) → pu | MW |
| `Q` | Potência reativa | Sn | Mvar |
| `Vt` | Tensão terminal | Vn | kV |
| `If` | Corrente de campo | If_FL | A |
| `Is` | Corrente de estator | In; `0` = calcula S/Vt | A; `0` = calcula |
| `f` | Frequência | fn | Hz |
| `H` | Queda útil (hidro) | Hn | m |
| `EmPorUnidade` | Interpretação | `true` / `false` | |

Chaves que começam com `_` são comentários e são ignoradas.

### 4.2 Quais grandezas mudam o envelope

| Grandeza | Efeito no plot |
|----------|----------------|
| **Vt** | Redimensiona SCL e OEL |
| **If** | Teto de campo / OEL disponível |
| **f** | V/Hz e derating do OEL |
| **H** | Referência hidráulica (não corta o envelope elétrico neste projeto) |
| **P, Q** | Posição do **ponto** no gráfico (não redesenham sozinhas o envelope) |

Para curva dinâmica “perfeita”, o Elipse **deve** atualizar pelo menos **Vt, If e f**
(além de P e Q para o ponto).

### 4.3 Como o Elipse grava o `campo.json` (implementação)

O Elipse não fala Python nativamente. Use um destes padrões:

#### Padrão A — Script VBScript / Domain no E3 (timer 0,5–1 s)

1. Criar tags `UG01.P`, `UG01.Q`, `UG01.Vt`, `UG01.If`, `UG01.f`, `UG01.H`
   (já existentes do SCADA ou convertidas para p.u.).
2. Timer periódico escreve o arquivo (ex.: via `FileSystemObject` / script
   auxiliar / Driver de arquivo).

Pseudológica:

```
a cada 1 s:
  montar JSON com Tags("UG01.P"), Tags("UG01.Q"), …
  gravar em  C:\...\dados\ug01\campo.json
  repetir para UG02 → dados\ug02\campo.json
```

**Importante:** gravar de forma atômica se possível (escrever em
`campo.json.tmp` e renomear para `campo.json`) para o Python não ler arquivo
pela metade.

#### Padrão B — Programa ponte (recomendado se VBS for limitado)

Um pequeno utilitário (Python, C#, PowerShell) no mesmo servidor:

1. Lê tags do Elipse via **OPC UA** / API do E3 / DDE (conforme licença).
2. Escreve `campo.json` de cada UG.
3. Pode ser o **mesmo** processo do `servico` no futuro; hoje o `servico` só lê JSON.

#### Padrão C — Teste manual

Editar `campo.json` à mão e rodar `python main.py servico --uma-vez` para validar
o envelope sem Elipse.

### 4.4 Conversão para p.u. no Elipse

Preferível converter **no Elipse** (ou no ponte) e gravar já em p.u.:

```
P_pu  = P_MW  / Sn
Q_pu  = Q_Mvar / Sn
Vt_pu = V_kV  / Vn
If_pu = If_A  / If_FL
f_pu  = f_Hz  / fn
H_pu  = H_m   / Hn
```

Sn, Vn, If_FL, fn, Hn vêm da placa (`gerador.json` / `turbina.json`) daquela UG.
Se preferir gravar em SI, use `"EmPorUnidade": false` e valores em MW, Mvar, kV, A, Hz, m.

---

## 5. Como o Python entrega informações ao Elipse

### 5.1 Pasta de saída

A cada ciclo, para cada UG:

```text
dados/<id_ug>/exportacao_elipse/
  CurvaCapabilidade_LimiteSuperior.csv
  CurvaCapabilidade_LimiteInferior.csv
  CurvaCapabilidade_ContornoFechado.csv      (se houver)
  CurvaCapabilidade_<Limitador>_Superior.csv
  CurvaCapabilidade_<Limitador>_Inferior.csv
  ResultadoOperacional.csv                   (snapshot; opcional no gráfico)
  INSTRUCOES_GRAFICO_ELIPSE.md
```

### 5.2 Formato dos CSV do envelope

```csv
PotenciaReativaPu,PotenciaAtivaPu
0.75,0.00
0.70,0.50
...
```

- **Eixo X (horizontal)** = Q (PotenciaReativaPu)  
- **Eixo Y (vertical)** = P (PotenciaAtivaPu)  
- Valores em **p.u.** na base Sn daquela máquina  

Se o gráfico do Elipse estiver em MW/Mvar:

```
P_MW   = P_pu  * Sn
Q_Mvar = Q_pu  * Sn
```

(Sn da UG correspondente.)

### 5.3 Arquivos mínimos para o gráfico dinâmico

| Arquivo | Uso no XY |
|---------|-----------|
| `…_LimiteSuperior.csv` | Contorno superior do envelope |
| `…_LimiteInferior.csv` | Contorno inferior do envelope |
| Demais `…_*_Superior/Inferior.csv` | Opcional (mostrar OEL, UEL, SCL individualmente) |

### 5.4 Como o Elipse consome os CSV

1. Na tela da UG 01, criar **Gráfico XY**.
2. Configurar séries de referência apontando para  
   `...\dados\ug01\exportacao_elipse\CurvaCapabilidade_LimiteSuperior.csv`  
   e `…_LimiteInferior.csv`.
3. Ponto dinâmico: X = tag `UG01.Q`, Y = tag `UG01.P` (mesma unidade do gráfico).
4. **Atualização dinâmica do fundo:**
   - Se o E3 permitir *reload* periódico do arquivo CSV → configure o intervalo
     próximo ao `--intervalo` do Python (ex.: 1 s).
   - Se o E3 só importa CSV uma vez → use um mecanismo de “fonte dinâmica”
     (tabela interna alimentada por script que relê o arquivo, ou evolução OPC).

Sem *reload*, o ponto P–Q ainda se move, mas o **desenho do envelope** fica
congelado no último import — aí o serviço Python sozinho não basta; o Elipse
precisa reler os CSV.

### 5.5 Checklist por UG no Elipse

- [ ] Tags `UG0N.P/Q/Vt/If/f/(H)` existem e estão em engenharia/pu corretos  
- [ ] Timer/ponte grava `dados/ug0N/campo.json`  
- [ ] Gráfico XY usa **somente** CSV de `dados/ug0N/exportacao_elipse/`  
- [ ] Ponto XY = tags P e Q da **mesma** UG  
- [ ] Reload dos CSV habilitado (ou equivalente)

---

## 6. Ciclo completo (passo a passo temporal)

```text
t = 0,0 s   Elipse mede P,Q,Vt,If,f da UG01 e UG02
t = 0,1 s   Script/ponte grava dados/ug01/campo.json e dados/ug02/campo.json
t = 0,2 s   Python (já no loop) lê ug01 → calcula envelope → grava CSV ug01
t = 0,3 s   Python lê ug02 → calcula → grava CSV ug02
t = 0,5 s   Elipse relê CSV ug01/ug02 e redesenha fundos; ponto segue tags P,Q
t = 1,0 s   Próximo ciclo (intervalo = 1 s)
```

Um **único** processo Python percorre **todas** as UGs no mesmo loop; não é
necessário um Python por máquina.

---

## 7. Como implementar na usina (roteiro prático)

### Fase 0 — Preparar dados

1. Instalar Python + `venv` + `pip install -r requirements.txt` no servidor E3.  
2. Para cada máquina:

   ```powershell
   python main.py nova-usina --pasta ug01 --nome "…"
   ```

3. Editar placa e CSVs de fabricante.  
4. Validar offline:

   ```powershell
   python main.py simulador --dados dados/ug01
   python main.py exportar --dados dados/ug01
   ```

### Fase 1 — Serviço contínuo

1. Rodar `python main.py servico --intervalo 1` (e configurar Agendador/NSSM).  
2. Alterar `campo.json` manualmente (ex.: Vt=0.95) e ver CSV mudarem.  
3. Confirmar que UGs independentes não se misturam.

### Fase 2 — Ligar Elipse → Python

1. Mapear tags → campos do JSON (tabela da seção 3.4).  
2. Implementar gravação periódica de `campo.json` (VBS ou ponte OPC).  
3. Testar: variar Vt no supervisório e observar mudança no CSV / no gráfico.

### Fase 3 — Ligar Python → Elipse

1. Montar XY por UG com LimiteSuperior / LimiteInferior.  
2. Ponto P–Q dinâmico.  
3. Ativar reload dos CSV (ou tabela intermediária).  
4. Aceite operacional: curva acompanha tensão/campo/frequência.

### Fase 4 — Endurecimento

1. Conta de serviço Windows, restart automático.  
2. Log em arquivo (redirecionar stdout do serviço).  
3. Monitorar falhas por UG (`ERRO ug0N` no console).  
4. Backup das pastas `dados/`.

---

## 8. Evoluções de comunicação (opcional)

O protocolo lógico (por UG: entradas P,Q,Vt,If,f + saída séries Q×P) não muda.
Só muda o *transporte*:

| Transporte | Elipse → Python | Python → Elipse | Quando usar |
|------------|-----------------|-----------------|-------------|
| **Arquivo (atual)** | `campo.json` | CSV em `exportacao_elipse/` | Padrão, simples |
| **OPC UA** | Tags escritas/lidas | Tags array ou nós de série | Produção sem depender de reload de arquivo |
| **HTTP local** | `POST /ug01/campo` | `GET /ug01/envelope` | Prototipagem / firewall local |
| **Pasta de rede** | Mesmos JSON/CSV em `\\servidor\curva\` | Idem | E3 e Python em máquinas diferentes |

Recomendação: começar com **arquivo no mesmo servidor**; migrar para OPC UA se
o gráfico XY não reler CSV de forma confiável.

---

## 9. Problemas comuns

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| Envelope não muda no E3 | CSV não é relido | Configurar reload / ponte OPC |
| Envelope “errado” em uma UG | Gráfico aponta pasta de outra UG | Conferir caminho `dados/ug0N/` |
| Ponto longe da curva | P/Q em MW no gráfico e CSV em pu (ou vice-versa) | Unificar unidades (tudo pu ou tudo SI×Sn) |
| Serviço não vê UG | Falta `gerador.json` na pasta | Criar com `nova-usina` |
| `campo.json` ignorado | Chaves erradas ou JSON inválido | Validar JSON; usar P,Q,Vt,If,f |
| Uma UG em erro, outras ok | Esperado | Corrigir dados da UG com `ERRO` no log |

---

## 10. Resumo executivo

1. **Python rodando:** `python main.py servico --intervalo 1` como serviço/tarefa no servidor do Elipse.  
2. **Elipse → Python:** a cada ciclo, grava `dados/<ug>/campo.json` com P, Q, Vt, If, f (H).  
3. **Python → Elipse:** a cada ciclo, grava CSV do envelope em `dados/<ug>/exportacao_elipse/`.  
4. **Diferenciar UGs:** uma pasta + um prefixo de tag + um gráfico por unidade; nunca cruzar caminhos.  
5. **Dinâmica de verdade:** Elipse atualiza Vt/If/f no JSON **e** relê os CSV (ou equivalente OPC).

Comandos úteis:

```powershell
python main.py servico --intervalo 1
python main.py servico --apenas ug01,ug02 --uma-vez
python main.py nova-usina --pasta ug03 --nome "UHE X - UG 03"
```

Ver também: `ELIPSE_E3.md` (resumo), `dados/usina/campo.json` (modelo de entrada),
`src/servico/envelope_dinamico.py` (implementação do loop),
e o pacote completo de scripts do supervisório em **`elipse_e3/`**
(`GUIA_IMPLEMENTACAO.md` + `scripts/BibliotecaCompleta.vbs`).
