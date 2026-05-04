import pandas as pd
from train import train_model  # твоя функция

df = pd.read_csv("stream_log.csv")

# можно отфильтровать аномалии
df = df[df["is_alert"] == 0]

train_model(df)