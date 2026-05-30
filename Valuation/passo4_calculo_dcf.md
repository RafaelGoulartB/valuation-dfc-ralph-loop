# Passo 4 — Execução do Modelo DCF

> **Pré-requisito:** o JSON consolidado do Passo 3 deve estar com `validacoes.pronto_para_passo4: true` e `campos_nulos_restantes: []`. Se não estiver, volte ao Passo 3.

**Objetivo:** executar todos os blocos de cálculo em sequência estrita usando exclusivamente os valores do JSON do Passo 3. Não assumir, estimar ou aproximar nenhum valor intermediário. Ao final, produzir a tabela de projeção completa, o resumo de valor e o diagnóstico de sobre/subvalorização.

---

## REGRAS DE EXECUÇÃO

```
REGRA 1: Nunca arredonde valores intermediários.
  Use precisão total nos cálculos. Arredonde APENAS na exibição final (2 casas decimais).

REGRA 2: Execute os blocos na ordem A → B → C → D → E → F. Nunca pule um bloco.

REGRA 3: A cada bloco, registre o resultado antes de passar ao próximo.

REGRA 4: Se qualquer resultado intermediário parecer fora do esperado,
  pause, sinalize e aguarde confirmação antes de continuar.

REGRA 5: Taxas sempre em decimal nos cálculos.
  Exiba como percentual apenas na tabela de output (ex: 0,1669 → "16,69%").
```

---

## BLOCO A — CUSTO DE CAPITAL (WACC)

Execute nesta ordem exata:

**A1. Capitalização de Mercado**
```
MktCap = P × Shares
MktCap = ____ × ____ = ____ M
```

**A2. Beta Alavancado**
```
Beta_L = Beta_u × [1 + (1 − IR_marg) × (D / MktCap)]
Beta_L = ____ × [1 + (1 − ____) × (____ / ____)]
Beta_L = ____
```

**A3. Custo de Capital Próprio**
```
Ke = Rf + Beta_L × ERP
Ke = ____ + ____ × ____
Ke = ____  (____%)
```

**A4. Custo Líquido da Dívida**
```
Kd_liq = Kd_pre × (1 − IR_marg)
Kd_liq = ____ × (1 − ____)
Kd_liq = ____  (____%)
```

**A5. Pesos na Estrutura de Capital**
```
W_equity = MktCap / (MktCap + D) = ____ / (____ + ____) = ____
W_debt   = D / (MktCap + D)       = ____ / (____ + ____) = ____
Verificação: W_equity + W_debt = ____ (deve ser = 1,0000)
```

**A6. WACC Inicial**
```
WACC_0 = W_equity × Ke + W_debt × Kd_liq
WACC_0 = ____ × ____ + ____ × ____
WACC_0 = ____  (____%)
```

**A7. WACC por Ano**

Fórmulas:
```
Anos 1–5:    WACC(t) = WACC_0
Anos 6–10:   WACC(t) = WACC_0 + [(t − 5) / 5] × (WACC_est − WACC_0)
Terminal:    WACC(t) = WACC_est
```

| Ano | Fórmula aplicada | WACC calculado |
|-----|-----------------|---------------|
| 1   | WACC_0          | |
| 2   | WACC_0          | |
| 3   | WACC_0          | |
| 4   | WACC_0          | |
| 5   | WACC_0          | |
| 6   | WACC_0 + (1/5)×(WACC_est−WACC_0) | |
| 7   | WACC_0 + (2/5)×(WACC_est−WACC_0) | |
| 8   | WACC_0 + (3/5)×(WACC_est−WACC_0) | |
| 9   | WACC_0 + (4/5)×(WACC_est−WACC_0) | |
| 10  | WACC_est        | |
| Term| WACC_est        | |

Verificação: `WACC(10) = WACC_est` → ____  (deve ser idêntico)

**A8. Alíquota de IR por Ano**

Fórmulas:
```
Anos 1–5:    IR(t) = IR_ef
Anos 6–10:   IR(t) = IR_ef + [(t − 5) / 5] × (IR_marg − IR_ef)
Terminal:    IR(t) = IR_marg
```

| Ano | IR(t) |
|-----|-------|
| 1–5 | |
| 6   | |
| 7   | |
| 8   | |
| 9   | |
| 10  | |
| Term| |

Verificação: `IR(10) = IR_marg` → ____  (deve ser idêntico)

---

## BLOCO B — PROJEÇÕES ANUAIS (t = 1 a 10)

Execute para cada ano em sequência. Cada linha depende da anterior.

**Fórmulas de referência:**
```
g(1)        = g1
g(2 a 5)    = g2_5
g(6 a 10)   = g2_5 − [(t−5)/5] × (g2_5 − g_perp)

Rev(t)      = Rev(t−1) × [1 + g(t)]        | Rev(0) = Rev_0

Mg(1)       = Mg_1
Mg(2..conv) = Mg_1 + [(t−1)/(Ano_conv−1)] × (Mg_alvo − Mg_1)
Mg(t>conv)  = Mg_alvo

EBIT(t)     = Rev(t) × Mg(t)
NOPAT(t)    = EBIT(t) × [1 − IR(t)]
Reinvest(t) = [Rev(t) − Rev(t−1)] / StC
FCFF(t)     = NOPAT(t) − Reinvest(t)
```

