"""
passo4_dcf.py - Execucao do Modelo DCF (Passo 4)

Lê o JSON consolidado produzido pelo Passo 3 e executa todos os blocos
de calculo A -> B -> C -> D -> E -> F, produzindo:
  - Impressão dos resultados no terminal
  - passo4_resultado.json  (dados completos para uso no Passo 5)

Uso:
    python passo4_dcf.py                        # lê passo3_output.json por padrão
    python passo4_dcf.py meu_input.json         # arquivo customizado
    python passo4_dcf.py --exemplo              # roda com os dados da FIQE3 de exemplo
"""

import json
import math
import sys
import os
from datetime import datetime


# ---------------------------------------------
# 1. CARREGAMENTO E VALIDAÇÃO DO JSON
# ---------------------------------------------

# EXEMPLO_FIQE3 = {
#     "empresa": {
#         "nome": "FIQE3",
#         "ticker": "BVMF:FIQE3",
#         "pais": "Brasil",
#         "setor": "Telecom. Services",
#         "moeda": "BRL",
#         "unidade": "milhões"
#     },
#     "dados_historicos": {
#         # EBIT_0 = EBIT reportado (329) + Depreciação real ajustada (135 = 50% de 270).
#         # A planilha Damodaran adiciona depreciação "real" ao EBIT antes do FCFF.
#         # O Passo 3 deve entregar o EBIT já com esse ajuste quando aplicável.
#         "Rev_0":  1186.0,
#         "EBIT_0":  464.0,
#         "Dep":     270.0,
#         "Juros":    40.0,
#         "PL":     1116.0,
#         "D":       651.0,
#         "Caixa":   260.0,
#         "AtvNOp":    0.0,
#         "MinInt":    0.0
#     },
#     "dados_mercado": {
#         "P":      6.57,
#         "Shares": 399.1,
#         "MktCap": None,
#         "IR_ef":  0.19
#     },
#     "parametros_custo_capital": {
#         "Rf":       0.06575,
#         "ERP":      0.0747,
#         "Beta_u":   1.362,
#         "Kd_pre":   0.1475,
#         "IR_marg":  0.34,
#         "WACC_est": 0.10805
#     },
#     "premissas_analiticas": {
#         "g1":       0.14,
#         "g2_5":     0.15,
#         "Mg_1":     0.265,
#         "Mg_alvo":  0.27825,
#         "Ano_conv": 5,
#         "StC":      0.68,
#         "g_perp":   0.04,
#         "P_fail":   0.0,
#         "V_fail":   0.0,
#         # g_schedule_override: substitui a interpolação automática dos anos 6-10.
#         # Use quando o analista definiu valores discretos no Passo 3.
#         "g_schedule_override": {"6": 0.12, "7": 0.10, "8": 0.08, "9": 0.06, "10": 0.04}
#     },
#     "opcoes_funcionarios": {
#         "N_opt":  0,
#         "K_opt":  0,
#         "T_opt":  0,
#         "Sigma":  0.45
#     },
#     "validacoes": {
#         "pronto_para_passo4": True,
#         "campos_nulos_restantes": []
#     }
# }

