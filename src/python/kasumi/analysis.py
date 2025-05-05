import os
import pandas as pd 
import xgboost as xgb
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import numpy as np

os.chdir(os.path.dirname(__file__))

data = pd.read_csv("./result.csv")
x = data[["A", "C", "S", "HP"]]
y = data["Win"] / 200
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

model = xgb.XGBRegressor()
model.fit(x_train, y_train)

def predict_win_rate(a, c, s, hp):
    input_df = pd.DataFrame([[a, c, s, hp]], columns=["A", "C", "S", "HP"])
    pred = model.predict(input_df)
    return float(pred[0])

# xgb.plot_importance(model)
# plt.show()

while True:
    try:
        a, c, s = map(int, input("A C S: ").split())
        hps = [x for x in range(40, 84)]
        rates = [predict_win_rate(a, c, s, x) for x in hps]

        plt.plot(hps, rates)
        plt.ylim(0, 1)
        plt.xlabel("HP")
        plt.ylabel("Win Rate")
        plt.title(f"A{a}, C{c}, S{s}")
        plt.grid()
        plt.show()
        # plt.axhline(y=rate, color="r", linestyle="--", label=f"Win Rate: {rate:.2f}%")
        # print(f"予測勝率: {rate:.2f}%")

    except ValueError:
        print("無効な入力です。整数を入力してください。")
    except KeyboardInterrupt:
        break