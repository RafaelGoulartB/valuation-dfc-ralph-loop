# Pipeline de Valuation DCF — Índice e Regras de Transição

> Este arquivo mapeia todos os documentos do pipeline e define as regras de entrada e saída de cada passo. Leia este arquivo primeiro antes de iniciar qualquer passo.

---

## Arquivos do Pipeline

| Arquivo | Passo | Função | Input | Output |
|---|---|---|---|---|
| `step1_release_extraction.md` | 1 | Extrair dados do PDF do release | PDF do release | JSON parcial + tabela de lacunas |
| `step2_market_parameters.md` | 2 | Coletar parâmetros externos (Rf, ERP, Beta, IR_marg) | JSON do Passo 1 + fontes de mercado | JSON complementar de mercado |
| `step3_analyst_assumptions.md` | 3 | Definir premissas futuras com o analista | JSONs dos Passos 1 e 2 | JSON consolidado final (todos os inputs) |
| `step4_dcf_calculation.md` | 4 | Executar todos os cálculos DCF | JSON do Passo 3 | Tabelas + valor por ação + diagnóstico |
| `step5_sensitivity_scenarios.md` | 5 *(opcional)* | Análise de sensibilidade e cenários | Resultado do Passo 4 | Matrizes + cenários + conclusão |
| `dcf_valuation_llm_instructions.md` | Referência | Fórmulas completas do modelo | — | Consulta durante o Passo 4 |

---

## Fluxo do Pipeline

```
[PDF do Release de Resultados]
            │
            ▼
┌───────────────────────┐
│  PASSO 1              │  Lê o PDF. Extrai dados históricos.
│  Extração do Release  │  Identifica o que falta.
│                       │
│  Output: JSON parcial │
│  + tabela de lacunas  │
└──────────┬────────────┘
           │  Gate: todos os campos históricos preenchidos ou marcados como PENDENTE
           ▼
┌───────────────────────┐
│  PASSO 2              │  Busca Rf, ERP, Beta_u, IR_marg, Kd_pre, WACC_est.
│  Parâmetros de        │  Um item de cada vez. Registra fonte de cada um.
│  Mercado              │
│                       │
│  Output: JSON         │
│  complementar         │
└──────────┬────────────┘
           │  Gate: zero campos nulos no bloco parametros_mercado
           ▼
┌───────────────────────┐
│  PASSO 3              │  Para cada premissa: apresenta referência histórica
│  Premissas do         │  e setorial → analista decide → registra no JSON.
│  Analista             │  Valida consistência entre premissas ao final.
│                       │
│  Output: JSON         │
│  consolidado final    │
│  (zero nulos)         │
└──────────┬────────────┘
           │  Gate: pronto_para_passo4 = true
           ▼
┌───────────────────────┐
│  PASSO 4              │  Executa Blocos A → B → C → D → E → F.
│  Cálculo DCF          │  Preenche tabelas intermediárias.
│                       │  Executa checklist de verificação.
│  Output: valor por    │
│  ação + diagnóstico   │
└──────────┬────────────┘
           │  (opcional)
           ▼
┌───────────────────────┐
│  PASSO 5              │  Matrizes de sensibilidade.
│  Sensibilidade        │  Breakevens por premissa.
│  e Cenários           │  Cenários Bear / Base / Bull.
│                       │  Conclusão narrativa.
└───────────────────────┘
```

---

## Regra de Transição (válida para todos os passos)

```
Só avance para o próximo passo quando:

1. O JSON de saída do passo atual tiver ZERO campos nulos
   nos blocos que aquele passo é responsável por preencher.

2. O campo de status do passo atual estiver marcado como true:
   Passo 1: (verificar manualmente — não há flag automático)
   Passo 2: status_passo2.pronto_para_passo3 = true
   Passo 3: validacoes.pronto_para_passo4 = true
   Passo 4: checklist de verificação sem falhas

3. Se houver campos PENDENTE (não encontrados no release),
   o usuário deve fornecê-los explicitamente antes do avanço.
   A LLM não deve inventar ou aproximar valores silenciosamente.
```

---

## O que cada passo NÃO faz

| Passo | Não faz |
|---|---|
| Passo 1 | Não define premissas. Não busca dados de mercado. Não calcula WACC. |
| Passo 2 | Não define premissas do analista. Não projeta receitas. Não calcula FCFF. |
| Passo 3 | Não re-extrai dados do release. Não executa cálculos do modelo. |
| Passo 4 | Não redefine premissas. Não busca dados externos. Não faz análise de sensibilidade. |
| Passo 5 | Não altera o valor base. Não substitui o Passo 4. |

---

## JSON Acumulado por Passo

O JSON cresce a cada passo. Ao iniciar um passo, sempre começar com o JSON completo do passo anterior.

```
Início Passo 2: JSON do Passo 1 (dados históricos + mercado)
Início Passo 3: JSON do Passo 1 + JSON do Passo 2 (+ parâmetros de mercado)
Início Passo 4: JSON consolidado do Passo 3 (todos os inputs)
Início Passo 5: resultado numérico do Passo 4 (valor_acao, VP_total, VP_VT, Fator_10)
```

---

## Tempo Estimado por Passo

| Passo | Complexidade | Bloqueadores comuns |
|---|---|---|
| Passo 1 | Baixa–Média | Release mal formatado, dados trimestrais sem LTM |
| Passo 2 | Baixa | Acesso às tabelas Damodaran, definir IR_marg do país |
| Passo 3 | Alta | Decisões do analista — requer diálogo e justificativas |
| Passo 4 | Média | Nenhum se o JSON do Passo 3 estiver correto |
| Passo 5 | Média | Volume de cálculos nas matrizes |
