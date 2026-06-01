# Step 1 — Release Extraction

**Objective:** read the earnings release PDF and produce `Acoes/<TICKER>/step1.json` with all historical data required for the DCF valuation.  
**Fundamental rule:** all financial values in the JSON must be in **MILLIONS (R$ M)**.

---

## PHASE 1 — Identify the document structure

Before extracting any number, answer:
1. Company name and ticker?
2. Release period (annual / quarterly / LTM)?
3. Reported unit (thousands / millions / billions)?
4. Does the release contain: Income Statement? Balance Sheet? Cash Flow Statement? Debt notes?

Record the answers. They determine how to treat the numbers.

---

## PHASE 2 — Unit Rule

**Convert everything to MILLIONS before recording in the JSON:**

| Unit in release | Example found | Operation | Value in JSON |
|---|---|---|---|
| Thousands (R$ k) | 1,185,600 | ÷ 1,000 | 1,185.6 |
| Millions (R$ M) | 1,185.6 | none | 1,185.6 |
| Billions (R$ B) | 1.186 | × 1,000 | 1,186.0 |

**Mandatory scale check:** calculate `MktCap / Rev_0` at the end.
- Between 0.3× and 15×: normal for most sectors.
- Above 20×: STOP — almost certainly a unit error. Review before continuing.

---

## PHASE 3 — Field-by-field extraction

For each field: locate in the document → convert unit → record value and source.  
If not found: record `"valor": null, "confianca": "PENDING"` and add to the gap list.

### Income Statement Block (DRE)

**Rev_0 — Net Revenue**
- Look for: "Receita Líquida", "Net Revenue", "Receita Operacional Líquida"
- Prefer LTM (last 12 months). If annual release: use directly.
- If quarterly without LTM column: `LTM = Q4_prior + YTD_current − YTD_prior_same_period`
- If LTM cannot be calculated: record quarterly value with note "needs annualisation"

**EBIT_0 — Operating Income**
- Look for: "EBIT", "Resultado Operacional", "Lucro Operacional", "Operating Income"
- **NOTE:** EBIT ≠ EBITDA. EBIT already deducts depreciation. If the release shows only EBITDA: `EBIT = EBITDA − Dep`
- Warning signal: if `EBIT_0 / Rev_0 > 40%` it is probably EBITDA by mistake — verify

**EBITDA**
- Look for: "EBITDA"
- Used to calculate Dep = EBITDA − EBIT. If not available, record null.

**Dep — Depreciation and Amortization**
- Look for: "Depreciação", "Amortização", "D&A" in the cash flow statement
- If not found directly: `Dep = EBITDA − EBIT_0` (if both available)

**Juros — Interest Expense**
- Look for: "Juros sobre dívida", "Despesas Financeiras — Juros", "Interest Expense"
- Include ONLY interest on financial debt.
- Exclude: FX variation, fines, tax interest, hedge results.
- If the release mixes them: note the gross interest separately from net financial result.

**LAIR — Earnings Before Tax**
- Look for: "LAIR", "EBT", "Lucro Antes do IR", "Pre-tax Income"

**IR_pago — Income Tax Paid**
- Look for: "IRPJ e CSLL", "Imposto de Renda", "Income Tax Expense"
- Use the accounting tax expense (not the cash tax from the cash flow, unless it is the only figure available)

### Balance Sheet Block

**D — Gross Financial Debt**
- Look for: "Dívida Bruta", "Empréstimos e Financiamentos", "Debêntures"
- Sum: current portion (short-term) + non-current portion (long-term)
- Exclude: IFRS 16 lease liabilities, accounts payable, deferred taxes
- Exception: if the company explicitly discloses "Dívida ex-IFRS 16", use that figure

**Caixa — Cash**
- Look for: "Caixa e Equivalentes", "Aplicações Financeiras de Curto Prazo"
- Include: cash + short-term investments with maturity < 90 days

**D_liq — Net Debt**
- Look for: "Dívida Líquida", "Net Debt" — use as a verification field
- Calculate: `D_liq_calc = D − Caixa`. Must match the release figure (2% tolerance).
- If difference > 2%: investigate before recording.

**PL — Shareholders' Equity**
- Look for: total consolidated "Patrimônio Líquido"

**MinInt — Minority Interest**
- Look for: "Não Controladores", "Minority Interest"
- If not found: record 0 with note "not identified in release"

**AtvNOp — Non-Operating Assets**
- Equity stakes in companies unrelated to operations, non-operating real estate
- If not identified: record 0

### Market and Shares Block

**Shares — Shares Outstanding**
- Look for: "Ações em Circulação", "Shares Outstanding", total common + preferred
- Exclude treasury shares
- Convert to millions: if release reports in units, divide by 1,000,000
- Example: "399,087,450 shares" → Shares = 399.087

**P — Share Price**
- Look for: price disclosed in the release or market cap ÷ Shares
- If not found in the release: record `"valor": null, "confianca": "PENDING"` and ask the user

