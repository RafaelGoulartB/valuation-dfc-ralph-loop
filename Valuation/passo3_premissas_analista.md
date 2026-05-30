# Passo 3 — Premissas do Analista

**Pré-requisito:** `passo1.json` e `passo2.json` completos, ambos com `pronto_para_passoN: true`.  
**Objetivo:** consolidar todos os inputs e definir as premissas futuras. Produzir `passo3.json` com zero nulos.  
**Fluxo:** para cada premissa, apresentar âncora histórica + proposta → aguardar confirmação do analista → registrar.

---

## BLOCO 0 — Consolidação e Verificação de Unidades

> **Execute este bloco completamente antes de discutir qualquer premissa.**  
> Se qualquer verificação falhar: corrigir os dados antes de avançar.

### 0.1 — Copiar dados dos passos anteriores

Transcrever os valores **exatos** dos JSONs. Não arredondar, não converter, não alterar escala.  
Todos os valores financeiros em MILHÕES (mesma unidade de `passo1.empresa.unidade`).

| Campo | Origem (campo exato no JSON) | Valor |
|---|---|---|
| Rev_0 | passo1.dre.Rev_0.valor | |
| EBIT_0 | passo1.dre.EBIT_0.valor | |
| Dep | passo1.dre.Dep.valor | |
| Juros | passo1.dre.Juros.valor | |
| PL | passo1.balanco.PL.valor | |
| D | passo1.balanco.D.valor | |
| Caixa | passo1.balanco.Caixa.valor | |
| AtvNOp | passo1.balanco.AtvNOp.valor | |
| MinInt | passo1.balanco.MinInt.valor | |
| Shares | passo1.mercado.Shares.valor | |
| P | passo1.mercado.P.valor | |
| MktCap | passo1.mercado.MktCap.valor | |
| IR_ef | passo1.dre.IR_ef.valor | |
| Rf | passo2.parametros_mercado.Rf.valor | |
| ERP | passo2.parametros_mercado.ERP.valor | |
| Beta_u | passo2.parametros_mercado.Beta_u.valor | |
| Kd_pre | passo2.parametros_mercado.Kd_pre.valor | |
| IR_marg | passo2.parametros_mercado.IR_marg.valor | |
| WACC_est | passo2.parametros_mercado.WACC_est.valor | |

### 0.2 — Verificações cruzadas (todas devem passar antes de avançar)

Calcular cada item e registrar o resultado:

```
A. MktCap_calc = P × Shares = ___ × ___ = ___ M
   MktCap do passo1 = ___ M
   Diferença: abs(MktCap_calc − MktCap_p1) / MktCap_p1 = ___%
   → OK se < 5%. Se >= 5%: verificar Shares (ex-tesouraria?) e P (data correta?)
   Resultado: OK | FALHOU

B. D_liq_calc = D − Caixa = ___ − ___ = ___ M
   D_liq do passo1 = ___ M
   Diferença: ___%
   → OK se < 2%. Se >= 2%: verificar componentes de D e Caixa
   Resultado: OK | FALHOU

C. Kd_pre (___%) vs Rf (___%)
   Kd_pre > Rf?
   → Se NÃO: BLOQUEADOR — não avançar. Ver Passo 2, item 2.4.
   Resultado: OK | BLOQUEADOR

D. Ratio de escala: MktCap_calc / Rev_0 = ___ / ___ = ___×
   → OK se entre 0,3× e 15×
   → Se > 20×: PARAR — erro de unidade em Rev_0 ou D ou Caixa. Identificar e corrigir antes de continuar.
   Resultado: OK (___×) | ALERTA

E. Se D > 0: D / MktCap_calc = ___ / ___ = ___%
   → Se < 1%: PARAR — provável erro de unidade em D.
   Resultado: OK (__%) | ALERTA
```

---

## PREMISSA 3.1 — g1 (Crescimento de Receita no Ano 1)

**Âncora:** `g_recente = ____%` (de passo1.operacional.g_recente)

Verificar no release:
- A empresa divulgou guidance de crescimento para o próximo exercício? → usar como referência primária
- O crescimento recente foi impulsionado por aquisição ou efeito de base? → ajustar para baixo se sim

**Restrição:** `g1 ≤ min(g_recente × 2, 50%)`. Crescimento mais que o dobro do recente exige justificativa explícita do analista.

```
g1 = ____%   Justificativa: ________________
```

---

## PREMISSA 3.2 — g2_5 (Crescimento Anos 2 a 5)

