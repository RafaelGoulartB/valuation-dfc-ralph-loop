# DCF Valuation Pipeline

A local DCF (Discounted Cash Flow) valuation system for Brazilian equities using the Damodaran methodology. An AI agent extracts financial data from company earnings releases (PDFs), runs a structured 5-step pipeline, and presents the results in a web dashboard with inline editing.

## Features

- **5-step pipeline** driven by an AI coding agent (`pi`) — from PDF extraction to sensitivity analysis
- **Web dashboard** — lists all analyzed tickers, detail view per company with all pipeline steps
- **Inline editing** — edit any extracted or assumed value directly in the browser; saves back to JSON instantly
- **One-click recalculation** — after editing passo 1 or 2, hit "Recalcular DCF" in passo 4 to rerun the model
- **Zero frontend dependencies** — vanilla HTML/CSS/JS, served by Python stdlib `http.server`

## Requirements

- Python 3.8+
- [`pi`](https://github.com/earendil-works/pi) CLI (`npm install -g @earendil-works/pi-coding-agent`)
- `pypdf` (`pip install pypdf`)

## Project Structure

```
Market/
├── Acoes/
│   └── <TICKER>/
│       ├── release.pdf          # earnings release (pipeline input)
│       ├── passo1.json          # extracted financials
│       ├── passo2.json          # market parameters
│       ├── passo3.json          # analyst assumptions
│       ├── passo4.json          # DCF calculation output
│       └── passo5.json          # sensitivity / scenarios
│
├── Valuation/
│   ├── script/
│   │   ├── valuation_pipeline.py   # pipeline orchestrator
│   │   └── passo4_dcf.py           # DCF calculation engine
│   ├── web/
│   │   ├── server.py               # local HTTP server
│   │   ├── index.html              # SPA shell
│   │   ├── style.css               # styles
│   │   └── app.js                  # frontend logic
│   ├── data/
│   │   ├── beta-by-sector.md       # Damodaran beta table
│   │   ├── country-default-spreads-and-risk-premiums.md
│   │   └── ratings.md              # synthetic rating spreads
│   └── passo{1-5}_*.md             # step instructions for the AI agent
```

## Running the Pipeline

Place the earnings release PDF at `Acoes/<TICKER>/release.pdf`, then:

```bash
# Run all 5 steps
python Valuation/script/valuation_pipeline.py FIQE3

# Resume from a specific step
python Valuation/script/valuation_pipeline.py FIQE3 --start-from 3

# Run only one step
python Valuation/script/valuation_pipeline.py FIQE3 --only 1

# Dry run (print prompts, don't execute)
python Valuation/script/valuation_pipeline.py FIQE3 --dry-run
```

Steps 1–3 and 5 are handled by the `pi` AI agent. Step 4 runs `passo4_dcf.py` directly as a Python script.

## Running the Dashboard

```bash
# From the Market/ root
python Valuation/web/server.py

# Custom port
python Valuation/web/server.py 3000
```

Open **http://localhost:8000/Valuation/web/** in your browser.

## The 5-Step Pipeline

| Step | Name | What happens |
|------|------|--------------|
| **1** | Extração do Release | AI agent reads the earnings PDF and extracts DRE, balance sheet, and market data into JSON |
| **2** | Parâmetros de Mercado | AI agent looks up Damodaran tables (ERP, beta, ratings) and calculates WACC inputs |
| **3** | Premissas do Analista | AI agent consolidates all data and sets growth, margin, and perpetuity assumptions |
| **4** | Cálculo DCF | Python script runs the full Damodaran DCF model (WACC → FCFF projections → terminal value → equity bridge) |
| **5** | Sensibilidade / Cenários | AI agent runs bear/base/bull scenarios and breakeven analysis |

## Dashboard Overview

**List view** — one card per ticker showing market price vs. intrinsic value, upside/downside badge, and pipeline completion bar.

**Detail view** — accordion with one section per step:
- **Passo 1**: DRE, balance sheet, and market data tables with confidence indicators
- **Passo 2**: Cost of capital parameters with source references and alerts
- **Passo 3**: Assumption cards (growth rates, margins, perpetuity) + analyst narrative
- **Passo 4**: KPI summary, 10-year FCF projection table with visual bars, equity value bridge, validation checklist, and **Recalcular DCF** button
- **Passo 5**: Bear/Base/Bull scenario cards and breakeven sensitivity table

All numeric fields are **editable inline** — click any value, type the new number, press Enter to save. The JSON file is updated immediately on disk.

## Recalculating After Edits

The **▶ Recalcular DCF** button in Passo 4:
1. Reads current `passo1.json` and propagates financials → `passo3.dados_historicos` / `dados_mercado`
2. Reads current `passo2.json` and propagates cost of capital → `passo3.parametros_custo_capital`
3. Saves the updated `passo3.json`
4. Runs `passo4_dcf.py` and writes the new `passo4.json`
5. Re-renders the dashboard in place — no page reload needed

## Server API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tickers` | List of ticker folders in `Acoes/` |
| `PUT` | `/api/passo/<ticker>/<n>` | Overwrite `Acoes/<ticker>/passo<n>.json` |
| `POST` | `/api/run-passo4/<ticker>` | Propagate edits and rerun the DCF script |
| `GET` | `/*` | Static file serving from `Market/` root |
