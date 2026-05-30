# Passo 3 — Definição das Premissas do Analista

> **Pré-requisito:** os JSONs dos Passos 1 e 2 devem estar completos e com `status.pronto_para_passo3: true`. Se não estiverem, volte ao passo anterior.

**Objetivo:** com base nos dados históricos (Passo 1) e parâmetros de mercado (Passo 2) já coletados, definir e justificar cada premissa futura que alimentará o modelo DCF. Ao final, produzir o JSON consolidado final com **todos os inputs** prontos para o Passo 4 executar os cálculos.

---

## COMO USAR ESTE DOCUMENTO

Para cada premissa abaixo, a estrutura é sempre:

1. **Referência histórica** — o que os dados do Passo 1 mostram sobre essa variável hoje
2. **Referência setorial** — o que o setor indica como patamar razoável
3. **Decisão** — o valor escolhido e a justificativa em uma frase
4. **Registro no JSON** — onde o valor entra no JSON de saída

O analista (usuário) toma a decisão final. A LLM apresenta as referências, calcula os indicadores de base e aguarda confirmação antes de registrar.

---

## BLOCO 0 — CONSOLIDAÇÃO E VERIFICAÇÃO DE UNIDADES

> **Execute este bloco COMPLETAMENTE antes de discutir qualquer premissa.**
> Se qualquer verificação falhar, corrija os dados antes de avançar. Premissas calibradas sobre dados errados são inválidas.

### 0.1 — Copiar dados históricos do Passo 1

Transcreva os valores **exatos** do JSON do Passo 1, campo a campo. Todos os valores financeiros devem estar em **MILHÕES (R$ M)** — mesma unidade declarada em `empresa.unidade`.

| Campo | Valor do JSON Passo 1 | Unidade esperada |
|---|---|---|
| Rev_0 | | R$ milhões |
| EBIT_0 | | R$ milhões |
| Juros | | R$ milhões |
| D | | R$ milhões |
| Caixa | | R$ milhões |
| MinInt | | R$ milhões |
| PL | | R$ milhões |
| AtvNOp | | R$ milhões |
| Shares | | Milhões de ações |
| P | | R$/ação |
| MktCap | | R$ milhões |
| IR_ef | | Decimal (ex: 0.28) |

### 0.2 — Copiar parâmetros de mercado do Passo 2

| Campo | Valor do JSON Passo 2 | Unidade esperada |
|---|---|---|
| Rf | | Decimal |
| ERP | | Decimal |
| Beta_u | | Número |
| Kd_pre | | Decimal |
| IR_marg | | Decimal |
| WACC_est | | Decimal |

### 0.3 — Verificações cruzadas de integridade (TODAS devem passar antes de avançar)

```
[ ] A. MktCap_calc = P × Shares = ___ × ___ = ___ M
        MktCap do Passo 1 = ___ M
        Diferença: ___% → deve ser < 5%
        Resultado: OK | FALHOU (se falhou: verificar Shares — total vs. circulante)

[ ] B. D_liq_calc = D − Caixa = ___ − ___ = ___ M
        D_liq do Passo 1 = ___ M
        Diferença: ___% → deve ser < 2%
        Resultado: OK | FALHOU

[ ] C. Kd_pre_calc = Juros / D = ___ / ___ = ____%
        Kd_pre do Passo 2 = ____%
        São iguais (diferença < 0,1%)? → OK | DIVERGÊNCIA
        (Se divergirem: usar o Passo 2 como referência e registrar o motivo)

[ ] D. Kd_pre (___%) > Rf (___%)
        Resultado: OK | BLOQUEADOR
        (Se Kd_pre < Rf: não avançar — ver Item 2.4 do Passo 2)

[ ] E. Ratio de escala: MktCap / Rev_0 = ___ / ___ = ___×
        Referência: entre 0,3× e 15× é normal para a maioria dos setores.
        Se > 20×: PARAR — provável erro de unidade em Rev_0 ou outros dados.
        Resultado: OK (___×) | ALERTA (___× — verificar unidade de Rev_0)

[ ] F. D / MktCap = ___ / ___ = ___%
        Se D > 0 e D/MktCap < 1%: PARAR — provável erro de unidade em D.
        Resultado: OK (__%) | ALERTA (< 1% — verificar unidade de D)
```

---

## PREMISSA 3.1 — Crescimento de Receita no Ano 1 (`g1`)

