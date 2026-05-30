# Passo 2 — Coleta de Parâmetros de Mercado

> **Pré-requisito:** o JSON do Passo 1 deve estar completo, com `Rev_0`, `EBIT_0`, `Juros`, `D`, `Caixa`, `PL`, `Shares`, `P`, `IR_ef`, e os campos `empresa.pais` e `empresa.setor` preenchidos.
> Se qualquer um desses campos estiver nulo, volte ao Passo 1 antes de continuar.

**Objetivo:** coletar os 6 parâmetros externos que não existem no release de resultados e que são necessários para calcular o WACC. Ao final, produzir o JSON do Passo 2 com todos os campos preenchidos e zero nulos.

---

## REGRA DE OURO DESTE PASSO

Nenhum parâmetro desta seção deve ser inventado ou estimado sem fonte. Para cada item:
1. Indique a fonte exata (URL, base de dados, data de consulta)
2. Indique se o valor é da data da avaliação ou o mais recente disponível
3. Se não conseguir obter o valor, marque como `PENDENTE` e solicite ao usuário — nunca use um placeholder silencioso

---

## ITEM 2.1 — Taxa Livre de Risco (`Rf`)

**O que é:** yield do título soberano de longo prazo (10 anos) do país de referência da avaliação.

**Como obter:**

```
1. Identificar o país do modelo (campo empresa.pais do JSON do Passo 1)
2. Para Brasil: usar a taxa do NTN-B 2035 (IPCA+) ou a ETTJ de 10 anos da ANBIMA
   → Fonte: https://www.anbima.com.br/pt_br/informar/taxas-e-indices/
   → Alternativa: usar a Selic esperada de longo prazo (Focus/BCB)
3. Para EUA: usar o yield do Treasury de 10 anos
   → Fonte: https://fred.stlouisfed.org (série DGS10)
4. Para outros países: buscar o yield do título soberano local de 10 anos
```

**Anotações obrigatórias:**
```
Rf = ____%
Fonte: ________________
Data de consulta: ________
Observação: ________________ (ex: taxa nominal ou real? em qual moeda?)
```

**Atenção:** se a avaliação for feita em moeda local (ex: BRL), use Rf em BRL. Se for em USD, use Rf em USD. O WACC deve ser calculado na mesma moeda dos fluxos de caixa.

---

## ITEM 2.2 — Prêmio de Risco de Equity do País (`ERP`)

**O que é:** retorno adicional exigido pelos investidores em equity em relação ao título livre de risco, já incorporando o risco-país.

**Como obter:**

```
Fonte primária: base de dados do Prof. Damodaran (NYU)
IMPORTANT: Verifique na pasta Valuation/data/country-default-spreads-and-risk-premiums.md

Procedimento:
1. Acessar a tabela "Country Risk Premiums" (atualizada em janeiro de cada ano)
2. Localizar o país do campo empresa.pais
3. Copiar o valor da coluna "Equity Risk Premium" (ERP total, não apenas o CRP)

Se o país não estiver listado individualmente:
→ Usar o ERP da região correspondente (ex: Latin America)
→ Registrar que foi usado o valor regional e não o específico do país
```

**Anotações obrigatórias:**
```
ERP = ____%
País consultado: ________________
Fonte: Damodaran — Country Risk Premiums
Data da tabela (ano de referência): ________
Coluna utilizada: "Equity Risk Premium"
```

---

## ITEM 2.3 — Beta Desalavancado do Setor (`Beta_u`)

**O que é:** medida de risco operacional do setor, sem o efeito da alavancagem financeira da empresa específica.

**Como obter:**

```
Fonte primária: base de dados do Prof. Damodaran (NYU)
IMPORTANT: Verifique na pasta Valuation/data/beta-by-sector.md

Procedimento:
1. Acessar a tabela "Betas by Sector (Global)"
2. Localizar o setor correspondente ao campo empresa.setor do JSON do Passo 1
3. Copiar o valor da coluna "Unlevered Beta (corrected for cash)"
   → Esta coluna já remove o efeito do caixa e da alavancagem

Se o setor não tiver correspondência exata:
→ Usar o setor mais próximo e registrar a justificativa
→ Alternativa: usar a média ponderada de dois setores se a empresa for diversificada
```

