
import numpy as np
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed, RepeatVector
from tensorflow.keras.optimizers import Adam
from datetime import datetime

def train_model(df):
    import json
    with open("model/config.json") as f:
        config = json.load(f)
    # ===== ТВОЙ preprocess =====
    from preprocess import preprocess, create_windows_3d

    df = preprocess(df)

    version = datetime.now().strftime("%Y%m%d_%H%M")

    features = [
        'cpu','memory','rps','latency_p95','errors',
        'cpu_diff','latency_p95_diff','errors_diff',
        'cpu_roll_mean','latency_roll_mean','rps_roll_mean',
        'hour','hour_sin','hour_cos'
    ]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])

    WINDOW_SIZE = config["window_size"]
    X_3d = create_windows_3d(X_scaled, WINDOW_SIZE)

    split = int(len(X_3d) * 0.8)
    X_train = X_3d[:split]

    # ===== модель =====
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(WINDOW_SIZE, len(features))),
        LSTM(16, return_sequences=False),
        RepeatVector(WINDOW_SIZE),
        LSTM(16, return_sequences=True),
        LSTM(64, return_sequences=True),
        TimeDistributed(Dense(len(features)))
    ])

    model.compile(optimizer=Adam(0.001), loss='mse')
    model.fit(X_train, X_train, epochs=20, batch_size=32)

    # ===== threshold =====
    X_pred = model.predict(X_train)
    error = np.mean((X_train - X_pred)**2, axis=1)

    threshold = np.mean(error) + 3 * np.std(error)

    # ===== save =====
    import joblib, json

    joblib.dump(scaler, f"model/scaler_{version}.pkl")
    model.save(f"model/ae_model_{version}.h5")

    with open(f"model/config_{version}.json", "w") as f:
        json.dump({
            "window_size": WINDOW_SIZE,
            "threshold": float(threshold),
            "min_len": 3
        }, f)

    with open("model/current_model.txt", "w") as f:
        f.write(version)

    print("Model retrained and saved")