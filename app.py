import pandas as pd
import json
import os
import streamlit as st
from matplotlib import pyplot as plt

USERNAME = "admin"
PASSWORD = "admin"
df = pd.DataFrame()
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("Login")

    user = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == USERNAME and password == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()


st.title("AI Monitoring System")

# ===== CONFIG =====

st.header("Model Configuration")

with open("model/config.json") as f:
    model_config = json.load(f)

threshold = st.slider(
    "Threshold",
    0.0,
    10.0,
    float(model_config["threshold"])
)

min_len = st.slider(
    "Min anomaly length",
    1,
    10,
    int(model_config["min_len"])
)

cooldown = st.slider(
    "Alert cooldown",
    10,
    300,
    int(model_config["cooldown"])
)

if st.button("Save model config"):
    model_config["threshold"] = threshold
    model_config["min_len"] = min_len
    model_config["cooldown"] = cooldown

    with open("model/config.json", "w") as f:
        json.dump(model_config, f, indent=4)

    st.success("Config saved")

# ===== Notifications =====

st.header("Notifications")

with open("user_config.json") as f:
    config = json.load(f)

email_enabled = st.checkbox(
    "Enable Email Alerts",
    value=config.get("email_enabled", True)
)

email_to = st.text_input(
    "Alert Email",
    value=config.get("email_to", "")
)

vk_enabled = st.checkbox(
    "Enable VK Alerts",
    value=config.get("vk_enabled", False)
)

vk_user_id = st.text_input(
    "VK User ID",
    value=config.get("vk_user_id", "")
)

if st.button("Save config"):
    config["email_enabled"] = email_enabled
    config["email_to"] = email_to
    config["vk_enabled"] = vk_enabled
    config["vk_user_id"] = vk_user_id

    with open("model/user_config.json", "w") as f:
        json.dump(config, f, indent=4)

    st.success("Config saved")

# ===== ALERTS =====

st.header("Recent alerts")

if os.path.exists("anomalies.csv"):
    df = pd.read_csv("anomalies.csv")

    st.dataframe(df.tail(20))

    if "score" in df.columns:
        fig, ax = plt.subplots()

        ax.plot(df["score"], label="Anomaly Score")

        ax.axhline(
            y=model_config["threshold"],
            linestyle="--",
            label="Threshold"
        )

        ax.set_title("Anomaly Score")
        ax.set_xlabel("Time")
        ax.set_ylabel("Score")

        ax.legend()

        st.pyplot(fig)

# ===== System status =====

st.header("System status")

if len(df) > 0:
    last_score = df["score"].iloc[-1]

    if last_score > model_config["threshold"]:
        st.error(f"ANOMALY DETECTED | score={last_score:.3f}")
    else:
        st.success(f"SYSTEM NORMAL | score={last_score:.3f}")


col1, col2, col3 = st.columns(3)

col1.metric("Alerts", int(df["is_alert"].sum()))

col2.metric("Max score", round(df["score"].max(), 3))

col3.metric("Threshold", round(model_config["threshold"], 3))

# ===== RETRAIN =====

st.header("Retraining")

if st.button("Run retraining"):
    os.system("python retrain.py")
    st.success("Retraining complete")