**Anotações obrigatórias:**
```
Beta_u = _____
Setor consultado na tabela: ________________
Setor da empresa (JSON Passo 1): ________________
Fonte: Damodaran — Betas by Sector (Global)
Data da tabela (ano de referência): ________
Coluna utilizada: "Unlevered Beta (corrected for cash)"
Observação: ________________ (ex: setor exato ou aproximação?)
```

---

## ITEM 2.4 — Custo Pré-Imposto da Dívida (`Kd_pre`)

**O que é:** taxa de juros efetiva que a empresa paga sobre sua dívida financeira.

**Como calcular (dados já disponíveis do Passo 1):**

```
Kd_pre = Juros / D

Onde:
  Juros = despesa com juros (campo dre.Juros do JSON do Passo 1)
  D     = dívida financeira total (campo balanco.D do JSON do Passo 1)
```

**CÁLCULO OBRIGATÓRIO — mostrar os números reais antes de registrar:**

```
Juros (do Passo 1) = ___ M   ← copiar de dre.Juros
D     (do Passo 1) = ___ M   ← copiar de balanco.D
Kd_pre = ___ / ___ = ____%

Rf (do Item 2.1)   = ____%
Kd_pre > Rf?       → SIM | NÃO
```

**Verificações:**

```
SE Kd_pre < Rf:
  → BLOQUEADOR — não avançar para o Passo 3.
    O custo da dívida abaixo da taxa livre de risco é financeiramente impossível
    em condições normais de mercado.
  → Verificar OBRIGATORIAMENTE (em ordem):
    1. Os valores de Juros e D foram copiados corretamente do Passo 1?
       (Confirmar que ambos estão em MILHÕES — mesma unidade)
    2. O campo Juros inclui APENAS juros de dívida financeira?
       (Excluir: variação cambial, multas, juros sobre impostos, resultado de hedge)
    3. O campo D inclui dívida completa (curto prazo + longo prazo)?
    4. Se a empresa tem benefício fiscal de dívida subsidiada (ex: BNDES),
       registrar explicitamente e exigir confirmação do usuário antes de avançar.

SE Kd_pre > Rf + 10%:
  → Empresa pode estar em situação de stress. Verificar rating de crédito.
  → Registrar como alerta para o Passo 3 (premissas de falência).

SE D = 0:
  → Empresa sem dívida. Kd_pre = Rf (convenção). W_debt = 0. WACC = Ke.
```

**Alternativa se Juros não estiver disponível no Passo 1:**

```
Opção A: buscar o custo médio ponderado da dívida no release (às vezes divulgado)
Opção B: usar rating sintético de Damodaran
  FILE: Verifique na pasta Valuation/data/ratings.md
  → Calcular índice de cobertura de juros: EBIT / Juros
  → Localizar o spread correspondente na tabela
  → Kd_pre = Rf + Spread
```

**Anotações obrigatórias:**
```
Juros_passo1 = ___ M   (de dre.Juros do JSON Passo 1)
D_passo1     = ___ M   (de balanco.D do JSON Passo 1)
Kd_pre       = ___ / ___ = ____%
Método: Juros/D | Rating sintético | Divulgado no release
Índice de cobertura (EBIT/Juros): _____ × (registrar para referência do Passo 3)
Kd_pre > Rf? → SIM | NÃO  (se NÃO: ver bloqueador acima)
Observações: ________________
```

---

## ITEM 2.5 — Alíquota Marginal de IR (`IR_marg`)

**O que é:** alíquota máxima legal de imposto de renda corporativo do país, aplicada ao lucro operacional na maturidade da empresa.

**Como obter:**

```
Não está no release de resultados. Fontes:

Verifique na pasta Valuation/data/country-default-spreads-and-risk-premiums.md Tem uma tabela com a Corporate Tax Rate de cada pais

Brasil:
  IRPJ = 15% + Adicional de 10% (sobre lucro > R$240k/ano) = 25%
  CSLL = 9% (empresas em geral) ou 20% (instituições financeiras)
  IR_marg = 34% (25% IRPJ + 9% CSLL) — padrão para empresas não financeiras brasileiras

EUA:
  IR_marg = 21% (federal) + média estadual ≈ 25% efetivo
```