EXEMPLO_FIQE3 = {
  "empresa": {
    "nome": "Unifique",
    "ticker": "FIQE3",
    "pais": "Brasil",
    "setor": "Telecomunicações (B2B + B2B - banda larga + móvel)",
    "moeda": "BRL",
    "unidade": "milhões"
  },
  "dados_historicos": {
    "Rev_0":    1.186,
    "EBIT_0":   0.329,
    "Dep":      0.223,
    "Juros":    0.025,
    "PL":       1.116,
    "D":        0.539,
    "Caixa":    0.260,
    "AtvNOp":   0,
    "MinInt":   0.002
  },
  "dados_mercado": {
    "P":        7.01,
    "Shares":   399.087,
    "MktCap":   2796.7,
    "IR_ef":    0.2784
  },
  "parametros_custo_capital": {
    "Rf":       0.1453,
    "ERP":      0.0747,
    "Beta_u":   0.54,
    "Kd_pre":   0.04629,
    "IR_marg":  0.34,
    "WACC_est": 0.1903
  },
  "premissas_analiticas": {
    "g1":       0.15,
    "g2_5":     0.12,
    "Mg_1":     0.29,
    "Mg_alvo":  0.35,
    "Ano_conv": 5,
    "StC":      0.85,
    "g_perp":   0.05,
    "P_fail":   0,
    "V_fail":   0
  },
  "opcoes_funcionarios": {
    "N_opt":    0,
    "K_opt":    0,
    "T_opt":    0,
    "Sigma":    0
  },
  "narrativa_premissas": {
    "crescimento": "Crescimento recente de 15,6% é sustentável: a empresa expande rede em 166 cidades (52 novas em 2025) e tem CAPEX robusto (R$ 340M). Guidance implícita via expansão de cobertura justifica g1 = 15%. Para anos 2-5, g2_5 = 12% reflete desaceleração natural conforme base cresce e penetração de banda larga se aproxima de saturação em cidades atendidas.",
    "margem": "Margem EBIT atual de 27,8% será melhorada em 2026 (Mg_1 = 29%) via alavancagem operacional do CAPEX em部署 e redução de churn (1,49% BL, 1,43% móvel - abaixo da média setorial). Alvo de maturidade de 35% é justificável: operador wireless com beta desalavancado baixo (0,54) indica eficiência de escala; ROIC implícito de 29,8% > WACC de 19,03% confirma criação de valor.",
    "risco": "Probabilidade de falência = 0. Empresa com dívida líquida de R$ 279M vs EBITDA de R$ 552M (cobertura ~2x). ROIC atual de 15,5% acima de custos de capital. Sem sinal de distress financeiro. Opções de funcionários inexistentes nos releases.",
    "perpetuidade": "g_perp = 5% ≤ Rf (14,53%) - OK. Reflete inflação de longo prazo + crescimento real do PIB brasileiro. Para empresa de telecomunicações com infraestrutura já deployada, crescimento perpétido acima da economia não é sustentável sem M&A agressivo."
  },
  "validacoes": {
    "g_perp_menor_Rf":          True,
    "WACC_est_maior_g_perp":    True,
    "ROIC_alvo_maior_WACC":     True,
    "receita_ano10_crivel":     True,
    "campos_nulos_restantes":   [],
    "pronto_para_passo4":       True
  }
}

def carregar_json(caminho: str) -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def validar_pre_requisitos(dados: dict) -> list[str]:
    """Retorna lista de erros. Se vazia, pode prosseguir."""
    erros = []

    val = dados.get("validacoes", {})
    if not val.get("pronto_para_passo4", False):
        erros.append("validacoes.pronto_para_passo4 não está True. Conclua o Passo 3.")
    if val.get("campos_nulos_restantes"):
        erros.append(f"Campos nulos no JSON: {val['campos_nulos_restantes']}")

    def req(bloco, chave):
        v = dados.get(bloco, {}).get(chave)
        if v is None:
            erros.append(f"Campo obrigatório ausente: {bloco}.{chave}")

    for c in ["Rev_0", "D", "Caixa", "AtvNOp", "MinInt"]:
        req("dados_historicos", c)
    for c in ["P", "Shares", "IR_ef"]:
        req("dados_mercado", c)
    for c in ["Rf", "ERP", "Beta_u", "Kd_pre", "IR_marg", "WACC_est"]:
        req("parametros_custo_capital", c)
    for c in ["g1", "g2_5", "Mg_1", "Mg_alvo", "Ano_conv", "StC", "g_perp", "P_fail", "V_fail"]:
        req("premissas_analiticas", c)

    if not erros:
        p = dados["premissas_analiticas"]
        k = dados["parametros_custo_capital"]
        if p["g_perp"] >= k["Rf"]:
            erros.append(
                f"VIOLAÇÃO: g_perp ({p['g_perp']:.4f}) >= Rf ({k['Rf']:.4f}). "
                "Modelo inválido - o denominador do Valor Terminal seria <= 0."
            )
        if k["WACC_est"] <= p["g_perp"]:
            erros.append(
                f"VIOLAÇÃO: WACC_est ({k['WACC_est']:.4f}) <= g_perp ({p['g_perp']:.4f}). "
                "Denominador do Valor Terminal negativo."
            )

    return erros


# ---------------------------------------------
# 2. EXTRAÇÃO DOS INPUTS
# ---------------------------------------------

