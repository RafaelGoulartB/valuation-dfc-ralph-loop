# Step 5 — Sensitivity Analysis and Scenarios

**Prerequisite:** Step 4 completed with no checklist failures.  
**Required inputs:** `Valor_acao_base`, `VP_total`, `VP_VT`, `Fator_10`, `NOPAT_term` and all inputs from `step3.json`.

---

## Analysis 5.1 — WACC_est × g_perp Matrix

This is the most important analysis: the Terminal Value represents ~40–70% of total value and is directly determined by these two variables.

**Configuration:**
- Rows: WACC_est varying from −1.0 pp to +1.0 pp in steps of 0.5 pp → 5 rows
- Columns: g_perp varying from −1.0 pp to +1.0 pp in steps of 0.5 pp → 5 columns

**Calculation for each cell (WACC_i, g_j):**

Only Blocks D and F change. `VP_total` and `Fator_10` remain fixed from Step 4.

```
1. ReinvRate_ij = g_j / WACC_i
2. FCFF_term_ij = NOPAT_term × (1 − ReinvRate_ij)
3. VT_ij        = FCFF_term_ij / (WACC_i − g_j)
4. VP_VT_ij     = VT_ij × Fator_10
5. Valor_op_ij  = VP_total + VP_VT_ij
6. Equity_ij    = Valor_op_ij + Caixa + AtvNOp − D − MinInt − Valor_opcoes
7. Valor_acao_ij = Equity_ij / Shares
```

**Fill rules:**
- If `g_j ≥ WACC_i`: fill with "—" (invalid model, denominator ≤ 0)
- Cell with Step 4 base values: mark with `*`
- Cell where `Valor_acao > P` (undervalued): mark with `✓`
- Cell where `Valor_acao < P` (overvalued): mark with `✗`

---

## Analysis 5.2 — g2_5 × Mg_alvo Matrix

Shows sensitivity to the analyst's operating assumptions.

**Configuration:**
- Rows: g2_5 varying −1.0 pp to +1.0 pp in steps of 0.5 pp → 5 rows
- Columns: Mg_alvo varying −2.0 pp to +2.0 pp in steps of 1.0 pp → 5 columns

**Calculation for each cell (g_i, Mg_j):**

Recalculate Blocks B, C, D, and F completely with new g2_5 = g_i and Mg_alvo = Mg_j.  
Keep fixed: WACC_est, g_perp, StC, g1, Mg_1, Ano_conv, and all of Blocks A and E.

```
For each t = 1..10:
  1. Recalculate g(t) using g_i in place of g2_5 (for t = 2..5 and transition 6..10)
  2. Recalculate Mg(t) using Mg_j in place of Mg_alvo
  3. Recalculate Rev(t), EBIT(t), NOPAT(t), Reinvest(t), FCFF(t)
  4. Recalculate VP_FCFF(t) → sum → new VP_total_ij
Recalculate Block D with Mg_alvo = Mg_j → new VP_VT_ij
Recalculate Block F → new Valor_acao_ij
```

Mark cells with `✓`, `✗`, and `*` in the same way as in Analysis 5.1.

---

## Analysis 5.3 — Breakevens

For each assumption below: find the exact value that makes `Valor_acao = P`, holding all other assumptions at Step 4 base values.

**Search method:** vary the assumption in the indicated range in steps of 0.1 pp until Valor_acao ≈ P.

| Assumption | Search range | Breakeven value | Distance from base |
|---|---|---|---|
| g_perp | 0% to WACC_est − 0.1% | ___% | ___ pp |
| WACC_est | WACC_est_base ± 5 pp | ___% | ___ pp |
| Mg_alvo | 0% to 60% | ___% | ___ pp |
| g2_5 | −5 pp to +10 pp from base | ___% | ___ pp |

**Interpretation:**
- Assumption with the shortest distance to breakeven → most sensitive → monitor in future releases
- If the breakeven implies an impossible value (e.g. g_perp ≥ Rf): the market price cannot be justified by reasonable assumptions → stock is significantly over or undervalued

```
Most sensitive assumption: ________________
Interpretation: "The market is pricing ___ = ___%, vs. base assumption of ____%"
```

---

## Analysis 5.4 — Bear / Base / Bull Scenarios

Build three coherent sets of assumptions and calculate Valor_acao in each.

**References for calibration:**

| Assumption | Bear (pessimistic) | Base (Step 4) | Bull (optimistic) |
|---|---|---|---|
| g1 | g1_base − 2pp | (base) | g1_base |
| g2_5 | sector median − 2pp | (base) | g_recente |
| Mg_1 | Mg_1_base − 1pp | (base) | Mg_1_base |
| Mg_alvo | sector median | (base) | best sector peer |
| StC | StC_hist × 0.85 | (base) | StC_hist |
| g_perp | inflation − 1pp | (base) | inflation + real GDP |
| WACC_est | WACC_est_base + 1pp | (base) | WACC_est_base − 0.5pp |

Fill the Bear and Bull columns with chosen values. Values must be internally consistent (e.g. high growth in the Bear scenario is inconsistent with low margin unless there is a specific reason).

**Calculation:** for Bear and Bull, recalculate Blocks B, C, D, and F completely with the new assumptions.

```
Bear scenario:  Valor_acao = ____  (____% vs P = ____)
Base scenario:  Valor_acao = ____  (____% vs P)   ← Step 4 value
Bull scenario:  Valor_acao = ____  (____% vs P)

Intrinsic value range: [___, ___]
Current price (P = ____) is within the range?  YES | NO
```

---

## Step 5 Output

Present in this order:

**5.A — WACC × g_perp Matrix** (table with ✓/✗/*/—)

**5.B — g2_5 × Mg_alvo Matrix** (table with ✓/✗/*)

**5.C — Breakevens**
```
g_perp:   base=___% → breakeven=___% → distance ___ pp
WACC_est: base=___% → breakeven=___% → distance ___ pp
Mg_alvo:  base=___% → breakeven=___% → distance ___ pp
g2_5:     base=___% → breakeven=___% → distance ___ pp
Most sensitive assumption: ________________
```

**5.D — Scenario Table**

| Scenario | g2_5 | Mg_alvo | g_perp | WACC_est | Valor_acao | vs P |
|---|---|---|---|---|---|---|
| Bear | | | | | | |
| Base | | | | | | ← Step 4 |
| Bull | | | | | | |

**5.E — Conclusion (3–4 sentences):**
1. Classification of the base value (over/under/fairly valued) and magnitude
2. Most sensitive assumption and what it represents operationally
3. In which scenario the current price P would be fair
4. What to monitor in future releases to revisit the thesis
