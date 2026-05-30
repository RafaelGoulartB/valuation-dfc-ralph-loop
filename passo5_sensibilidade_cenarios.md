# Passo 5 — Análise de Sensibilidade e Cenários

**Pré-requisito:** Passo 4 concluído sem falhas no checklist.  
**Input necessário:** `Valor_acao_base`, `VP_total`, `VP_VT`, `Fator_10`, `NOPAT_term` e todos os inputs do `passo3.json`.

---

## Análise 5.1 — Matriz WACC_est × g_perp

Esta é a análise mais importante: o Valor Terminal representa ~40–70% do valor total e é determinado diretamente por essas duas variáveis.

**Configuração:**
- Linhas: WACC_est variando de −1,0 p.p. a +1,0 p.p. em passos de 0,5 p.p. → 5 linhas
- Colunas: g_perp variando de −1,0 p.p. a +1,0 p.p. em passos de 0,5 p.p. → 5 colunas

**Cálculo para cada célula (WACC_i, g_j):**

Apenas os Blocos D e F mudam. `VP_total` e `Fator_10` permanecem fixos do Passo 4.

```
1. ReinvRate_ij = g_j / WACC_i
2. FCFF_term_ij = NOPAT_term × (1 − ReinvRate_ij)
3. VT_ij        = FCFF_term_ij / (WACC_i − g_j)
4. VP_VT_ij     = VT_ij × Fator_10
5. Valor_op_ij  = VP_total + VP_VT_ij
6. Equity_ij    = Valor_op_ij + Caixa + AtvNOp − D − MinInt − Valor_opcoes
7. Valor_acao_ij = Equity_ij / Shares
```

**Regras de preenchimento:**
- Se `g_j ≥ WACC_i`: preencher com "—" (modelo inválido, denominador ≤ 0)
- Célula com valores base do Passo 4: marcar com `*`
- Célula onde `Valor_acao > P` (subvalorizada): marcar com `✓`
- Célula onde `Valor_acao < P` (sobrevalorizada): marcar com `✗`

---

## Análise 5.2 — Matriz g2_5 × Mg_alvo

Mostra sensibilidade às premissas operacionais do analista.

**Configuração:**
- Linhas: g2_5 variando −1,0 p.p. a +1,0 p.p. em passos de 0,5 p.p. → 5 linhas
- Colunas: Mg_alvo variando −2,0 p.p. a +2,0 p.p. em passos de 1,0 p.p. → 5 colunas

**Cálculo para cada célula (g_i, Mg_j):**

Recalcular Blocos B, C, D e F completos com novos g2_5 = g_i e Mg_alvo = Mg_j.  
Manter fixos: WACC_est, g_perp, StC, g1, Mg_1, Ano_conv e todos os Blocos A e E.

```
Para cada t = 1..10:
  1. Recalcular g(t) usando g_i no lugar de g2_5 (para t = 2..5 e transição 6..10)
  2. Recalcular Mg(t) usando Mg_j no lugar de Mg_alvo
  3. Recalcular Rev(t), EBIT(t), NOPAT(t), Reinvest(t), FCFF(t)
  4. Recalcular VP_FCFF(t) → somar → novo VP_total_ij
Recalcular Bloco D com Mg_alvo = Mg_j → novo VP_VT_ij
Recalcular Bloco F → novo Valor_acao_ij
```

Marcar células com `✓`, `✗` e `*` da mesma forma que na Análise 5.1.

---

## Análise 5.3 — Breakevens

Para cada premissa abaixo: encontrar o valor exato que faz `Valor_acao = P`, mantendo todas as demais premissas nos valores base do Passo 4.

**Método de busca:** variar a premissa no intervalo indicado em passos de 0,1 p.p. até Valor_acao ≈ P.

| Premissa | Intervalo de busca | g_perp_breakeven | Distância ao base |
|---|---|---|---|
| g_perp | 0% até WACC_est − 0,1% | ___% | ___ p.p. |
| WACC_est | WACC_est_base ± 5 p.p. | ___% | ___ p.p. |
| Mg_alvo | 0% até 60% | ___% | ___ p.p. |
| g2_5 | −5 p.p. até +10 p.p. do base | ___% | ___ p.p. |

**Interpretação:**
- Premissa com menor distância ao breakeven → mais sensível → monitorar nos próximos releases
- Se o breakeven implica valor impossível (ex: g_perp ≥ Rf): preço de mercado não é justificável por premissas razoáveis → ação muito sobre ou subvalorizada

```
Premissa mais sensível: ________________
Interpretação: "O mercado está precificando ___ = ___%, vs. premissa base de ____%"
```

---

## Análise 5.4 — Cenários Bear / Base / Bull

Construir três conjuntos coerentes de premissas e calcular Valor_acao em cada um.

**Referências para calibrar:**

| Premissa | Bear (pessimista) | Base (Passo 4) | Bull (otimista) |
|---|---|---|---|
| g1 | g1_base − 2pp | (base) | g1_base |
| g2_5 | mediana setor − 2pp | (base) | g_recente |
| Mg_1 | Mg_1_base − 1pp | (base) | Mg_1_base |
| Mg_alvo | mediana setor | (base) | melhor peer do setor |
| StC | StC_hist × 0,85 | (base) | StC_hist |
| g_perp | inflação − 1pp | (base) | inflação + PIB real |
| WACC_est | WACC_est_base + 1pp | (base) | WACC_est_base − 0,5pp |

Preencher a coluna Bear e Bull com os valores escolhidos. Os valores devem ser coerentes entre si (ex: crescimento alto no Bear é inconsistente com margem baixa apenas se houver razão).

**Cálculo:** para Bear e Bull, recalcular Blocos B, C, D e F completamente com as novas premissas.

```
Cenário Bear:  Valor_acao = ____  (____% vs P = ____)
Cenário Base:  Valor_acao = ____  (____% vs P)   ← valor do Passo 4
Cenário Bull:  Valor_acao = ____  (____% vs P)

Intervalo de valor intrínseco: [___, ___]
Preço atual (P = ____) está dentro do intervalo?  SIM | NÃO
```

---

## Output do Passo 5

Apresentar nesta ordem:

**5.A — Matriz WACC × g_perp** (tabela com ✓/✗/*/—)

**5.B — Matriz g2_5 × Mg_alvo** (tabela com ✓/✗/*)

**5.C — Breakevens**
```
g_perp:   base=___% → breakeven=___% → distância ___ p.p.
WACC_est: base=___% → breakeven=___% → distância ___ p.p.
Mg_alvo:  base=___% → breakeven=___% → distância ___ p.p.
g2_5:     base=___% → breakeven=___% → distância ___ p.p.
Premissa mais sensível: ________________
```

**5.D — Tabela de Cenários**

| Cenário | g2_5 | Mg_alvo | g_perp | WACC_est | Valor_acao | vs P |
|---|---|---|---|---|---|---|
| Bear | | | | | | |
| Base | | | | | | ← Passo 4 |
| Bull | | | | | | |

**5.E — Conclusão (3–4 frases):**
1. Classificação do valor base (sobre/sub/justo) e magnitude
2. Premissa mais sensível e o que ela representa operacionalmente
3. Em qual cenário o preço atual P seria justo
4. O que monitorar nos próximos releases para revisar a tese