**Tabela de projeção (preencher completamente):**

| Ano | g(t) | Rev(t) | Mg(t) | EBIT(t) | IR(t) | NOPAT(t) | Reinvest(t) | FCFF(t) |
|-----|------|--------|-------|---------|-------|----------|------------|---------|
| 0   | —    | Rev_0  | —     | —       | —     | —        | —          | —       |
| 1   |      |        |       |         |       |          |            |         |
| 2   |      |        |       |         |       |          |            |         |
| 3   |      |        |       |         |       |          |            |         |
| 4   |      |        |       |         |       |          |            |         |
| 5   |      |        |       |         |       |          |            |         |
| 6   |      |        |       |         |       |          |            |         |
| 7   |      |        |       |         |       |          |            |         |
| 8   |      |        |       |         |       |          |            |         |
| 9   |      |        |       |         |       |          |            |         |
| 10  |      |        |       |         |       |          |            |         |

Verificações:
```
Mg(Ano_conv) = Mg_alvo → ____  (deve ser idêntico)
g(10) = g_perp         → ____  (deve ser idêntico)
FCFF(t) crescente nos primeiros anos? → ____  (esperado na maioria dos casos)
```

---

## BLOCO C — DESCONTO DOS FCFF

**Fórmulas:**
```
Fator(1) = 1 / (1 + WACC(1))
Fator(t) = Fator(t−1) / (1 + WACC(t))   para t = 2 a 10

VP_FCFF(t) = FCFF(t) × Fator(t)
```

**Tabela de desconto:**

| Ano | FCFF(t) | WACC(t) | Fator(t) | VP_FCFF(t) |
|-----|---------|---------|---------|-----------|
| 1   |         |         |         |           |
| 2   |         |         |         |           |
| 3   |         |         |         |           |
| 4   |         |         |         |           |
| 5   |         |         |         |           |
| 6   |         |         |         |           |
| 7   |         |         |         |           |
| 8   |         |         |         |           |
| 9   |         |         |         |           |
| 10  |         |         |         |           |

```
VP_total = Σ VP_FCFF(t) para t = 1 a 10
VP_total = ____ M
```

Verificações:
```
Fator(1) > Fator(10)  → ____  (fatores devem ser decrescentes — sempre verdadeiro)
Fator(10) = ____      (registrar para uso no Bloco D)
```

---

## BLOCO D — VALOR TERMINAL

**D1. Receita Terminal (Ano 11)**
```
Rev_term = Rev(10) × (1 + g_perp)
Rev_term = ____ × (1 + ____) = ____ M
```

**D2. EBIT Terminal**
```
EBIT_term = Rev_term × Mg_alvo
EBIT_term = ____ × ____ = ____ M
```

**D3. NOPAT Terminal**
```
NOPAT_term = EBIT_term × (1 − IR_marg)
NOPAT_term = ____ × (1 − ____) = ____ M
```

**D4. Taxa de Reinvestimento na Perpetuidade**
```
ROIC_term = WACC_est   (empresa ganha exatamente seu custo de capital na maturidade)
ROIC_term = ____

ReinvRate_term = g_perp / ROIC_term
ReinvRate_term = ____ / ____ = ____  (____%)
```

**D5. FCFF Terminal**
```
FCFF_term = NOPAT_term × (1 − ReinvRate_term)
FCFF_term = ____ × (1 − ____) = ____ M
```

**D6. Valor Terminal Bruto**
```
Denominador = WACC_est − g_perp = ____ − ____ = ____
Verificação: denominador > 0 → ____  (se falso, PARAR — modelo inválido)

VT = FCFF_term / (WACC_est − g_perp)
VT = ____ / ____ = ____ M
```

**D7. Valor Presente do Valor Terminal**
```
VP_VT = VT × Fator(10)
VP_VT = ____ × ____ = ____ M
```

**Participação do Valor Terminal:**
```
VP_VT / (VP_total + VP_VT) = ____ / (____ + ____) = ____%

Referência: entre 40% e 75% é considerado normal.
Se > 75%: alertar que o valor depende muito das premissas de longo prazo.
Se < 40%: verificar se WACC não está superestimado.
```

---

## BLOCO E — AJUSTE DE FALÊNCIA

```
SE P_fail = 0 (do JSON do Passo 3):
  Ajuste_fail = 0
  → Ir direto para o Bloco F

SE P_fail > 0:
  Valor_distress = V_fail × (VP_total + VP_VT)
  Valor_distress = ____ × (____ + ____) = ____ M

  Valor_op_ajustado = (VP_total + VP_VT) × (1 − P_fail) + P_fail × Valor_distress
  Valor_op_ajustado = (____ + ____) × (1 − ____) + ____ × ____ = ____ M
```

---