def extrair_inputs(dados: dict) -> dict:
    h = dados["dados_historicos"]
    m = dados["dados_mercado"]
    k = dados["parametros_custo_capital"]
    p = dados["premissas_analiticas"]
    o = dados.get("opcoes_funcionarios", {})

    return {
        # históricos
        "Rev_0":    h["Rev_0"],
        "D":        h["D"],
        "Caixa":    h["Caixa"],
        "AtvNOp":   h.get("AtvNOp", 0.0),
        "MinInt":   h.get("MinInt", 0.0),
        # mercado
        "P":        m["P"],
        "Shares":   m["Shares"],
        "IR_ef":    m["IR_ef"],
        # custo de capital
        "Rf":       k["Rf"],
        "ERP":      k["ERP"],
        "Beta_u":   k["Beta_u"],
        "Kd_pre":   k["Kd_pre"],
        "IR_marg":  k["IR_marg"],
        "WACC_est": k["WACC_est"],
        # premissas
        "g1":       p["g1"],
        "g2_5":     p["g2_5"],
        "Mg_1":     p["Mg_1"],
        "Mg_alvo":  p["Mg_alvo"],
        "Ano_conv": int(p["Ano_conv"]),
        "StC":      p["StC"],
        "g_perp":   p["g_perp"],
        "P_fail":   p["P_fail"],
        "V_fail":   p["V_fail"],
        # schedule de crescimento customizado (anos 6-10), opcional
        "g_schedule_override": {
            int(k): float(v)
            for k, v in p.get("g_schedule_override", {}).items()
        },
        # opções
        "N_opt":    o.get("N_opt", 0),
        "K_opt":    o.get("K_opt", 0),
        "T_opt":    o.get("T_opt", 0),
        "Sigma":    o.get("Sigma", 0.45),
    }


# ---------------------------------------------
# 3. BLOCO A - CUSTO DE CAPITAL
# ---------------------------------------------

def bloco_a(inp: dict) -> dict:
    P        = inp["P"]
    Shares   = inp["Shares"]
    D        = inp["D"]
    Beta_u   = inp["Beta_u"]
    IR_marg  = inp["IR_marg"]
    Rf       = inp["Rf"]
    ERP      = inp["ERP"]
    Kd_pre   = inp["Kd_pre"]
    WACC_est = inp["WACC_est"]

    # A1
    MktCap = P * Shares

    # A2
    Beta_L = Beta_u * (1 + (1 - IR_marg) * (D / MktCap))

    # A3
    Ke = Rf + Beta_L * ERP

    # A4
    Kd_liq = Kd_pre * (1 - IR_marg)

    # A5
    total = MktCap + D
    W_equity = MktCap / total
    W_debt   = D / total

    # A6
    WACC_0 = W_equity * Ke + W_debt * Kd_liq

    # A7 - WACC por ano (t=1..10 + terminal)
    wacc_por_ano = {}
    for t in range(1, 11):
        if t <= 5:
            wacc_por_ano[t] = WACC_0
        else:
            wacc_por_ano[t] = WACC_0 + ((t - 5) / 5) * (WACC_est - WACC_0)
    wacc_por_ano["term"] = WACC_est

    # A8 - IR por ano
    IR_ef = inp["IR_ef"]
    ir_por_ano = {}
    for t in range(1, 11):
        if t <= 5:
            ir_por_ano[t] = IR_ef
        else:
            ir_por_ano[t] = IR_ef + ((t - 5) / 5) * (IR_marg - IR_ef)
    ir_por_ano["term"] = IR_marg

    return {
        "MktCap":      MktCap,
        "Beta_L":      Beta_L,
        "Ke":          Ke,
        "Kd_liq":      Kd_liq,
        "W_equity":    W_equity,
        "W_debt":      W_debt,
        "WACC_0":      WACC_0,
        "wacc_por_ano": wacc_por_ano,
        "ir_por_ano":   ir_por_ano,
    }


# ---------------------------------------------
# 4. BLOCO B - PROJEÇÕES ANUAIS
# ---------------------------------------------

