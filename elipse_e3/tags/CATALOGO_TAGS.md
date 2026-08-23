# Catálogo de tags — Elipse E3 × Curva de Capabilidade

Crie estas tags no **Domain** (Internal Tags ou vinculadas a drivers).
Substitua `UG01` pelo prefixo da unidade (`UG02`, `USINA`, …) — um conjunto **por UG**.

---

## 1. Entradas de campo (Elipse → Python)

O script `01_EnviarCampoParaPython.vbs` lê estas tags e grava `campo.json`.

### Opção A — Engenharia (SI) — conversão automática para p.u.

| Tag | Tipo | Unidade | Obrigatória | Descrição |
|-----|------|---------|-------------|-----------|
| `UG01.P_MW` | Real | MW | Sim* | Potência ativa |
| `UG01.Q_Mvar` | Real | Mvar | Sim* | Potência reativa |
| `UG01.Vt_kV` | Real | kV | Sim* | Tensão terminal |
| `UG01.If_A` | Real | A | Sim* | Corrente de campo |
| `UG01.f_Hz` | Real | Hz | Sim* | Frequência |
| `UG01.Is_A` | Real | A | Não | Estator; `0` = Python calcula |
| `UG01.H_m` | Real | m | Não | Queda útil (hidro) |

\*Obrigatória se não existirem as tags em p.u. abaixo.

Bases de conversão vêm de `00_Config.vbs` (Sn, Vn, If_FL, fn, Hn) por UG.

### Opção B — Já em p.u. (prioridade se existirem)

| Tag | Base |
|-----|------|
| `UG01.P_pu` | Sn |
| `UG01.Q_pu` | Sn |
| `UG01.Vt_pu` | Vn |
| `UG01.If_pu` | If_FL |
| `UG01.f_pu` | fn |
| `UG01.Is_pu` | In (`0` = calcula) |
| `UG01.H_pu` | Hn |

---

## 2. Status e ponto (Python → Elipse / script de leitura)

| Tag | Tipo | Descrição |
|-----|------|-----------|
| `UG01.CampoJsonOk` | Bool/Int | `1` se `campo.json` gravado com sucesso |
| `UG01.EnvelopeCsvOk` | Bool/Int | `1` se CSV superior/inferior existem |
| `UG01.CurvaTimestamp` | Date/Text | Última atualização do plot |
| `UG01.PontoP_pu` | Real | P do ponto (para pen Y) |
| `UG01.PontoQ_pu` | Real | Q do ponto (para pen X) |
| `UG01.Qsup_pu` | Real | Q superior efetivo no P atual |
| `UG01.Qinf_pu` | Real | Q inferior efetivo no P atual |
| `UG01.NPontosSup` | Int | Pontos carregados no array superior |
| `UG01.NPontosInf` | Int | Pontos carregados no array inferior |

### Globais (opcional)

| Tag | Descrição |
|-----|-----------|
| `CurvaCapabilidade.UGsCampoOk` | Quantidade de UGs com campo.json OK |
| `CurvaCapabilidade.UGsCsvOk` | Quantidade de UGs com CSV OK |

---

## 3. Arrays para plot (estratégia B — opcional)

Se `CARREGAR_ARRAYS_NO_TIMER = True` em `03_TimerCicloCompleto.vbs`:

| Tag | Tamanho sugerido | Conteúdo |
|-----|------------------|----------|
| `UG01.EnvSup_Q[0..499]` | 500 | Q (pu) envelope superior |
| `UG01.EnvSup_P[0..499]` | 500 | P (pu) envelope superior |
| `UG01.EnvInf_Q[0..499]` | 500 | Q (pu) envelope inferior |
| `UG01.EnvInf_P[0..499]` | 500 | P (pu) envelope inferior |

Vincule as pens do **ChartXY** a esses arrays (X = Q, Y = P).

---

## 4. Checklist rápido por UG

- [ ] Prefixo único (`UG01`, `UG02`, …)  
- [ ] Tags SI **ou** pu de campo  
- [ ] Tags de status criadas  
- [ ] Pasta `dados/<id>/` existe com `gerador.json`  
- [ ] ChartXY da tela usa CSV/`Env*` **dessa** UG apenas  
- [ ] Ponto XY: X = `PontoQ_pu` (ou `Q_pu`), Y = `PontoP_pu` (ou `P_pu`)  
