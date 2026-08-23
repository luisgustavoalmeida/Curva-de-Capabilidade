# Pastas de dados

Há **um template**: [`usina/`](usina/) (dados alinhados ao Sobradinho, com comentários). Visão geral do projeto: [`../README.md`](../README.md).

```
dados/
  usina/          — template (edite uma cópia para cada instalação)
  <sua_usina>/    — python main.py nova-usina --pasta sua_usina
```

Cada pasta com `gerador.json` é uma **UG**. O serviço dinâmico percorre todas:

```powershell
python main.py servico --intervalo 1
```

Entradas por UG: `campo.json` → saída: `exportacao_elipse/`.

## Nova usina

```powershell
python main.py nova-usina --pasta minha_usina --nome "Usina X"
python main.py simulador --dados dados/minha_usina
```

Edite os valores em `gerador.json`, `curvas.json` e `turbina.json`.  
Chaves `_…` no JSON e linhas `#…` no CSV são comentários (ignoradas).

## CSVs

Opcionais. Declare o nome em `curvas.json`; se o arquivo não existir, é ignorado.  
Sem CSV: envelope = SCL + OEL analíticos + Pmec + V/Hz.

## TipoMaquina (`gerador.json`)

- `Gerador`
- `CompensadorSincrono` — P ≈ 0; remova `turbina.json`
