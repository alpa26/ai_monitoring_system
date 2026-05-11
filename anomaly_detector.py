import pandas as pd
import numpy as np
import random
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import LSTM
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed, RepeatVector
from sklearn.preprocessing import RobustScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import tensorflow as tf

from preprocess import preprocess, create_windows_3d


def detect_anomalies(df, model, scaler, config, features):
    # предобработка полученных данных
    df = preprocess(df)
    # нормализация признаков и формирование окон
    X = scaler.transform(df[features])
    X_3d = create_windows_3d(X, config["window_size"])
    # реконструкция последовательностей  и расчёт ошибки
    X_pred = model.predict(X_3d, verbose=0)
    error = np.mean((X_3d - X_pred)**2, axis=1)
    # формирование anomaly score
    mse = (
        error[:, features.index('cpu')] * 2 +
        error[:, features.index('latency_p95')] * 3 +
        error[:, features.index('errors')] * 2
    )

    # классификация аномалий
    y_pred = (mse > config["threshold"]).astype(int)

    # сглаживание
    kernel = np.ones(config["smooth_window"])
    y_pred = np.convolve(y_pred, kernel, mode='same')
    y_pred = (y_pred >= 3).astype(int)

    # фильтрация коротких аномалий
    min_len = config["min_len"]
    final_pred = np.zeros_like(y_pred)
    count = 0
    for i in range(len(y_pred)):
        if y_pred[i] == 1:
            count += 1
        else:
            if count >= min_len:
                final_pred[i - count:i] = 1
            count = 0
    return final_pred, mse, error