**Âncora:** CAGR histórico disponível no release (últimos 3–5 anos)  
**Referência setorial:** Damodaran Industry Averages — coluna "Revenue Growth (last 5 years)" do setor

Regra de calibração:
- Se a empresa cresce consistentemente acima do setor: g2_5 pode ser até setor + 3pp (com justificativa de vantagem competitiva)
- Default conservador: g2_5 = g_recente com decaimento suave até g_perp

**Restrição:** `g2_5 ≥ g_perp`

```
g2_5 = ____%   Justificativa: ________________
```

---

## PREMISSA 3.3 — Mg_1 (Margem EBIT no Ano 1)

**Âncora:** `Mg_atual = EBIT_0 / Rev_0 = ___ / ___ = ____%` (de passo1.dre.Mg_atual)

Ajustes a Mg_atual:
- Se há pressões de custo conhecidas para o próximo período (inflação salarial, insumos): reduzir levemente
- Se há programa de eficiência ou alavancagem operacional esperada: pode aumentar levemente
- Default: `Mg_1 = Mg_atual` (sem ajuste se não há razão clara)

```
Mg_1 = ____%   Justificativa: ________________
```

---

## PREMISSA 3.4 — Mg_alvo (Margem EBIT na Maturidade)

**Âncora setorial:** Damodaran Industry Averages, coluna "Pre-tax Operating Margin" do setor  
**Referência de benchmark:** margem da melhor empresa comparável do setor (se conhecida)

Regra de calibração:
- Se a empresa tem vantagens competitivas duráveis (pricing power, switching costs, escala): Mg_alvo pode ser acima da mediana setorial
- Se o setor tem pressão estrutural de margem: usar mediana ou abaixo
- Mg_alvo deve estar entre Mg_1 (improvável que margem alvo seja abaixo da atual) e melhor peer

**Validação obrigatória de criação de valor:**
```
ROIC_term = Mg_alvo × (1 − IR_marg) × StC
          = ___ × (1 − ___) × ___ = ___
WACC_est  = ___
ROIC_term > WACC_est?  →  SIM (cria valor) | NÃO (destrói valor — revisar Mg_alvo ou StC)
```
*(StC ainda não definido — calcular após definir 3.6. Voltar e validar.)*

```
Mg_alvo = ____%   Justificativa: ________________
```

---

## PREMISSA 3.5 — Ano_conv (Ano de Convergência da Margem)

Define até qual ano a margem EBIT converge linearmente de Mg_1 para Mg_alvo.

| Valor | Quando usar |
|---|---|
| 1 | Margem já está no alvo (Mg_1 = Mg_alvo) |
| 3 | Empresa próxima da maturidade, melhoria rápida |
| 5 | Default — maioria das empresas |
| 7–10 | Empresa em expansão intensa, eficiência vem tarde |

**Restrição:** `Ano_conv ∈ [1, 10]`

```
Ano_conv = ____   Justificativa: ________________
```

---

## PREMISSA 3.6 — StC (Sales-to-Capital Ratio)

**Âncora histórica:** `StC_hist = Rev_0 / CI = ___ / ___ = ___` (de passo1.operacional.StC_hist)  
**Referência setorial:** Damodaran Industry Averages, coluna "Sales/Capital"

Regra de calibração:
- Se `StC_hist` é próximo da mediana setorial: usar StC_hist como default
- Se `StC_hist` é muito diferente do setor: investigar (aquisição recente? desinvestimento?)
- Um StC alto significa crescimento barato (menos capital por real de receita) — verificar se sustentável

**Revalidar criação de valor após definir StC:**
```
ROIC_term = Mg_alvo × (1 − IR_marg) × StC = ___ × (1 − ___) × ___ = ___
WACC_est  = ___
Resultado: ROIC_term > WACC_est →  OK | Revisar Mg_alvo ou StC
```

```
StC = ____   Justificativa: ________________
```

---

## PREMISSA 3.7 — g_perp (Crescimento na Perpetuidade)

**Restrição absoluta:** `g_perp < Rf`. Se `g_perp ≥ Rf`, o modelo explode (valor infinito). Não aceitar.

Referências:
- Brasil: inflação de longo prazo (~4%) + crescimento real do PIB (~1–2%) → g_perp entre 4% e 6%
- EUA: ~2% a 3%
- Setor em declínio estrutural: g_perp pode ser 0% ou negativo

