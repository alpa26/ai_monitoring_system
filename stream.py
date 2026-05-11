import time
from utils import get_severity
import pandas as pd
from collections import deque
from detector import detect_anomalies
from prometheus_integration import get_metrics
from telegram_integration import send_alert

def get_top_features(error_vector, features, top_k=3):
    pairs = list(zip(features, error_vector))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:top_k]

def run_streaming(model, scaler, config, features):
    MIN_HISTORY = max(config["window_size"], 50)
    maxlen = max(config["window_size"] * 5, 100)
    buffer = deque(maxlen=maxlen)
    last_alert_time = 0
    COOLDOWN = 120  # секунд

    while True:
        row = get_metrics()
        if row is None:
            print("NO DATA FROM PROMETHEUS")
            time.sleep(10)
            continue
        buffer.append(row)
        if len(buffer) < MIN_HISTORY:
            time.sleep(10)
            continue
        if len(buffer) >= config["window_size"]:
            df = pd.DataFrame(buffer)
            y_pred, mse, error = detect_anomalies(df, model, scaler, config, features)
            last_error = error[-1]
            top = get_top_features(last_error, features)
            explanation = "\n".join([f"{f}: {v:.4f}" for f, v in top])
            severity = get_severity(mse[-1], config["threshold"], mse)
            print(f"{row['timestamp']} score={mse[-1]:.4f} severity={severity}")
            if y_pred[-1] == 1:
                with open("stream_log.csv", "a") as f:
                    f.write(
                        f"{row['timestamp']},{row['cpu']},{row['memory']},{row['network']},"
                        f"{row['rps']},{row['errors']},{row['latency_p95']},{row['restarts']},"
                        f"{y_pred[-1]}\n"
                    )
                now = time.time()
                if now - last_alert_time > COOLDOWN:
                    msg = f"""ANOMALY DETECTED

                    time: {row['timestamp']}
                    score: {mse[-1]:.2f}
                    severity: {severity}

                    Top contributors:
                    {explanation}
                    """
                    send_alert(msg)
                    last_alert_time = now
        time.sleep(10)