**Referência histórica (do Passo 1):**
```
g_recente = Rev_0 / Rev_anterior − 1  →  ____% (calculado no Passo 1)
Crescimento divulgado no próprio release: ____%
Guidance da empresa (se mencionado no release): ____
```

**Perguntas de calibração:**
```
1. O crescimento recente é sustentável ou foi pontual (ex: aquisição, efeito base)?
2. A empresa deu guidance explícito para o próximo exercício no release?
3. Há fatores conhecidos que acelerarão ou desacelerarão o crescimento no ano 1
   (novo produto, expansão geográfica, perda de contrato, retração macro)?
```

**Decisão:**
```
g1 = ____%
Justificativa: ________________
```

---

## PREMISSA 3.2 — Crescimento de Receita Anos 2 a 5 (`g2_5`)

**Referência histórica (do Passo 1):**
```
CAGR de receita dos últimos 3–5 anos (se disponível no release): ____%
g_recente = ____%  (referência de curto prazo)
```

**Referência setorial:**
```
Taxa de crescimento médio do setor (Damodaran — Industry Averages):
  Setor: ________________
  "Annual Average Revenue Growth — Last 5 Years": ____%

Posição competitiva da empresa:
  → Se empresa cresce acima da média do setor: justificar ganho de market share
  → Se cresce abaixo: justificar perda ou segmento maduro
```

**Perguntas de calibração:**
```
1. A empresa tem capacidade instalada para crescer nessa taxa (CAPEX do Passo 1)?
2. O mercado endereçável ainda tem espaço suficiente?
3. A receita do Ano 10 implícita (Rev_0 × (1+g2_5)^5 × ...) é crível para o setor?
```

**Cálculo de referência rápida:**
```
Receita projetada Ano 5 = Rev_0 × (1 + g1) × (1 + g2_5)^4
Receita projetada Ano 5 = ____ × ____ × ____^4 = ____ M
→ Representaria ____% do mercado total estimado. Faz sentido?
```

**Decisão:**
```
g2_5 = ____%
Justificativa: ________________
```

---

## PREMISSA 3.3 — Margem EBIT no Ano 1 (`Mg_1`)

**Referência histórica (do Passo 1):**
```
Mg_atual = EBIT_0 / Rev_0 = ____%
```

**Perguntas de calibração:**
```
1. A margem atual está acima ou abaixo da margem histórica da empresa?
2. Há pressões de custo conhecidas para o próximo ano (inflação salarial, energia, insumos)?
3. Há programas de eficiência ou reestruturação que impactarão a margem?
4. A margem atual inclui itens não recorrentes que devem ser excluídos?
```

**Nota:** `Mg_1` costuma ser próxima de `Mg_atual`, a menos que haja razão clara para divergir.

**Decisão:**
```
Mg_1 = ____%
Justificativa: ________________
```

---

## PREMISSA 3.4 — Margem EBIT Alvo na Maturidade (`Mg_alvo`)

**Referência setorial:**
```
Fonte: Damodaran — Industry Averages (Global)
Setor: ________________
"Pre-tax Operating Margin (Unadjusted)": ____%

Melhor empresa comparável do setor (benchmark):
  Empresa: ________________
  Margem EBIT: ____%
```

**Perguntas de calibração:**
```
1. A empresa tem vantagens competitivas duráveis que justificam margem acima da mediana?
   (ex: pricing power, switching costs, economias de escala)
2. Há tendências estruturais de compressão de margem no setor?
3. A margem alvo implica ROIC > WACC? (necessário para criação de valor)
   → ROIC_alvo = Mg_alvo × StC  →  deve ser > WACC_0
```

**Validação rápida:**
```
ROIC_implícito = Mg_alvo × StC = ____% × ____ = ____%
WACC_0 = ____%  (do Passo 2)
Criação de valor? ROIC > WACC → ____
```

**Decisão:**
```
Mg_alvo = ____%
Justificativa: ________________
```

---

## PREMISSA 3.5 — Ano de Convergência da Margem (`Ano_conv`)

**Lógica:**
```
Define em qual ano a margem EBIT atinge Mg_alvo, partindo de Mg_1 no Ano 1.
A convergência é linear entre Ano 1 e Ano_conv.
```

**Referências para decidir:**
```
Ano_conv = 3 → empresa já próxima da maturidade, melhorias rápidas esperadas
Ano_conv = 5 → padrão Damodaran para a maioria das empresas (USAR COMO DEFAULT)
Ano_conv = 7 → empresa ainda em fase de crescimento, eficiência virá mais tarde
Ano_conv = 1 → margem já está no alvo desde o início (Mg_1 = Mg_alvo)
```

