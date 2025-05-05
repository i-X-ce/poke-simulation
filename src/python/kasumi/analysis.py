import os
import pandas as pd 
import xgboost as xgb
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import numpy as np

os.chdir(os.path.dirname(__file__))

data = pd.read_csv("./result/result.csv")
x = data[["A", "S", "C", "HP"]]
y = data["Win"] / 200
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

model = xgb.XGBRegressor()
model.fit(x_train, y_train)

def predict_win_rate(a, s, c, hp):
    input_df = pd.DataFrame([[a, s, c, hp]], columns=["A", "S", "C", "HP"])
    pred = model.predict(input_df)
    return float(pred[0])

xgb.plot_importance(model)
plt.show()

while True:
    try:
        a, s, c = map(int, input("A S C: ").split())
        hps = [x for x in range(40, 84)]
        rates = [predict_win_rate(a, s, c, x) for x in hps]
        for i in range(len(hps)):
            print(f"{hps[i]}:{rates[i] * 100: .2f}%")

        plt.plot(hps, rates)
        plt.ylim(0, 1)
        plt.xlabel("HP")
        plt.ylabel("Win Rate")
        plt.title(f"A{a}, S{s}, C{c}")
        plt.grid()
        plt.show()
        # plt.axhline(y=rate, color="r", linestyle="--", label=f"Win Rate: {rate:.2f}%")
        # print(f"予測勝率: {rate:.2f}%")

    except ValueError:
        print("無効な入力です。整数を入力してください。")
    except KeyboardInterrupt:
        break