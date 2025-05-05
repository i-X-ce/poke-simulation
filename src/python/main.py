# テンプレート
from pyboy import PyBoy
import os
import signal

os.chdir(os.path.dirname(__file__))

# ROMのパスを指定
romPath = ""
# 画面を表示させる場合はrender=Trueにする
render = False
# saveする場合はTrueにする
save = True

def signal_handler(sig, frame):
    print("Exiting...")
    pyboy.stop()
    exit(0)

# Ctrl+Cで終了するための処理
signal.signal(signal.SIGINT, signal_handler)

# 入力を受け付けたい場合はno_input=Falseにする
pyboy = PyBoy(romPath, sound_volume=0, window="SDL2" if render else "null", no_input=True)
# エミュレーション速度を最速にする 1で等速になる
pyboy.set_emulation_speed(0)
# ステートを読み込む
# 読み込む必要がなければこの行は削除しても良い
with open(f"{romPath}.state", "rb") as f:
    pyboy.load_state(f)


# 条件が満たされていれば待機させる関数
# triggerがTrueならば条件が満たされるまで待機
def wait_until(condition_fn, trigger=False):
    while True:
        pyboy.tick(1, render, False)
        c = condition_fn()
        if (c and trigger) or ((not trigger) and (not c)):
            break


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
if save:
    with open(f"{romPath}.state", "wb") as f:
        pyboy.save_state(f)
pyboy.stop()
