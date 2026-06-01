# DCF Valuation Pipeline

A local DCF (Discounted Cash Flow) valuation system for Brazilian equities using the Damodaran methodology. An AI agent extracts financial data from company earnings releases (PDFs), runs a structured 5-step pipeline, and presents the results in a web dashboard with inline editing.

<img width="1260" height="720" alt="image" src="https://github.com/user-attachments/assets/fc97c30a-0bd0-42fa-8181-41c3e72a2903" />
<img width="640" height="420" alt="image" src="https://github.com/user-attachments/assets/bcfa4bdd-990e-4ca6-9877-314e3482d071" />


## Features

- **5-step pipeline** driven by an AI coding agent (`pi`) — from PDF extraction to sensitivity analysis
- **Web dashboard** — lists all analyzed tickers, detail view per company with all pipeline steps
- **Inline editing** — edit any extracted or assumed value directly in the browser; saves back to JSON instantly
- **One-click recalculation** — after editing step 1 or 2, hit "Recalcular DCF" in step 4 to rerun the model
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
│       ├── step1.json           # extracted financials
│       ├── step2.json           # market parameters
│       ├── step3.json           # analyst assumptions
│       ├── step4.json           # DCF calculation output
│       └── step5.json           # sensitivity / scenarios
│
├── Valuation/
│   ├── script/
│   │   ├── valuation_pipeline.py   # pipeline orchestrator
│   │   └── step4_dcf.py            # DCF calculation engine
│   ├── web/
│   │   ├── server.py               # local HTTP server
│   │   ├── index.html              # SPA shell
│   │   ├── style.css               # styles
│   │   └── app.js                  # frontend logic
│   ├── data/
│   │   ├── beta-by-sector.md       # Damodaran beta table
│   │   ├── country-default-spreads-and-risk-premiums.md
│   │   └── ratings.md              # synthetic rating spreads
│   └── instructions/
│       ├── 00_pipeline_index.md        # pipeline index and transition rules
│       ├── step{1-5}_*.md              # step instructions for the AI agent
│       └── system_prompt_agente_dcf.md # AI agent system prompt
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

Steps 1–3 and 5 are handled by the `pi` AI agent. Step 4 runs `step4_dcf.py` directly as a Python script.

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
| **1** | Release Extraction | AI agent reads the earnings PDF and extracts income statement, balance sheet, and market data into JSON |
| **2** | Market Parameters | AI agent looks up Damodaran tables (ERP, beta, ratings) and calculates WACC inputs |
| **3** | Analyst Assumptions | AI agent consolidates all data and sets growth, margin, and perpetuity assumptions |
| **4** | DCF Calculation | Python script runs the full Damodaran DCF model (WACC → FCFF projections → terminal value → equity bridge) |
| **5** | Sensitivity / Scenarios | AI agent runs bear/base/bull scenarios and breakeven analysis |

## Dashboard Overview

**List view** — one card per ticker showing market price vs. intrinsic value, upside/downside badge, and pipeline completion bar.

**Detail view** — accordion with one section per step:
- **Step 1**: DRE, balance sheet, and market data tables with confidence indicators
- **Step 2**: Cost of capital parameters with source references and alerts
- **Step 3**: Assumption cards (growth rates, margins, perpetuity) + analyst narrative
- **Step 4**: KPI summary, 10-year FCF projection table with visual bars, equity value bridge, validation checklist, and **Recalcular DCF** button
- **Step 5**: Bear/Base/Bull scenario cards and breakeven sensitivity table

All numeric fields are **editable inline** — click any value, type the new number, press Enter to save. The JSON file is updated immediately on disk.

## Recalculating After Edits

The **▶ Recalcular DCF** button in Step 4:
1. Reads current `step1.json` and propagates financials → `step3.dados_historicos` / `dados_mercado`
2. Reads current `step2.json` and propagates cost of capital → `step3.parametros_custo_capital`
3. Saves the updated `step3.json`
4. Runs `step4_dcf.py` and writes the new `step4.json`
5. Re-renders the dashboard in place — no page reload needed

## Server API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tickers` | List of ticker folders in `Acoes/` |
| `PUT` | `/api/passo/<ticker>/<n>` | Overwrite `Acoes/<ticker>/step<n>.json` |
| `POST` | `/api/run-passo4/<ticker>` | Propagate edits and rerun the DCF script |
| `GET` | `/*` | Static file serving from `Market/` root |
