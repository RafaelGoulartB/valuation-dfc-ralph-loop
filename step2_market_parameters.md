# Passo 2 — Parâmetros de Mercado

**Pré-requisito:** `step1.json` completo, sem campos PENDENTE nos blocos dre/balanco/mercado.  
**Objetivo:** coletar os 6 parâmetros externos para calcular o WACC.  
**Regra:** nenhum valor estimado sem fonte. Se não conseguir obter: marcar `PENDENTE` e solicitar ao usuário.

---

## 2.1 — Rf (Taxa Livre de Risco)

**Brasil:** buscar o yield da NTN-B 2035 (IPCA+ longo prazo) no site da ANBIMA.  
Usar a taxa nominal (IPCA + prêmio real), expressa em decimal (ex: 0,1453 para 14,53%).  
Registrar a data de consulta — o yield muda diariamente.

**EUA:** yield do Treasury 10Y (fonte: FRED, série DGS10), em decimal.

**Atenção:** Rf deve estar na mesma moeda que os fluxos de caixa do modelo (BRL para empresas brasileiras).

```
Rf = ____   Fonte: ________________   Data: ________
```

---

## 2.2 — ERP (Prêmio de Risco de Equity)

Fonte: arquivo `Valuation/data/country-default-spreads-and-risk-premiums.md`

Procedimento:
1. Localizar o país de `empresa.pais` do step1.json
2. Copiar o valor da coluna **"Equity Risk Premium"** (ERP total = base EUA + Country Risk Premium)
3. Se o país não estiver listado individualmente: usar o ERP da região (ex: "Latin America")

```
ERP = ____   País consultado: ________________   Ano da tabela: ____
```

---

## 2.3 — Beta_u (Beta Desalavancado do Setor)

Fonte: arquivo `Valuation/data/beta-by-sector.md`

Procedimento:
1. Identificar o setor em `empresa.setor` do step1.json
2. Localizar o setor mais próximo na tabela
3. Copiar o valor da coluna **"Unlevered Beta corrected for cash"**
4. Se não houver correspondência exata: registrar o setor usado e a justificativa

```
Beta_u = ____   Setor consultado: ________________   Setor da empresa: ________________
```

---

## 2.4 — Kd_pre (Custo Pré-Imposto da Dívida)

**Cálculo principal** (usar os valores do step1.json):

```
Juros = passo1.dre.Juros.valor  = ___ M
D     = passo1.balanco.D.valor  = ___ M
Kd_pre = Juros / D = ___ / ___ = ____%
```

**Verificação obrigatória — comparar com Rf:**

```
Rf = ____%   (do item 2.1)
Kd_pre (___%) > Rf (___%) ?   →   SIM | NÃO
```

**SE Kd_pre < Rf → BLOQUEADOR. Não avançar ao Passo 3.**

Verificar nesta ordem antes de aceitar:
1. O campo `Juros` inclui apenas juros sobre dívida financeira? (excluir variação cambial, multas, hedge)
2. O campo `D` inclui dívida completa (curto + longo prazo)?
3. Os dois valores estão em MILHÕES (mesma unidade)?
4. Se após correção ainda Kd_pre < Rf: registrar o alerta, apresentar ao usuário e aguardar confirmação antes de avançar.

**Alternativa se `Juros` não estiver disponível no passo1:**
- Usar `Valuation/data/ratings.md`: calcular índice de cobertura `EBIT_0 / Juros`
- Localizar o rating sintético e spread correspondente
- `Kd_pre = Rf + spread`

```
Kd_pre = ____%
Método usado: Juros/D | Rating sintético | Divulgado no release
Kd_pre > Rf: SIM | NÃO (se NÃO: ver bloqueador acima)
```

---

## 2.5 — IR_marg (Alíquota Marginal de IR)

Esta é a alíquota legal máxima — diferente de `IR_ef` (efetiva atual do passo1).

| País | IR_marg | Composição |
|---|---|---|
| Brasil (não-financeiro) | 0,34 | 25% IRPJ + 9% CSLL |
| Brasil (financeiro) | 0,45 | 25% IRPJ + 20% CSLL |
| EUA | 0,25 | federal + média estadual |
| Outros | — | `Valuation/data/country-default-spreads-and-risk-premiums.md`, coluna "Corporate Tax Rate" |

```
IR_marg = ____   Composição: ________________
```

---

## 2.6 — WACC_est (WACC na Maturidade)

Fórmula padrão Damodaran (empresa madura, beta ≈ 1, sem risco-país adicional):

```
WACC_est = Rf + 0,045
```

Ajustes ao padrão:
- Setor de alto risco regulatório ou muito cíclico: adicionar +0,5 a +1,5 p.p.
- Setor de baixo risco (utilities reguladas, concessões): pode reduzir −0,5 p.p.
- Se o usuário fornecer uma estimativa própria: usar o valor do usuário e registrar justificativa.

**Validação:** `WACC_est > g_perp` (verificar no Passo 3 quando g_perp for definida).

```
WACC_est = Rf + 0,045 = ____ + 0,045 = ____
Método: Rf+4,5% padrão | Ajustado | Fornecido pelo usuário
Justificativa (se ajustado): ________________
```

---

## JSON de saída

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

**Gate:** `pronto_para_passo3: true` somente quando:
- Todos os 6 campos preenchidos (sem null)
- `Kd_pre > Rf` confirmado
- `status_passo2.campos_nulos = []`
