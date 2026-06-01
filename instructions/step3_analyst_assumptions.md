# Step 3 — Analyst Assumptions

**Prerequisite:** `step1.json` and `step2.json` complete, both with `pronto_para_passoN: true`.  
**Objective:** consolidate all inputs and define future assumptions. Produce `step3.json` with zero nulls.  
**Flow:** for each assumption, present historical anchor + proposal → wait for analyst confirmation → record.

---

## BLOCK 0 — Consolidation and Unit Verification

> **Run this block completely before discussing any assumption.**  
> If any check fails: correct the data before advancing.

### 0.1 — Copy data from previous steps

Transcribe the **exact** values from the JSONs. Do not round, convert, or change scale.  
All financial values in MILLIONS (same unit as `step1.empresa.unidade`).

| Field | Origin (exact JSON field) | Value |
|---|---|---|
| Rev_0 | step1.dre.Rev_0.valor | |
| EBIT_0 | step1.dre.EBIT_0.valor | |
| Dep | step1.dre.Dep.valor | |
| Juros | step1.dre.Juros.valor | |
| PL | step1.balanco.PL.valor | |
| D | step1.balanco.D.valor | |
| Caixa | step1.balanco.Caixa.valor | |
| AtvNOp | step1.balanco.AtvNOp.valor | |
| MinInt | step1.balanco.MinInt.valor | |
| Shares | step1.mercado.Shares.valor | |
| P | step1.mercado.P.valor | |
| MktCap | step1.mercado.MktCap.valor | |
| IR_ef | step1.dre.IR_ef.valor | |
| Rf | step2.parametros_mercado.Rf.valor | |
| ERP | step2.parametros_mercado.ERP.valor | |
| Beta_u | step2.parametros_mercado.Beta_u.valor | |
| Kd_pre | step2.parametros_mercado.Kd_pre.valor | |
| IR_marg | step2.parametros_mercado.IR_marg.valor | |
| WACC_est | step2.parametros_mercado.WACC_est.valor | |

### 0.2 — Cross-checks (all must pass before advancing)

Calculate each item and record the result:

```
A. MktCap_calc = P × Shares = ___ × ___ = ___ M
   MktCap from step1 = ___ M
   Difference: abs(MktCap_calc − MktCap_p1) / MktCap_p1 = ___%
   → OK if < 5%. If >= 5%: check Shares (ex-treasury?) and P (correct date?)
   Result: OK | FAILED

B. D_liq_calc = D − Caixa = ___ − ___ = ___ M
   D_liq from step1 = ___ M
   Difference: ___%
   → OK if < 2%. If >= 2%: check D and Caixa components
   Result: OK | FAILED

C. Kd_pre (___%) vs Rf (___%)
   Kd_pre > Rf?
   → If NO: BLOCKER — do not advance. See Step 2, item 2.4.
   Result: OK | BLOCKER

D. Scale ratio: MktCap_calc / Rev_0 = ___ / ___ = ___×
   → OK if between 0.3× and 15×
   → If > 20×: STOP — unit error in Rev_0 or D or Caixa. Identify and correct before continuing.
   Result: OK (___×) | ALERT

E. If D > 0: D / MktCap_calc = ___ / ___ = ___%
   → If < 1%: STOP — probable unit error in D.
   Result: OK (__%) | ALERT
```

---

## ASSUMPTION 3.1 — g1 (Year 1 Revenue Growth)

**Anchor:** `g_recente = ____%` (from step1.operacional.g_recente)

Check in the release:
- Did the company publish growth guidance for the next fiscal year? → use as primary reference
- Was recent growth driven by an acquisition or base effect? → adjust downward if yes

**Restriction:** `g1 ≤ min(g_recente × 2, 50%)`. Growth more than double the recent rate requires explicit analyst justification.

```
g1 = ____%   Justification: ________________
```

---

## ASSUMPTION 3.2 — g2_5 (Years 2 to 5 Growth)

**Anchor:** historical CAGR available in the release (last 3–5 years)  
**Sector reference:** Damodaran Industry Averages — "Revenue Growth (last 5 years)" column for the sector