**Restrição:** `Ano_conv` deve ser entre 1 e 10.

**Decisão:**
```
Ano_conv = ____
Justificativa: ________________
```

---

## PREMISSA 3.6 — Sales-to-Capital Ratio (`StC`)

**O que é:** quantos reais de receita a empresa gera para cada real de capital investido. Mede a eficiência do crescimento.

**Referência histórica (calculada com dados do Passo 1):**
```
StC_histórico = Rev_0 / CI
CI = PL + D − Caixa = ____ + ____ − ____ = ____ M
StC_histórico = Rev_0 / CI = ____ / ____ = ____
```

**Referência setorial:**
```
Fonte: Damodaran — Industry Averages (Global)
Setor: ________________
Coluna "Sales/Capital": ____
```

**Perguntas de calibração:**
```
1. O StC histórico é representativo ou foi distorcido por algum evento (desinvestimento, aquisição)?
2. Empresas do setor têm StC crescente ou decrescente à medida que escalam?
3. Um StC maior que o setor implica crescimento mais barato — há evidência que suporte isso?
```

**Nota:** use o mesmo StC para os anos 1–10 (simplificação padrão do modelo). Só diferencie anos 1–5 e 6–10 se houver razão clara (ex: empresa em expansão intensa nos primeiros anos).

**Decisão:**
```
StC = ____
Justificativa: ________________
```

---

## PREMISSA 3.7 — Taxa de Crescimento na Perpetuidade (`g_perp`)

**O que é:** taxa à qual os fluxos de caixa crescerão para sempre após o Ano 10.

**Restrição absoluta:** `g_perp ≤ Rf`

```
Rf = ____%  (do Passo 2)
Logo: g_perp ≤ ____%
```

**Referências:**
```
Inflação de longo prazo do país: ____%
Crescimento real esperado do PIB de longo prazo: ____%
g_perp típico = inflação + crescimento real = ____%

Para o Brasil: g_perp entre 4% e 6% tem sido usual (inflação meta + crescimento modesto)
Para o EUA: g_perp entre 2% e 3%
```

**Perguntas de calibração:**
```
1. A empresa opera em setor com tendência de declínio (g_perp pode ser negativo)?
2. A empresa tem capacidade de crescer acima da economia no longo prazo?
   → Se sim, quanto acima? Justificar.
3. g_perp > Rf faz o modelo explodir — confirmar que a escolha está dentro do limite.
```

**Decisão:**
```
g_perp = ____%
Validação: g_perp (____%) ≤ Rf (____%) → OK | VIOLAÇÃO
Justificativa: ________________
```

---

## PREMISSA 3.8 — Probabilidade de Falência (`P_fail`) e Recuperação (`V_fail`)

**Quando usar P_fail > 0:**
```
→ Empresa com rating de crédito abaixo de BB
→ Empresa com dívida líquida > 5× EBITDA
→ Empresa com fluxo de caixa operacional negativo nos últimos 2+ anos
→ Empresa em setor com disrupção tecnológica iminente
```

**Como estimar (se aplicável):**
```
Fonte: tabela de probabilidade de default por rating (Damodaran)
URL: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html

Índice de cobertura de juros = EBIT_0 / Juros = ____ / ____ = ____×
Rating sintético implícito: ________________
Probabilidade de default em 10 anos (tabela): ____%
```

**Para a maioria das empresas:**
```
P_fail = 0
V_fail = 0
→ Registrar e avançar sem mais cálculos nesta seção
```

**Decisão:**
```
P_fail = ____ (decimal, ex: 0.12 para 12%)
V_fail = ____ (decimal, ex: 0.50 para 50% do valor recuperado)
Referência usada: ________________
```

---

## PREMISSA 3.9 — Opções de Funcionários (`N_opt`, `K_opt`, `T_opt`, `Sigma`)

**Quando usar:**
```
→ Apenas se o release mencionar opções de funcionários em aberto (stock options, SARs)
→ Verificar nas notas explicativas do release: "Plano de opções", "Stock Option Plan"
```

**Se não há opções:**
```
N_opt = 0  →  Valor_opcoes = 0  →  avançar
```

**Se há opções (coletar do release ou solicitar ao usuário):**
```
N_opt  = número total de opções em aberto (em milhões de ações)
K_opt  = preço médio de exercício (mesma moeda do modelo)
T_opt  = prazo médio até o vencimento (em anos)
Sigma  = desvio padrão anualizado do preço da ação (histórico — geralmente 30–60%)
         Se não disponível: usar Sigma do setor (Damodaran: "Std deviation in stock prices")
```

