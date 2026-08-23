# Guia de implementação — Elipse E3 × Curva de Capabilidade

Este guia detalha **todas** as responsabilidades do lado Elipse:
enviar variáveis ao Python, ler CSV e montar o plot.  
Scripts prontos: pasta `elipse_e3/scripts/`.

Documento irmão (arquitetura geral):  
[`../documentacao/COMUNICACAO_ELIPSE_PYTHON.md`](../documentacao/COMUNICACAO_ELIPSE_PYTHON.md)

---

## 1. Princípio (não confundir)

| Sistema | Responsabilidade |
|---------|------------------|
| **Python** (`main.py servico`) | Calcula o envelopamento e **grava CSV** (números Q×P) |
| **Elipse E3** | **Plota** o Gráfico XY com esses CSV + ponto das tags |

O Python **não** gera imagem PNG para o Elipse.  
O Elipse **não** recalcula OEL/UEL/MEL.

---

## 2. Arquivos desta pasta

```
elipse_e3/
  README.md
  GUIA_IMPLEMENTACAO.md          ← este arquivo
  config/ugs.txt                 ← lista de UGs (espelho do VBS)
  tags/CATALOGO_TAGS.md          ← todas as tags necessárias
  scripts/
    00_Config.vbs                ← caminhos, UGs, nomes de tags/arquivos
    04_Utilitarios.vbs           ← FSO, leitura de tags, JSON numérico
    01_EnviarCampoParaPython.vbs ← Elipse → campo.json
    02_LerCsvEAtualizarPlot.vbs  ← CSV → status / arrays do plot
    03_TimerCicloCompleto.vbs    ← Timer: envia + lê
    BibliotecaCompleta.vbs       ← tudo em um arquivo (colar no E3)
```

---

## 3. Preparar o Python (servidor)

```powershell
cd <pasta-do-clone>
.\venv\Scripts\Activate.ps1
python main.py servico --intervalo 1
```

Deixe rodando (Agendador de Tarefas / NSSM).  
Cada pasta em `dados/` com `gerador.json` é uma UG.

Ajuste `CAMINHO_RAIZ_DADOS` em `00_Config.vbs` para o mesmo caminho.

---

## 4. Preparar tags no Elipse

1. Abra [`tags/CATALOGO_TAGS.md`](tags/CATALOGO_TAGS.md).  
2. Para cada UG, crie o conjunto com o prefixo (`UG01`, `UG02`, …).  
3. Ligue tags de campo aos drivers (MW, Mvar, kV, A, Hz) **ou** já em p.u.

---

## 5. Configurar scripts no Elipse

### 5.1 Biblioteca

1. No Studio, crie um **Library** / Script compartilhado.  
2. Cole o conteúdo de `scripts/BibliotecaCompleta.vbs`  
   **ou** os arquivos `00` → `04` → `01` → `02` → `03` nesta ordem.  
3. Edite no topo:
   - `CAMINHO_RAIZ_DADOS`
   - `ObterDefinicaoUGs()` (pastas e bases Sn, Vn, …)

### 5.2 Timer

1. Crie um Timer no Domain (Enabled = True, Interval = **1000** ms).  
2. No evento:

```vb
Call CicloCurvaCapabilidade()
```

Isso:
1. Grava `campo.json` de todas as UGs  
2. Lê CSV / atualiza status e (opcional) arrays do plot  

O cálculo do envelope continua no processo Python externo.

### 5.3 Sintaxe de Tags

Os scripts usam `Application.GetObject(nome).Value`.  
Se na sua versão o padrão for `Tags("nome")`, altere as funções
`LerTag` / `EscreverTag` em `04_Utilitarios.vbs` (há comentários no código).

---

## 6. Montar o Gráfico XY (plot)

Para **cada** UG, uma tela com um **Chart XY**.

### Eixos (obrigatório)

| Eixo | Grandeza | Tag do ponto |
|------|----------|--------------|
| **X** (horizontal) | Q | `UG01.PontoQ_pu` ou `UG01.Q_pu` |
| **Y** (vertical) | P | `UG01.PontoP_pu` ou `UG01.P_pu` |

Unidade: **p.u.** (igual aos CSV do Python).  
Se o gráfico for em MW/Mvar, multiplique por Sn nas pens ou converta tags.

### Estratégia A — ChartXY ligado ao arquivo (recomendada)

1. Pen **Envelope Superior**  
   - Fonte:  
     `...\dados\ug01\exportacao_elipse\CurvaCapabilidade_LimiteSuperior.csv`  
   - Coluna X = `PotenciaReativaPu`, Y = `PotenciaAtivaPu`  
2. Pen **Envelope Inferior** → `…_LimiteInferior.csv`  
3. Pen **Ponto operacional** → X/Y = tags `PontoQ_pu` / `PontoP_pu`  
4. Se a versão do E3 permitir, configure **atualização periódica** do arquivo
   (mesmo período do timer / serviço Python).

