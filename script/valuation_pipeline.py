#!/usr/bin/env python3
"""
valuation_pipeline.py — Ralph Loop para o valuation DCF Damodaran.

Uso:
    python Valuation/script/valuation_pipeline.py <TICKER>
    python Valuation/script/valuation_pipeline.py <TICKER> --start-from 3
    python Valuation/script/valuation_pipeline.py <TICKER> --only 1
    python Valuation/script/valuation_pipeline.py <TICKER> --dry-run

Requer: `pi` instalado e acessível no PATH.
Release em: Acoes/<TICKER>/release.pdf
Outputs em: Acoes/<TICKER>/step{N}.json  (step5 também gera step5.txt)
"""

import subprocess
import sys
import json
import re
import os
import time
import io
import shutil
import tempfile
from pathlib import Path

# Forcar UTF-8 no console Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Caminhos base ───────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
MARKET     = SCRIPT_DIR.parent.parent          # .../Market
VAL        = MARKET / "Valuation"

INST = {
    1: VAL / "instructions" / "step1_release_extraction.md",
    2: VAL / "instructions" / "step2_market_parameters.md",
    3: VAL / "instructions" / "step3_analyst_assumptions.md",
    4: VAL / "instructions" / "step4_dcf_calculation.md",
    5: VAL / "instructions" / "step5_sensitivity_scenarios.md",
}

DATA = {
    "erp":     VAL / "data" / "country-default-spreads-and-risk-premiums.md",
    "beta":    VAL / "data" / "beta-by-sector.md",
    "ratings": VAL / "data" / "ratings.md",
}

DCF_SCRIPT = SCRIPT_DIR / "step4_dcf.py"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def sep(title: str = ""):
    line = "=" * 60
    if title:
        print(f"\n{line}\n  {title}\n{line}")
    else:
        print(line)

def log(msg: str):
    print(f"  {msg}")

def abort(msg: str):
    print(f"\n[ERRO] {msg}", file=sys.stderr)
    sys.exit(1)

def _resolve_pi() -> tuple:
    """
    Retorna (node_exe, pi_js_path).
    Prefere chamar node diretamente sobre o cli.js do pi para evitar
    problemas de PATH do cmd.exe com pi.CMD no Windows.
    """
    node_exe = shutil.which("node")
    pi_cmd   = shutil.which("pi")

    if not pi_cmd:
        abort("Comando `pi` nao encontrado. Instale o pi CLI e adicione ao PATH.")

    # Extrair o caminho do .js a partir do conteudo do pi.CMD
    try:
        content = Path(pi_cmd).read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'"%dp0%\\([^"]+\.js)"', content)
        if m:
            pi_js = Path(pi_cmd).parent / m.group(1).replace("\\", os.sep)
            if pi_js.exists() and node_exe:
                return node_exe, pi_js
    except Exception:
        pass

    # Fallback: tentar localizar cli.js pelo padrao npm
    npm_dir = Path(pi_cmd).parent
    for candidate in [
        npm_dir / "node_modules" / "@earendil-works" / "pi-coding-agent" / "dist" / "cli.js",
        npm_dir / "node_modules" / "pi" / "dist" / "cli.js",
        npm_dir / "node_modules" / "pi" / "cli.js",
    ]:
        if candidate.exists() and node_exe:
            return node_exe, candidate

    return None, None  # sinaliza: usar pi.CMD diretamente


