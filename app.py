from flask import Flask, Response, request, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request

app = Flask(__name__)

PORT = 5000

# ---------- Metrics ----------

# Counter: only goes up. Total number of HTTP requests.
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# Histogram: records how long requests take (in seconds), in buckets.
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)

# Gauge: can go up and down. Requests being processed right now.
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)


def endpoint_label():
    """Use the route pattern, not the raw URL, to keep labels under control."""
    return request.url_rule.rule if request.url_rule else "unmatched"


# ---------- Middleware: measure every request ----------



@app.before_request
def start_timer():
    if request.path == "/metrics":
        return
    request.start_time = time.time()
    http_requests_in_progress.inc()


@app.after_request
def record_metrics(response):
    if request.path == "/metrics" or not hasattr(request, "start_time"):
        return response
    duration = time.time() - request.start_time
    endpoint = endpoint_label()

    http_requests_total.labels(request.method, endpoint, str(response.status_code)).inc()
    http_request_duration_seconds.labels(request.method, endpoint).observe(duration)
    return response


@app.teardown_request
def finish_request(exc):
    if request.path != "/metrics" and hasattr(request, "start_time"):
        http_requests_in_progress.dec()


# ---------- Routes ----------

@app.route("/")
def home():
    return jsonify({"message": "Prometheus lab app", "metrics": "/metrics"})


@app.route("/api/users")
def get_users():
    time.sleep(random.uniform(0.01, 0.2))          # fake work
    return jsonify([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])


@app.route("/api/orders", methods=["POST"])
def create_order():
    time.sleep(random.uniform(0.05, 0.5))
    if random.random() < 0.15:                      # 15% random failures
        return jsonify({"error": "order failed"}), 500
    return jsonify({"status": "created"}), 201


@app.route("/api/slow")
def slow():
    time.sleep(random.uniform(1, 2.5))              # slow endpoint
    return jsonify({"status": "done slowly"})


@app.route("/api/error")
def always_error():
    return jsonify({"error": "this endpoint always fails"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ---------- Metrics endpoint that Prometheus scrapes ----------

@app.route("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), mimetype="text/plain; version=0.0.4")


# ---------- Built-in traffic generator (runs only with --traffic) ----------

def send_request(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"http://localhost:{PORT}{path}", data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def traffic_loop():
    actions = [
        ("GET", "/api/users", None),
        ("GET", "/api/users", None),
        ("GET", "/api/users", None),
        ("POST", "/api/orders", {"user_id": 1, "amount": 99.99}),
        ("POST", "/api/orders", {"user_id": 2, "amount": 49.5}),
        ("GET", "/api/slow", None),
        ("GET", "/api/error", None),
        ("GET", "/health", None),
        ("GET", "/does-not-exist", None),
    ]
    time.sleep(2)                                   # wait for the server to start
    print("Traffic generator started (sending random requests)")
    while True:
        method, path, body = random.choice(actions)
        send_request(method, path, body)
        time.sleep(random.uniform(0.1, 0.6))


# ---------- Create prometheus.yml next to this file if missing ----------

PROMETHEUS_CONFIG = f"""global:
  scrape_interval: 5s

scrape_configs:
  - job_name: "flask-app"
    metrics_path: /metrics
    static_configs:
      - targets: ["localhost:{PORT}"]
"""


def ensure_prometheus_config():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prometheus.yml")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(PROMETHEUS_CONFIG)
        print(f"Created {path}")


if __name__ == "__main__":
    ensure_prometheus_config()
    if "--traffic" in sys.argv:
        threading.Thread(target=traffic_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)