## BLOCO F — VALOR DO PATRIMÔNIO E PREÇO POR AÇÃO

**F1. Valor dos Ativos Operacionais**
```
SE P_fail = 0:
  Valor_op = VP_total + VP_VT = ____ + ____ = ____ M

SE P_fail > 0:
  Valor_op = Valor_op_ajustado = ____ M  (calculado no Bloco E)
```

**F2. Valor das Opções de Funcionários (se N_opt > 0)**

Usar modelo Black-Scholes:
```
S  = P (preço atual da ação)
K  = K_opt
T  = T_opt
r  = Rf
σ  = Sigma

d1 = [ln(S/K) + (r + σ²/2) × T] / (σ × √T)
d1 = [ln(____ / ____) + (____ + ____²/2) × ____] / (____ × √____)
d1 = ____

d2 = d1 − σ × √T = ____ − ____ × √____ = ____

Valor_opcao_unit = S × N(d1) − K × e^(−r×T) × N(d2)
Valor_opcao_unit = ____ × N(____) − ____ × e^(−____×____) × N(____)
Valor_opcao_unit = ____

Valor_opcoes = N_opt × Valor_opcao_unit = ____ × ____ = ____ M
```

Se `N_opt = 0`: `Valor_opcoes = 0`

**F3. Equity Value (Bridge)**

```
Equity_Value = Valor_op
             + Caixa
             + AtvNOp
             − D
             − MinInt
             − Valor_opcoes
```

| Item                          | Operação | Valor (M) |
|-------------------------------|----------|-----------|
| Valor dos Ativos Operacionais | +        |           |
| Caixa e equivalentes          | +        |           |
| Outros ativos não operacionais| +        |           |
| Dívida total                  | −        |           |
| Participações minoritárias    | −        |           |
| Valor das opções              | −        |           |
| **Equity Value**              | **=**    |           |

**F4. Valor por Ação**
```
Valor_acao = Equity_Value / Shares
Valor_acao = ____ / ____ = ____
```

**F5. Diagnóstico de Valorização**
```
Premio = (P / Valor_acao) − 1
Premio = (____ / ____) − 1 = ____  (____%)

SE Premio > 0:  ação está SOBREVALORIZADA em ____%
SE Premio < 0:  ação está SUBVALORIZADA em ____%
SE |Premio| < 5%: ação está próxima do VALOR JUSTO
```

---

## OUTPUT FINAL DO PASSO 4

Apresente os resultados nesta ordem e formato exatos:

### Tabela 1 — Parâmetros de Capital

```
Beta desalavancado:              ____
Beta alavancado:                 ____
Custo de capital próprio (Ke):   _____%
Custo da dívida líquido (Kd):    _____%
Peso equity / dívida:            ____% / ____%
WACC inicial:                    _____%
WACC estável:                    _____%
```

### Tabela 2 — Projeção Anual Completa

| Ano | g(t) | Receita | Mg EBIT | EBIT | IR | NOPAT | Reinvest | FCFF | WACC | Fator | VP(FCFF) |
|-----|------|---------|---------|------|----|-------|---------|------|------|-------|---------|
| 1   | | | | | | | | | | | |
| 2   | | | | | | | | | | | |
| 3   | | | | | | | | | | | |
| 4   | | | | | | | | | | | |
| 5   | | | | | | | | | | | |
| 6   | | | | | | | | | | | |
| 7   | | | | | | | | | | | |
| 8   | | | | | | | | | | | |
| 9   | | | | | | | | | | | |
| 10  | | | | | | | | | | | |
| Term| | | | | | | | | | | |

### Tabela 3 — Resumo de Valor

```
VP dos FCFFs (anos 1–10):              ____ M
Valor Terminal (bruto):                ____ M
VP do Valor Terminal:                  ____ M   (____% do total)
─────────────────────────────────────────────
Valor dos Ativos Operacionais:         ____ M
(+) Caixa e equivalentes:             ____ M
(+) Outros ativos não operacionais:   ____ M
(−) Dívida total:                      ____ M
(−) Participações minoritárias:        ____ M
(−) Valor das opções:                  ____ M
─────────────────────────────────────────────
Equity Value:                          ____ M
Ações em circulação:                   ____ M
─────────────────────────────────────────────
VALOR POR AÇÃO (intrínseco):          ____
Preço de mercado:                      ____
Sobre(sub)valorização:                _____%
```

### Checklist de Verificação Final

```
[ ] WACC(10) = WACC_est                    → ____
[ ] IR(10) = IR_marg                       → ____
[ ] Mg(Ano_conv) = Mg_alvo                 → ____
[ ] g(10) = g_perp                         → ____
[ ] Fator(10) < Fator(1)                   → ____
[ ] Denominador VT = WACC_est − g_perp > 0 → ____
[ ] VP_VT entre 40% e 75% do total         → ____% (alerta se fora do range)
[ ] Equity_Value > 0                       → ____
[ ] Valor_acao > 0                         → ____
```

Se qualquer item do checklist falhar, identifique a causa antes de entregar o resultado ao usuário.