def run_pi(prompt: str, cwd: Path = None, dry_run: bool = False) -> str:
    """
    Escreve o prompt em arquivo temp e chama: node cli.js -p @<tempfile>
    cwd: pasta do ticker — limita o escaneamento de codebase do pi.
    """
    node_exe, pi_js = _resolve_pi()
    pi_cmd = shutil.which("pi")

    if not (node_exe and pi_js) and not pi_cmd:
        abort("pi / node nao encontrado. Verifique a instalacao.")

    run_cwd = str(cwd) if cwd else None

    fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="pi_prompt_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(prompt)
        tmp = Path(tmp_path)

        if node_exe and pi_js:
            cmd_parts = [node_exe, str(pi_js), "-p", f"@{tmp}"]
            use_shell = False
        else:
            cmd_parts = f'"{pi_cmd}" -p "@{tmp}"'
            use_shell = True

        display = f"node cli.js -p @<tempfile {len(prompt):,} chars>"

        if dry_run:
            print(f"\n[DRY-RUN] {display}" + (f"  cwd={run_cwd}" if run_cwd else ""))
            return '{"dry_run": true}'

        log(f"Chamando pi ({len(prompt):,} chars no prompt)...")
        t0 = time.time()
        result = subprocess.run(
            cmd_parts,
            shell=use_shell,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=run_cwd,
        )
        elapsed = time.time() - t0
        log(f"pi concluiu em {elapsed:.1f}s")

        if result.returncode != 0:
            print(f"\n[STDERR pi]\n{result.stderr[:2000]}", file=sys.stderr)
            abort(f"pi retornou codigo {result.returncode}")

        return result.stdout

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

def extract_json(text: str, raw_path: Path = None) -> dict:
    """
    Extrai o primeiro JSON válido da resposta do pi.
    Tenta: bloco ```json ... ``` → bloco ``` ... ``` → { ... } bruto.
    """
    # Bloco explícito ```json
    m = re.search(r"```json\s*([\s\S]+?)\s*```", text)
    if m:
        return json.loads(m.group(1))

    # Bloco genérico ``` (pode ser JSON sem label)
    m = re.search(r"```\s*(\{[\s\S]+?\})\s*```", text)
    if m:
        return json.loads(m.group(1))

    # JSON bruto — pegar o maior objeto { } da resposta
    candidates = list(re.finditer(r"\{", text))
    for start_m in reversed(candidates):  # tentar do maior para o menor
        start = start_m.start()
        depth = 0
        for i, ch in enumerate(text[start:]):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : start + i + 1])
                    except json.JSONDecodeError:
                        break
    if raw_path:
        raw_path.write_text(text, encoding="utf-8")
        log(f"[!] Resposta bruta salva em: {raw_path}")
    preview = text[:500].replace("\n", " ")
    raise ValueError(f"Nenhum JSON valido encontrado. Primeiros 500 chars: {preview!r}")

def save_json(data: dict, path: Path):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"[OK] Salvo: {path.relative_to(MARKET)}")

def save_text(text: str, path: Path):
    path.write_text(text, encoding="utf-8")
    log(f"[OK] Salvo: {path.relative_to(MARKET)}")

