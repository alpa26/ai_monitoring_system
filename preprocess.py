import numpy as np
import pandas as pd

metrics = ['cpu', 'memory', 'network', 'rps', 'errors', 'latency_p95', 'restarts']
features = [
    'cpu',
    'memory',
    'rps',
    'latency_p95',
    'errors',
    'cpu_diff',
    'latency_p95_diff',
    'errors_diff',
    'cpu_roll_mean',
    'latency_roll_mean',
    'rps_roll_mean',
    'hour',
    'hour_sin',
    'hour_cos',
]

def preprocess(df):
    df = df.drop_duplicates()
    df['restarts'] = (df['restarts'] > 0).astype(int)
    df.bfill(inplace=True)
    df.ffill(inplace=True)
    for col in metrics:
        df[f'{col}_diff'] = df[col].pct_change().fillna(0)

    # Заменяем inf на NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # df[metrics] = df[metrics].rolling(window=3).mean()
    # Заполняем после этого
    df.fillna(0, inplace=True)
    df['latency_p95'] = df['latency_p95'].clip(0, df['latency_p95'].quantile(0.99))
    df['latency_p95'] = np.log1p(df['latency_p95'])
    df['latency_per_rps'] = df['latency_p95'] / (df['rps'] + 1)
    df['errors_per_rps'] = df['errors'] / (df['rps'] + 1)
    df['cpu_per_rps'] = df['cpu'] / (df['rps'] + 1)
    df['cpu_to_latency'] = df['cpu'] / (df['latency_p95'] + 1)
    df['load_level'] = pd.qcut(df['rps'], q=4, labels=False)
    df['is_peak'] = (df['rps'] > df['rps'].quantile(0.8)).astype(int)
    df['rolling_cpu'] = df['cpu'].rolling(10).mean()
    df['cpu_zscore'] = (df['cpu'] - df['cpu'].rolling(50).mean()) / (df['cpu'].rolling(50).std() + 1e-6)
    df['cpu_spike'] = (df['cpu_diff'].abs() > df['cpu_diff'].std() * 2).astype(int)
    df['latency_spike'] = (df['latency_p95_diff'].abs() > df['latency_p95_diff'].std() * 2).astype(int)
    df['cpu_roll_mean'] = df['cpu'].rolling(5).mean()
    df['latency_roll_mean'] = df['latency_p95'].rolling(5).mean()
    df['rps_roll_mean'] = df['rps'].rolling(5).mean()

    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    # df['latency_diff'] = df['latency_p95'].diff().fillna(0)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)
    # df['is_anomaly'] = 0 ?????
    return df
def create_windows_3d(X, window_size):
    Xs = []
    for i in range(len(X) - window_size):
        Xs.append(X[i:i+window_size])
    return np.array(Xs)