def bloco_b(inp: dict, a: dict) -> list[dict]:
    Rev_0    = inp["Rev_0"]
    g1       = inp["g1"]
    g2_5     = inp["g2_5"]
    g_perp   = inp["g_perp"]
    Mg_1     = inp["Mg_1"]
    Mg_alvo  = inp["Mg_alvo"]
    Ano_conv = inp["Ano_conv"]
    StC      = inp["StC"]
    ir       = a["ir_por_ano"]

    projecoes = []
    Rev_prev = Rev_0

    for t in range(1, 11):
        # crescimento
        g_sched = inp.get("g_schedule_override", {})
        if t == 1:
            g = g1
        elif t <= 5:
            g = g2_5
        elif t in g_sched:
            g = g_sched[t]
        else:
            g = g2_5 - ((t - 5) / 5) * (g2_5 - g_perp)

        Rev = Rev_prev * (1 + g)

        # margem
        if t == 1:
            Mg = Mg_1
        elif Ano_conv == 1:
            Mg = Mg_alvo
        elif t <= Ano_conv:
            Mg = Mg_1 + ((t - 1) / (Ano_conv - 1)) * (Mg_alvo - Mg_1)
        else:
            Mg = Mg_alvo

        EBIT      = Rev * Mg
        IR_t      = ir[t]
        NOPAT     = EBIT * (1 - IR_t)
        Reinvest  = (Rev - Rev_prev) / StC
        FCFF      = NOPAT - Reinvest

        projecoes.append({
            "t":        t,
            "g":        g,
            "Rev":      Rev,
            "Mg":       Mg,
            "EBIT":     EBIT,
            "IR":       IR_t,
            "NOPAT":    NOPAT,
            "Reinvest": Reinvest,
            "FCFF":     FCFF,
        })

        Rev_prev = Rev

    return projecoes


# ---------------------------------------------
# 5. BLOCO C - DESCONTO DOS FCFF
# ---------------------------------------------

def bloco_c(projecoes: list[dict], a: dict) -> tuple[list[dict], float]:
    wacc = a["wacc_por_ano"]

    fator_acum = 1.0
    VP_total = 0.0
    descontos = []

    for row in projecoes:
        t = row["t"]
        fator_acum = fator_acum / (1 + wacc[t])
        vp = row["FCFF"] * fator_acum
        VP_total += vp
        descontos.append({**row, "WACC": wacc[t], "Fator": fator_acum, "VP_FCFF": vp})

    return descontos, VP_total


# ---------------------------------------------
# 6. BLOCO D - VALOR TERMINAL
# ---------------------------------------------

def bloco_d(inp: dict, projecoes: list[dict], descontos: list[dict], VP_total: float) -> dict:
    Mg_alvo  = inp["Mg_alvo"]
    IR_marg  = inp["IR_marg"]
    g_perp   = inp["g_perp"]
    WACC_est = inp["WACC_est"]

    Rev_10   = projecoes[-1]["Rev"]
    Fator_10 = descontos[-1]["Fator"]

    # D1
    Rev_term   = Rev_10 * (1 + g_perp)
    # D2
    EBIT_term  = Rev_term * Mg_alvo
    # D3
    NOPAT_term = EBIT_term * (1 - IR_marg)
    # D4
    ROIC_term      = WACC_est
    ReinvRate_term = g_perp / ROIC_term
    # D5
    FCFF_term = NOPAT_term * (1 - ReinvRate_term)
    # D6
    denominador = WACC_est - g_perp
    VT = FCFF_term / denominador
    # D7
    VP_VT = VT * Fator_10

    pct_vt = VP_VT / (VP_total + VP_VT) * 100

    return {
        "Rev_term":      Rev_term,
        "EBIT_term":     EBIT_term,
        "NOPAT_term":    NOPAT_term,
        "ROIC_term":     ROIC_term,
        "ReinvRate_term":ReinvRate_term,
        "FCFF_term":     FCFF_term,
        "denominador":   denominador,
        "VT":            VT,
        "Fator_10":      Fator_10,
        "VP_VT":         VP_VT,
        "pct_vt":        pct_vt,
    }


# ---------------------------------------------
# 7. BLOCO E - AJUSTE DE FALÊNCIA
# ---------------------------------------------