**Validação:**
```
g_perp = ____%
Rf     = ____%
g_perp < Rf?  →  OK | VIOLAÇÃO (não aceitar — reduzir g_perp)

WACC_est (___%) > g_perp (___%)?  →  OK | VIOLAÇÃO
```

```
g_perp = ____%   Justificativa: ________________
```

---

## PREMISSA 3.8 — P_fail e V_fail (Ajuste de Falência)

Para a maioria das empresas: `P_fail = 0` e `V_fail = 0`. Avançar se for o caso.

Usar P_fail > 0 se pelo menos um dos seguintes:
- `D / EBITDA_0 > 5×` → calcular: ___ / ___ = ___× → `P_fail = 0` | considerar
- FCO negativo por 2+ anos consecutivos
- Rating implícito < BB (calcular cobertura: `EBIT_0 / Juros = ___ / ___ = ___×`)

Se aplicável:
1. Consultar `Valuation/data/ratings.md` com o índice de cobertura EBIT/Juros
2. Identificar rating sintético
3. Localizar probabilidade de default em 10 anos (tabela Damodaran)
4. `V_fail` = fração do valor recuperado em liquidação (tipicamente 0,20 a 0,50)

```
D / EBITDA_0 = ___ / ___ = ___×   (EBITDA_0 = passo1.dre.EBITDA.valor)
EBIT_0 / Juros = ___ / ___ = ___×  (cobertura de juros)
P_fail = ____   V_fail = ____   Justificativa: ________________
```

---

## PREMISSA 3.9 — Opções de Funcionários

Verificar no release: há menção de "Plano de Opções", "Stock Options", "SARs" em aberto?
- **Não há:** `N_opt = 0, K_opt = 0, T_opt = 0, Sigma = 0` → avançar
- **Há opções:** coletar do release ou solicitar ao usuário:
  - `N_opt` = total de opções em aberto (em milhões de ações)
  - `K_opt` = preço médio de exercício (em R$)
  - `T_opt` = prazo médio até o vencimento (em anos)
  - `Sigma` = volatilidade anualizada do preço da ação (se não disponível: buscar no Damodaran "Std deviation in stock prices" do setor)

---

## Checklist de Saída

```
[ ] Bloco 0 completo — verificações A, B, C, D, E passaram
[ ] g_perp < Rf
[ ] WACC_est > g_perp
[ ] ROIC_term = Mg_alvo × (1 − IR_marg) × StC > WACC_est  (ou alerta registrado)
[ ] g1 ≤ g_recente × 2  (ou justificativa registrada)
[ ] g2_5 ≥ g_perp
[ ] Ano_conv ∈ [1, 10]
[ ] P_fail ∈ [0, 1]
[ ] campos_nulos_restantes = []
[ ] pronto_para_passo4: true
```

---

## JSON de Saída

```json
{
  "empresa": {
    "nome": "", "ticker": "", "pais": "", "setor": "", "moeda": "BRL", "unidade": "milhões"
  },
  "dados_historicos": {
    "Rev_0": null, "EBIT_0": null, "Dep": null, "Juros": null,
    "PL": null, "D": null, "Caixa": null, "AtvNOp": null, "MinInt": null
  },
  "dados_mercado": {
    "P": null, "Shares": null, "MktCap": null, "IR_ef": null
  },
  "parametros_custo_capital": {
    "Rf": null, "ERP": null, "Beta_u": null,
    "Kd_pre": null, "IR_marg": null, "WACC_est": null
  },
  "premissas_analiticas": {
    "g1": null, "g2_5": null, "Mg_1": null, "Mg_alvo": null,
    "Ano_conv": null, "StC": null, "g_perp": null, "P_fail": null, "V_fail": null
  },
  "opcoes_funcionarios": {
    "N_opt": 0, "K_opt": 0, "T_opt": 0, "Sigma": 0
  },
  "narrativa_premissas": {
    "crescimento": "",
    "margem": "",
    "risco": "",
    "perpetuidade": ""
  },
  "validacoes": {
    "bloco0_MktCap_PxShares": null,
    "bloco0_D_liq": null,
    "bloco0_Kd_pre_Rf": null,
    "bloco0_escala": null,
    "bloco0_D_MktCap": null,
    "g_perp_menor_Rf": null,
    "WACC_est_maior_g_perp": null,
    "ROIC_alvo_maior_WACC": null,
    "campos_nulos_restantes": [],
    "pronto_para_passo4": false
  }
}
```
