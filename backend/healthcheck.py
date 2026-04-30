import http.server
import threading
import subprocess
import sys
import os

def run_celery():
    print("Starting Celery worker...", flush=True)
    process = subprocess.Popen(
        [
            "celery",
            "-A", "app.workers.celery_app.celery_app",
            "worker",
            "--loglevel=info",
            "--pool=solo"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    # Stream output line by line so nothing is lost
    for line in iter(process.stdout.readline, b""):
        print(line.decode("utf-8"), end="", flush=True)

    process.wait()
    print(f"Celery worker exited with code {process.returncode}", flush=True)

t = threading.Thread(target=run_celery, daemon=True)
t.start()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass

print("Health check server starting on port 8080...", flush=True)
http.server.HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()