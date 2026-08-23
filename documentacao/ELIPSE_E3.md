# Integração com Elipse E3

Documento completo de comunicação dinâmica (serviço, tags, multi-UG, implementação):

→ **[COMUNICACAO_ELIPSE_PYTHON.md](COMUNICACAO_ELIPSE_PYTHON.md)**

Scripts VBScript prontos para o Elipse (enviar campo + ler CSV + plot):

→ **[../elipse_e3/GUIA_IMPLEMENTACAO.md](../elipse_e3/GUIA_IMPLEMENTACAO.md)**  
→ **[../elipse_e3/scripts/BibliotecaCompleta.vbs](../elipse_e3/scripts/BibliotecaCompleta.vbs)**

## Objetivo

A curva de capabilidade no Elipse E3 é **apenas representação visual**:
envelope e limitadores calculados em Python, exibidos no gráfico XY.

## Exportação estática (uma máquina)

```powershell
python main.py exportar --dados dados/usina
```

Arquivos em `dados/usina/exportacao_elipse/` (CSV Q × P em p.u.).

## Envelope dinâmico (várias UGs)

Um **único serviço** percorre todas as pastas em `dados/` (com `gerador.json`) no mesmo loop:

```powershell
# Contínuo (servidor da usina, junto do Elipse)
python main.py servico --intervalo 1

# Um ciclo (teste)
python main.py servico --uma-vez

# Só algumas UGs
python main.py servico --apenas usina,ug02 --intervalo 1
```

### Por UG

| Arquivo | Função |
|---------|--------|
| `campo.json` | Entradas P, Q, Vt, If, f, H (Elipse/OPC pode sobrescrever) |
| `exportacao_elipse/*.csv` | Séries do gráfico XY (atualizadas a cada ciclo) |

```
dados/
  ug01/  campo.json → serviço → exportacao_elipse/
  ug02/  campo.json → serviço → exportacao_elipse/
```

### Loop

```text
carregar todas as UGs
enquanto True:
  para cada UG:
    ler campo.json
    recalcular envelope
    gravar CSVs em exportacao_elipse/
  esperar intervalo
```

### Gráfico XY no Elipse

| Eixo | Grandeza | Tag |
|------|----------|-----|
| X | Q | `UG01.PotenciaReativa` |
| Y | P | `UG01.PotenciaAtiva` |

1. Importar/vincular CSVs da pasta `exportacao_elipse` **dessa** UG.
2. Ponto dinâmico com tags P e Q.
3. Se o E3 puder reler CSV periodicamente (ou via OPC), o envelope acompanha Vt/If/f.

Para produção: rode `python main.py servico` como serviço Windows no mesmo servidor do Elipse. Um script/OPC grava `campo.json` (ou evolua para OPC UA direto).

## O que não fazer no Elipse

- Não recalcular OEL/UEL/MEL/SCL no VBScript
- Não usar a curva para alarme

## Referências

- Manual Elipse E3: Gráficos XY
- IEEE Std 1110-2002 / Kundur — diagrama P–Q
