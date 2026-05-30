# Passo 1 — Extração do Release

**Objetivo:** ler o PDF do release e produzir `Acoes/<TICKER>/passo1.json` com todos os dados históricos necessários para o valuation DCF.  
**Regra fundamental:** todos os valores financeiros no JSON devem estar em **MILHÕES (R$ M)**.

---

## FASE 1 — Identificar estrutura do documento

Antes de extrair qualquer número, responda:
1. Nome da empresa e ticker?
2. Período do release (anual / trimestral / LTM)?
3. Unidade reportada (milhares / milhões / bilhões)?
4. O release contém: DRE? Balanço? Fluxo de Caixa? Notas sobre dívida?

Registre as respostas. Elas determinam como tratar os números.

---

## FASE 2 — Regra de Unidades

**Converter tudo para MILHÕES antes de registrar no JSON:**

| Unidade no release | Exemplo encontrado | Operação | Valor no JSON |
|---|---|---|---|
| Milhares (R$ mil) | 1.185.600 | ÷ 1.000 | 1.185,6 |
| Milhões (R$ M) | 1.185,6 | nenhuma | 1.185,6 |
| Bilhões (R$ B) | 1,186 | × 1.000 | 1.186,0 |

**Verificação de escala obrigatória:** calcule `MktCap / Rev_0` ao final.
- Entre 0,3× e 15×: normal para maioria dos setores.
- Acima de 20×: PARAR — há quase certeza de erro de unidade. Revisar antes de continuar.

---

## FASE 3 — Extração campo a campo

Para cada campo: localizar no documento → converter unidade → registrar valor e fonte.  
Se não encontrado: registrar `"valor": null, "confianca": "PENDENTE"` e incluir na lista de lacunas.

### Bloco DRE

**Rev_0 — Receita Líquida**
- Buscar: "Receita Líquida", "Net Revenue", "Receita Operacional Líquida"
- Preferir LTM (últimos 12 meses). Se release anual: usar diretamente.
- Se trimestral sem coluna LTM: `LTM = 4T_anterior + Acumulado_atual − Acumulado_anterior_mesmo_período`
- Se impossível calcular LTM: registrar valor trimestral com nota "necessita anualização"

**EBIT_0 — Resultado Operacional**
- Buscar: "EBIT", "Resultado Operacional", "Lucro Operacional", "Operating Income"
- **ATENÇÃO:** EBIT ≠ EBITDA. EBIT já deduz depreciação. Se o release mostrar apenas EBITDA: `EBIT = EBITDA − Dep`
- Sinal de alerta: se `EBIT_0 / Rev_0 > 40%` provavelmente é EBITDA por engano — verificar

**EBITDA**
- Buscar: "EBITDA"
- Usado para calcular Dep = EBITDA − EBIT. Se não disponível, registrar null.

**Dep — Depreciação e Amortização**
- Buscar: "Depreciação", "Amortização", "D&A" no fluxo de caixa
- Se não encontrado diretamente: `Dep = EBITDA − EBIT_0` (se ambos disponíveis)

**Juros — Despesa com Juros**
- Buscar: "Juros sobre dívida", "Despesas Financeiras — Juros", "Interest Expense"
- Incluir APENAS juros sobre dívida financeira.
- Excluir: variação cambial, multas, juros sobre impostos, resultado de hedge.
- Se o release misturar: anotar o valor bruto de juros separadamente do resultado financeiro líquido.

**LAIR — Lucro Antes do Imposto**
- Buscar: "LAIR", "EBT", "Lucro Antes do IR", "Pre-tax Income"

**IR_pago — Imposto de Renda Pago**
- Buscar: "IRPJ e CSLL", "Imposto de Renda", "Income Tax Expense"
- Usar o valor da despesa contábil (não o IR em caixa do fluxo de caixa, salvo se for o único disponível)

### Bloco Balanço

**D — Dívida Financeira Bruta**
- Buscar: "Dívida Bruta", "Empréstimos e Financiamentos", "Debêntures"
- Somar: parte circulante (curto prazo) + parte não circulante (longo prazo)
- Excluir: arrendamentos IFRS 16, contas a pagar, impostos diferidos
- Exceção: se a empresa divulga "Dívida ex-IFRS 16" explicitamente, usar esse valor