Calibration rule:
- If the company grows consistently above the sector: g2_5 can be up to sector + 3pp (with competitive advantage justification)
- Conservative default: g2_5 = g_recente with gentle decay toward g_perp

**Restriction:** `g2_5 ≥ g_perp`

```
g2_5 = ____%   Justification: ________________
```

---

## ASSUMPTION 3.3 — Mg_1 (EBIT Margin in Year 1)

**Anchor:** `Mg_atual = EBIT_0 / Rev_0 = ___ / ___ = ____%` (from step1.dre.Mg_atual)

Adjustments to Mg_atual:
- If there are known cost pressures for the next period (wage inflation, input costs): reduce slightly
- If there is an efficiency programme or expected operating leverage: may increase slightly
- Default: `Mg_1 = Mg_atual` (no adjustment if there is no clear reason)

```
Mg_1 = ____%   Justification: ________________
```

---

## ASSUMPTION 3.4 — Mg_alvo (Mature EBIT Margin)

**Sector anchor:** Damodaran Industry Averages, "Pre-tax Operating Margin" column for the sector  
**Benchmark reference:** margin of the best comparable company in the sector (if known)

Calibration rule:
- If the company has durable competitive advantages (pricing power, switching costs, scale): Mg_alvo can be above the sector median
- If the sector faces structural margin pressure: use the median or below
- Mg_alvo should fall between Mg_1 (unlikely that the target margin is below current) and the best peer

**Mandatory value-creation check:**
```
ROIC_term = Mg_alvo × (1 − IR_marg) × StC
          = ___ × (1 − ___) × ___ = ___
WACC_est  = ___
ROIC_term > WACC_est?  →  YES (value creating) | NO (value destroying — review Mg_alvo or StC)
```
*(StC not yet defined — calculate after defining 3.6. Come back and validate.)*

```
Mg_alvo = ____%   Justification: ________________
```

---

## ASSUMPTION 3.5 — Ano_conv (Margin Convergence Year)

Defines by which year the EBIT margin converges linearly from Mg_1 to Mg_alvo.

| Value | When to use |
|---|---|
| 1 | Margin already at target (Mg_1 = Mg_alvo) |
| 3 | Company close to maturity, rapid improvement |
| 5 | Default — most companies |
| 7–10 | Company in intense expansion, efficiency comes late |

**Restriction:** `Ano_conv ∈ [1, 10]`

```
Ano_conv = ____   Justification: ________________
```

---

## ASSUMPTION 3.6 — StC (Sales-to-Capital Ratio)

**Historical anchor:** `StC_hist = Rev_0 / CI = ___ / ___ = ___` (from step1.operacional.StC_hist)  
**Sector reference:** Damodaran Industry Averages, "Sales/Capital" column

Calibration rule:
- If `StC_hist` is close to the sector median: use StC_hist as the default
- If `StC_hist` is very different from the sector: investigate (recent acquisition? divestiture?)
- A high StC means cheap growth (less capital per unit of revenue) — verify if sustainable

**Revalidate value creation after defining StC:**
```
ROIC_term = Mg_alvo × (1 − IR_marg) × StC = ___ × (1 − ___) × ___ = ___
WACC_est  = ___
Result: ROIC_term > WACC_est →  OK | Review Mg_alvo or StC
```

```
StC = ____   Justification: ________________
```

---

## ASSUMPTION 3.7 — g_perp (Perpetuity Growth Rate)

**Absolute restriction:** `g_perp < Rf`. If `g_perp ≥ Rf`, the model explodes (infinite value). Do not accept.

References:
- Brazil: long-term inflation (~4%) + real GDP growth (~1–2%) → g_perp between 4% and 6%
- USA: ~2% to 3%
- Structurally declining sector: g_perp can be 0% or negative

**Validation:**
```
g_perp = ____%
Rf     = ____%
g_perp < Rf?  →  OK | VIOLATION (do not accept — reduce g_perp)

WACC_est (___%) > g_perp (___%)?  →  OK | VIOLATION
```