Com `CARREGAR_ARRAYS_NO_TIMER = False` (padrão em `03_`), o script só valida
CSV e preenche Qsup/Qinf/status.

### Estratégia B — Arrays de tags

1. Em `03_TimerCicloCompleto.vbs`: `CARREGAR_ARRAYS_NO_TIMER = True`  
2. Crie tags array `UG01.EnvSup_Q[0..499]`, `EnvSup_P`, `EnvInf_Q`, `EnvInf_P`  
3. Pens do ChartXY apontam para esses arrays  
4. O script `02_` recarrega os arrays a cada ciclo a partir do CSV  

Use B se o E3 **não** reler arquivo CSV automaticamente.

### Limitadores individuais (opcional)

Arquivos extras na mesma pasta, ex.:

- `CurvaCapabilidade_LimiteEstator_Superior.csv`  
- `CurvaCapabilidade_LimiteSobreExcitacao_Superior.csv`  
- `CurvaCapabilidade_LimiteEstabilidade_Inferior.csv`  

Importe como pens adicionais (cores diferentes), se desejar visualizar
cada limitador além do envelope.

---

## 7. Variáveis enviadas ao Python (checklist)

| Variável | Tag típica | Efeito |
|----------|------------|--------|
| P | `P_MW` / `P_pu` | Ponto no gráfico |
| Q | `Q_Mvar` / `Q_pu` | Ponto no gráfico |
| Vt | `Vt_kV` / `Vt_pu` | Redimensiona SCL/OEL |
| If | `If_A` / `If_pu` | Teto de campo |
| f | `f_Hz` / `f_pu` | V/Hz e derating OEL |
| Is | `Is_A` / `Is_pu` | Opcional (0 = calcula) |
| H | `H_m` / `H_pu` | Referência hidro |

Arquivo gerado:

```text
dados/<IdPasta>/campo.json
```

Exemplo:

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

---

## 8. Diferenciar unidades geradoras

| Conceito | Exemplo UG 01 | Exemplo UG 02 |
|----------|---------------|---------------|
| Pasta Python | `dados/ug01/` | `dados/ug02/` |
| Prefixo tag | `UG01` | `UG02` |
| campo.json | `dados/ug01/campo.json` | `dados/ug02/campo.json` |
| CSV plot | `dados/ug01/exportacao_elipse/` | `dados/ug02/exportacao_elipse/` |
| Tela / ChartXY | Tela UG 01 | Tela UG 02 |

**Nunca** aponte o gráfico da UG 01 para a pasta da UG 02.  
A lista mestra está em `00_Config.vbs` → `ObterDefinicaoUGs()` e em `config/ugs.txt`.

---

## 9. Sequência de implantação (passo a passo)

1. Instalar Python + venv no servidor E3; testar `servico --uma-vez`.  
2. Criar pastas `ug01`, `ug02`, … com `nova-usina`.  
3. Ajustar `00_Config.vbs` (caminho + lista UGs + bases).  
4. Criar todas as tags do catálogo.  
5. Importar `BibliotecaCompleta.vbs` + Timer.  
6. Verificar que `campo.json` é reescrito a cada segundo.  
7. Verificar que `exportacao_elipse/*.csv` mudam com Vt/If.  
8. Montar ChartXY (estratégia A ou B).  
9. Validar ponto dinâmico e envelope.  
10. Registrar serviço Python no Agendador/NSSM.

---

## 10. Testes manuais

| Teste | Como | Esperado |
|-------|------|----------|
| Só envio | `Call Teste_SoEnviarCampo()` | `campo.json` atualizado; `CampoJsonOk=1` |
| Só plot | `Call Teste_SoAtualizarPlot()` | `EnvelopeCsvOk=1`; arrays/Qsup preenchidos |
| Vt baixo | Forçar `Vt_pu=0.95` | Envelope CSV muda após ciclo Python |
| UG isolada | Parar tag de ug02 | Só ug01 continua OK no log Python |

---

## 11. Problemas comuns

| Sintoma | Causa | Ação |
|---------|-------|------|
| `CampoJsonOk=0` | Caminho errado / permissão | Conferir `CAMINHO_RAIZ_DADOS` e ACL |
| `EnvelopeCsvOk=0` | Python parado | Iniciar `main.py servico` |
| Plot não mexe | CSV não relido / arrays off | Estratégia B ou reload de arquivo |
| Ponto deslocado | MW no gráfico e pu no CSV | Unificar unidades |
| Mistura de UGs | Prefixo/pasta trocados | Revisar `ObterDefinicaoUGs` e pens |

---

## 12. Resumo das responsabilidades do Elipse

1. **Enviar** P, Q, Vt, If, f (, Is, H) → `campo.json` por UG.  
2. **Ler** CSV do envelope → alimentar ChartXY (arquivo ou arrays).  
3. **Plotar** no ChartXY (Elipse desenha; não usa imagem Python).  
4. **Separar** UGs por pasta + prefixo + tela.  
5. **Temporizar** o ciclo com Timer (~1 s), alinhado ao serviço Python.
