# Template de usina (`dados/usina`)

Único exemplo do projeto. Dados alinhados ao **Sobradinho** (Sn 194,5 MVA, FP 0,9), já validados nos testes.

Documentação geral: [`../../README.md`](../../README.md).

## Nova usina

1. Copie a pasta ou rode:
   ```powershell
   python main.py nova-usina --pasta minha_usina
   ```
2. Edite **só os valores** em `gerador.json`, `curvas.json` e (se houver) `turbina.json`.
3. Ajuste ou remova CSVs conforme o fabricante.
4. Rode:
   ```powershell
   python main.py simulador --dados dados/minha_usina
   python main.py servico --intervalo 1
   ```

## Arquivos

| Arquivo | Obrigatório | Função |
|---------|-------------|--------|
| `gerador.json` | Sim | Placa + `TipoMaquina` |
| `curvas.json` | Sim | Pmec, Imax, V/Hz + nomes dos CSVs |
| `turbina.json` | Não | Hidro (referência de queda) |
| `campo.json` | Não* | Entradas P, Q, Vt, If, f, H do serviço dinâmico |
| `*.csv` | Não | Curvas de fabricante |

\*Obrigatório para o serviço atualizar o ponto; sem ele, usa o ponto padrão do simulador.

Chaves JSON que começam com `_` e linhas CSV que começam com `#` são **comentários** (ignoradas).

## Compensador

Em `gerador.json`: `"TipoMaquina": "CompensadorSincrono"`, potências ativas = 0. Remova `turbina.json`.

## Sem CSV

Se apagar os CSVs (ou as chaves em `curvas.json`), o envelope usa **SCL + OEL analíticos** + Pmec + V/Hz.
