# テンプレート
from pyboy import PyBoy
import os

os.chdir(os.path.dirname(__file__))

# 画面を表示させる場合はrender=Trueにする
render = False

# ROMのパスを指定
# 画面を表示させる場合はwindow="null"にする
# 入力を受け付けたい場合はno_input=Falseにする
pyboy = PyBoy("pokemonBlue.gb", sound_volume=0, window="SDL2" if render else "null", no_input=True)
# エミュレーション速度を最速にする 1で等速になる
pyboy.set_emulation_speed(0)
# ステートを読み込む
# 読み込む必要がなければこの行は削除しても良い
with open("./pokemonBlue.gb.state", "rb") as f:
    pyboy.load_state(f)


# 条件が満たされていれば待機させる関数
def wait_until(condition_fn):
    while condition_fn():
        pyboy.tick(1, render, False)


# イベント
# 状況に合わせて複数用意する
def event_01():

    # 条件を定義する
    # Trueならば待機
    def condition():
        return True
    
    # 条件が外れるまで待つ
    wait_until(condition)

# イベントを実行する
event_01()
# event_02()
# event_03()
# ...

# ステートを保存する場合はsave=Trueを指定する
pyboy.stop(save=True)
