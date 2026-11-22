# Flask Prometheus Integration

A lightweight Flask application instrumented with Prometheus metrics, together with a ready-to-use Prometheus configuration for scraping and monitoring it.

## Overview

This project demonstrates how to expose application metrics from a Flask service and collect them with Prometheus. It is a practical starting point for learning application monitoring and observability as part of an AIOps / DevOps workflow.

## Features

- Flask web application (app.py)
- Metrics exposed in Prometheus format at the /metrics endpoint
- Prometheus scrape configuration (prometheus.yml)
- Simple setup, easy to extend with custom metrics

## Project Structure


flask_prometheus_integration/
├── app.py            # Flask application with Prometheus metrics
├── prometheus.yml    # Prometheus scrape configuration
└── README.md         # Project documentation


## Prerequisites

- Python 3.8+
- pip
- Prometheus ([download](https://prometheus.io/download/)) or Docker

## Installation

1. Clone the repository:

   bash
   git clone https://github.com/farhadalizahid/flask_prometheus_integration.git
   cd flask_prometheus_integration
   

2. (Recommended) Create and activate a virtual environment:

   bash
   python3 -m venv venv
   source venv/bin/activate
   

3. Install dependencies:

   bash
   pip install flask prometheus_client
   

## Usage

### 1. Start the Flask application

bash
python3 app.py


The application starts on the port defined in app.py (commonly 5000).

### 2. Verify the metrics endpoint

bash
curl http://localhost:5000/metrics


### 3. Start Prometheus

bash
prometheus --config.file=prometheus.yml


Or with Docker:

bash
docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus


### 4. Open the Prometheus dashboard

Visit http://localhost:9090, go to *Status → Targets, and confirm the Flask target shows as **UP. You can then query your metrics in the **Graph* tab.

## Configuration

Edit prometheus.yml to match your environment. The key setting is the scrape target, which must point to the host and port where the Flask app is running:

yaml
scrape_configs:
  - job_name: "flask_app"
    static_configs:
      - targets: ["localhost:5000"]


> If Prometheus runs in Docker and Flask runs on the host, use the host's IP address (or host.docker.internal) instead of localhost.

## Troubleshooting

| Problem | Solution |
|---|---|
| Target shows *DOWN* in Prometheus | Check that the Flask app is running and the target host/port in prometheus.yml is correct |
| /metrics returns 404 | Make sure the metrics route is defined in app.py |
| Connection refused from Docker | Use the host IP instead of localhost in prometheus.yml |

## Roadmap

- [ ] Add custom metrics (request counters, latency histograms)
- [ ] Add Grafana dashboards
- [ ] Containerize with Docker and Docker Compose
- [ ] Add alerting rules

## Author

*Farhad Ali Zahid*
GitHub: [@farhadalizahid](https://github.com/farhadalizahid)

## License

This project is open source and available under the [MIT License](LICENSE).