def read_pi_output(raw: str, target: Path, acoes: Path) -> dict:
    """
    Pi e um agente que salva arquivos — preferir ler o arquivo que ele escreveu.
    Fallback: extrair JSON do stdout.
    Fallback 2: ler qualquer .json recente na pasta do ticker.
    """
    # 1. Arquivo no caminho esperado
    if target.exists() and target.stat().st_size > 10:
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            log(f"[OK] Lido arquivo salvo pelo pi: {target.name}")
            return data
        except json.JSONDecodeError:
            pass

    # 2. Procurar qualquer .json recente na pasta (pi pode ter errado o nome)
    import time as _time
    now = _time.time()
    for jf in sorted(acoes.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        if now - jf.stat().st_mtime < 3600:  # modificado na ultima hora
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
                log(f"[OK] Encontrado JSON recente: {jf.name} — copiando para {target.name}")
                return data
            except json.JSONDecodeError:
                continue

    # 3. Extrair do stdout
    log("[!] Pi nao salvou arquivo — extraindo JSON do stdout...")
    return extract_json(raw, raw_path=acoes / (target.stem + "_raw.txt"))

# Palavras-chave que indicam paginas com dados financeiros
_FIN_KEYWORDS = [
    "receita", "ebitda", "ebit", "resultado", "lucro", "prejuizo",
    "balanco", "patrimonio", "divida", "caixa", "dre", "demonstracao",
    "financeiro", "ativo", "passivo", "capex", "depreciacao",
    "revenue", "income", "balance", "equity", "debt",
]

def extract_pdf_text(pdf_path: Path, max_chars: int = 80_000) -> str:
    """
    Extrai texto do PDF com pypdf e retorna ate max_chars chars.
    Prioriza paginas com maior densidade de termos financeiros.
    Retorna string com cabecalho indicando paginas incluidas.
    """
    try:
        import pypdf
    except ImportError:
        abort("pypdf nao instalado. Execute: pip install pypdf")

    reader = pypdf.PdfReader(str(pdf_path))
    n_pages = len(reader.pages)

    # Extrair texto de cada pagina
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append((i, text))

    total_chars = sum(len(t) for _, t in pages)
    log(f"PDF: {n_pages} paginas, {total_chars:,} chars extraidos")

    if total_chars <= max_chars:
        # Cabe tudo — incluir todas as paginas em ordem
        parts = [f"\n=== Pagina {i+1}/{n_pages} ===\n{t}" for i, t in pages if t.strip()]
        return f"[Release: {n_pages} paginas — texto completo]\n" + "".join(parts)

    # Selecionar paginas mais relevantes por densidade de palavras-chave
    log(f"PDF maior que {max_chars:,} chars — selecionando paginas relevantes...")
    scored: list[tuple[int, int, str]] = []
    for i, text in pages:
        tl = text.lower()
        score = sum(tl.count(kw) for kw in _FIN_KEYWORDS)
        scored.append((score, i, text))

    scored.sort(key=lambda x: (-x[0], x[1]))  # maior score primeiro

    selected: list[tuple[int, str]] = []
    used = 0
    for score, i, text in scored:
        part = f"\n=== Pagina {i+1}/{n_pages} ===\n{text}"
        if used + len(part) > max_chars:
            break
        selected.append((i, part))
        used += len(part)

    selected.sort(key=lambda x: x[0])  # reordenar por numero de pagina
    included = [i+1 for i, _ in selected]
    header = f"[Release: {n_pages} paginas — exibindo paginas {included} por relevancia financeira]\n"
    return header + "".join(p for _, p in selected)

# ─── Passos ──────────────────────────────────────────────────────────────────

def passo1(acoes: Path, ticker: str, dry_run: bool):
    sep("PASSO 1 — Extração do Release")
    release = acoes / "release.pdf"
    if not release.exists():
        abort(f"PDF não encontrado: {release}")

    # Extrair texto do PDF localmente — evita estourar o contexto do pi
    # (PDF binario passado como @file pode gerar 700k+ tokens)
    if dry_run:
        pdf_content = "[DRY-RUN: conteudo do PDF seria extraido aqui]"
        log(f"[DRY-RUN] Extracao de PDF simulada")
    else:
        pdf_content = extract_pdf_text(release, max_chars=80_000)

    instructions = txt(INST[1])
    prompt = f"""{instructions}

--------------------------------------------
INSTRUÇÃO DE EXECUÇÃO (modo não-interativo):
--------------------------------------------
Ticker: {ticker}

Execute as FASES 1 a 5 internamente.
Execute a FASE 6 e produza o JSON de saída.

IMPORTANTE: use sua ferramenta de escrita de arquivos para salvar o JSON
exatamente no arquivo `step1.json` no diretorio atual.
O JSON deve seguir o template da FASE 6. Nenhum campo pode ser omitido.

--------------------------------------------
CONTEUDO DO RELEASE (extraido do PDF):
--------------------------------------------
{pdf_content}
"""
    raw = run_pi(prompt, cwd=acoes, dry_run=dry_run)
    data = read_pi_output(raw, target=acoes / "step1.json", acoes=acoes)
    save_json(data, acoes / "step1.json")


def passo2(acoes: Path, ticker: str, dry_run: bool):
    sep("PASSO 2 — Parâmetros de Mercado")
    p1 = txt(acoes / "step1.json")
    instructions = txt(INST[2])
    erp  = txt(DATA["erp"])
    beta = txt(DATA["beta"])
    rtg  = txt(DATA["ratings"])

    prompt = f"""{instructions}

--------------------------------------------
DADOS DE ENTRADA
--------------------------------------------

## step1.json (dados históricos extraídos do release):
```json
{p1}
```

## country-default-spreads-and-risk-premiums.md (tabela ERP):
{erp}

## beta-by-sector.md (tabela Beta desalavancado por setor):
{beta}

## ratings.md (spreads por rating sintético):
{rtg}

--------------------------------------------
INSTRUÇÃO DE EXECUÇÃO (modo não-interativo):
--------------------------------------------
Ticker: {ticker}

Execute os itens 2.1 a 2.6 usando os dados acima.
Para Rf (item 2.1): como não há acesso à internet, use o valor mais recente de Rf
implícito nos dados (se disponível no step1.json) ou registre como PENDENTE.
Se Kd_pre < Rf: tente o método alternativo (rating sintético) antes de marcar BLOQUEADOR.

IMPORTANTE: use sua ferramenta de escrita de arquivos para salvar o JSON
exatamente no arquivo `step2.json` no diretorio atual.
O JSON deve seguir o template do JSON de saída do Passo 2. Nenhum campo pode ser omitido.
"""
    raw = run_pi(prompt, cwd=acoes, dry_run=dry_run)
    data = read_pi_output(raw, target=acoes / "step2.json", acoes=acoes)
    save_json(data, acoes / "step2.json")


def passo3(acoes: Path, ticker: str, dry_run: bool):
    sep("PASSO 3 — Premissas do Analista")
    p1 = txt(acoes / "step1.json")
    p2 = txt(acoes / "step2.json")
    instructions = txt(INST[3])
    erp  = txt(DATA["erp"])
    beta = txt(DATA["beta"])

    prompt = f"""{instructions}

--------------------------------------------
DADOS DE ENTRADA
--------------------------------------------

## step1.json:
```json
{p1}
```

## step2.json:
```json
{p2}
```

## Referência setorial — country-default-spreads-and-risk-premiums.md:
{erp}

## Referência setorial — beta-by-sector.md (inclui Sales/Capital e margens):
{beta}

--------------------------------------------
INSTRUÇÃO DE EXECUÇÃO (modo não-interativo):
--------------------------------------------
Ticker: {ticker}

Você está operando sem analista disponível.
1. Execute o BLOCO 0 completamente (verificações A–E). Se qualquer verificação falhar,
   registre o problema no campo "validacoes" e use os dados corretos disponíveis.
2. Para cada PREMISSA 3.1–3.9: use a âncora histórica e a regra de calibração para
   definir o valor mais justificado pelos dados. Não deixe nulos nas premissas.
3. Execute a validação de ROIC_term após definir Mg_alvo e StC.
4. Preencha "narrativa_premissas" com frases curtas justificando as escolhas.

IMPORTANTE: use sua ferramenta de escrita de arquivos para salvar o JSON
exatamente no arquivo `step3.json` no diretorio atual.
O JSON deve seguir o template do JSON de saída do Passo 3. Nenhum campo pode ser omitido.
"""
    raw = run_pi(prompt, cwd=acoes, dry_run=dry_run)
    data = read_pi_output(raw, target=acoes / "step3.json", acoes=acoes)
    save_json(data, acoes / "step3.json")


def passo4(acoes: Path, ticker: str, dry_run: bool):
    sep("PASSO 4 — Cálculo DCF (script Python)")
    p3_json = acoes / "step3.json"
    p4_json = acoes / "step4.json"

    if not p3_json.exists():
        abort(f"step3.json não encontrado: {p3_json}")
    if not DCF_SCRIPT.exists():
        abort(f"Script DCF não encontrado: {DCF_SCRIPT}")

    cmd = [sys.executable, str(DCF_SCRIPT), str(p3_json), "--output", str(p4_json)]
    log(f"Executando: {' '.join(str(c) for c in cmd)}")

    if dry_run:
        log("[DRY-RUN] Passo 4 não executado.")
        return

    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        abort(f"step4_dcf.py falhou com código {result.returncode}")
    log(f"[OK] Salvo: Acoes/{ticker}/step4.json")


def passo5(acoes: Path, ticker: str, dry_run: bool):
    sep("PASSO 5 — Sensibilidade e Cenários")
    if dry_run:
        log("[DRY-RUN] Passo 5 - leria step3.json + step4.json e chamaria pi.")
        log("[DRY-RUN] Salvaria step5.txt e step5.json")
        return
    p3 = txt(acoes / "step3.json")
    p4 = txt(acoes / "step4.json")
    instructions = txt(INST[5])

    prompt = f"""{instructions}

--------------------------------------------
DADOS DE ENTRADA
--------------------------------------------

## step3.json (premissas base):
```json
{p3}
```

## step4.json (resultado DCF base):
```json
{p4}
```

--------------------------------------------
INSTRUÇÃO DE EXECUÇÃO (modo não-interativo):
--------------------------------------------
Ticker: {ticker}

Execute as análises 5.1 (Matriz WACC×g_perp), 5.2 (Matriz g2_5×Mg_alvo),
5.3 (Breakevens) e 5.4 (Cenários Bear/Base/Bull) exatamente conforme as instruções acima.

Apresente o resultado completo no formato especificado em "Output do Passo 5" (5.A a 5.E).

Ao final da resposta, inclua este bloco JSON com os dados numéricos chave:
```json
{{
  "ticker": "{ticker}",
  "passo5": {{
    "valor_acao_bear": null,
    "valor_acao_base": null,
    "valor_acao_bull": null,
    "g_perp_breakeven": null,
    "WACC_est_breakeven": null,
    "Mg_alvo_breakeven": null,
    "g2_5_breakeven": null,
    "premissa_mais_sensivel": "",
    "conclusao": ""
  }}
}}
```
Preencha todos os campos null com os valores calculados.
Use sua ferramenta de escrita para salvar a analise completa em `step5.txt`
e o JSON resumido em `step5.json` no diretorio atual.
"""
    raw = run_pi(prompt, cwd=acoes, dry_run=dry_run)

    # Salvar stdout como fallback (pi pode ter escrito direto em disco)
    if raw.strip():
        save_text(raw, acoes / "step5_raw.txt")

    # Ler o que pi salvou (ou fallback para stdout)
    try:
        data = read_pi_output(raw, target=acoes / "step5.json", acoes=acoes)
        save_json(data, acoes / "step5.json")
    except (ValueError, json.JSONDecodeError):
        log("! JSON do passo5 nao extraido — ver step5.txt ou step5_raw.txt")


# ─── Orquestrador ────────────────────────────────────────────────────────────

PASSOS = {
    1: passo1,
    2: passo2,
    3: passo3,
    4: passo4,
    5: passo5,
}

def parse_args():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print(__doc__)
        sys.exit(0)

    ticker     = args[0].upper()
    start_from = 1
    only       = None
    dry_run    = "--dry-run" in args

    if "--start-from" in args:
        i = args.index("--start-from")
        start_from = int(args[i + 1])

    if "--only" in args:
        i = args.index("--only")
        only = int(args[i + 1])

    return ticker, start_from, only, dry_run


def main():
    ticker, start_from, only, dry_run = parse_args()

    acoes = MARKET / "Acoes" / ticker
    if not acoes.exists():
        abort(f"Pasta não encontrada: {acoes}\nCrie a pasta e coloque o release.pdf dentro.")

    sep(f"VALUATION PIPELINE — {ticker}" + (" [DRY-RUN]" if dry_run else ""))
    log(f"Market:    {MARKET}")
    log(f"Acoes dir: {acoes}")

    if only:
        passos_a_rodar = [only]
    else:
        passos_a_rodar = [n for n in range(1, 6) if n >= start_from]

    for n in passos_a_rodar:
        fn = PASSOS[n]
        try:
            fn(acoes, ticker, dry_run)
        except json.JSONDecodeError as e:
            abort(f"JSON inválido no Passo {n}: {e}")
        except FileNotFoundError as e:
            abort(f"Arquivo não encontrado no Passo {n}: {e}")

    sep(f"PIPELINE CONCLUÍDO — {ticker}")
    log(f"Arquivos em: Acoes/{ticker}/")
    print()


if __name__ == "__main__":
    main()
