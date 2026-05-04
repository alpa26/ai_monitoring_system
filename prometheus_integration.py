from datetime import datetime

import requests
import pandas as pd

PROM_URL = "http://localhost:9090"

def query(promql):
    #print("Start request")
    r = requests.get(f"{PROM_URL}/api/v1/query", params={"query": promql})
    data = r.json()
    #print("End request")

    if not data["data"]["result"]:
        return 0.0

    return float(data["data"]["result"][0]["value"][1])

def safe_query(q):
    try:
        return query(q)
    except:
        return 0.0

def get_metrics():
    return {
        "timestamp": datetime.now(),
        "cpu": safe_query('sum(rate(container_cpu_usage_seconds_total[2m]))'),
        "memory": safe_query('sum(container_memory_usage_bytes)'),
        "network": safe_query('sum(rate(container_network_receive_bytes_total[2m]))'),
        "rps": safe_query("sum(rate(istio_requests_total{reporter='destination'}[2m]))"),
        "errors": safe_query("sum(rate(istio_requests_total{reporter='destination', response_code!~'2..'}[2m]))"),
        "latency_p95": safe_query( 'histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket[2m])) by (le))'),
        "restarts": safe_query('sum(increase(kube_pod_container_status_restarts_total[5m]))')
    }