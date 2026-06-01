# Step 2 — Market Parameters

**Prerequisite:** `step1.json` complete, with no PENDING fields in the dre/balanco/mercado blocks.  
**Objective:** collect the 6 external parameters to calculate the WACC.  
**Rule:** no estimated value without a source. If you cannot obtain one: mark it `PENDING` and ask the user.

---

## 2.1 — Rf (Risk-Free Rate)

**Brazil:** look up the NTN-B 2035 yield (long-term IPCA+) on the ANBIMA website.  
Use the nominal rate (IPCA + real premium), expressed as a decimal (e.g. 0.1453 for 14.53%).  
Record the date of lookup — the yield changes daily.

**USA:** 10Y Treasury yield (source: FRED, series DGS10), as a decimal.

**Note:** Rf must be in the same currency as the model's cash flows (BRL for Brazilian companies).

```
Rf = ____   Source: ________________   Date: ________
```

---

## 2.2 — ERP (Equity Risk Premium)

Source: file `Valuation/data/country-default-spreads-and-risk-premiums.md`

Procedure:
1. Locate the country from `empresa.pais` in step1.json
2. Copy the value from the **"Equity Risk Premium"** column (total ERP = US base + Country Risk Premium)
3. If the country is not listed individually: use the regional ERP (e.g. "Latin America")

```
ERP = ____   Country consulted: ________________   Table year: ____
```

---

## 2.3 — Beta_u (Unlevered Sector Beta)

Source: file `Valuation/data/beta-by-sector.md`

Procedure:
1. Identify the sector from `empresa.setor` in step1.json
2. Locate the closest sector in the table
3. Copy the value from the **"Unlevered Beta corrected for cash"** column
4. If there is no exact match: record the sector used and the justification

```
Beta_u = ____   Sector consulted: ________________   Company sector: ________________
```

---

## 2.4 — Kd_pre (Pre-Tax Cost of Debt)

**Primary calculation** (use values from step1.json):

```
Juros = step1.dre.Juros.valor  = ___ M
D     = step1.balanco.D.valor  = ___ M
Kd_pre = Juros / D = ___ / ___ = ____%
```

**Mandatory check — compare with Rf:**

```
Rf = ____%   (from item 2.1)
Kd_pre (___%) > Rf (___%) ?   →   YES | NO
```

**IF Kd_pre < Rf → BLOCKER. Do not advance to Step 3.**

Check in this order before accepting:
1. Does the `Juros` field include only interest on financial debt? (exclude FX variation, fines, hedge)
2. Does the `D` field include total debt (short + long term)?
3. Are both values in MILLIONS (same unit)?
4. If after correction Kd_pre is still < Rf: record the alert, present to the user, and wait for confirmation before advancing.

**Alternative if `Juros` is not available in step1:**
- Use `Valuation/data/ratings.md`: calculate interest coverage ratio `EBIT_0 / Juros`
- Locate the synthetic rating and corresponding spread
- `Kd_pre = Rf + spread`

```
Kd_pre = ____%
Method used: Juros/D | Synthetic rating | Disclosed in release
Kd_pre > Rf: YES | NO (if NO: see blocker above)
```

---

## 2.5 — IR_marg (Marginal Tax Rate)

This is the maximum statutory rate — different from `IR_ef` (current effective rate from step1).

| Country | IR_marg | Composition |
|---|---|---|
| Brazil (non-financial) | 0.34 | 25% IRPJ + 9% CSLL |
| Brazil (financial) | 0.45 | 25% IRPJ + 20% CSLL |
| USA | 0.25 | federal + state average |
| Others | — | `Valuation/data/country-default-spreads-and-risk-premiums.md`, "Corporate Tax Rate" column |

```
IR_marg = ____   Composition: ________________
```

---

## 2.6 — WACC_est (Mature WACC)

Standard Damodaran formula (mature company, beta ≈ 1, no additional country risk):

```
WACC_est = Rf + 0.045
```

Adjustments to the default:
- High regulatory risk or highly cyclical sector: add +0.5 to +1.5 pp.
- Low-risk sector (regulated utilities, concessions): may reduce by −0.5 pp.
- If the user provides their own estimate: use the user's value and record the justification.

**Validation:** `WACC_est > g_perp` (check in Step 3 when g_perp is defined).

```
WACC_est = Rf + 0.045 = ____ + 0.045 = ____
Method: Rf+4.5% default | Adjusted | Provided by user
Justification (if adjusted): ________________
```

---

## Output JSON

```json
{
  "parametros_mercado": {
    "Rf": {
      "valor": null,
      "fonte": "",
      "data_consulta": "YYYY-MM-DD",
      "moeda": "BRL"
    },
    "ERP": {
      "valor": null,
      "fonte": "Damodaran — Country Risk Premiums",
      "pais_consultado": "",
      "ano_tabela": null
    },
    "Beta_u": {
      "valor": null,
      "fonte": "Damodaran — Betas by Sector Global",
      "setor_consultado": "",
      "ano_tabela": null
    },
    "Kd_pre": {
      "valor": null,
      "metodo": "Juros/D | Rating sintético | Divulgado",
      "juros_usados": null,
      "D_usada": null
    },
    "IR_marg": {
      "valor": null,
      "composicao": ""
    },
    "WACC_est": {
      "valor": null,
      "metodo": "Rf+4.5% | Ajustado | Usuário",
      "justificativa": ""
    }
  },
  "status_passo2": {
    "campos_nulos": [],
    "alertas": [],
    "pronto_para_passo3": false
  }
}
```

**Gate:** `pronto_para_passo3: true` only when:
- All 6 fields filled (no nulls)
- `Kd_pre > Rf` confirmed
- `status_passo2.campos_nulos = []`
