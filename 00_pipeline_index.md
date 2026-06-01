# DCF Valuation Pipeline — Index and Transition Rules

> This file maps all pipeline documents and defines the entry and exit rules for each step. Read this file first before starting any step.

---

## Pipeline Files

| File | Step | Function | Input | Output |
|---|---|---|---|---|
| `step1_release_extraction.md` | 1 | Extract data from the earnings release PDF | Earnings release PDF | Partial JSON + gap table |
| `step2_market_parameters.md` | 2 | Collect external parameters (Rf, ERP, Beta, IR_marg) | Step 1 JSON + market sources | Supplementary market JSON |
| `step3_analyst_assumptions.md` | 3 | Define future assumptions with the analyst | Step 1 and 2 JSONs | Final consolidated JSON (all inputs) |
| `step4_dcf_calculation.md` | 4 | Run all DCF calculations | Step 3 JSON | Tables + value per share + diagnostics |
| `step5_sensitivity_scenarios.md` | 5 *(optional)* | Sensitivity analysis and scenarios | Step 4 results | Matrices + scenarios + conclusion |

---

## Pipeline Flow

```
[Earnings Release PDF]
            │
            ▼
┌───────────────────────┐
│  STEP 1               │  Reads the PDF. Extracts historical data.
│  Release Extraction   │  Identifies what is missing.
│                       │
│  Output: partial JSON │
│  + gap table          │
└──────────┬────────────┘
           │  Gate: all historical fields filled or marked as PENDING
           ▼
┌───────────────────────┐
│  STEP 2               │  Looks up Rf, ERP, Beta_u, IR_marg, Kd_pre, WACC_est.
│  Market               │  One item at a time. Records source for each.
│  Parameters           │
│                       │
│  Output: supplementary│
│  JSON                 │
└──────────┬────────────┘
           │  Gate: zero null fields in parametros_mercado block
           ▼
┌───────────────────────┐
│  STEP 3               │  For each assumption: presents historical reference
│  Analyst              │  and sector benchmark → analyst decides → records in JSON.
│  Assumptions          │  Validates consistency between assumptions at the end.
│                       │
│  Output: final        │
│  consolidated JSON    │
│  (zero nulls)         │
└──────────┬────────────┘
           │  Gate: pronto_para_passo4 = true
           ▼
┌───────────────────────┐
│  STEP 4               │  Executes Blocks A → B → C → D → E → F.
│  DCF Calculation      │  Fills intermediate tables.
│                       │  Runs verification checklist.
│  Output: value per    │
│  share + diagnostics  │
└──────────┬────────────┘
           │  (optional)
           ▼
┌───────────────────────┐
│  STEP 5               │  Sensitivity matrices.
│  Sensitivity          │  Breakevens per assumption.
│  and Scenarios        │  Bear / Base / Bull scenarios.
│                       │  Narrative conclusion.
└───────────────────────┘
```

---

## Transition Rule (applies to all steps)

```
Only advance to the next step when:

1. The output JSON of the current step has ZERO null fields
   in the blocks that step is responsible for filling.

2. The status field of the current step is marked as true:
   Step 1: (verify manually — no automatic flag)
   Step 2: status_passo2.pronto_para_passo3 = true
   Step 3: validacoes.pronto_para_passo4 = true
   Step 4: verification checklist with no failures

3. If there are PENDING fields (not found in the release),
   the user must provide them explicitly before advancing.
   The LLM must not invent or silently approximate values.
```

---

## What Each Step Does NOT Do

| Step | Does not |
|---|---|
| Step 1 | Does not define assumptions. Does not look up market data. Does not calculate WACC. |
| Step 2 | Does not define analyst assumptions. Does not project revenues. Does not calculate FCFF. |
| Step 3 | Does not re-extract release data. Does not run model calculations. |
| Step 4 | Does not redefine assumptions. Does not look up external data. Does not run sensitivity analysis. |
| Step 5 | Does not alter the base value. Does not replace Step 4. |

---

## Accumulated JSON by Step

The JSON grows with each step. When starting a step, always begin with the complete JSON from the previous step.

```
Start of Step 2: Step 1 JSON (historical data + market data)
Start of Step 3: Step 1 JSON + Step 2 JSON (+ market parameters)
Start of Step 4: Consolidated Step 3 JSON (all inputs)
Start of Step 5: Numerical result of Step 4 (valor_acao, VP_total, VP_VT, Fator_10)
```

---

## Estimated Time per Step

| Step | Complexity | Common blockers |
|---|---|---|
| Step 1 | Low–Medium | Poorly formatted release, quarterly data without LTM |
| Step 2 | Low | Access to Damodaran tables, defining country IR_marg |
| Step 3 | High | Analyst decisions — requires dialogue and justifications |
| Step 4 | Medium | None if Step 3 JSON is correct |
| Step 5 | Medium | Volume of calculations in the matrices |
