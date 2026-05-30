# Passo 1 — Extração de Dados do Release de Resultados

> **Objetivo deste passo:** Ler o release de resultados (PDF) fornecido pelo usuário e extrair todos os dados financeiros que alimentarão o valuation DCF. Ao final, produzir um JSON estruturado com os dados encontrados e uma lista clara do que ainda está faltando e precisará ser fornecido manualmente.

---

## INSTRUÇÕES DE EXECUÇÃO

Ao receber o release, execute as três fases abaixo em ordem. Não pule fases.

---

## FASE 1 — LEITURA E MAPEAMENTO DO DOCUMENTO

Antes de extrair qualquer número, identifique a estrutura do release:

```
1. Qual é o nome da empresa e ticker?
2. Qual é o período de referência (trimestre/ano)?
3. Qual é a moeda reportada e a unidade (milhares, milhões, bilhões)?
4. O documento contém DRE (Demonstração de Resultado)?
5. O documento contém Balanço Patrimonial?
6. O documento contém Fluxo de Caixa?
7. O documento contém notas explicativas com detalhamento de dívida?
8. O documento contém informações sobre número de ações?
```

Registre as respostas antes de continuar.

---

## FASE 2 — EXTRAÇÃO DE DADOS

Para cada item abaixo, tente localizar o valor no documento. Registre:
- O valor encontrado
- A seção/página onde foi encontrado
- O nível de confiança: `DIRETO` (número exato no documento), `CALCULADO` (derivado de outros números do documento), ou `NÃO ENCONTRADO`

---

### BLOCO A — Dados da DRE (Demonstração de Resultado)

**A1. Receita Líquida**
```
Procure por: "Receita Líquida", "Net Revenue", "Net Sales", "Receita de Vendas"
Símbolo no modelo: Rev_0
Período: preferir LTM (últimos 12 meses). Se não disponível, usar o anual mais recente.
Se o release for trimestral: verificar se há coluna "Acumulado 12M" ou "LTM". 
Se não houver, registrar como "trimestral — necessita anualização".
```

**A2. EBIT (Lucro Operacional)**
```
Procure por: "EBIT", "Resultado Operacional", "Lucro Operacional", "Operating Income"
Símbolo no modelo: EBIT_0
Atenção: alguns releases usam "EBIT ajustado" (exclui itens não recorrentes).
Registrar os dois se ambos existirem e indicar qual foi usado.
Se não encontrado diretamente: EBIT = Lucro Bruto − Despesas Operacionais
```

**A3. EBITDA**
```
Procure por: "EBITDA", "Resultado antes de juros, impostos, depreciação e amortização"
Símbolo no modelo: usado para derivar Depreciação (D&A = EBITDA − EBIT)
```

**A4. Depreciação e Amortização (D&A)**
```
Procure por: "Depreciação", "Amortização", "D&A", "Depreciation and Amortization"
Símbolo no modelo: Dep
Se não encontrado diretamente: Dep = EBITDA − EBIT (se ambos disponíveis)
```

**A5. Resultado Financeiro / Despesa com Juros**
```
Procure por: "Resultado Financeiro", "Despesas Financeiras", "Juros sobre Dívida",
             "Financial Expenses", "Interest Expense"
Símbolo no modelo: Juros
Atenção: separar despesa de juros de variação cambial e outros itens financeiros.
Registrar o valor bruto de juros pagos, não o resultado financeiro líquido.
```

**A6. Lucro Antes do IR (LAIR)**
```
Procure por: "LAIR", "EBT", "Lucro Antes do Imposto de Renda", "Pre-tax Income"
Usado para: calcular alíquota efetiva de IR
```

**A7. Imposto de Renda e CSLL Pagos**
```
Procure por: "Imposto de Renda", "IRPJ", "CSLL", "Income Tax Expense"
Símbolo no modelo: usado para calcular IR_ef = IR_pago / LAIR
```

**A8. Lucro Líquido**
```
Procure por: "Lucro Líquido", "Net Income", "Resultado Líquido"
Usado para: verificação de consistência (não entra diretamente no DCF)
```

**A9. Margem EBIT Atual**
```
Calcular: Mg_atual = EBIT_0 / Rev_0
Registrar como referência para definição da Mg_1 pelo analista.
```

---

### BLOCO B — Dados do Balanço Patrimonial

**B1. Patrimônio Líquido Contábil**
```
Procure por: "Patrimônio Líquido", "Equity", "Shareholders' Equity"
Símbolo no modelo: PL
Usar o valor total consolidado (incluindo minoritários separadamente, se houver).
```

**B2. Dívida Financeira Total**
```
Procure por: "Dívida Bruta", "Empréstimos e Financiamentos", "Gross Debt",
             "Loans and Borrowings", "Debentures", "CRI", "CRA"
Símbolo no modelo: D
= Dívida Circulante (curto prazo) + Dívida Não Circulante (longo prazo)
Excluir: contas a pagar, impostos diferidos, arrendamentos IFRS 16 (a menos que 
         a empresa já converta leases em dívida na sua apresentação)
```