**Atenção:** diferenciar de `IR_ef` (alíquota efetiva atual, extraída do release no Passo 1). `IR_marg` é a alíquota legal que a empresa vai pagar na maturidade, quando todos os benefícios fiscais temporários tiverem se esgotado.

**Anotações obrigatórias:**
```
IR_marg = ____%
País: ________________
Composição: ________________ (ex: 25% IRPJ + 9% CSLL = 34%)
Fonte: ________________
```

---

## ITEM 2.6 — WACC Estável na Maturidade (`WACC_est`)

**O que é:** custo de capital que a empresa terá quando atingir maturidade (após o ano 10). Reflete o risco de uma empresa madura e estável no setor.

**Como calcular (padrão Damodaran):**

```
WACC_est = Rf + 4,5%

Onde 4,5% é o prêmio de risco médio de uma empresa madura (beta ≈ 1, sem risco-país adicional).
```

**Quando sobrescrever o padrão:**

```
SE a empresa opera em setor de altíssimo risco regulatório ou cíclico:
  → Aumentar para Rf + 5,0% a Rf + 6,0%

SE a empresa será adquirida por uma grande corporação diversificada:
  → Pode-se reduzir para Rf + 3,5%

SE o usuário tiver uma estimativa própria:
  → Usar o valor fornecido e registrar a justificativa
```

**Validação obrigatória:**

```
WACC_est deve ser > g_perp (definida no Passo 3)
Se WACC_est = 10,8% e g_perp = 4%, o denominador do VT = 6,8% ✓
Se WACC_est ≤ g_perp, o modelo explode → alertar imediatamente
```

**Anotações obrigatórias:**
```
WACC_est = ____%
Método: Rf + 4,5% (padrão) | Sobrescrito pelo analista
Rf utilizado: ____%
Justificativa (se sobrescrito): ________________
```

---

## OUTPUT DO PASSO 2 — JSON Complementar

Ao final, produza o bloco JSON abaixo com todos os campos preenchidos. Cole ao lado do JSON do Passo 1 — eles serão mesclados no início do Passo 3.

Salvar json em pasta Acoes/:ticker/:passo.json

```json
{
  "parametros_mercado": {
    "Rf": {
      "valor": null,
      "unidade": "decimal (ex: 0.06575)",
      "fonte": "...",
      "data_consulta": "YYYY-MM-DD",
      "moeda": "BRL | USD | EUR | ..."
    },
    "ERP": {
      "valor": null,
      "unidade": "decimal",
      "fonte": "Damodaran — Country Risk Premiums",
      "pais_consultado": "...",
      "ano_tabela": null
    },
    "Beta_u": {
      "valor": null,
      "fonte": "Damodaran — Betas by Sector Global",
      "setor_consultado": "...",
      "coluna": "Unlevered Beta corrected for cash",
      "ano_tabela": null
    },
    "Kd_pre": {
      "valor": null,
      "unidade": "decimal",
      "metodo": "Juros/D | Rating sintético | Divulgado",
      "juros_usados": null,
      "D_usada": null
    },
    "IR_marg": {
      "valor": null,
      "unidade": "decimal (ex: 0.34)",
      "pais": "...",
      "composicao": "..."
    },
    "WACC_est": {
      "valor": null,
      "unidade": "decimal",
      "metodo": "Rf + 4.5% padrão | Sobrescrito",
      "justificativa": "..."
    }
  },
  "status_passo2": {
    "campos_nulos": [],
    "alertas": [],
    "pronto_para_passo3": false
  }
}
```

---

## CHECKLIST DE SAÍDA

Antes de declarar o Passo 2 completo, confirme:

```
[ ] Rf preenchido com fonte e data de consulta
[ ] ERP preenchido com fonte Damodaran e ano da tabela
[ ] Beta_u preenchido com setor correto identificado
[ ] Kd_pre calculado ou obtido, com método registrado
[ ] IR_marg definido com composição detalhada
[ ] WACC_est definido e validado (> g_perp esperado)
[ ] Nenhum campo nulo no bloco parametros_mercado
[ ] status_passo2.pronto_para_passo3 = true
```

Se qualquer item estiver incompleto: registrar em `status_passo2.alertas`, marcar `pronto_para_passo3: false` e solicitar ao usuário antes de avançar.