**MktCap**
- Look for: "Market Cap", "Valor de Mercado" — verification field
- Calculate: `MktCap_calc = P × Shares`. Must match release (5% tolerance).

### Operating Block

**Rev_ant — Prior Period Revenue**
- Comparative column for the same period of the prior year

**CAPEX**
- Look for: "Investimentos", "Aquisição de imobilizado", "Additions to PP&E"

---

## PHASE 4 — Calculate derived fields

After extracting all fields, calculate:

```
IR_ef      = IR_pago / LAIR
             → expected between 0.15 and 0.45 for Brazilian companies
             → if < 0 or > 0.60: review IR_pago and LAIR

Mg_atual   = EBIT_0 / Rev_0
             → if > 0.40: verify that EBIT_0 is truly EBIT (not EBITDA)

g_recente  = (Rev_0 / Rev_ant) − 1

CI         = PL + D − Caixa

ROIC_atual = (EBIT_0 × (1 − IR_ef)) / CI

StC_hist   = Rev_0 / CI

D_liq_calc = D − Caixa  → compare with D_liq from release

MktCap_calc = P × Shares  → compare with MktCap from release
```

---

## PHASE 5 — Consistency checks

Run before producing the final JSON:

```
[ ] 1. MktCap_calc = P × Shares = ___ × ___ = ___ M
        MktCap from release = ___ M   |   Difference: ___%
        → OK if < 5%. If > 5%: review Shares (total vs. outstanding vs. ex-treasury)

[ ] 2. D_liq_calc = D − Caixa = ___ − ___ = ___ M
        D_liq from release = ___ M   |   Difference: ___%
        → OK if < 2%. If > 2%: check D and Caixa components

[ ] 3. EBIT_0 < EBITDA  (must always be true)
        EBIT_0 = ___ M, EBITDA = ___ M   →   OK | FAIL (review extraction)

[ ] 4. IR_ef = ___ (expected 0.15–0.45)   →   OK | ALERT

[ ] 5. MktCap_calc / Rev_0 = ___ / ___ = ___×
        → OK if ≤ 15×. If > 20×: STOP — unit error. Do not continue.

[ ] 6. D > 0 and D / MktCap_calc = ___%
        → If D > 0 but ratio < 1%: STOP — unit error in D.
```

If any check fails: correct before saving the JSON.

---

## PHASE 6 — Output JSON

```json
{
  "empresa": {
    "nome": "",
    "ticker": "",
    "pais": "",
    "setor": "",
    "moeda": "BRL",
    "unidade": "milhões"
  },
  "periodo_referencia": {
    "tipo": "anual | LTM | trimestral",
    "data": "YYYY-MM-DD"
  },
  "dre": {
    "Rev_0":    { "valor": null, "confianca": "DIRETO | CALCULADO | PENDENTE", "fonte": "" },
    "EBIT_0":   { "valor": null, "confianca": "", "fonte": "" },
    "EBITDA":   { "valor": null, "confianca": "", "fonte": "" },
    "Dep":      { "valor": null, "confianca": "", "fonte": "" },
    "Juros":    { "valor": null, "confianca": "", "fonte": "" },
    "LAIR":     { "valor": null, "confianca": "", "fonte": "" },
    "IR_pago":  { "valor": null, "confianca": "", "fonte": "" },
    "IR_ef":    { "valor": null, "confianca": "CALCULADO", "fonte": "IR_pago / LAIR" },
    "Mg_atual": { "valor": null, "confianca": "CALCULADO", "fonte": "EBIT_0 / Rev_0" }
  },
  "balanco": {
    "PL":     { "valor": null, "confianca": "", "fonte": "" },
    "D":      { "valor": null, "confianca": "", "fonte": "" },
    "Caixa":  { "valor": null, "confianca": "", "fonte": "" },
    "D_liq":  { "valor": null, "confianca": "", "fonte": "" },
    "MinInt": { "valor": null, "confianca": "", "fonte": "" },
    "AtvNOp": { "valor": null, "confianca": "", "fonte": "" },
    "CI":     { "valor": null, "confianca": "CALCULADO", "fonte": "PL + D − Caixa" }
  },
  "mercado": {
    "Shares": { "valor": null, "confianca": "", "fonte": "" },
    "P":      { "valor": null, "confianca": "", "fonte": "" },
    "MktCap": { "valor": null, "confianca": "", "fonte": "" }
  },
  "operacional": {
    "Rev_ant":    { "valor": null, "confianca": "", "fonte": "" },
    "g_recente":  { "valor": null, "confianca": "CALCULADO", "fonte": "Rev_0/Rev_ant − 1" },
    "ROIC_atual": { "valor": null, "confianca": "CALCULADO", "fonte": "NOPAT/CI" },
    "StC_hist":   { "valor": null, "confianca": "CALCULADO", "fonte": "Rev_0/CI" },
    "CAPEX":      { "valor": null, "confianca": "", "fonte": "" }
  }
}
```

**At the end:** list all fields with PENDING status and ask the user before advancing to Step 2.