**Caixa**
- Buscar: "Caixa e Equivalentes", "Aplicações Financeiras de Curto Prazo"
- Incluir: caixa + aplicações com vencimento < 90 dias

**D_liq — Dívida Líquida**
- Buscar: "Dívida Líquida", "Net Debt" — usar como campo de verificação
- Calcular: `D_liq_calc = D − Caixa`. Deve bater com o valor do release (tolerância 2%).
- Se divergir > 2%: investigar antes de registrar.

**PL — Patrimônio Líquido**
- Buscar: "Patrimônio Líquido" total consolidado

**MinInt — Participações Minoritárias**
- Buscar: "Não Controladores", "Minority Interest"
- Se não encontrado: registrar 0 com nota "não identificado no release"

**AtvNOp — Ativos Não Operacionais**
- Participações em empresas não relacionadas à operação, imóveis não operacionais
- Se não identificado: registrar 0

### Bloco Mercado e Ações

**Shares — Ações em Circulação**
- Buscar: "Ações em Circulação", "Shares Outstanding", total ON + PN
- Excluir ações em tesouraria
- Converter para milhões: se o release reportar em unidades, dividir por 1.000.000
- Exemplo: "399.087.450 ações" → Shares = 399,087

**P — Preço da Ação**
- Buscar: cotação divulgada no release ou valor de mercado ÷ Shares
- Se não encontrado no release: registrar `"valor": null, "confianca": "PENDENTE"` e solicitar ao usuário

**MktCap**
- Buscar: "Market Cap", "Valor de Mercado" — campo de verificação
- Calcular: `MktCap_calc = P × Shares`. Deve bater com release (tolerância 5%).

### Bloco Operacional

**Rev_ant — Receita do Período Anterior**
- Coluna comparativa do mesmo período do ano anterior

**CAPEX**
- Buscar: "Investimentos", "Aquisição de imobilizado", "Additions to PP&E"

---

## FASE 4 — Calcular campos derivados

Após extrair todos os campos, calcular:

```
IR_ef      = IR_pago / LAIR
             → esperado entre 0,15 e 0,45 para empresas brasileiras
             → se < 0 ou > 0,60: revisar IR_pago e LAIR

Mg_atual   = EBIT_0 / Rev_0
             → se > 0,40: verificar se EBIT_0 é realmente EBIT (não EBITDA)

g_recente  = (Rev_0 / Rev_ant) − 1

CI         = PL + D − Caixa

ROIC_atual = (EBIT_0 × (1 − IR_ef)) / CI

StC_hist   = Rev_0 / CI

D_liq_calc = D − Caixa  → comparar com D_liq do release

MktCap_calc = P × Shares  → comparar com MktCap do release
```

---

## FASE 5 — Verificações de consistência

Executar antes de produzir o JSON final:

```
[ ] 1. MktCap_calc = P × Shares = ___ × ___ = ___ M
        MktCap do release = ___ M   |   Diferença: ___%
        → OK se < 5%. Se > 5%: revisar Shares (total vs. circulante vs. ex-tesouraria)

[ ] 2. D_liq_calc = D − Caixa = ___ − ___ = ___ M
        D_liq do release = ___ M   |   Diferença: ___%
        → OK se < 2%. Se > 2%: verificar componentes de D e Caixa

[ ] 3. EBIT_0 < EBITDA  (sempre deve ser verdade)
        EBIT_0 = ___ M, EBITDA = ___ M   →   OK | FALHA (revisar extração)

[ ] 4. IR_ef = ___ (esperado 0,15–0,45)   →   OK | ALERTA

[ ] 5. MktCap_calc / Rev_0 = ___ / ___ = ___×
        → OK se ≤ 15×. Se > 20×: PARAR — erro de unidade. Não continuar.

[ ] 6. D > 0 e D / MktCap_calc = ___% 
        → Se D > 0 mas ratio < 1%: PARAR — erro de unidade em D.
```

Se alguma verificação falhar: corrigir antes de salvar o JSON.

---

## FASE 6 — JSON de saída

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

**Ao final:** listar todos os campos com status PENDENTE e solicitar ao usuário antes de avançar ao Passo 2.
