import streamlit as st
import pandas as pd
import json
import os

st.title("AI Monitoring System")

# ===== CONFIG =====

st.header("Configuration")

with open("model/config.json") as f:
    config = json.load(f)

threshold = st.slider(
    "Threshold",
    0.0,
    10.0,
    float(config["threshold"])
)

min_len = st.slider(
    "Min anomaly length",
    1,
    10,
    int(config["min_len"])
)

cooldown = st.slider(
    "Alert cooldown",
    10,
    300,
    int(config["cooldown"])
)

if st.button("Save config"):
    config["threshold"] = threshold
    config["min_len"] = min_len
    config["cooldown"] = cooldown

    with open("model/config.json", "w") as f:
        json.dump(config, f, indent=4)

    st.success("Config saved")

# ===== ALERTS =====

st.header("Recent alerts")

if os.path.exists("anomalies.csv"):
    df = pd.read_csv("anomalies.csv")

    st.dataframe(df.tail(20))

    if "score" in df.columns:
        st.line_chart(df["score"])

# ===== RETRAIN =====

st.header("Retraining")

if st.button("Run retraining"):
    os.system("python retrain.py")
    st.success("Retraining complete")