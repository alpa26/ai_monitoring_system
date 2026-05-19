import pandas as pd
from train import train_model

MIN_ROWS = 500

#df = pd.read_csv("stream_log.csv")

df = pd.read_csv("data/dataset.csv")

# убираем аномалии
#df = df[df["is_alert"] == 0]

if len(df) < MIN_ROWS:
    print("NOT ENOUGH DATA")
    exit()

train_model(df)

print("RETRAIN COMPLETE")