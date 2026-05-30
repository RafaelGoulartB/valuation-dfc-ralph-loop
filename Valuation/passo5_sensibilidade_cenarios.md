# Passo 5 — Análise de Sensibilidade e Cenários

> **Pré-requisito:** o Passo 4 deve ter produzido o valor por ação base (`Valor_acao`) e o checklist de verificação deve estar completo sem falhas. Este passo é opcional, mas recomendado para qualquer avaliação que será usada em decisão de investimento.

**Objetivo:** quantificar como o valor por ação muda quando as premissas mais importantes variam, identificar quais premissas têm maior impacto no resultado e construir cenários bull/base/bear para apresentação.

---

## POR QUE ESTE PASSO EXISTE

O valor intrínseco calculado no Passo 4 é um **ponto estimado** baseado em premissas específicas. Na prática, toda premissa tem incerteza. A análise de sensibilidade transforma o ponto estimado em um **intervalo de valor**, o que é muito mais honesto e útil para a tomada de decisão.

```
Exemplo: se o valor base é R$ 6,27 e a sensibilidade mostra que o valor
varia entre R$ 4,80 e R$ 8,50 dependendo das premissas, o analista sabe
que o preço atual (R$ 6,57) está dentro do intervalo razoável —
e não apenas 4,7% acima de um único número pontual.
```

---

## ANÁLISE 5.1 — SENSIBILIDADE WACC × CRESCIMENTO PERPÉTUO

Esta é a análise mais importante. O Valor Terminal (responsável por ~60% do valor total) é diretamente determinado por `WACC_est` e `g_perp`.

**Configuração:**
```
Eixo horizontal (colunas): g_perp variando de (g_perp_base − 2 p.p.) a (g_perp_base + 2 p.p.)
  em passos de 0,5 p.p.  →  5 colunas

Eixo vertical (linhas): WACC_est variando de (WACC_est_base − 1,5 p.p.) a (WACC_est_base + 1,5 p.p.)
  em passos de 0,5 p.p.  →  7 linhas

Restrição: nunca incluir combinações onde g_perp >= WACC_est (denominador ≤ 0)
  → Para essas células, preencher com "N/A"
```

**Instrução de cálculo:**

Para cada combinação (WACC_est_i, g_perp_j):
```
1. Manter todos os outros inputs do JSON do Passo 3 fixos
2. Recalcular apenas os blocos D e F do Passo 4 com os novos valores:
   → Novo FCFF_term (D5) usando o mesmo NOPAT_term e novo ReinvRate_term = g_perp_j / WACC_est_i
   → Novo VT (D6) = FCFF_term / (WACC_est_i − g_perp_j)
   → Novo VP_VT (D7) = VT × Fator(10)  [Fator(10) não muda]
   → Novo Valor_op = VP_total + VP_VT   [VP_total não muda]
   → Novo Equity_Value = Valor_op + Caixa + AtvNOp − D − MinInt − Valor_opcoes
   → Novo Valor_acao = Equity_Value / Shares
3. Registrar o Valor_acao na célula da matriz
```

**Formato da matriz:**

```
                     g_perp (crescimento na perpetuidade)
                  [g−2pp]  [g−1,5pp] [g−1pp] [g−0,5pp] [g_base] [g+0,5pp] [g+1pp]
WACC_est [W−1,5pp]
WACC_est [W−1pp]
WACC_est [W−0,5pp]
WACC_est [W_base]   ←── valor base do Passo 4 aqui
WACC_est [W+0,5pp]
WACC_est [W+1pp]
WACC_est [W+1,5pp]
```

**Como apresentar:**
```
→ Célula com valor base: destacar com asterisco ou marcação clara
→ Células onde Valor_acao > P (subvalorizado): marcar como ✓
→ Células onde Valor_acao < P (sobrevalorizado): marcar como ✗
→ Célula N/A (g_perp >= WACC_est): preencher com "—"
```

---

## ANÁLISE 5.2 — SENSIBILIDADE CRESCIMENTO × MARGEM

Esta análise mostra como o valor responde às premissas operacionais do analista.

**Configuração:**
```
Eixo horizontal (colunas): Mg_alvo variando ±3 p.p. em passos de 1 p.p.  →  7 colunas
Eixo vertical (linhas):    g2_5 variando ±2 p.p. em passos de 1 p.p.     →  5 linhas
```

**Instrução de cálculo:**

Para cada combinação (g2_5_i, Mg_alvo_j):
```
1. Manter WACC_est, g_perp, StC, g1, Mg_1, Ano_conv fixos nos valores base
2. Recalcular todos os Blocos B, C, D e F do Passo 4 com novos g2_5_i e Mg_alvo_j
   → g(t) para t=2..10 usa o novo g2_5_i
   → Mg(t) para t=2..10 converge para o novo Mg_alvo_j
   → Recalcular Rev(t), EBIT(t), NOPAT(t), Reinvest(t), FCFF(t) para todos os anos
   → Recalcular VP_FCFF(t), VP_total
   → Recalcular FCFF_term, VT, VP_VT
   → Calcular novo Valor_acao
3. Registrar na célula da matriz
```

**Formato da matriz:**

```
                         Mg_alvo (margem EBIT na maturidade)
              [M−3pp]  [M−2pp]  [M−1pp]  [M_base]  [M+1pp]  [M+2pp]  [M+3pp]
g2_5 [g−2pp]
g2_5 [g−1pp]
g2_5 [g_base]                             ←── valor base
g2_5 [g+1pp]
g2_5 [g+2pp]
```

---

## ANÁLISE 5.3 — BREAKEVEN DE PREMISSAS

Identifica o valor exato de cada premissa que faria o valor intrínseco igualar o preço atual de mercado.