**Decisão:**
```
N_opt  = ____ M opções
K_opt  = ____
T_opt  = ____ anos
Sigma  = ____
```

---

## CHECKLIST DE CONSISTÊNCIA ENTRE PREMISSAS

Antes de produzir o JSON final, execute estas verificações:

**Integridade dos dados (Bloco 0):**
```
[ ] Bloco 0 executado e todas as verificações A–F passaram
[ ] Nenhum valor de dados_historicos foi alterado em relação ao Passo 1
[ ] Nenhum valor de parametros_custo_capital foi alterado em relação ao Passo 2
[ ] Kd_pre > Rf confirmado               → OK | VIOLAÇÃO
```

**Consistência entre premissas:**
```
[ ] g_perp ≤ Rf                          → OK | VIOLAÇÃO
[ ] WACC_est > g_perp                     → OK | VIOLAÇÃO
[ ] Mg_alvo × StC > WACC_0               → cria valor | destrói valor (alertar)
[ ] g1 e g2_5 são consistentes com g_recente (não mais que 2× ou metade sem justificativa)
[ ] Receita projetada no Ano 10 é crível para o tamanho do mercado
[ ] Ano_conv entre 1 e 10                 → OK | FORA DO RANGE
[ ] P_fail entre 0 e 1                    → OK | FORA DO RANGE
```

**Cálculo de referência obrigatório:**
```
Receita projetada Ano 10 = Rev_0 × (1+g1) × (1+g2_5)^4 × produto de g(t) t=6..10
Estimativa rápida (assumindo g2_5 até ano 5, g_perp a partir do 6):
  Rev_Ano5  ≈ ___ × (1+g1) × (1+g2_5)^4 = ___ M
  Rev_Ano10 ≈ ___ M (aplicar decaimento linear até g_perp)
Faz sentido para o mercado endereçável da empresa? → SIM | REVISAR
```

---

## OUTPUT DO PASSO 3 — JSON Consolidado Final

Produza o JSON abaixo **completamente preenchido** (zero nulos). Este é o input direto do Passo 4.

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
  "_INSTRUCAO_UNIDADE": "Todos os valores em dados_historicos e dados_mercado devem estar em MILHOES (R$ M). Copiar exatamente do Passo 1. Nao converter, nao arredondar, nao mudar escala.",
  "dados_historicos": {
    "Rev_0":    null,
    "EBIT_0":   null,
    "Dep":      null,
    "Juros":    null,
    "PL":       null,
    "D":        null,
    "Caixa":    null,
    "AtvNOp":   null,
    "MinInt":   null
  },
  "dados_mercado": {
    "P":        null,
    "Shares":   null,
    "MktCap":   null,
    "IR_ef":    null
  },
  "parametros_custo_capital": {
    "Rf":       null,
    "ERP":      null,
    "Beta_u":   null,
    "Kd_pre":   null,
    "IR_marg":  null,
    "WACC_est": null
  },
  "premissas_analiticas": {
    "g1":       null,
    "g2_5":     null,
    "Mg_1":     null,
    "Mg_alvo":  null,
    "Ano_conv": null,
    "StC":      null,
    "g_perp":   null,
    "P_fail":   null,
    "V_fail":   null
  },
  "opcoes_funcionarios": {
    "N_opt":    0,
    "K_opt":    0,
    "T_opt":    0,
    "Sigma":    0
  },
  "narrativa_premissas": {
    "crescimento": "...",
    "margem":      "...",
    "risco":       "...",
    "perpetuidade":"..."
  },
  "validacoes": {
    "bloco0_MktCap_vs_PxShares": null,
    "bloco0_D_liq_consistente":  null,
    "bloco0_Kd_pre_maior_Rf":    null,
    "bloco0_escala_MktCap_Rev":  null,
    "bloco0_D_MktCap_ratio":     null,
    "g_perp_menor_Rf":           null,
    "WACC_est_maior_g_perp":     null,
    "ROIC_alvo_maior_WACC":      null,
    "receita_ano10_crivel":      null,
    "campos_nulos_restantes":    [],
    "pronto_para_passo4":        false
  }
}
```

Preencha o campo `narrativa_premissas` com uma frase por bloco explicando a lógica do analista. Esse bloco acompanhará o relatório final.

Só marque `pronto_para_passo4: true` quando `campos_nulos_restantes` for uma lista vazia e todas as validações forem `true`.
