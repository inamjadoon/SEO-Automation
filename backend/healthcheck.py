import http.server
import threading
import subprocess
import sys

def run_celery():
    process = subprocess.Popen(
        [
            "celery",
            "-A", "app.workers.celery_app.celery_app",
            "worker",
            "--loglevel=info",
            "--pool=solo"
        ],
        stdout=sys.stdout,
        stderr=sys.stdout  # redirect stderr to stdout so Cloud Logging captures it
    )
    process.wait()

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