import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import argparse
import pandas as pd
import joblib
import json
import numpy as np
import random
import tensorflow as tf
# python main.py --input data/test.csv
from tensorflow.keras.models import load_model
from anomaly_detector import detect_anomalies
from stream import run_streaming

SEED = 43
np.random.seed(SEED)
random.seed(SEED)
tf.random.set_seed(SEED)

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=str, required=False)
parser.add_argument("--output", type=str, default="anomalies.csv")
parser.add_argument("--stream", action="store_true")

args = parser.parse_args()
import time


def run_batch(model, scaler, config, features):
    df = pd.read_csv(args.input)

    # ===== предсказание =====
    y_pred, mse = detect_anomalies(df, model, scaler, config, features)

    events = []
    start = None

    timestamps = df["timestamp"][config["window_size"]:].values

    for i in range(len(y_pred)):
        if y_pred[i] == 1 and start is None:
            start = timestamps[i]

        elif y_pred[i] == 0 and start is not None:
            end = timestamps[i]
            events.append((start, end))
            start = None

    if start is not None:
        events.append((start, timestamps[-1]))

    for e in events:
        print(f"ANOMALY: {e[0]} → {e[1]}")
        # ===== сохранение =====
    p95 = np.percentile(mse, 95)
    p99 = np.percentile(mse, 99)

    def get_severity(score):
        if score > p99:
            return "critical"
        elif score > p95:
            return "high"
        elif score > config["threshold"]:
            return "medium"
        else:
            return "low"

    result = pd.DataFrame({
        "timestamp": df["timestamp"][config["window_size"]:],
        "score": mse,
        "is_alert": y_pred,
        "severity": [get_severity(s) for s in mse]
    })

    result.to_csv(args.output, index=False)

    print("Saved to", args.output)

# ===== загрузка данных =====

model = load_model("model/ae_model.h5", compile=False)
scaler = joblib.load("model/scaler.pkl")

# ===== признаки =====
features = [
    'cpu', 'memory', 'rps', 'latency_p95', 'errors',
    'cpu_diff', 'latency_p95_diff', 'errors_diff',
    'cpu_roll_mean', 'latency_roll_mean', 'rps_roll_mean',
    'hour', 'hour_sin', 'hour_cos'
]

with open("model/config.json") as f:
    config = json.load(f)
if args.stream:
    print("Start stream")
    run_streaming(model, scaler, config, features)
else:
    print("Start batch")
    if not args.input:
        raise ValueError("Для batch режима нужен --input")
    run_batch(model, scaler, config, features)