```
g_perp = ____%   Justification: ________________
```

---

## ASSUMPTION 3.8 — P_fail and V_fail (Distress Adjustment)

For most companies: `P_fail = 0` and `V_fail = 0`. Advance if that is the case.

Use P_fail > 0 if at least one of the following applies:
- `D / EBITDA_0 > 5×` → calculate: ___ / ___ = ___× → `P_fail = 0` | consider
- Negative FCO for 2+ consecutive years
- Implied rating < BB (calculate coverage: `EBIT_0 / Juros = ___ / ___ = ___×`)

If applicable:
1. Consult `Valuation/data/ratings.md` with the EBIT/Juros coverage ratio
2. Identify the synthetic rating
3. Locate the 10-year default probability (Damodaran table)
4. `V_fail` = fraction of value recovered in liquidation (typically 0.20 to 0.50)

```
D / EBITDA_0 = ___ / ___ = ___×   (EBITDA_0 = step1.dre.EBITDA.valor)
EBIT_0 / Juros = ___ / ___ = ___×  (interest coverage)
P_fail = ____   V_fail = ____   Justification: ________________
```

---

## ASSUMPTION 3.9 — Employee Stock Options

Check in the release: is there mention of "Plano de Opções", "Stock Options", "SARs" outstanding?
- **None:** `N_opt = 0, K_opt = 0, T_opt = 0, Sigma = 0` → advance
- **Options exist:** collect from the release or ask the user:
  - `N_opt` = total options outstanding (in millions of shares)
  - `K_opt` = average exercise price (in R$)
  - `T_opt` = average time to expiry (in years)
  - `Sigma` = annualised stock price volatility (if not available: look up Damodaran "Std deviation in stock prices" for the sector)

---

## Output Checklist

```
[ ] Block 0 complete — checks A, B, C, D, E passed
[ ] g_perp < Rf
[ ] WACC_est > g_perp
[ ] ROIC_term = Mg_alvo × (1 − IR_marg) × StC > WACC_est  (or alert recorded)
[ ] g1 ≤ g_recente × 2  (or justification recorded)
[ ] g2_5 ≥ g_perp
[ ] Ano_conv ∈ [1, 10]
[ ] P_fail ∈ [0, 1]
[ ] campos_nulos_restantes = []
[ ] pronto_para_passo4: true
```

---

## Output JSON

```json
{
  "empresa": {
    "nome": "", "ticker": "", "pais": "", "setor": "", "moeda": "BRL", "unidade": "milhões"
  },
  "dados_historicos": {
    "Rev_0": null, "EBIT_0": null, "Dep": null, "Juros": null,
    "PL": null, "D": null, "Caixa": null, "AtvNOp": null, "MinInt": null
  },
  "dados_mercado": {
    "P": null, "Shares": null, "MktCap": null, "IR_ef": null
  },
  "parametros_custo_capital": {
    "Rf": null, "ERP": null, "Beta_u": null,
    "Kd_pre": null, "IR_marg": null, "WACC_est": null
  },
  "premissas_analiticas": {
    "g1": null, "g2_5": null, "Mg_1": null, "Mg_alvo": null,
    "Ano_conv": null, "StC": null, "g_perp": null, "P_fail": null, "V_fail": null
  },
  "opcoes_funcionarios": {
    "N_opt": 0, "K_opt": 0, "T_opt": 0, "Sigma": 0
  },
  "narrativa_premissas": {
    "crescimento": "",
    "margem": "",
    "risco": "",
    "perpetuidade": ""
  },
  "validacoes": {
    "bloco0_MktCap_PxShares": null,
    "bloco0_D_liq": null,
    "bloco0_Kd_pre_Rf": null,
    "bloco0_escala": null,
    "bloco0_D_MktCap": null,
    "g_perp_menor_Rf": null,
    "WACC_est_maior_g_perp": null,
    "ROIC_alvo_maior_WACC": null,
    "campos_nulos_restantes": [],
    "pronto_para_passo4": false
  }
}
```