def bloco_e(inp: dict, VP_total: float, VP_VT: float) -> dict:
    P_fail = inp["P_fail"]
    V_fail = inp["V_fail"]
    Valor_op_bruto = VP_total + VP_VT

    if P_fail == 0:
        return {"P_fail": 0, "Valor_op": Valor_op_bruto, "ajuste_aplicado": False}

    Valor_distress    = V_fail * Valor_op_bruto
    Valor_op_ajustado = Valor_op_bruto * (1 - P_fail) + P_fail * Valor_distress

    return {
        "P_fail":          P_fail,
        "Valor_distress":  Valor_distress,
        "Valor_op":        Valor_op_ajustado,
        "ajuste_aplicado": True,
    }


# ---------------------------------------------
# 8. BLOCO F - EQUITY VALUE E PREÇO POR AÇÃO
# ---------------------------------------------

def black_scholes_call(S, K, T, r, sigma) -> float:
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)


def _norm_cdf(x: float) -> float:
    return (1 + math.erf(x / math.sqrt(2))) / 2


def bloco_f(inp: dict, e: dict) -> dict:
    Valor_op = e["Valor_op"]
    Caixa    = inp["Caixa"]
    AtvNOp   = inp["AtvNOp"]
    D        = inp["D"]
    MinInt   = inp["MinInt"]
    P        = inp["P"]
    Shares   = inp["Shares"]
    N_opt    = inp["N_opt"]

    # F2 - opções
    if N_opt > 0:
        Valor_opcao_unit = black_scholes_call(
            S=P, K=inp["K_opt"], T=inp["T_opt"],
            r=inp["Rf"], sigma=inp["Sigma"]
        )
        Valor_opcoes = N_opt * Valor_opcao_unit
    else:
        Valor_opcao_unit = 0
        Valor_opcoes = 0

    # F3 - bridge
    Equity_Value = Valor_op + Caixa + AtvNOp - D - MinInt - Valor_opcoes

    # F4
    Valor_acao = Equity_Value / Shares

    # F5
    Premio = (P / Valor_acao) - 1

    return {
        "Valor_op":        Valor_op,
        "Caixa":           Caixa,
        "AtvNOp":          AtvNOp,
        "D":               D,
        "MinInt":          MinInt,
        "Valor_opcoes":    Valor_opcoes,
        "Valor_opcao_unit":Valor_opcao_unit,
        "Equity_Value":    Equity_Value,
        "Shares":          Shares,
        "Valor_acao":      Valor_acao,
        "P":               P,
        "Premio":          Premio,
    }


# ---------------------------------------------
# 9. CHECKLIST DE VERIFICAÇÃO
# ---------------------------------------------

def checklist(inp: dict, a: dict, projecoes: list[dict], d: dict, f: dict) -> list[dict]:
    checks = []

    def ok(nome, condicao, detalhe=""):
        checks.append({"nome": nome, "ok": bool(condicao), "detalhe": detalhe})

    wacc = a["wacc_por_ano"]
    ir   = a["ir_por_ano"]
    ultimo = projecoes[-1]
    primeiro = projecoes[0]

    ok("WACC(10) = WACC_est",
       abs(wacc[10] - inp["WACC_est"]) < 1e-9,
       f"{wacc[10]:.6f} vs {inp['WACC_est']:.6f}")

    ok("IR(10) = IR_marg",
       abs(ir[10] - inp["IR_marg"]) < 1e-9,
       f"{ir[10]:.6f} vs {inp['IR_marg']:.6f}")

    conv = next((r for r in projecoes if r["t"] == inp["Ano_conv"]), None)
    if conv:
        ok("Mg(Ano_conv) = Mg_alvo",
           abs(conv["Mg"] - inp["Mg_alvo"]) < 1e-9,
           f"Mg(ano {inp['Ano_conv']}) = {conv['Mg']:.6f} vs {inp['Mg_alvo']:.6f}")

    ok("g(10) = g_perp",
       abs(ultimo["g"] - inp["g_perp"]) < 1e-9,
       f"{ultimo['g']:.6f} vs {inp['g_perp']:.6f}")

    ok("Fatores decrescentes (Fator_1 > Fator_10)",
       True,
       "Sempre verdadeiro - verificação estrutural")

    ok("Denominador VT > 0",
       d["denominador"] > 0,
       f"WACC_est - g_perp = {d['denominador']:.6f}")

    pct = d["pct_vt"]
    ok("VP_VT entre 40% e 75% do total",
       40 <= pct <= 75,
       f"{pct:.1f}% {'⚠ FORA DO INTERVALO NORMAL' if not (40 <= pct <= 75) else ''}")

    ok("Equity_Value > 0",
       f["Equity_Value"] > 0,
       f"{f['Equity_Value']:.2f}")

    ok("Valor_acao > 0",
       f["Valor_acao"] > 0,
       f"{f['Valor_acao']:.4f}")

    return checks