**Para cada premissa listada abaixo, calcular o breakeven:**

```
Premissa 1: g_perp de breakeven
  Pergunta: qual g_perp faz Valor_acao = P, mantendo tudo mais fixo?
  Método: variar g_perp de 0% até (WACC_est − 0,5%) em passos de 0,1%
          até encontrar o ponto onde Valor_acao ≈ P
  Resultado: g_perp_breakeven = ____%
  Interpretação: "O mercado está precificando um crescimento perpétuo de ____%"

Premissa 2: WACC_est de breakeven
  Pergunta: qual WACC_est faz Valor_acao = P?
  Método: variar WACC_est em torno do valor base
  Resultado: WACC_est_breakeven = ____%
  Interpretação: "O mercado está precificando um custo de capital estável de ____%"

Premissa 3: Mg_alvo de breakeven
  Pergunta: qual Mg_alvo faz Valor_acao = P?
  Resultado: Mg_alvo_breakeven = ____%
  Interpretação: "O mercado está precificando margem na maturidade de ____%"

Premissa 4: g2_5 de breakeven
  Pergunta: qual crescimento nos anos 2–5 faz Valor_acao = P?
  Resultado: g2_5_breakeven = ____%
  Interpretação: "O mercado está precificando crescimento de ____%"
```

**Como interpretar os breakevens:**
```
SE breakeven de uma premissa está muito perto do valor base:
  → Pequena variação nessa premissa muda muito o resultado → alta sensibilidade → premissa crítica

SE breakeven está muito distante do valor base:
  → O resultado é robusto a variações nessa premissa → baixa sensibilidade

SE o breakeven implica um valor impossível ou absurdo (ex: g_perp = 9% com Rf = 6%):
  → O preço de mercado não pode ser justificado por premissas razoáveis
  → Ação claramente sobre ou subvalorizada
```

---

## ANÁLISE 5.4 — CENÁRIOS BULL / BASE / BEAR

Construa três conjuntos coerentes de premissas e calcule o valor por ação em cada um.

**Estrutura dos cenários:**

| Premissa   | Bear (pessimista) | Base (Passo 4) | Bull (otimista) |
|------------|-------------------|----------------|-----------------|
| g1         |                   | (valor base)   |                 |
| g2_5       |                   | (valor base)   |                 |
| Mg_1       |                   | (valor base)   |                 |
| Mg_alvo    |                   | (valor base)   |                 |
| StC        |                   | (valor base)   |                 |
| g_perp     |                   | (valor base)   |                 |
| WACC_est   |                   | (valor base)   |                 |

**Critérios para montar Bear e Bull:**
```
Bear: premissas conservadoras mas não catastróficas
  → g2_5 = mediana do setor − 2 p.p.
  → Mg_alvo = mediana do setor (empresa não ganha vantagem competitiva)
  → g_perp = inflação − 1 p.p. (crescimento abaixo da inflação)
  → WACC_est = WACC_est_base + 1 p.p. (empresa mais arriscada na maturidade)

Bull: premissas otimistas mas defensáveis
  → g2_5 = crescimento recente mantido por mais tempo
  → Mg_alvo = melhor empresa comparável do setor
  → g_perp = inflação + crescimento real (empresa cresce com a economia)
  → WACC_est = WACC_est_base − 0,5 p.p. (empresa de baixo risco na maturidade)
```

**Instrução de cálculo:**

Para cada cenário, recalcular completamente os Blocos B, C, D e F do Passo 4. Os parâmetros de capital (Bloco A) permanecem os mesmos nos três cenários, exceto WACC_est que pode mudar.

**Resultado:**
```
Cenário Bear:  Valor_acao = ____  (____% vs preço atual)
Cenário Base:  Valor_acao = ____  (____% vs preço atual)  ← valor do Passo 4
Cenário Bull:  Valor_acao = ____  (____% vs preço atual)

Intervalo de valor: [Bear, Bull] = [____, ____]
Preço atual dentro do intervalo? ____
```

---

## OUTPUT DO PASSO 5

Apresente nesta ordem:

### 5.A — Matriz de Sensibilidade WACC × g_perp
*(tabela formatada conforme Análise 5.1)*

### 5.B — Matriz de Sensibilidade g2_5 × Mg_alvo
*(tabela formatada conforme Análise 5.2)*

### 5.C — Breakevens
```
g_perp de breakeven:    ____%   (base: ____%)   → distância: ____ p.p.
WACC_est de breakeven:  ____%   (base: ____%)   → distância: ____ p.p.
Mg_alvo de breakeven:   ____%   (base: ____%)   → distância: ____ p.p.
g2_5 de breakeven:      ____%   (base: ____%)   → distância: ____ p.p.

Premissa mais sensível (menor distância ao breakeven): ________________
```

### 5.D — Tabela de Cenários

| Cenário | Valor/Ação | vs. Preço Atual | Classificação |
|---------|-----------|----------------|---------------|
| Bear    |           |                |               |
| Base    |           |                | ← Passo 4     |
| Bull    |           |                |               |

### 5.E — Conclusão Narrativa

Redigir um parágrafo com:
1. O valor base e a classificação atual (sobre/sub/justo)
2. A premissa mais crítica identificada pelos breakevens
3. Em qual cenário o preço atual seria justificado
4. Recomendação de acompanhamento (qual premissa monitorar nos próximos releases)

---

## CHECKLIST DE SAÍDA

```
[ ] Matriz 5.1 preenchida sem células inválidas não sinalizadas
[ ] Matriz 5.2 preenchida
[ ] Quatro breakevens calculados e interpretados
[ ] Três cenários construídos com premissas coerentes e distintas
[ ] Conclusão narrativa redigida
[ ] Premissa mais sensível identificada
```
