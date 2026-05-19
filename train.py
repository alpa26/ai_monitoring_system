from tensorflow.python.keras.callbacks import EarlyStopping


def train_model(df):
    import os
    import json
    import joblib
    import mlflow
    import mlflow.keras
    import numpy as np

    from datetime import datetime
    from sklearn.preprocessing import StandardScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import (
        LSTM,
        Dense,
        TimeDistributed,
        RepeatVector
    )
    from tensorflow.keras.optimizers import Adam

    from preprocess import preprocess, create_windows_3d

    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("anomaly_detection")

    with open("model/config.json") as f:
        config = json.load(f)

    version = datetime.now().strftime("%Y%m%d_%H%M")

    df = preprocess(df)

    features = [
        'cpu','memory','rps','latency_p95','errors',
        'cpu_diff','latency_p95_diff','errors_diff',
        'cpu_roll_mean','latency_roll_mean','rps_roll_mean',
        'hour','hour_sin','hour_cos'
    ]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])
    X_scaled[:, features.index('memory')] *= 0.3

    WINDOW_SIZE = config["window_size"]

    X_3d = create_windows_3d(X_scaled, WINDOW_SIZE)

    split = int(len(X_3d) * 0.8)
    X_train = X_3d[:split]

    # ===== MLFLOW =====

    with mlflow.start_run(run_name=f"lstm_ae_{version}"):

        exp = mlflow.get_experiment_by_name("anomaly_detection")
        print("EXPERIMENT:", exp)

        # ===== логируем параметры =====
        mlflow.log_param("window_size", WINDOW_SIZE)
        mlflow.log_param("features_count", len(features))
        mlflow.log_param("epochs", 20)
        mlflow.log_param("batch_size", 32)
        mlflow.log_param("learning_rate", 0.001)

        # ===== модель =====
        model = Sequential([
            LSTM(
                64,
                return_sequences=True,
                input_shape=(WINDOW_SIZE, len(features))
            ),
            LSTM(16, return_sequences=False),
            RepeatVector(WINDOW_SIZE),
            LSTM(16, return_sequences=True),
            LSTM(64, return_sequences=True),
            TimeDistributed(Dense(len(features)))
        ])

        model.compile(
            optimizer=Adam(
                learning_rate=0.001,
                clipnorm=1.0
            ),
            loss='mse'
        )
        early_stop = EarlyStopping(patience=10, restore_best_weights=True)

        history = model.fit(
            X_train,
            X_train,
            epochs=80,
            batch_size=32,
            validation_split=0.1,
            callbacks=[early_stop]
        )

        # ===== threshold =====
        X_pred = model.predict(X_train)
        error_per_feature = np.mean(
            (X_train - X_pred) ** 2,
            axis=1
        )

        error = (
                error_per_feature[:, features.index('cpu')] * 2 +
                error_per_feature[:, features.index('latency_p95')] * 3 +
                error_per_feature[:, features.index('errors')] * 2
        )

        threshold = np.mean(error) + 4 * np.std(error)

        import numpy as np
        import matplotlib.pyplot as plt
        import mlflow

        # ===== split normal / anomaly =====
        df_aligned = df.iloc[WINDOW_SIZE: WINDOW_SIZE + len(error)].reset_index(drop=True)

        cpu = df_aligned["cpu"].values
        latency = df_aligned["latency_p95"].values

        is_anomaly = (error > threshold)
        is_anomaly = is_anomaly.astype(bool)

        min_len = min(len(cpu), len(is_anomaly))

        cpu = cpu[:min_len]
        latency = latency[:min_len]
        is_anomaly = is_anomaly[:min_len]

        normal_idx = ~is_anomaly
        anomaly_idx = is_anomaly
        # =========================
        # 1. CPU HISTOGRAM
        # =========================
        plt.figure()
        '''
        plt.hist(cpu[normal_idx], bins=50, alpha=0.6, label="normal")
        plt.hist(cpu[anomaly_idx], bins=50, alpha=0.6, label="anomaly")'''
        plt.hist(
            cpu[normal_idx],
            bins=50,
            alpha=0.6,
            label="normal",
            density=True
        )

        plt.hist(
            cpu[anomaly_idx],
            bins=50,
            alpha=0.6,
            label="anomaly",
            density=True
        )

        plt.legend()
        plt.title("Распределение CPU")

        plt.savefig("cpu_hist.png")
        mlflow.log_artifact("cpu_hist.png")
        plt.close()

        # =========================
        # 2. LATENCY HISTOGRAM
        # =========================
        plt.figure()
        '''
        plt.hist(latency[normal_idx], bins=50, alpha=0.6, label="normal")
        plt.hist(latency[anomaly_idx], bins=50, alpha=0.6, label="anomaly")
        '''
        plt.hist(
            latency[normal_idx],
            bins=50,
            alpha=0.6,
            label="normal",
            density=True
        )

        plt.hist(
            latency[anomaly_idx],
            bins=50,
            alpha=0.6,
            label="anomaly",
            density=True
        )

        plt.legend()
        plt.title("Распределение latency")

        plt.savefig("latency_hist.png")
        mlflow.log_artifact("latency_hist.png")
        plt.close()

        # =========================
        # 3. RECONSTRUCTION ERROR
        # =========================
        plt.figure()

        x = np.arange(len(error))

        plt.plot(
            x,
            error,
            label="reconstruction error"
        )

        plt.axhline(
            threshold,
            color="red",
            linestyle="--",
            label="threshold"
        )

        plt.scatter(
            np.where(is_anomaly)[0],
            error[is_anomaly],
            color="red",
            s=10,
            label="anomaly"
        )

        plt.legend()
        plt.title("Reconstruction error")

        plt.savefig("score.png")
        mlflow.log_artifact("score.png")
        plt.close()

        # ===== метрики =====
        final_loss = history.history["loss"][-1]
        val_loss = history.history["val_loss"][-1]

        mlflow.log_metric("train_loss", final_loss)
        mlflow.log_metric("val_loss", val_loss)
        mlflow.log_metric("threshold", float(threshold))

        # ===== save =====
        os.makedirs("model", exist_ok=True)

        scaler_path = f"model/scaler_{version}.pkl"
        model_path = f"model/ae_model_{version}.h5"
        config_path = f"model/config_{version}.json"

        joblib.dump(scaler, scaler_path)

        model.save(model_path)

        with open(config_path, "w") as f:
            json.dump({
                "window_size": WINDOW_SIZE,
                "threshold": float(threshold),
                "min_len": 3
            }, f)

        # ===== current model =====
        with open("model/current_model.txt", "w") as f:
            f.write(version)

        # ===== артефакты =====
        mlflow.log_artifact(model_path)
        mlflow.log_artifact(scaler_path)
        mlflow.log_artifact(config_path)
        mlflow.keras.log_model(model, "model")

        print("Model retrained and saved")