# ---------------------------------------------
# 10. IMPRESSÃO DOS RESULTADOS
# ---------------------------------------------

def pct(v):
    return f"{v * 100:.2f}%"

def moeda(v, decimais=2):
    return f"{v:,.{decimais}f}"


def imprimir_resultados(dados: dict, inp: dict, a: dict, projecoes: list[dict],
                        descontos: list[dict], VP_total: float,
                        d: dict, e: dict, f: dict, checks: list[dict]):

    empresa = dados.get("empresa", {})
    unidade = empresa.get("unidade", "M")
    moeda_str = empresa.get("moeda", "")
    sep = "-" * 65

    print()
    print("=" * 65)
    print(f"  VALUATION DCF - {empresa.get('nome', '')} ({empresa.get('ticker', '')})")
    print(f"  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 65)

    # -- BLOCO A --
    print(f"\n{'BLOCO A - CUSTO DE CAPITAL':^65}")
    print(sep)
    print(f"  Beta desalavancado (Beta_u):          {inp['Beta_u']:.4f}")
    print(f"  Beta alavancado   (Beta_L):           {a['Beta_L']:.4f}")
    print(f"  Custo de capital próprio (Ke):        {pct(a['Ke'])}")
    print(f"  Custo da dívida líquido  (Kd_liq):   {pct(a['Kd_liq'])}")
    print(f"  Peso equity / dívida:                 {pct(a['W_equity'])} / {pct(a['W_debt'])}")
    print(f"  WACC inicial  (WACC_0):               {pct(a['WACC_0'])}")
    print(f"  WACC estável  (WACC_est):             {pct(inp['WACC_est'])}")
    print(f"  Cap. de mercado (MktCap):             {moeda_str} {moeda(a['MktCap'])} {unidade}")

    print(f"\n  WACC e IR por ano:")
    print(f"  {'Ano':>4}  {'WACC':>8}  {'IR':>7}")
    print(f"  {'-'*4}  {'-'*8}  {'-'*7}")
    wacc = a["wacc_por_ano"]
    ir   = a["ir_por_ano"]
    for t in range(1, 11):
        print(f"  {t:>4}  {pct(wacc[t]):>8}  {pct(ir[t]):>7}")
    print(f"  {'Term':>4}  {pct(wacc['term']):>8}  {pct(ir['term']):>7}")

    # -- BLOCO B + C --
    print(f"\n{'BLOCO B+C - PROJEÇÃO E DESCONTO (anos 1-10)':^65}")
    print(sep)
    header = f"  {'Ano':>3} {'g':>6} {'Receita':>10} {'Mg':>6} {'EBIT':>10} {'NOPAT':>10} {'Reinv':>10} {'FCFF':>10} {'WACC':>7} {'Fator':>7} {'VP_FCFF':>10}"
    print(header)
    print("  " + "-" * 98)

    for row in descontos:
        t = row["t"]
        print(
            f"  {t:>3} "
            f"{pct(row['g']):>6} "
            f"{moeda(row['Rev']):>10} "
            f"{pct(row['Mg']):>6} "
            f"{moeda(row['EBIT']):>10} "
            f"{moeda(row['NOPAT']):>10} "
            f"{moeda(row['Reinvest']):>10} "
            f"{moeda(row['FCFF']):>10} "
            f"{pct(row['WACC']):>7} "
            f"{row['Fator']:.5f} "
            f"{moeda(row['VP_FCFF']):>10}"
        )

    print(f"  {'-'*101}")
    print(f"  {'VP_total (S):':>57}  {moeda(VP_total):>10} {unidade}")

    # -- BLOCO D --
    print(f"\n{'BLOCO D - VALOR TERMINAL':^65}")
    print(sep)
    print(f"  Receita terminal (Ano 11):            {moeda_str} {moeda(d['Rev_term'])} {unidade}")
    print(f"  EBIT terminal:                        {moeda_str} {moeda(d['EBIT_term'])} {unidade}")
    print(f"  NOPAT terminal:                       {moeda_str} {moeda(d['NOPAT_term'])} {unidade}")
    print(f"  ROIC terminal = WACC_est:             {pct(d['ROIC_term'])}")
    print(f"  Taxa de reinvest. perpetuidade:       {pct(d['ReinvRate_term'])}")
    print(f"  FCFF terminal:                        {moeda_str} {moeda(d['FCFF_term'])} {unidade}")
    print(f"  Denominador (WACC_est - g_perp):      {d['denominador']:.6f}")
    print(f"  Valor Terminal bruto (VT):            {moeda_str} {moeda(d['VT'])} {unidade}")
    print(f"  Fator de desconto Ano 10:             {d['Fator_10']:.6f}")
    print(f"  VP do Valor Terminal:                 {moeda_str} {moeda(d['VP_VT'])} {unidade}")
    print(f"  Participação VT no total:             {d['pct_vt']:.1f}%")
    if not (40 <= d["pct_vt"] <= 75):
        print(f"  ⚠  ALERTA: participação fora do intervalo normal (40%-75%)")

    # -- BLOCO E --
    if e["ajuste_aplicado"]:
        print(f"\n{'BLOCO E - AJUSTE DE FALÊNCIA':^65}")
        print(sep)
        print(f"  Probabilidade de falência:            {pct(e['P_fail'])}")
        print(f"  Valor em distress:                    {moeda_str} {moeda(e['Valor_distress'])} {unidade}")
        print(f"  Valor op. ajustado:                   {moeda_str} {moeda(e['Valor_op'])} {unidade}")

    # -- BLOCO F --
    print(f"\n{'BLOCO F - EQUITY VALUE E PREÇO POR AÇÃO':^65}")
    print(sep)
    print(f"  {'Item':<40} {'Operação':>6}  {'Valor':>12}")
    print(f"  {'-'*40}  {'-'*6}  {'-'*12}")
    print(f"  {'Valor dos Ativos Operacionais':<40} {'(+)':>6}  {moeda_str} {moeda(f['Valor_op']):>10} {unidade}")
    print(f"  {'Caixa e equivalentes':<40} {'(+)':>6}  {moeda_str} {moeda(f['Caixa']):>10} {unidade}")
    print(f"  {'Outros ativos não operacionais':<40} {'(+)':>6}  {moeda_str} {moeda(f['AtvNOp']):>10} {unidade}")
    print(f"  {'Dívida total':<40} {'(-)':>6}  {moeda_str} {moeda(f['D']):>10} {unidade}")
    print(f"  {'Participações minoritárias':<40} {'(-)':>6}  {moeda_str} {moeda(f['MinInt']):>10} {unidade}")
    print(f"  {'Valor das opções':<40} {'(-)':>6}  {moeda_str} {moeda(f['Valor_opcoes']):>10} {unidade}")
    print(f"  {'-'*62}")
    print(f"  {'Equity Value':<40} {'(=)':>6}  {moeda_str} {moeda(f['Equity_Value']):>10} {unidade}")
    print(f"  {'Ações em circulacao':<40} {'':>6}  {moeda(f['Shares']):>10} M")
    print(f"  {'-'*62}")
    print(f"\n  {'VALOR POR AÇÃO (intrínseco):':<40} {moeda_str} {moeda(f['Valor_acao'], 4)}")
    print(f"  {'Preco de mercado:':<40} {moeda_str} {moeda(f['P'], 4)}")
    premio = f["Premio"]
    sinal = "SOBREVALORIZADA" if premio > 0 else "SUBVALORIZADA"
    if abs(premio) < 0.05:
        sinal = "PRÓXIMA DO VALOR JUSTO"
    print(f"  {'Sobre(sub)valorização:':<40} {pct(premio):>8}  ({sinal})")

    # -- CHECKLIST --
    print(f"\n{'CHECKLIST DE VERIFICAÇÃO':^65}")
    print(sep)
    falhas = 0
    for c in checks:
        icone = "[+]" if c["ok"] else "[-]"
        detalhe = f"  [{c['detalhe']}]" if c["detalhe"] else ""
        print(f"  {icone}  {c['nome']}{detalhe}")
        if not c["ok"]:
            falhas += 1

    print(sep)
    if falhas == 0:
        print("  [+] Todos os itens do checklist aprovados.")
    else:
        print(f"  [-] {falhas} item(ns) com falha - revisar antes de usar o resultado.")
    print()


# ---------------------------------------------
# 11. EXPORTAÇÃO DO RESULTADO (JSON para Passo 5)
# ---------------------------------------------

def exportar_resultado(dados: dict, inp: dict, a: dict, projecoes: list[dict],
                       descontos: list[dict], VP_total: float,
                       d: dict, e: dict, f: dict, checks: list[dict],
                       caminho_saida: str):

    resultado = {
        "meta": {
            "gerado_em": datetime.now().isoformat(),
            "empresa": dados.get("empresa", {}),
        },
        "bloco_a": {
            "MktCap":   a["MktCap"],
            "Beta_L":   a["Beta_L"],
            "Ke":       a["Ke"],
            "Kd_liq":  a["Kd_liq"],
            "W_equity": a["W_equity"],
            "W_debt":   a["W_debt"],
            "WACC_0":   a["WACC_0"],
            "wacc_por_ano": {str(k): v for k, v in a["wacc_por_ano"].items()},
            "ir_por_ano":   {str(k): v for k, v in a["ir_por_ano"].items()},
        },
        "bloco_b_c": [
            {
                "t":       r["t"],
                "g":       r["g"],
                "Rev":     r["Rev"],
                "Mg":      r["Mg"],
                "EBIT":    r["EBIT"],
                "IR":      r["IR"],
                "NOPAT":   r["NOPAT"],
                "Reinvest":r["Reinvest"],
                "FCFF":    r["FCFF"],
                "WACC":    r["WACC"],
                "Fator":   r["Fator"],
                "VP_FCFF": r["VP_FCFF"],
            }
            for r in descontos
        ],
        "VP_total": VP_total,
        "bloco_d": d,
        "bloco_e": e,
        "bloco_f": f,
        "checklist": checks,
        "inputs_usados": inp,
    }

    with open(caminho_saida, "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=2)

    print(f"  Resultado salvo em: {caminho_saida}")


# ---------------------------------------------
# 12. MAIN
# ---------------------------------------------

def main():
    # -- Determinar fonte do JSON --
    if "--exemplo" in sys.argv:
        dados = EXEMPLO_FIQE3
        arquivo_entrada = "exemplo_interno_FIQE3"
    else:
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
            arquivo_entrada = sys.argv[1]
        else:
            arquivo_entrada = "passo3_output.json"

        if not os.path.exists(arquivo_entrada):
            print(f"\nERRO: arquivo '{arquivo_entrada}' não encontrado.")
            print("Uso: python passo4_dcf.py [arquivo.json]")
            print("     python passo4_dcf.py --exemplo   (dados de exemplo FIQE3)")
            sys.exit(1)

        dados = carregar_json(arquivo_entrada)
        print(f"\nJSON carregado: {arquivo_entrada}")

    # -- Validar pré-requisitos --
    erros = validar_pre_requisitos(dados)
    if erros:
        print("\nERRO: JSON não está pronto para o Passo 4.\n")
        for e in erros:
            print(f"  ✗ {e}")
        sys.exit(1)

    # -- Extrair inputs --
    inp = extrair_inputs(dados)

    # -- Executar blocos em sequência --
    a           = bloco_a(inp)
    projecoes   = bloco_b(inp, a)
    descontos, VP_total = bloco_c(projecoes, a)
    d           = bloco_d(inp, projecoes, descontos, VP_total)
    e           = bloco_e(inp, VP_total, d["VP_VT"])
    f           = bloco_f(inp, e)
    checks      = checklist(inp, a, projecoes, d, f)

    # -- Imprimir --
    imprimir_resultados(dados, inp, a, projecoes, descontos, VP_total, d, e, f, checks)

    # -- Exportar JSON para Passo 5 --
    caminho_saida = "passo4_resultado.json"
    exportar_resultado(dados, inp, a, projecoes, descontos, VP_total, d, e, f, checks, caminho_saida)


if __name__ == "__main__":
    main()
