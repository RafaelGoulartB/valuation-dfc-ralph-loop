# Step 4 — DCF Model Execution

> **This step is executed by the Python script:**
> ```
> python Valuation/script/step4_dcf.py Acoes/<TICKER>/step3.json --output Acoes/<TICKER>/step4.json
> ```
> The script runs all calculations and generates the report. This file is a formula reference and output format guide for interpreting and validating the results.

---

## Block A — Cost of Capital (WACC)

```
MktCap   = P × Shares
Beta_L   = Beta_u × [1 + (1 − IR_marg) × (D / MktCap)]
Ke       = Rf + Beta_L × ERP
Kd_liq   = Kd_pre × (1 − IR_marg)
W_e      = MktCap / (MktCap + D)
W_d      = D / (MktCap + D)
WACC_0   = W_e × Ke + W_d × Kd_liq
```

**WACC by year:**
| Period | Formula |
|---|---|
| Years 1–5 | WACC(t) = WACC_0 |
| Years 6–10 | WACC(t) = WACC_0 + [(t−5)/5] × (WACC_est − WACC_0) |
| Terminal | WACC(t) = WACC_est |

**Tax rate by year:**
| Period | Formula |
|---|---|
| Years 1–5 | IR(t) = IR_ef |
| Years 6–10 | IR(t) = IR_ef + [(t−5)/5] × (IR_marg − IR_ef) |
| Terminal | IR(t) = IR_marg |

---

## Block B — Annual Projections (t = 1 to 10)

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

## Block C — Discounting FCFFs

```
Fator(1)   = 1 / (1 + WACC(1))
Fator(t)   = Fator(t−1) / (1 + WACC(t))   for t = 2..10
VP_FCFF(t) = FCFF(t) × Fator(t)
VP_total   = Σ VP_FCFF(t),  t = 1..10
```

---

## Block D — Terminal Value

```
Rev_term    = Rev(10) × (1 + g_perp)
EBIT_term   = Rev_term × Mg_alvo
NOPAT_term  = EBIT_term × (1 − IR_marg)
ReinvRate   = g_perp / WACC_est
FCFF_term   = NOPAT_term × (1 − ReinvRate)
VT          = FCFF_term / (WACC_est − g_perp)
VP_VT       = VT × Fator(10)
```

**Terminal value share:**
```
pct_VT = VP_VT / (VP_total + VP_VT) × 100
→ Normal: between 40% and 75%
→ > 75%: value highly dependent on long-term assumptions — flag
→ < 40%: check whether WACC is overestimated
```

---

## Block E — Distress Adjustment (only if P_fail > 0)

```
Valor_distress    = V_fail × (VP_total + VP_VT)
Valor_op_ajustado = (VP_total + VP_VT) × (1 − P_fail) + P_fail × Valor_distress
```

---

## Block F — Equity Value and Price per Share

```
Valor_op     = VP_total + VP_VT          [if P_fail = 0]
             = Valor_op_ajustado         [if P_fail > 0]

Equity_Value = Valor_op + Caixa + AtvNOp − D − MinInt − Valor_opcoes
Valor_acao   = Equity_Value / Shares
Premio       = (P / Valor_acao) − 1
```

**Black-Scholes for options (if N_opt > 0):**
```
d1 = [ln(P/K_opt) + (Rf + Sigma²/2) × T_opt] / (Sigma × √T_opt)
d2 = d1 − Sigma × √T_opt
Valor_opcao_unit = P × N(d1) − K_opt × e^(−Rf × T_opt) × N(d2)
Valor_opcoes     = N_opt × Valor_opcao_unit
```

---

## Verification Checklist (run automatically by the script)

| # | Check | Condition |
|---|---|---|
| 1 | WACC(10) = WACC_est | identity |
| 2 | IR(10) = IR_marg | identity |
| 3 | Mg(Ano_conv) = Mg_alvo | identity |
| 4 | g(10) = g_perp | identity |
| 5 | Discount factors decreasing | Fator(1) > Fator(10) |
| 6 | Terminal value denominator > 0 | WACC_est − g_perp > 0 |
| 7 | VP_VT between 40–75% | alert if outside range |
| 8 | Equity_Value > 0 | — |
| 9 | Valor_acao > 0 | — |
| 10 | Kd_pre ≥ Rf (if D > 0) | data alert |
| 11 | MktCap/Rev_0 ≤ 100× | unit alert |
| 12 | D/MktCap ≥ 0.1% (if D > 0) | unit alert |
| 13 | 0.05× ≤ P/Valor_acao ≤ 20× | unit alert |

---

## Cross-check: Implied EV/EBITDA

After running the script, calculate to validate the reasonableness of the result:

```
EV_impl        = Valor_op + D − Caixa
EV_EBITDA_impl = EV_impl / EBITDA_0
```

Compare with sector multiples (Damodaran or listed peers).  
- Divergence < 30%: result is reasonable.  
- Divergence > 50%: review assumptions — growth, margin, or WACC may be outside the plausible range.
