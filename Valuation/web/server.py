#!/usr/bin/env python3
"""
Valuation Dashboard — servidor local
Uso:  python Valuation/web/server.py [porta]
URL:  http://localhost:8000/Valuation/web/
"""
import http.server
import json
import sys
from pathlib import Path

ROOT  = Path(__file__).parent.parent.parent   # .../Market
ACOES = ROOT / "Acoes"
PORT  = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class DashHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/api/tickers":
            tickers = sorted(
                d.name for d in ACOES.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            )
            self._send_json(tickers)
        else:
            super().do_GET()

    def do_PUT(self):
        # /api/passo/<ticker>/<n>  → sobrescreve Acoes/<ticker>/passo<n>.json
        parts = self.path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "passo"]:
            ticker, n = parts[2], parts[3]
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw)
                target = ACOES / ticker / f"passo{n}.json"
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

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

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
