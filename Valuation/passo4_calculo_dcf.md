# Passo 4 — Execução do Modelo DCF

> **Este passo é executado pelo script Python:**
> ```
> python Valuation/passo4_dcf.py Acoes/<TICKER>/passo3.json --output Acoes/<TICKER>/passo4.json
> ```
> O script executa todos os cálculos e gera o relatório. Este arquivo é referência de fórmulas e formato de output para interpretação e validação dos resultados.

---

## Bloco A — Custo de Capital (WACC)

```
MktCap   = P × Shares
Beta_L   = Beta_u × [1 + (1 − IR_marg) × (D / MktCap)]
Ke       = Rf + Beta_L × ERP
Kd_liq   = Kd_pre × (1 − IR_marg)
W_e      = MktCap / (MktCap + D)
W_d      = D / (MktCap + D)
WACC_0   = W_e × Ke + W_d × Kd_liq
```

**WACC por ano:**
| Período | Fórmula |
|---|---|
| Anos 1–5 | WACC(t) = WACC_0 |
| Anos 6–10 | WACC(t) = WACC_0 + [(t−5)/5] × (WACC_est − WACC_0) |
| Terminal | WACC(t) = WACC_est |

**IR por ano:**
| Período | Fórmula |
|---|---|
| Anos 1–5 | IR(t) = IR_ef |
| Anos 6–10 | IR(t) = IR_ef + [(t−5)/5] × (IR_marg − IR_ef) |
| Terminal | IR(t) = IR_marg |

---

## Bloco B — Projeções Anuais (t = 1 a 10)

```
g(1)     = g1
g(2–5)   = g2_5
g(6–10)  = g2_5 − [(t−5)/5] × (g2_5 − g_perp)

Rev(t)   = Rev(t−1) × (1 + g(t))        [Rev(0) = Rev_0]

Mg(1)          = Mg_1
Mg(2..Ano_conv) = Mg_1 + [(t−1)/(Ano_conv−1)] × (Mg_alvo − Mg_1)
Mg(t > Ano_conv) = Mg_alvo

EBIT(t)     = Rev(t) × Mg(t)
NOPAT(t)    = EBIT(t) × (1 − IR(t))
Reinvest(t) = [Rev(t) − Rev(t−1)] / StC
FCFF(t)     = NOPAT(t) − Reinvest(t)
```

---

## Bloco C — Desconto dos FCFFs

```
Fator(1)   = 1 / (1 + WACC(1))
Fator(t)   = Fator(t−1) / (1 + WACC(t))   para t = 2..10
VP_FCFF(t) = FCFF(t) × Fator(t)
VP_total   = Σ VP_FCFF(t),  t = 1..10
```

---

## Bloco D — Valor Terminal

```
Rev_term    = Rev(10) × (1 + g_perp)
EBIT_term   = Rev_term × Mg_alvo
NOPAT_term  = EBIT_term × (1 − IR_marg)
ReinvRate   = g_perp / WACC_est
FCFF_term   = NOPAT_term × (1 − ReinvRate)
VT          = FCFF_term / (WACC_est − g_perp)
VP_VT       = VT × Fator(10)
```

**Participação do VT:**
```
pct_VT = VP_VT / (VP_total + VP_VT) × 100
→ Normal: entre 40% e 75%
→ > 75%: valor muito dependente das premissas de longo prazo — alertar
→ < 40%: verificar se WACC não está superestimado
```

---

## Bloco E — Ajuste de Falência (apenas se P_fail > 0)

```
Valor_distress    = V_fail × (VP_total + VP_VT)
Valor_op_ajustado = (VP_total + VP_VT) × (1 − P_fail) + P_fail × Valor_distress
```

---

## Bloco F — Equity Value e Preço por Ação

```
Valor_op     = VP_total + VP_VT          [se P_fail = 0]
             = Valor_op_ajustado         [se P_fail > 0]

Equity_Value = Valor_op + Caixa + AtvNOp − D − MinInt − Valor_opcoes
Valor_acao   = Equity_Value / Shares
Premio       = (P / Valor_acao) − 1
```

**Black-Scholes para opções (se N_opt > 0):**
```
d1 = [ln(P/K_opt) + (Rf + Sigma²/2) × T_opt] / (Sigma × √T_opt)
d2 = d1 − Sigma × √T_opt
Valor_opcao_unit = P × N(d1) − K_opt × e^(−Rf × T_opt) × N(d2)
Valor_opcoes     = N_opt × Valor_opcao_unit
```

---

## Checklist de Verificação (executado automaticamente pelo script)

| # | Check | Condição |
|---|---|---|
| 1 | WACC(10) = WACC_est | identidade |
| 2 | IR(10) = IR_marg | identidade |
| 3 | Mg(Ano_conv) = Mg_alvo | identidade |
| 4 | g(10) = g_perp | identidade |
| 5 | Fatores decrescentes | Fator(1) > Fator(10) |
| 6 | Denominador VT > 0 | WACC_est − g_perp > 0 |
| 7 | VP_VT entre 40–75% | alerta se fora |
| 8 | Equity_Value > 0 | — |
| 9 | Valor_acao > 0 | — |
| 10 | Kd_pre ≥ Rf (se D>0) | alerta de dados |
| 11 | MktCap/Rev_0 ≤ 100× | alerta de unidade |
| 12 | D/MktCap ≥ 0,1% (se D>0) | alerta de unidade |
| 13 | 0,05× ≤ P/Valor_acao ≤ 20× | alerta de unidade |

---

## Cross-check: EV/EBITDA Implícito

Após executar o script, calcular para validar razoabilidade do resultado:

```
EV_impl       = Valor_op + D − Caixa
EV_EBITDA_impl = EV_impl / EBITDA_0
```

Comparar com múltiplos do setor (Damodaran ou peers listados).  
- Divergência < 30%: resultado é razoável.  
- Divergência > 50%: revisar premissas — crescimento, margem ou WACC podem estar fora do intervalo plausível.
