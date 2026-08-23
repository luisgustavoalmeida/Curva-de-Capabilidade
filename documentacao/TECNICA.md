# Documentação Técnica — Curva de Capabilidade

## 1. Introdução

A curva de capabilidade de um gerador síncrono define a **região permitida de operação** no diagrama Potência Ativa (P) × Potência Reativa (Q), delimitada por restrições térmicas, magnéticas e de estabilidade.

## 2. Referências Bibliográficas

| Referência | Aplicação na biblioteca |
|------------|-------------------------|
| Kundur (1994), Cap. 3 | Diagrama P-Q, limites de estabilidade |
| IEEE Std 1110-2002 | Modelagem, curvas de fabricante, limite de estator |
| IEC 60034-3 | Curvas de capabilidade padronizadas |
| Fitzgerald & Kingsley | Equações de potência aparente e corrente |
| Machowski et al. | Estabilidade estática |

## 3. Limites Implementados

### 3.1 Limite do Estator (Potência Aparente)

**Equação:**
$$Q_{limite} = \pm\sqrt{(V_t \cdot I_{max})^2 - P^2}$$

Em p.u. com \(I_{max}=1\): \(Q = \pm\sqrt{V_t^2 - P^2}\). O código usa `CorrenteEstatorMaximaPu` (configurável).

**Significado físico:** Restrição térmica do enrolamento do estator pela corrente total.

**Unidades:** P em MW (ou p.u.), S = \(V_t·I_{max}\) em MVA (ou p.u.), Q em Mvar (ou p.u.).

**Referência:** IEEE Std 1110-2002, Seção de stator heating limit.

### 3.2 Limite do Rotor (Sobre-excitação)

**Método:** Interpolação linear em curva tabulada do fabricante Q(P).

**Significado físico:** Aquecimento do enrolamento de campo por corrente de excitação elevada.

**Referência:** Kundur (1994), Seção 3.4.2; IEC 60034-3.

### 3.3 Limite de Sub-excitação

**Método:** Curva tabulada Q_min(P) do fabricante.

**Significado físico:** Limite inferior de excitação e aquecimento do rotor em operação capacitiva.

### 3.4 Limite de Estabilidade Estática

**Método:** Curva tabulada ou estimativa conservadora.

**Significado físico:** Margem mínima de estabilidade estática em regime permanente.

**Referência:** Kundur (1994), Cap. 5; Machowski et al., Cap. 4.

### 3.5 Limite Volts/Hertz (V/Hz — sobrefluxo)

**Equação:**
$$(V/Hz)_{pu} = \frac{V_{t,pu}}{f_{pu}}$$

**Limite típico:** \(1{,}05\) pu (configurável em `RelacaoVoltsHertzMaximaPu`).

**Efeitos:**
- Verificação operacional: se \(V_t/f > (V/Hz)_{max}\) → fora da curva
- Derating do OEL: \(fator = \min\!\big(1,\; (V/Hz)_{max}/(V_t/f)\big)\) multiplica \(Q_{OEL}\)

**Referência:** IEEE Std C37.102; Kundur — overfluxing; IEC 60034.

### 3.6 Limite de Potência Mecânica (Pmec)

**Método:** `PotenciaMecanicaMaximaPu` / `PotenciaMecanicaMinimaPu` em `curvas.json`.

**Significado físico:** Teto/piso de potência ativa da região permitida (máquina / conjunto).

A **queda útil** e o **teto da turbina** são traçados como referência e **não** cortam o envelope.

## 4. Composição do Envelope

Traçado operacional (ONS BD Anatem / IEEE Std 1110):

$$P_{mec,min} \le P \le P_{mec,max}$$
$$Q_{sup}(P) = \min\big(Q_{OEL\,TH}(V_t,I_f),\; Q_{SCL}(V_t)[,\; Q_{sat\,magnética}]\big)$$
$$Q_{inf}(P) = \max\big(Q_{UEL},\; Q_{MEL},\; Q_{estator,min}(V_t)[,\; Q_{UEL\,prático}][,\; Q_{saliência}][,\; Q_{end\text{-}iron}]\big)$$

A **turbina / Pmec** restringe a faixa de \(P\), não entra em \(Q_{sup}\).

