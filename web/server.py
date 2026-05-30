#!/usr/bin/env python3
"""
Valuation Dashboard — servidor local
Uso:  python Valuation/web/server.py [porta]
URL:  http://localhost:8000/Valuation/web/
"""
import http.server
import json
import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).parent.parent.parent          # .../Market
ACOES      = ROOT / "Acoes"
DCF_SCRIPT = Path(__file__).parent.parent / "script" / "step4_dcf.py"
PORT       = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class DashHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ── GET ────────────────────────────────────────────────────────────────────

    def do_GET(self):
        if self.path == "/api/tickers":
            tickers = sorted(
                d.name for d in ACOES.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            )
            self._send_json(tickers)
        else:
            super().do_GET()

    # ── PUT ────────────────────────────────────────────────────────────────────

    def do_PUT(self):
        # /api/passo/<ticker>/<n>  → sobrescreve Acoes/<ticker>/passo<n>.json
        parts = self.path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "passo"]:
            ticker, n = parts[2], parts[3]
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw)
                target = ACOES / ticker / f"step{n}.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                self._send_json({"ok": True})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)
        else:
            self.send_error(404)

    # ── POST ───────────────────────────────────────────────────────────────────

    def do_POST(self):
        # /api/run-passo4/<ticker>  → propaga p1+p2→p3, roda DCF, devolve passo4
        parts = self.path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["api", "run-passo4"]:
            try:
                self._run_passo4(parts[2])
            except Exception as exc:
                import traceback
                self._send_json({"ok": False, "error": traceback.format_exc()}, status=500)
        else:
            self.send_error(404)

    def _run_passo4(self, ticker):
        acoes  = ACOES / ticker
        p1_path = acoes / "step1.json"
        p2_path = acoes / "step2.json"
        p3_path = acoes / "step3.json"
        p4_path = acoes / "step4.json"

        if not p3_path.exists():
            self._send_json({"ok": False, "error": "step3.json não encontrado"}, status=400)
            return

        p3 = json.loads(p3_path.read_text(encoding="utf-8"))

        def _val(obj, key):
            """Extrai .valor se for dict aninhado, caso contrário retorna o valor direto."""
            field = obj.get(key)
            if field is None:
                return None
            return field.get("valor") if isinstance(field, dict) else field

        # Propaga passo1 → passo3 (dados_historicos + dados_mercado)
        if p1_path.exists():
            p1  = json.loads(p1_path.read_text(encoding="utf-8"))
            dre = p1.get("dre", {})
            bal = p1.get("balanco", {})
            mkt = p1.get("mercado", {})

            hist = p3.setdefault("dados_historicos", {})
            for key in ["Rev_0", "EBIT_0", "Dep", "Juros"]:
                v = _val(dre, key)
                if v is not None:
                    hist[key] = v
            for key in ["PL", "D", "Caixa", "AtvNOp", "MinInt"]:
                v = _val(bal, key)
                if v is not None:
                    hist[key] = v

            dmkt = p3.setdefault("dados_mercado", {})
            for key in ["P", "Shares", "MktCap"]:
                v = _val(mkt, key)
                if v is not None:
                    dmkt[key] = v
            ir_ef = _val(dre, "IR_ef")
            if ir_ef is not None:
                dmkt["IR_ef"] = ir_ef

        # Propaga passo2 → passo3 (parametros_custo_capital)
        if p2_path.exists():
            p2 = json.loads(p2_path.read_text(encoding="utf-8"))
            pm  = p2.get("parametros_mercado", {})
            cck = p3.setdefault("parametros_custo_capital", {})
            for key in ["Rf", "ERP", "Beta_u", "Kd_pre", "IR_marg", "WACC_est"]:
                v = _val(pm, key)
                if v is not None:
                    cck[key] = v

        # Salva passo3 atualizado
        p3_path.write_text(json.dumps(p3, ensure_ascii=False, indent=2), encoding="utf-8")

        # Roda step4_dcf.py
        if not DCF_SCRIPT.exists():
            self._send_json({"ok": False, "error": f"Script não encontrado: {DCF_SCRIPT}"}, status=500)
            return

        try:
            result = subprocess.run(
                [sys.executable, str(DCF_SCRIPT), str(p3_path),
                 "--output", str(p4_path), "--quiet"],
                capture_output=True, timeout=60,
            )
        except subprocess.TimeoutExpired:
            self._send_json({"ok": False, "error": "Timeout ao rodar DCF (>60s)"}, status=500)
            return

        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        if result.returncode != 0:
            err = (stderr or stdout or "Erro desconhecido").strip()
            self._send_json({"ok": False, "error": err}, status=500)
            return

        if not p4_path.exists():
            self._send_json({"ok": False, "error": "step4.json não foi gerado"}, status=500)
            return

        p4 = json.loads(p4_path.read_text(encoding="utf-8"))
        self._send_json({"ok": True, "passo4": p4})

    # ── OPTIONS ────────────────────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silencia logs de request


if __name__ == "__main__":
    with http.server.HTTPServer(("", PORT), DashHandler) as httpd:
        print(f"\n  Dashboard  →  http://localhost:{PORT}/Valuation/web/\n")
        print("  Ctrl+C para parar\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Servidor parado.")