**B3. Caixa e Equivalentes**
```
Procure por: "Caixa e Equivalentes de Caixa", "Cash and Cash Equivalents",
             "Aplicações Financeiras de Curto Prazo", "Disponibilidades"
Símbolo no modelo: Caixa
Incluir: caixa + aplicações financeiras de curtíssimo prazo (< 90 dias)
```

**B4. Dívida Líquida**
```
Procure por: "Dívida Líquida", "Net Debt"
= D − Caixa
Registrar como verificação: se encontrado no release, deve bater com B2 − B3.
```

**B5. Participações Minoritárias**
```
Procure por: "Participações de Acionistas Não Controladores", "Minority Interest",
             "Não Controladores"
Símbolo no modelo: MinInt
Se não mencionado, registrar como 0 e indicar "não encontrado no release".
```

**B6. Outros Ativos Não Operacionais**
```
Procure por: participações em outras empresas, imóveis não operacionais,
             investimentos de longo prazo não ligados à operação principal
Símbolo no modelo: AtvNOp
Este item raramente aparece de forma explícita; registrar 0 se não identificado.
```

**B7. Capital Investido**
```
Calcular: CI = PL + D − Caixa
Registrar como dado auxiliar para validação do Sales-to-Capital ratio.
```

---

### BLOCO C — Dados de Mercado e Ações

**C1. Número de Ações em Circulação**
```
Procure por: "Ações em Circulação", "Shares Outstanding", "Quantidade de Ações",
             "Capital Social — ações ordinárias + preferenciais"
Símbolo no modelo: Shares
Atenção: registrar total de ações (ON + PN se houver), excluindo ações em tesouraria.
Se o release apresentar em unidades: converter para milhões dividindo por 1.000.000.
```

**C2. Preço da Ação na Data do Release**
```
Procure por: cotação divulgada no release, valor de mercado + ações = preço implícito.
Símbolo no modelo: P
Observação: o release pode não trazer o preço atual — registrar como NÃO ENCONTRADO
            e solicitar ao usuário separadamente.
```

**C3. Capitalização de Mercado**
```
Procure por: "Market Cap", "Valor de Mercado", mencionado em seção de "Destaques"
Símbolo no modelo: MktCap (calculado = P × Shares, mas pode vir explícito)
```

**C4. Valor Patrimonial por Ação (VPA)**
```
Calcular: VPA = PL / Shares
Registrar como referência comparativa.
```

---

### BLOCO D — Dados Operacionais Complementares

**D1. ROIC (Retorno sobre Capital Investido)**
```
Procure por: "ROIC", "Retorno sobre Capital Investido"
Se não encontrado: ROIC = NOPAT / CI = [EBIT × (1 − IR_ef)] / (PL + D − Caixa)
Símbolo no modelo: referência para validar StC ratio
```

**D2. Receita do Período Anterior**
```
Procure por: coluna comparativa do ano/trimestre anterior
Usado para: calcular crescimento de receita recente (referência para premissas g1 e g2_5)
```

**D3. Crescimento de Receita Recente**
```
Calcular: g_recente = (Rev_atual / Rev_anterior) − 1
Registrar como dado de referência para o analista calibrar g1 e g2_5.
```

**D4. CAPEX**
```
Procure por: "CAPEX", "Investimentos", "Additions to PP&E", "Imobilizado"
             (variação do imobilizado bruto entre períodos)
Registrar como dado auxiliar — não entra diretamente no modelo DCF de Damodaran,
mas ajuda a calibrar o Sales-to-Capital ratio.
```

**D5. Número de Funcionários / Outras Métricas Operacionais**
```
Registrar apenas se o setor usar métricas específicas de valor:
- Telecoms: assinantes, ARPU, churn
- Varejo: lojas, SSS (same-store sales)
- Bancos: carteira de crédito, NIM, inadimplência
Estas métricas auxiliam a narrativa do analista, não os cálculos do DCF.
```

---

## FASE 3 — OUTPUT ESTRUTURADO

Após a extração, produza obrigatoriamente os dois blocos abaixo.

### BLOCO OUTPUT 1 — JSON de Dados Extraídos

Salvar json em pasta Acoes/:ticker/:passo.json