Curvas tabuladas em \(V_{t,ref}\) são escaladas para \(V_t\) atual (raio aparente ou \(V^2\) no UEL).
\(E_{fd}(I_f)\) usa OCC (`ArquivoCurvaV`) ou modelo bipartido \(I_{f,NL}/I_{f,FL}\) (IEEE 1110).

Se \(Q_{sup} < Q_{inf}\), a região é **inválida** (sem envelope) — não se colapsa ao ponto médio.

## 5. Margem Operacional

$$\text{Margem (\%)} = 100 \times \frac{\min(Q_{sup} - Q,\; Q - Q_{inf})}{S_{base}}$$

## 6. Convenção Gráfica e Traçado Operacional (p.u.)

| Eixo | Grandeza | Unidade |
|------|----------|---------|
| Horizontal (X) | Potência Reativa (Q) | p.u. |
| Vertical (Y) | Potência Ativa (P) | p.u. |

**Base:** potência aparente nominal Sn (MVA).

$$P_{pu} = \frac{P_{MW}}{S_n} \qquad Q_{pu} = \frac{Q_{Mvar}}{S_n} \qquad V_{t,pu} = \frac{V_{kV}}{V_n}$$

### Traçado Operacional (ONS BD Anatem)

$$P_{mec,min} \le P \le P_{mec,max}$$
$$Q_{inf}(P,V_t) \le Q \le Q_{sup}(P,V_t)$$

$$Q_{sup} = \min\big(Q_{OEL\,TH}(V_t,I_f),\; Q_{SCL/estator}(V_t)\big)$$
$$Q_{inf} = \max\big(Q_{UEL},\; Q_{MEL},\; Q_{estator,min}(V_t)[,\; Q_{UEL\,prático}]\big)$$

**Limitadores plotados (referência ONS):**

| Série | Papel |
|-------|--------|
| OEL TH | Sobre-excitação térmica contínua (envelope) |
| OEL PK | Pico de campo / curto prazo (referência) |
| SCL / Estator | Aquecimento do estator (±) |
| IFD | Curva de corrente de campo (referência) |
| UEL | Limite de subexcitação / estabilidade ativo |
| UEL Prático | Estabilidade prática (referência / envelope) |
| MEL | Minimum Excitation Limiter |
| Saliência polar | Referência (só no envelope se habilitada) |
| End-iron | Aquecimento extremo do estator (IEEE 1110; envelope com curva) |
| Saturação magnética | Limite superior adicional (`ArquivoSaturacaoMagnetica`) |
| Pmec Max | **Limite** da região permitida em P (`PotenciaMecanicaMaximaPu`) |
| Queda útil | **Referência** \(P(H)\) — não corta o envelope; H pode variar livremente |
| Turbina Max | **Referência** teto mecânico da turbina |
| Pmec Min | **Limite** inferior da região (se > 0) |
| fp nominal | Reta do fator de potência nominal (gerador) |
| Eixo P = 0 | Eixo de operação do compensador síncrono |
| SCL efetivo | Arco `LimiteEstator` do envelope (tab ∩ analítico) |
| S = Vt·Imax | Círculo analítico de capacidade do estator |

### Compensador síncrono

Máquina síncrona sem turbina (`TipoMaquina = CompensadorSincrono`), operando com **P ≈ 0**:

- `turbina.json` ausente; `PotenciaMecanicaMaximaPu = 0`
- Região permitida: faixa estreita em torno de P = 0 entre Qinf e Qsup
- Curvas de referência (OEL, UEL, MEL, SCL…): varrem P ∈ [−0,25; 1,25] sem restrição de Pmec
- Entrada P fixada em 0; queda H omitida na interface

Exemplo: altere `TipoMaquina` em `dados/usina/gerador.json` (ou numa cópia) para `CompensadorSincrono` e remova `turbina.json`.

### Dependência da tensão de barramento \(V_t\)

**Estator (Kundur / IEEE 1110):**
$$Q = \pm\sqrt{(V_t \cdot I_{max})^2 - P^2}$$

**Campo / rotor:**
$$Q = -\frac{V_t^2}{X_d} + \sqrt{\left(\frac{V_t E_{fd,max}}{X_d}\right)^2 - P^2}$$

