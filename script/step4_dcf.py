#!/usr/bin/env python3
"""
Passo 4 -- Execucao do Modelo DCF (Metodologia Damodaran)

Le o JSON consolidado do Passo 3 e executa todos os blocos de calculo
em sequencia estrita (A -> B -> C -> D -> E -> F).

Uso:
    python step4_dcf.py <caminho_para_step3.json> [--output <saida.json>] [--quiet]

Exemplo:
    python step4_dcf.py Acoes/FIQE3/step3.json
    python step4_dcf.py step4_resultado.json --output resultado.json
"""

import argparse
import json
import math
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# UTILITARIOS
# ---------------------------------------------------------------------------

def norm_cdf(x: float) -> float:
    """Funcao de distribuicao cumulativa da normal padrao (sem dependencias externas)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def fmt(v: float, dp: int = 2) -> str:
    """Formata numero com casas decimais fixas (sem separador de milhar)."""
    return f"{v:.{dp}f}"


def pct(v: float, dp: int = 2) -> str:
    """Formata decimal como percentual (ex: 0.1669 -> '16,69%')."""
    return f"{v * 100:,.{dp}f}%"


def tabela(headers: list[str], rows: list[list[str]],
           col_widths: list[int] | None = None) -> str:
    """Monta tabela alinhada em formato texto (Markdown amigavel)."""
    if col_widths is None:
        col_widths = [max(len(h), *(len(str(r[i])) for r in rows)) + 2
                      for i, h in enumerate(headers)]
    sep = "+" + "+".join("-" * w for w in col_widths) + "+"
    hdr = "|" + "|".join(h.center(w) for h, w in zip(headers, col_widths)) + "|"
    body = "\n".join(
        "|" + "|".join(str(c).center(w) for c, w in zip(row, col_widths)) + "|"
        for row in rows
    )
    return f"{sep}\n{hdr}\n{sep}\n{body}\n{sep}"


def verifica(check: bool, nome: str, detalhe: str, ok: list, falhas: list) -> None:
    """Verifica uma condicao e registra no checklist."""
    if check:
        ok.append((nome, detalhe))
    else:
        falhas.append((nome, detalhe))


# ---------------------------------------------------------------------------
# EXTRACAO DE INPUTS (suporta formato canonical Passo 3 e flat)
# ---------------------------------------------------------------------------

def extrair_inputs(data: dict) -> dict:
    """Extrai todos os inputs do JSON, suportando formato aninhado (passo3) e flat."""

    def _get(path: str, default=0.0):
        """Busca valor por caminho pontilhado no dict, ou no nivel raiz."""
        keys = path.split(".")
        val = data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                # fallback: busca flat no raiz (ex: inputs_usados, ou top-level)
                for source in [data.get("inputs_usados", {}), data]:
                    if isinstance(source, dict) and keys[-1] in source:
                        return source[keys[-1]]
                return data.get(keys[-1], default)
        return val if val is not None else default

    return {
        # Empresa
        "nome": data.get("empresa", data.get("meta", {}).get("empresa", {})).get("nome", "N/A"),
        "ticker": data.get("empresa", data.get("meta", {}).get("empresa", {})).get("ticker", "N/A"),
        "pais": data.get("empresa", data.get("meta", {}).get("empresa", {})).get("pais", "N/A"),
        "setor": data.get("empresa", data.get("meta", {}).get("empresa", {})).get("setor", "N/A"),
        "moeda": data.get("empresa", data.get("meta", {}).get("empresa", {})).get("moeda", "BRL"),
        "unidade": data.get("empresa", data.get("meta", {}).get("empresa", {})).get("unidade", "milhoes"),

        # Dados historicos
        "Rev_0": float(_get("dados_historicos.Rev_0", data.get("Rev_0", 0))),
        "EBIT_0": float(_get("dados_historicos.EBIT_0", data.get("EBIT_0", 0))),
        "D": float(_get("dados_historicos.D", data.get("D", 0))),
        "Caixa": float(_get("dados_historicos.Caixa", data.get("Caixa", 0))),
        "AtvNOp": float(_get("dados_historicos.AtvNOp", data.get("AtvNOp", 0))),
        "MinInt": float(_get("dados_historicos.MinInt", data.get("MinInt", 0))),

        # Dados de mercado
        "P": float(_get("dados_mercado.P", data.get("P", 0))),
        "Shares": float(_get("dados_mercado.Shares", data.get("Shares", 0))),
        "IR_ef": float(_get("dados_mercado.IR_ef", data.get("IR_ef", 0))),

        # Parametros de custo de capital
        "Rf": float(_get("parametros_custo_capital.Rf", data.get("Rf", 0))),
        "ERP": float(_get("parametros_custo_capital.ERP", data.get("ERP", 0))),
        "Beta_u": float(_get("parametros_custo_capital.Beta_u", data.get("Beta_u", 0))),
        "Kd_pre": float(_get("parametros_custo_capital.Kd_pre", data.get("Kd_pre", 0))),
        "IR_marg": float(_get("parametros_custo_capital.IR_marg", data.get("IR_marg", 0))),
        "WACC_est": float(_get("parametros_custo_capital.WACC_est", data.get("WACC_est", 0))),

        # Premissas analiticas
        "g1": float(_get("premissas_analiticas.g1", data.get("g1", 0))),
        "g2_5": float(_get("premissas_analiticas.g2_5", data.get("g2_5", 0))),
        "Mg_1": float(_get("premissas_analiticas.Mg_1", data.get("Mg_1", 0))),
        "Mg_alvo": float(_get("premissas_analiticas.Mg_alvo", data.get("Mg_alvo", 0))),
        "Ano_conv": int(_get("premissas_analiticas.Ano_conv", data.get("Ano_conv", 5))),
        "StC": float(_get("premissas_analiticas.StC", data.get("StC", 1))),
        "g_perp": float(_get("premissas_analiticas.g_perp", data.get("g_perp", 0))),
        "P_fail": float(_get("premissas_analiticas.P_fail", data.get("P_fail", 0))),
        "V_fail": float(_get("premissas_analiticas.V_fail", data.get("V_fail", 0))),

        # Opcoes de funcionarios
        "N_opt": float(_get("opcoes_funcionarios.N_opt", data.get("N_opt", 0))),
        "K_opt": float(_get("opcoes_funcionarios.K_opt", data.get("K_opt", 0))),
        "T_opt": float(_get("opcoes_funcionarios.T_opt", data.get("T_opt", 0))),
        "Sigma": float(_get("opcoes_funcionarios.Sigma", data.get("Sigma", 0))),
    }


# ---------------------------------------------------------------------------
# BLOCO A -- CUSTO DE CAPITAL (WACC)
# ---------------------------------------------------------------------------

def bloco_a(inp: dict) -> dict:
    """Executa Bloco A -- calculo do WACC e aliquotas de IR por ano."""
    # A1. Capitalizacao de Mercado
    mkt_cap = inp["P"] * inp["Shares"]

    # A2. Beta Alavancado
    if mkt_cap > 0:
        beta_l = inp["Beta_u"] * (1 + (1 - inp["IR_marg"]) * (inp["D"] / mkt_cap))
    else:
        beta_l = inp["Beta_u"]

    # A3. Custo de Capital Proprio
    ke = inp["Rf"] + beta_l * inp["ERP"]

    # A4. Custo Liquido da Divida
    kd_liq = inp["Kd_pre"] * (1 - inp["IR_marg"])

    # A5. Pesos na Estrutura de Capital
    denominador = mkt_cap + inp["D"]
    if denominador > 0:
        w_equity = mkt_cap / denominador
        w_debt = inp["D"] / denominador
    else:
        w_equity = 1.0
        w_debt = 0.0

    # A6. WACC Inicial
    wacc_0 = w_equity * ke + w_debt * kd_liq

    # A7. WACC por Ano
    wacc_por_ano = {}
    for t in range(1, 11):
        if t <= 5:
            wacc_por_ano[t] = wacc_0
        else:
            frac = (t - 5) / 5.0
            wacc_por_ano[t] = wacc_0 + frac * (inp["WACC_est"] - wacc_0)
    wacc_por_ano["term"] = inp["WACC_est"]

    # A8. Aliquota de IR por Ano
    ir_por_ano = {}
    for t in range(1, 11):
        if t <= 5:
            ir_por_ano[t] = inp["IR_ef"]
        else:
            frac = (t - 5) / 5.0
            ir_por_ano[t] = inp["IR_ef"] + frac * (inp["IR_marg"] - inp["IR_ef"])
    ir_por_ano["term"] = inp["IR_marg"]

    return {
        "MktCap": mkt_cap,
        "Beta_L": beta_l,
        "Ke": ke,
        "Kd_liq": kd_liq,
        "W_equity": w_equity,
        "W_debt": w_debt,
        "WACC_0": wacc_0,
        "wacc_por_ano": wacc_por_ano,
        "ir_por_ano": ir_por_ano,
    }


# ---------------------------------------------------------------------------
# BLOCO B -- PROJECOES ANUAIS (t = 1 a 10)
# ---------------------------------------------------------------------------

def bloco_b(inp: dict, a: dict) -> list[dict]:
    """Executa Bloco B -- projecao de receita, EBIT, NOPAT, reinvestimento e FCFF."""
    rows = []
    rev_prev = inp["Rev_0"]  # Rev(0)

    for t in range(1, 11):
        # Taxa de crescimento g(t)
        if t == 1:
            g_t = inp["g1"]
        elif t <= 5:
            g_t = inp["g2_5"]
        else:
            frac = (t - 5) / 5.0
            g_t = inp["g2_5"] - frac * (inp["g2_5"] - inp["g_perp"])

        # Receita
        rev_t = rev_prev * (1 + g_t)

        # Margem EBIT Mg(t)
        if t == 1:
            mg_t = inp["Mg_1"]
        elif t <= inp["Ano_conv"]:
            frac = (t - 1) / (inp["Ano_conv"] - 1) if inp["Ano_conv"] > 1 else 0
            mg_t = inp["Mg_1"] + frac * (inp["Mg_alvo"] - inp["Mg_1"])
        else:
            mg_t = inp["Mg_alvo"]

        # EBIT
        ebit_t = rev_t * mg_t

        # IR do ano
        ir_t = a["ir_por_ano"][t]

        # NOPAT
        nopat_t = ebit_t * (1 - ir_t)

        # Reinvestimento
        reinvest_t = (rev_t - rev_prev) / inp["StC"]

        # FCFF
        fcff_t = nopat_t - reinvest_t

        rows.append({
            "t": t,
            "g": g_t,
            "Rev": rev_t,
            "Mg": mg_t,
            "EBIT": ebit_t,
            "IR": ir_t,
            "NOPAT": nopat_t,
            "Reinvest": reinvest_t,
            "FCFF": fcff_t,
        })

        rev_prev = rev_t

    return rows


# ---------------------------------------------------------------------------
# BLOCO C -- DESCONTO DOS FCFF
# ---------------------------------------------------------------------------

def bloco_c(proj: list[dict], a: dict) -> dict:
    """Executa Bloco C -- desconto dos FCFFs e calculo do VP total."""
    fator_prev = 1.0
    vp_total = 0.0

    for row in proj:
        t = row["t"]
        wacc_t = a["wacc_por_ano"][t]
        if t == 1:
            fator_t = 1.0 / (1.0 + wacc_t)
        else:
            fator_t = fator_prev / (1.0 + wacc_t)

        vp_fcff = row["FCFF"] * fator_t
        row["WACC"] = wacc_t
        row["Fator"] = fator_t
        row["VP_FCFF"] = vp_fcff

        vp_total += vp_fcff
        fator_prev = fator_t

    return {
        "rows": proj,         # proj atualizado com WACC, Fator, VP_FCFF
        "VP_total": vp_total,
    }


# ---------------------------------------------------------------------------
# BLOCO D -- VALOR TERMINAL
# ---------------------------------------------------------------------------

def bloco_d(inp: dict, proj: list[dict], fator_10: float) -> dict:
    """Executa Bloco D -- calculo do valor terminal."""
    rev_10 = proj[9]["Rev"]   # ultimo ano projetado (t=10)

    # D1. Receita Terminal (Ano 11)
    rev_term = rev_10 * (1 + inp["g_perp"])

    # D2. EBIT Terminal
    ebit_term = rev_term * inp["Mg_alvo"]

    # D3. NOPAT Terminal
    nopat_term = ebit_term * (1 - inp["IR_marg"])

    # D4. Taxa de Reinvestimento na Perpetuidade
    roic_term = inp["WACC_est"]
    reinv_rate = inp["g_perp"] / roic_term if roic_term > 0 else 0

    # D5. FCFF Terminal
    fcff_term = nopat_term * (1 - reinv_rate)

    # D6. Valor Terminal Bruto
    denominador = inp["WACC_est"] - inp["g_perp"]
    vt = fcff_term / denominador if denominador > 0 else float("inf")

    # D7. Valor Presente do Valor Terminal
    vp_vt = vt * fator_10

    pct_vt = (vp_vt / (proj[0].get("_vp_total", 0) + vp_vt) * 100
              if (proj[0].get("_vp_total", 0) + vp_vt) > 0 else 0)

    return {
        "Rev_term": rev_term,
        "EBIT_term": ebit_term,
        "NOPAT_term": nopat_term,
        "ROIC_term": roic_term,
        "ReinvRate_term": reinv_rate,
        "FCFF_term": fcff_term,
        "denominador": denominador,
        "VT": vt,
        "Fator_10": fator_10,
        "VP_VT": vp_vt,
        "pct_vt": pct_vt,  # sera recalculado depois
    }


# ---------------------------------------------------------------------------
# BLOCO E -- AJUSTE DE FALENCIA
# ---------------------------------------------------------------------------

def bloco_e(inp: dict, vp_total: float, vp_vt: float) -> dict:
    """Executa Bloco E -- ajuste de probabilidade de falencia."""
    if inp["P_fail"] == 0:
        valor_op = vp_total + vp_vt
        return {
            "P_fail": 0,
            "Valor_op": valor_op,
            "ajuste_aplicado": False,
            "Valor_distress": 0,
            "Valor_op_ajustado": valor_op,
        }

    valor_distress = inp["V_fail"] * (vp_total + vp_vt)
    valor_op_ajustado = (vp_total + vp_vt) * (1 - inp["P_fail"]) + inp["P_fail"] * valor_distress

    return {
        "P_fail": inp["P_fail"],
        "Valor_distress": valor_distress,
        "Valor_op_ajustado": valor_op_ajustado,
        "ajuste_aplicado": True,
        "Valor_op": valor_op_ajustado,
    }


# ---------------------------------------------------------------------------
# BLOCO F -- VALOR DO PATRIMONIO E PRECO POR ACAO
# ---------------------------------------------------------------------------

def bloco_f(inp: dict, e: dict, vp_total: float, vp_vt: float) -> dict:
    """Executa Bloco F -- equity value, valor por acao e diagnostico de valorizacao."""

    # F1. Valor dos Ativos Operacionais
    if inp["P_fail"] == 0:
        valor_op = vp_total + vp_vt
    else:
        valor_op = e["Valor_op_ajustado"]

    # F2. Valor das Opcoes de Funcionarios (Black-Scholes)
    if inp["N_opt"] > 0 and inp["Sigma"] > 0 and inp["T_opt"] > 0:
        S = inp["P"]
        K = inp["K_opt"]
        T = inp["T_opt"]
        r = inp["Rf"]
        sigma = inp["Sigma"]

        d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        valor_opcao_unit = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        valor_opcoes = inp["N_opt"] * valor_opcao_unit
    else:
        valor_opcao_unit = 0.0
        valor_opcoes = 0.0

    # F3. Equity Value (Bridge)
    equity_value = (valor_op
                    + inp["Caixa"]
                    + inp["AtvNOp"]
                    - inp["D"]
                    - inp["MinInt"]
                    - valor_opcoes)

    # F4. Valor por Acao
    if inp["Shares"] > 0:
        valor_acao = equity_value / inp["Shares"]
    else:
        valor_acao = 0.0

    # F5. Diagnostico de Valorizacao
    if valor_acao > 0:
        premio = (inp["P"] / valor_acao) - 1
    else:
        premio = float("inf")

    return {
        "Valor_op": valor_op,
        "Caixa": inp["Caixa"],
        "AtvNOp": inp["AtvNOp"],
        "D": inp["D"],
        "MinInt": inp["MinInt"],
        "Valor_opcoes": valor_opcoes,
        "Valor_opcao_unit": valor_opcao_unit,
        "Equity_Value": equity_value,
        "Shares": inp["Shares"],
        "Valor_acao": valor_acao,
        "P": inp["P"],
        "Premio": premio,
    }


# ---------------------------------------------------------------------------
# EXECUCAO PRINCIPAL
# ---------------------------------------------------------------------------

def executar_dcf(input_path: str) -> dict:
    """Executa o pipeline DCF completo a partir do JSON de entrada."""

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    inp = extrair_inputs(data)

    # =====================================================================
    # BLOCO A -- CUSTO DE CAPITAL (WACC)
    # =====================================================================
    a = bloco_a(inp)

    # =====================================================================
    # BLOCO B -- PROJECOES ANUAIS
    # =====================================================================
    proj = bloco_b(inp, a)

    # =====================================================================
    # BLOCO C -- DESCONTO DOS FCFF
    # =====================================================================
    c = bloco_c(proj, a)
    proj = c["rows"]
    vp_total = c["VP_total"]

    # Armazena VP_total para uso no Bloco D
    for row in proj:
        row["_vp_total"] = vp_total

    fator_10 = proj[9]["Fator"]

    # =====================================================================
    # BLOCO D -- VALOR TERMINAL
    # =====================================================================
    d = bloco_d(inp, proj, fator_10)

    # Recalcula % do VT com o VP_total real
    vp_vt = d["VP_VT"]
    if (vp_total + vp_vt) > 0:
        d["pct_vt"] = (vp_vt / (vp_total + vp_vt)) * 100
    else:
        d["pct_vt"] = 0

    # =====================================================================
    # BLOCO E -- AJUSTE DE FALENCIA
    # =====================================================================
    e = bloco_e(inp, vp_total, vp_vt)

    # =====================================================================
    # BLOCO F -- VALOR DO PATRIMONIO E PRECO POR ACAO
    # =====================================================================
    f = bloco_f(inp, e, vp_total, vp_vt)

    # =====================================================================
    # CHECKLIST DE VERIFICACAO FINAL
    # =====================================================================
    ok, falhas = [], []

    verifica(abs(a["wacc_por_ano"][10] - inp["WACC_est"]) < 1e-10,
             "WACC(10) = WACC_est",
             f"WACC(10)={pct(a['wacc_por_ano'][10])} vs WACC_est={pct(inp['WACC_est'])}",
             ok, falhas)

    verifica(abs(a["ir_por_ano"][10] - inp["IR_marg"]) < 1e-10,
             "IR(10) = IR_marg",
             f"IR(10)={pct(a['ir_por_ano'][10])} vs IR_marg={pct(inp['IR_marg'])}",
             ok, falhas)

    verifica(abs(proj[inp["Ano_conv"] - 1]["Mg"] - inp["Mg_alvo"]) < 1e-10,
             f"Mg(Ano_conv={inp['Ano_conv']}) = Mg_alvo",
             f"Mg({inp['Ano_conv']})={pct(proj[inp['Ano_conv']-1]['Mg'])} vs Mg_alvo={pct(inp['Mg_alvo'])}",
             ok, falhas)

    verifica(abs(proj[9]["g"] - inp["g_perp"]) < 1e-10,
             "g(10) = g_perp",
             f"g(10)={pct(proj[9]['g'])} vs g_perp={pct(inp['g_perp'])}",
             ok, falhas)

    verifica(proj[0]["Fator"] > proj[9]["Fator"],
             "Fator_1 > Fator_10 (decrescentes)",
             f"Fator(1)={fmt(proj[0]['Fator'],6)} > Fator(10)={fmt(proj[9]['Fator'],6)}",
             ok, falhas)

    verifica(d["denominador"] > 0,
             "Denominador VT = WACC_est − g_perp > 0",
             f"WACC_est − g_perp = {fmt(d['denominador'],4)}",
             ok, falhas)

    verifica(40 <= d["pct_vt"] <= 75,
             "VP_VT entre 40% e 75% do total",
             f"VP_VT = {fmt(d['pct_vt'],1)}% do total" + (
                 " !! ALERTA: fora do range 40%-75%" if not (40 <= d["pct_vt"] <= 75) else ""
             ),
             ok, falhas)

    verifica(f["Equity_Value"] > 0,
             "Equity_Value > 0",
             f"Equity_Value = {fmt(f['Equity_Value'],2)} M",
             ok, falhas)

    verifica(f["Valor_acao"] > 0,
             "Valor_acao > 0",
             f"Valor_acao = {fmt(f['Valor_acao'],2)}",
             ok, falhas)

    # ---- Sanidade de unidades e consistencia dos inputs ----
    if inp["D"] > 0:
        verifica(inp["Kd_pre"] >= inp["Rf"],
                 "Sanidade: Kd_pre >= Rf",
                 f"Kd_pre={pct(inp['Kd_pre'])} vs Rf={pct(inp['Rf'])}" + (
                     " !! custo da divida abaixo do Rf -- revisar Kd_pre no Passo 3"
                     if inp["Kd_pre"] < inp["Rf"] else ""
                 ),
                 ok, falhas)

    if inp["Rev_0"] > 0:
        psales = a["MktCap"] / inp["Rev_0"]
        verifica(psales <= 100,
                 "Sanidade: MktCap/Rev_0 <= 100x",
                 f"MktCap/Rev_0 = {fmt(psales, 1)}x" + (
                     " !! POSSIVEL ERRO DE UNIDADE: Rev_0 muito baixa vs MktCap"
                     if psales > 100 else ""
                 ),
                 ok, falhas)

    if inp["D"] > 0:
        d_ratio = inp["D"] / a["MktCap"]
        verifica(d_ratio >= 0.001,
                 "Sanidade: D/MktCap >= 0.1%",
                 f"D/MktCap = {pct(d_ratio, 3)}" + (
                     " !! POSSIVEL ERRO DE UNIDADE: D muito baixa vs MktCap"
                     if d_ratio < 0.001 else ""
                 ),
                 ok, falhas)

    if f["Valor_acao"] > 0 and inp["P"] > 0:
        ratio_pv = inp["P"] / f["Valor_acao"]
        verifica(0.05 <= ratio_pv <= 20,
                 "Sanidade: P/Valor_acao entre 0.05x e 20x",
                 f"P/Valor_acao = {fmt(ratio_pv, 2)}x" + (
                     " !! POSSIVEL ERRO DE UNIDADE nos inputs financeiros"
                     if not (0.05 <= ratio_pv <= 20) else ""
                 ),
                 ok, falhas)

    return {
        "inp": inp,
        "a": a,
        "proj": proj,
        "vp_total": vp_total,
        "d": d,
        "e": e,
        "f": f,
        "ok": ok,
        "falhas": falhas,
    }


# ---------------------------------------------------------------------------
# OUTPUT FORMATADO
# ---------------------------------------------------------------------------

def imprimir_resultado(result: dict) -> str:
    """Formata o resultado final conforme a especificacao do Passo 4."""
    inp = result["inp"]
    a = result["a"]
    proj = result["proj"]
    vp_total = result["vp_total"]
    d = result["d"]
    e = result["e"]
    f = result["f"]
    ok = result["ok"]
    falhas = result["falhas"]

    linhas = []
    L = linhas.append

    L("=" * 80)
    L(f"  DCF VALUATION -- {inp['nome']} ({inp['ticker']})")
    L(f"  Pais: {inp['pais']} | Setor: {inp['setor']} | Moeda: {inp['moeda']} ({inp['unidade']})")
    L("=" * 80)

    # ------------------------------------------------------------------
    # Tabela 1 -- Parametros de Capital
    # ------------------------------------------------------------------
    L("")
    L("  TABELA 1 -- PARAMETROS DE CAPITAL")
    L("  " + "-" * 60)
    L(f"  Beta desalavancado:              {fmt(inp['Beta_u'], 4)}")
    L(f"  Beta alavancado:                 {fmt(a['Beta_L'], 4)}")
    L(f"  Custo de capital proprio (Ke):   {pct(a['Ke'], 2)}")
    L(f"  Custo da divida liquido (Kd):    {pct(a['Kd_liq'], 2)}")
    L(f"  Peso equity / divida:            {pct(a['W_equity'], 2)} / {pct(a['W_debt'], 2)}")
    L(f"  WACC inicial:                    {pct(a['WACC_0'], 2)}")
    L(f"  WACC estavel:                    {pct(inp['WACC_est'], 2)}")

    # ------------------------------------------------------------------
    # Tabela 2 -- Projecao Anual Completa
    # ------------------------------------------------------------------
    L("")
    L("  TABELA 2 -- PROJECAO ANUAL COMPLETA")
    L("")
    headers = ["Ano", "g(t)", "Receita", "Mg EBIT", "EBIT", "IR",
               "NOPAT", "Reinvest", "FCFF", "WACC", "Fator", "VP(FCFF)"]
    rows = []
    for r in proj:
        t = r["t"]
        rows.append([
            str(t),
            pct(r["g"], 1),
            fmt(r["Rev"], 2),
            pct(r["Mg"], 1),
            fmt(r["EBIT"], 2),
            pct(r["IR"], 2),
            fmt(r["NOPAT"], 2),
            fmt(r["Reinvest"], 2),
            fmt(r["FCFF"], 2),
            pct(r["WACC"], 2),
            fmt(r["Fator"], 4),
            fmt(r["VP_FCFF"], 2),
        ])
    # Linha Terminal
    rows.append([
        "Term",
        pct(inp["g_perp"], 1),
        fmt(d["Rev_term"], 2),
        pct(inp["Mg_alvo"], 1),
        fmt(d["EBIT_term"], 2),
        pct(inp["IR_marg"], 2),
        fmt(d["NOPAT_term"], 2),
        "--",
        fmt(d["FCFF_term"], 2),
        pct(inp["WACC_est"], 2),
        fmt(d["Fator_10"], 4),
        fmt(d["VP_VT"], 2),
    ])
    L(tabela(headers, rows))

    L(f"  VP total (anos 1-10): {fmt(vp_total, 2)} M")

    # ------------------------------------------------------------------
    # Tabela 3 -- Resumo de Valor
    # ------------------------------------------------------------------
    L("")
    L("  TABELA 3 -- RESUMO DE VALOR")
    L("")
    L(f"  VP dos FCFFs (anos 1-10):              {fmt(vp_total, 2)} M")
    L(f"  Valor Terminal (bruto):                {fmt(d['VT'], 2)} M")
    L(f"  VP do Valor Terminal:                  {fmt(d['VP_VT'], 2)} M   ({fmt(d['pct_vt'], 1)}% do total)")
    L(f"  ---------------------------------------------")
    L(f"  Valor dos Ativos Operacionais:         {fmt(f['Valor_op'], 2)} M")
    L(f"  (+) Caixa e equivalentes:             {fmt(inp['Caixa'], 2)} M")
    L(f"  (+) Outros ativos nao operacionais:   {fmt(inp['AtvNOp'], 2)} M")
    L(f"  (−) Divida total:                     {fmt(inp['D'], 2)} M")
    L(f"  (−) Participacoes minoritarias:        {fmt(inp['MinInt'], 2)} M")
    L(f"  (−) Valor das opcoes:                 {fmt(f['Valor_opcoes'], 2)} M")
    L(f"  ---------------------------------------------")
    L(f"  Equity Value:                          {fmt(f['Equity_Value'], 2)} M")
    L(f"  Acoes em circulacao:                   {fmt(inp['Shares'], 1)} M")
    L(f"  ---------------------------------------------")
    L(f"  VALOR POR ACAO (intrinseco):           {fmt(f['Valor_acao'], 4)}")
    L(f"  Preco de mercado:                      {fmt(inp['P'], 2)}")

    premio_pct = f["Premio"] * 100
    if f["Premio"] > 0:
        diag = f"SOBREVALORIZADA em {fmt(abs(premio_pct), 1)}%"
    elif f["Premio"] < 0:
        diag = f"SUBVALORIZADA em {fmt(abs(premio_pct), 1)}%"
    else:
        diag = "proxima do VALOR JUSTO"
    L(f"  Sobre(sub)valorizacao:                 {fmt(premio_pct, 1)}%  -> {diag}")

    # Bloco E (se aplicavel)
    if inp["P_fail"] > 0:
        L("")
        L(f"  !! AJUSTE DE FALENCIA aplicado (P_fail = {pct(inp['P_fail'], 1)})")
        L(f"    Valor em distress: {fmt(e['Valor_distress'], 2)} M")
        L(f"    Valor operacional ajustado: {fmt(e['Valor_op_ajustado'], 2)} M")

    # Black-Scholes (se aplicavel)
    if f["Valor_opcoes"] > 0:
        L("")
        L(f"  Black-Scholes: valor unitario da opcao = {fmt(f['Valor_opcao_unit'], 4)}")
        L(f"  Total opcoes ({inp['N_opt']} unidades): {fmt(f['Valor_opcoes'], 2)} M")

    # Alerta de % VT
    if not (40 <= d["pct_vt"] <= 75):
        L("")
        if d["pct_vt"] > 75:
            L("  !! ALERTA: VP do VT > 75% -- valor depende muito das premissas de longo prazo.")
        else:
            L("  !! ALERTA: VP do VT < 40% -- verificar se WACC nao esta superestimado.")

    # ------------------------------------------------------------------
    # Checklist de Verificacao
    # ------------------------------------------------------------------
    L("")
    L("  CHECKLIST DE VERIFICACAO FINAL")
    L("  " + "-" * 60)
    for nome, det in ok:
        L(f"  [OK] {nome}")
        L(f"      -> {det}")
    for nome, det in falhas:
        L(f"  [XX] {nome}  <- FALHOU")
        L(f"      -> {det}")

    # Alerta critico se houver suspeita de erro de unidade
    if any("ERRO DE UNIDADE" in det for _, det in falhas):
        L("")
        L("  !! ALERTA CRITICO: POSSIVEL ERRO DE UNIDADE nos inputs!")
        L(f"  Certifique-se de que Rev_0, D, Caixa, AtvNOp e MinInt estao em {inp['unidade']}")
        L(f"  (mesma escala de P x Shares = MktCap = {fmt(a['MktCap'], 1)} {inp['unidade']}).")
        L("  Exemplo: se Shares=399.087 (M) e P=7.01, MktCap=2.797,6 M,")
        L("  entao Rev_0=1186 (M), D=650 (M), Caixa=260 (M) -- NAO 1.186, 0.65, 0.26.")

    L("")
    L("=" * 80)

    if falhas:
        L("  !! ATENCAO: Ha verificacoes que FALHARAM. Revise as premissas antes de usar.")
    else:
        L("  OK Todas as verificacoes passaram.")

    L("=" * 80)

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Passo 4 -- Execucao do Modelo DCF (Metodologia Damodaran)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python step4_dcf.py Acoes/FIQE3/step3.json
  python step4_dcf.py step4_resultado.json --output resultado.json
        """
    )
    parser.add_argument(
        "input", type=str,
        help="Caminho para o JSON do Passo 3 (consolidado)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Caminho para salvar o JSON de saida (opcional)"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suprimir saida formatada (util com --output)"
    )
    parser.add_argument(
        "--json-only", action="store_true",
        help="Emitir apenas o JSON de saida no stdout"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERRO: Arquivo nao encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        result = executar_dcf(str(input_path))
    except Exception as ex:
        print(f"ERRO na execucao do DCF: {ex}", file=sys.stderr)
        raise

    # Monta o JSON de saida
    output_json = {
        "meta": {
            "gerado_em": "",
            "script": "step4_dcf.py",
            "input": str(input_path),
            "empresa": {
                "nome": result["inp"]["nome"],
                "ticker": result["inp"]["ticker"],
                "pais": result["inp"]["pais"],
                "setor": result["inp"]["setor"],
                "moeda": result["inp"]["moeda"],
                "unidade": result["inp"]["unidade"],
            }
        },
        "bloco_a": {
            "MktCap": result["a"]["MktCap"],
            "Beta_L": result["a"]["Beta_L"],
            "Ke": result["a"]["Ke"],
            "Kd_liq": result["a"]["Kd_liq"],
            "W_equity": result["a"]["W_equity"],
            "W_debt": result["a"]["W_debt"],
            "WACC_0": result["a"]["WACC_0"],
            "wacc_por_ano": {str(k): v for k, v in result["a"]["wacc_por_ano"].items()},
            "ir_por_ano": {str(k): v for k, v in result["a"]["ir_por_ano"].items()},
        },
        "bloco_b_c": [
            {
                "t": r["t"],
                "g": r["g"],
                "Rev": r["Rev"],
                "Mg": r["Mg"],
                "EBIT": r["EBIT"],
                "IR": r["IR"],
                "NOPAT": r["NOPAT"],
                "Reinvest": r["Reinvest"],
                "FCFF": r["FCFF"],
                "WACC": r["WACC"],
                "Fator": r["Fator"],
                "VP_FCFF": r["VP_FCFF"],
            }
            for r in result["proj"]
        ],
        "VP_total": result["vp_total"],
        "bloco_d": {
            "Rev_term": result["d"]["Rev_term"],
            "EBIT_term": result["d"]["EBIT_term"],
            "NOPAT_term": result["d"]["NOPAT_term"],
            "ROIC_term": result["d"]["ROIC_term"],
            "ReinvRate_term": result["d"]["ReinvRate_term"],
            "FCFF_term": result["d"]["FCFF_term"],
            "denominador": result["d"]["denominador"],
            "VT": result["d"]["VT"],
            "Fator_10": result["d"]["Fator_10"],
            "VP_VT": result["d"]["VP_VT"],
            "pct_vt": result["d"]["pct_vt"],
        },
        "bloco_e": {
            "P_fail": result["inp"]["P_fail"],
            "Valor_op": result["e"]["Valor_op"],
            "ajuste_aplicado": result["e"]["ajuste_aplicado"],
        },
        "bloco_f": {
            "Valor_op": result["f"]["Valor_op"],
            "Caixa": result["f"]["Caixa"],
            "AtvNOp": result["f"]["AtvNOp"],
            "D": result["f"]["D"],
            "MinInt": result["f"]["MinInt"],
            "Valor_opcoes": result["f"]["Valor_opcoes"],
            "Valor_opcao_unit": result["f"]["Valor_opcao_unit"],
            "Equity_Value": result["f"]["Equity_Value"],
            "Shares": result["f"]["Shares"],
            "Valor_acao": result["f"]["Valor_acao"],
            "P": result["f"]["P"],
            "Premio": result["f"]["Premio"],
        },
        "checklist": [
            {"nome": nome, "ok": True, "detalhe": det} for nome, det in result["ok"]
        ] + [
            {"nome": nome, "ok": False, "detalhe": det} for nome, det in result["falhas"]
        ],
        "inputs_usados": {
            "Rev_0": result["inp"]["Rev_0"],
            "D": result["inp"]["D"],
            "Caixa": result["inp"]["Caixa"],
            "AtvNOp": result["inp"]["AtvNOp"],
            "MinInt": result["inp"]["MinInt"],
            "P": result["inp"]["P"],
            "Shares": result["inp"]["Shares"],
            "IR_ef": result["inp"]["IR_ef"],
            "Rf": result["inp"]["Rf"],
            "ERP": result["inp"]["ERP"],
            "Beta_u": result["inp"]["Beta_u"],
            "Kd_pre": result["inp"]["Kd_pre"],
            "IR_marg": result["inp"]["IR_marg"],
            "WACC_est": result["inp"]["WACC_est"],
            "g1": result["inp"]["g1"],
            "g2_5": result["inp"]["g2_5"],
            "Mg_1": result["inp"]["Mg_1"],
            "Mg_alvo": result["inp"]["Mg_alvo"],
            "Ano_conv": result["inp"]["Ano_conv"],
            "StC": result["inp"]["StC"],
            "g_perp": result["inp"]["g_perp"],
            "P_fail": result["inp"]["P_fail"],
            "V_fail": result["inp"]["V_fail"],
            "N_opt": result["inp"]["N_opt"],
            "K_opt": result["inp"]["K_opt"],
            "T_opt": result["inp"]["T_opt"],
            "Sigma": result["inp"]["Sigma"],
        }
    }

    if args.json_only:
        sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
        print(json.dumps(output_json, indent=2, ensure_ascii=False))
    else:
        if not args.quiet:
            sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
            print(imprimir_resultado(result))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)
        if not args.quiet:
            print(f"\nJSON salvo em: {out_path.resolve()}")


if __name__ == "__main__":
    main()