```json
{
  "empresa": {
    "nome": "...",
    "ticker": "...",
    "pais": "...",
    "setor": "...",
    "moeda": "...",
    "unidade": "milhões"
  },
  "periodo_referencia": {
    "tipo": "anual | trimestral | LTM",
    "data": "YYYY-MM-DD ou AAAA-TT"
  },
  "dre": {
    "Rev_0":       { "valor": null, "confianca": "DIRETO | CALCULADO | NÃO ENCONTRADO", "fonte": "..." },
    "EBIT_0":      { "valor": null, "confianca": "...", "fonte": "..." },
    "EBITDA":      { "valor": null, "confianca": "...", "fonte": "..." },
    "Dep":         { "valor": null, "confianca": "...", "fonte": "..." },
    "Juros":       { "valor": null, "confianca": "...", "fonte": "..." },
    "LAIR":        { "valor": null, "confianca": "...", "fonte": "..." },
    "IR_pago":     { "valor": null, "confianca": "...", "fonte": "..." },
    "IR_ef":       { "valor": null, "confianca": "CALCULADO", "fonte": "IR_pago / LAIR" },
    "Mg_atual":    { "valor": null, "confianca": "CALCULADO", "fonte": "EBIT_0 / Rev_0" }
  },
  "balanco": {
    "PL":          { "valor": null, "confianca": "...", "fonte": "..." },
    "D":           { "valor": null, "confianca": "...", "fonte": "..." },
    "Caixa":       { "valor": null, "confianca": "...", "fonte": "..." },
    "D_liq":       { "valor": null, "confianca": "CALCULADO", "fonte": "D − Caixa" },
    "MinInt":      { "valor": null, "confianca": "...", "fonte": "..." },
    "AtvNOp":      { "valor": null, "confianca": "...", "fonte": "..." },
    "CI":          { "valor": null, "confianca": "CALCULADO", "fonte": "PL + D − Caixa" }
  },
  "mercado": {
    "Shares":      { "valor": null, "confianca": "...", "fonte": "..." },
    "P":           { "valor": null, "confianca": "...", "fonte": "..." },
    "MktCap":      { "valor": null, "confianca": "...", "fonte": "..." }
  },
  "operacional": {
    "Rev_anterior":    { "valor": null, "confianca": "...", "fonte": "..." },
    "g_recente":       { "valor": null, "confianca": "CALCULADO", "fonte": "Rev_0/Rev_ant − 1" },
    "ROIC_atual":      { "valor": null, "confianca": "CALCULADO", "fonte": "NOPAT / CI" },
    "CAPEX":           { "valor": null, "confianca": "...", "fonte": "..." },
    "metricas_setor":  {}
  }
}
```

### BLOCO OUTPUT 2 — Tabela de Status e Lacunas

Após o JSON, apresente esta tabela resumindo o que foi e o que não foi encontrado:

```
DADOS EXTRAÍDOS DO RELEASE
══════════════════════════════════════════════════════════════════
Variável          │ Valor encontrado │ Status      │ Ação necessária
──────────────────┼──────────────────┼─────────────┼───────────────
Rev_0             │                  │             │
EBIT_0            │                  │             │
Dep               │                  │             │
Juros             │                  │             │
IR_ef             │                  │             │
PL                │                  │             │
D                 │                  │             │
Caixa             │                  │             │
MinInt            │                  │             │
Shares            │                  │             │
P                 │                  │             │
══════════════════════════════════════════════════════════════════

STATUS: DIRETO = extraído diretamente | CALCULADO = derivado | FALTANDO = não encontrado

INPUTS QUE PRECISARÃO SER FORNECIDOS PELO ANALISTA (não estão no release):
  → [listar aqui todos os itens com status FALTANDO ou que são premissas]
```

---

## ALERTAS E CASOS ESPECIAIS

### Releases Trimestrais
```
Se o release for trimestral (ex: 1T25, 2T25), verificar:
1. Existe coluna "Acumulado 12M" ou "LTM"? → usar diretamente
2. Existe coluna "Acumulado no ano" (YTD)? → não anualizar diretamente; alertar o usuário
3. Apenas dados do trimestre? → multiplicar por 4 apenas como estimativa aproximada;
   alertar que anualização simples pode distorcer sazonalidade
```

### EBIT Ajustado vs. Reportado
```
Muitos releases apresentam EBIT ajustado (excluindo itens não recorrentes).
Registrar os dois valores se disponíveis.
Recomendação: usar o EBIT ajustado para projeções futuras (mais representativo da
operação recorrente), mas indicar a diferença ao analista.
```

### Empresas com Leasing (IFRS 16)
```
Após 2019, balanços IFRS incluem direito de uso (arrendamentos) como ativo e dívida.
Se a empresa divulga dívida ajustada (ex-IFRS 16), registrar os dois valores.
Indicar ao analista qual usar — o modelo padrão usa dívida financeira
(empréstimos e debêntures), excluindo arrendamentos operacionais.
```

### EBITDA não Divulgado
```
Se o EBITDA não aparecer explicitamente:
  EBITDA = EBIT + Dep (se Dep disponível no fluxo de caixa)
  D&A = EBITDA − EBIT (se EBITDA disponível e EBIT disponível)
Registrar qual caminho foi usado.
```

---

## O QUE ESTE PASSO NÃO FAZ

Os itens abaixo **não** podem ser extraídos de releases de resultados e serão coletados em passos posteriores:

```
✗ Beta desalavancado do setor         → requer base de dados de mercado (Damodaran)
✗ Prêmio de risco do país (ERP)       → requer base de dados de mercado (Damodaran)
✗ Taxa livre de risco (Rf)            → requer dados de mercado de renda fixa
✗ WACC estável de maturidade          → calculado no Passo 3
✗ Premissas de crescimento (g1, g2_5) → definidas pelo analista no Passo 2
✗ Margem EBIT alvo (Mg_alvo)          → definida pelo analista no Passo 2
✗ Sales-to-Capital ratio              → definido/calibrado pelo analista no Passo 2
✗ Taxa de crescimento na perpetuidade → definida pelo analista no Passo 2
```