Para o conjunto de demonstração: \(P_{mec,max}=0{,}9\) pu, \(X_d=0{,}8\) pu, \(V_t\) configurável.

## 7. Entradas de campo para posicionar a máquina na curva

Para saber **onde a máquina está** no diagrama P–Q e se o envelope está correto,
a prática profissional (Kundur Cap. 3, IEEE Std 1110, ONS BD Anatem, IEC 60034-3,
supervisórios tipo Elipse E3) usa as seguintes tags de campo, **preferencialmente em p.u.**:

| Entrada | Símbolo | Base | Necessária para | Observação |
|---------|---------|------|-----------------|------------|
| Potência ativa | \(P\) | \(S_n\) | Coordenada Y do ponto | Medida de wattímetro / SCADA |
| Potência reativa | \(Q\) | \(S_n\) | Coordenada X do ponto | Medida de varmetro / SCADA |
| Tensão terminal | \(V_t\) | \(V_n\) | Recalcular envelope (SCL/OEL) | Kundur / ONS — limites dependem de \(V_t\) |
| Corrente de campo | \(I_f\) | \(I_{f,FL}\) | Limite OEL / lado direito | \(E_{fd}\propto I_f\); teto de excitação disponível |
| Corrente de estator | \(I_s\) | \(I_n\) | Verificação SCL | `Is=0` → \(I_s=S/V_t\); `Is>0` → medida. Curva usa **Imax** (`CorrenteEstatorMaximaPu`) |
| Frequência | \(f\) | \(f_n\) | Limite V/Hz + derating OEL | \((V/Hz)=V_t/f\); típ. máx 1,05 pu |
| Queda útil (hidro) | \(H\) | \(H_n\) | Referência \(P(H)\) no gráfico | Não altera a região permitida (só Pmec Max/Min) |

**Derivadas (não são entradas):** \(S=\sqrt{P^2+Q^2}\), \(\mathrm{fp}=P/S\).

Conversões:
$$
P_{pu}=\frac{P_{MW}}{S_n},\quad
Q_{pu}=\frac{Q_{Mvar}}{S_n},\quad
V_{t,pu}=\frac{V_{kV}}{V_n},\quad
I_{f,pu}=\frac{I_f}{I_{f,FL}},\quad
I_{s,pu}=\frac{I_s}{I_n},\quad
f_{pu}=\frac{f}{f_n},\quad
H_{pu}=\frac{H}{H_n}
$$

No simulador, todas essas entradas estão no painel **Entradas de campo (p.u.)**.

## 8. Integração Elipse E3

1. Exportar CSVs com `python main.py exportar --dados dados/<usina>`
   **ou** serviço contínuo: `python main.py servico` (todas as UGs no mesmo loop)
2. Configurar gráfico XY no Elipse E3 (um por UG)
3. Importar séries de `exportacao_elipse/` da pasta da UG
4. Vincular tags de P e Q ao ponto operacional

Uso no E3: **somente representação visual**. Entradas dinâmicas: `campo.json` por UG.

## 9. Arquivos de Configuração

| Arquivo | Conteúdo |
|---------|----------|
| gerador.json | Placa + TipoMaquina (obrigatório) |
| curvas.json | Pmec, Imax, V/Hz; ponteiros CSV **opcionais** |
| turbina.json | Turbina (opcional; omitir no compensador) |
| *.csv | Curvas de fabricante (opcional) |

Template: `dados/usina/`. Sem CSV, envelope = SCL analítico + OEL analítico; UEL/MEL não entram.

Chaves opcionais em `curvas.json` (arquivo CSV deve existir; senão é ignorado):
- `ArquivoSobreExcitacao`, `ArquivoRotor`, `ArquivoEstabilidade`, `ArquivoSubExcitacao`
- `ArquivoEstator`, `ArquivoCorrenteCampo`, `ArquivoSalienciaPolar`
- `ArquivoCurvaV`, `ArquivoAquecimentoExtremo`, `ArquivoSaturacaoMagnetica`
- `RelacaoVoltsHertzMaximaPu`, `DeratingOelPorVoltsHertz`

