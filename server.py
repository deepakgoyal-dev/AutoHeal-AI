"""
AutoHeal AI - Local Web Server & API Portal
# Authored by: Deepak & Nikhil
Provides a zero-dependency web interface with live upload, simulation, visual dashboards, and API endpoints.
"""

import os
import json
import io
import re
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import pandas as pd

from aegis import AutoHealPipeline, CorruptedDataGenerator, PipelineConfig

BASE_DIR = Path(__file__).resolve().parent
CONFIG = PipelineConfig()
PIPELINE = AutoHealPipeline(CONFIG)


class AutoHealWebHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler serving the interactive AegisData AI dashboard and REST API.
    """

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_portal()
        elif path.startswith("/api/reports"):
            self._handle_get_reports()
        elif path.startswith("/download/"):
            self._handle_download(path)
        elif path.startswith("/data/"):
            self._serve_static_file(path)
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/simulate":
            self._handle_simulate()
        elif path == "/api/upload":
            self._handle_upload()
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Not Found")

    def _serve_portal(self):
        """Serves the primary interactive AutoHeal AI web application."""
        index_file = BASE_DIR / "index.html"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                html = f.read()
            self._set_headers(200, "text/html")
            self.wfile.write(html.encode("utf-8"))
            return

        report_files = list(CONFIG.reports_dir.glob("*_dashboard.html"))
        if not report_files:
            demo_df = CorruptedDataGenerator.generate_ecommerce_dataset(n_rows=300)
            PIPELINE.process(demo_df, dataset_name="Ecommerce_Transactions_Demo")
            report_files = list(CONFIG.reports_dir.glob("*_dashboard.html"))

        latest_dashboard = max(report_files, key=os.path.getmtime)
        with open(latest_dashboard, "r", encoding="utf-8") as f:
            html = f.read()

        self._set_headers(200, "text/html")
        self.wfile.write(html.encode("utf-8"))

    def _handle_get_reports(self):
        """Returns JSON list of all available reports."""
        reports = []
        for p in CONFIG.reports_dir.glob("*_audit_ledger.json"):
            dataset_name = p.stem.replace("_audit_ledger", "")
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            reports.append({
                "dataset_name": dataset_name,
                "created_at": data.get("created_at"),
                "initial_score": data.get("initial_health_score"),
                "final_score": data.get("final_health_score"),
                "total_repairs": data.get("total_healing_actions")
            })
        self._set_headers(200)
        self.wfile.write(json.dumps(reports).encode("utf-8"))

    def _handle_simulate(self):
        """Generates a fresh batch of realistic corrupted enterprise data and runs the pipeline."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            params = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            params = {}

        domain = params.get("domain", "ecommerce")
        n_rows = int(params.get("n_rows", 350))

        if domain == "healthcare":
            df = CorruptedDataGenerator.generate_healthcare_dataset(n_rows=n_rows)
            name = "Clinical_Patients_Telemetry"
        else:
            df = CorruptedDataGenerator.generate_ecommerce_dataset(n_rows=n_rows)
            name = "Omnichannel_Retail_Orders"

        result = PIPELINE.process(df, dataset_name=name)

        # Return the summary and web link
        response_payload = {
            "status": "success",
            "dataset_name": result["dataset_name"],
            "initial_score": result["initial_health_score"],
            "final_score": result["final_health_score"],
            "total_repairs": result["total_repairs"],
            "insights": result["insights"],
            "dashboard_url": f"/download/html/{result['dataset_name']}_dashboard.html",
            "healed_csv_url": f"/download/csv/{result['dataset_name']}_healed.csv"
        }

        self._set_headers(200)
        self.wfile.write(json.dumps(response_payload).encode("utf-8"))

    def _handle_upload(self):
        """Accepts a multipart or raw CSV upload, self-heals, and returns visual report."""
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        if "multipart/form-data" in content_type and "boundary=" in content_type:
            boundary = content_type.split("boundary=")[-1].strip().encode('utf-8')
            raw_body = self.rfile.read(content_length)
            parts = raw_body.split(b"--" + boundary)
            file_bytes = None
            filename = "uploaded_data.csv"
            for part in parts:
                if b'filename="' in part:
                    header_part, _, file_data = part.partition(b"\r\n\r\n")
                    file_bytes = file_data.rstrip(b"\r\n--")
                    fn_match = re.search(r'filename="([^"]+)"', header_part.decode('utf-8', errors='ignore'))
                    if fn_match:
                        filename = fn_match.group(1)
                    break

            if not file_bytes:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "No file content parsed"}).encode("utf-8"))
                return

            df = pd.read_csv(io.BytesIO(file_bytes), dtype=object)
            dataset_name = Path(filename).stem

        else:
            # Raw CSV body
            raw_bytes = self.rfile.read(content_length)
            df = pd.read_csv(io.BytesIO(raw_bytes), dtype=object)
            dataset_name = "Uploaded_Stream_Data"

        result = PIPELINE.process(df, dataset_name=dataset_name)

        response_payload = {
            "status": "success",
            "dataset_name": result["dataset_name"],
            "initial_score": result["initial_health_score"],
            "final_score": result["final_health_score"],
            "total_repairs": result["total_repairs"],
            "insights": result["insights"],
            "dashboard_url": f"/download/html/{result['dataset_name']}_dashboard.html"
        }
        self._set_headers(200)
        self.wfile.write(json.dumps(response_payload).encode("utf-8"))

    def _handle_download(self, path: str):
        """Allows direct download of healed files or dashboards."""
        parts = path.strip("/").split("/")
        if len(parts) < 3:
            self._set_headers(400, "text/plain")
            self.wfile.write(b"Invalid download path")
            return

        file_type, filename = parts[1], parts[2]
        if file_type == "csv":
            file_path = CONFIG.healed_dir / filename
            mime = "text/csv"
        elif file_type == "html":
            file_path = CONFIG.reports_dir / filename
            mime = "text/html"
        elif file_type == "md":
            file_path = CONFIG.reports_dir / filename
            mime = "text/markdown"
        else:
            self._set_headers(400, "text/plain")
            self.wfile.write(b"Unsupported file type")
            return

        if not file_path.exists():
            self._set_headers(404, "text/plain")
            self.wfile.write(b"File not found")
            return

        with open(file_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f"inline; filename={filename}")
        self.end_headers()
        self.wfile.write(data)

    def _serve_static_file(self, path: str):
        file_path = (BASE_DIR / path.strip("/")).resolve()
        if not file_path.exists():
            self._set_headers(404, "text/plain")
            self.wfile.write(b"File Not Found")
            return

        mime, _ = mimetypes.guess_type(str(file_path))
        with open(file_path, "rb") as f:
            data = f.read()
        self._set_headers(200, mime or "application/octet-stream")
        self.wfile.write(data)


def run_server(port: int = 8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, AutoHealWebHandler)
    print(f"============================================================")
    print(f" AutoHeal AI Portal running at http://localhost:{port}")
    print(f" Features: Autonomous Self-Healing, Live Diff, Visual Dashboards")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down AutoHeal AI server.")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AutoHeal AI Web Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    args = parser.parse_args()
    run_server(args.port)
