import time
from utils import get_severity
import pandas as pd
from collections import deque
from anomaly_detector import detect_anomalies
from prometheus_integration import get_metrics
from alerting import send_telegram, send_email, send_vk_alert
import os

def get_top_features(error_vector, features, top_k=3):
    pairs = list(zip(features, error_vector))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:top_k]

def run_streaming(model, scaler, config, features):
    MIN_HISTORY = max(config["window_size"], 50)
    maxlen = max(config["window_size"] * 5, 100)
    buffer = deque(maxlen=maxlen)
    last_alert_time = 0
    COOLDOWN = config["cooldown"]
    check_cooldown = 30

    if not os.path.exists("stream_log.csv"):
        with open("stream_log.csv", "w") as f:
            f.write(
                "timestamp,cpu,memory,network,rps,errors,"
                "latency_p95,restarts,is_alert\n"
            )
    if not os.path.exists("anomalies.csv"):
        with open("anomalies.csv", "w") as f:
            f.write(
                "timestamp,score,is_alert,severity"
            )
    while True:
        row = get_metrics()
        if row is None:
            print("NO DATA FROM PROMETHEUS")
            time.sleep(config["poll_interval"])
            continue
        buffer.append(row)
        if len(buffer) < MIN_HISTORY:
            time.sleep(config["poll_interval"])
            continue
        if check_cooldown == 0:
            check_cooldown = 30
            print("STREAM ALIVE")
        else:
            check_cooldown -= 1
        if len(buffer) >= config["window_size"]:
            df = pd.DataFrame(buffer)
            final_pred, mse, error = detect_anomalies(df, model, scaler, config, features)
            last_error = error[-1]
            top = get_top_features(last_error, features)
            explanation = "\n".join([f"{f}: {v:.4f}" for f, v in top])
            severity = get_severity(mse[-1], config["threshold"], mse)
            print(f"{row['timestamp']} score={mse[-1]:.4f} severity={severity}")
            with open("stream_log.csv", "a") as f:
                f.write(
                    f"{row['timestamp']},{row['cpu']},{row['memory']},{row['network']},"
                    f"{row['rps']},{row['errors']},{row['latency_p95']},{row['restarts']},"
                    f"{final_pred[-1]}\n"
                )
            if final_pred[-1] == 1:
                now = time.time()
                if now - last_alert_time > COOLDOWN:
                    msg = f"""ANOMALY DETECTED

                    time: {row['timestamp']}
                    score: {mse[-1]:.2f}
                    severity: {severity}

                    Top contributors:
                    {explanation}
                    """
                    #send_telegram(msg)
                    send_email(msg)
                    send_vk_alert(msg)
                    last_alert_time = now
        time.sleep(config["poll_interval"])

