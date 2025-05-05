# テンプレート
import time
from pyboy import PyBoy
import os
import signal
import math
import random
from tqdm import tqdm
import csv

os.chdir(os.path.dirname(__file__))

# ROMのパスを指定
romPath = "./pokemonBlue.gb"
# 画面を表示させる場合はrender=Trueにする
render = False
# saveする場合はTrueにする
save = False

# 1サンプル当たりの試行回数
N = 200

def signal_handler(sig, frame):
    print("Exiting...")
    pyboy.stop()
    exit(0)

# Ctrl+Cで終了するための処理
signal.signal(signal.SIGINT, signal_handler)

# 入力を受け付けたい場合はno_input=Falseにする
pyboy = PyBoy(romPath, sound_volume=0, window="SDL2" if render else "null", no_input=not render)
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

# ニドキングのステータス
def nid_states(a, b, s, c): # 個体値とレベルを渡す
    lv = 23
    IV = (a, b, s, c) # 個体値
    base = (81, 92, 77, 85, 75) # 種族値
    exp = (1288, 1528, 1599, 1638, 1927) # 努力値
    return poke_states(lv, base, IV, exp)

# ポケモンのステータス実数値
# lv:レベル, base:種族値, IVs:個体値, exp:努力値
STATES_TYPE = ("h", "a", "b", "s", "c")
def poke_states(lv, base, IV, exp):
    a, b, s, c = IV
    h = (a % 2 << 3) + (b % 2 << 2) + (s % 2 << 1) + c % 2 
    IV = {"h":h, "a": a, "b": b, "s": s, "c": c} # 個体値
    base = {x: base[i] for i, x in enumerate(STATES_TYPE)} # 種族値
    exp = {x: exp[i] for i, x in enumerate(STATES_TYPE)} # 努力値
    return {x: (((2 *(base[x] + IV[x]) + math.ceil((math.sqrt(exp[x]))) // 4) * lv) // 100)
            + (5 if x != "h" else (lv + 10)) for x in IV}

# あばれる
def event_abareru():
    cnt = 0
    def condition():
        nonlocal cnt
        cnt -= 1
        if cnt <= 0:
            pyboy.button("a")
            cnt = random.randint(1, 5)
        return pyboy.memory[0xd034] != 2
    wait_until(condition, True)

# にらみつける
def event_nirami():
    cnt = 0
    # ランダムなタイミングでボタンを押す
    def rnd_push(button):
        nonlocal cnt
        if cnt <= 0:
            pyboy.button(button)
            cnt = random.randint(1, 5)
        cnt -= 1
    # わざを開く 
    def condtion():
        rnd_push("a")
        return pyboy.memory[0xc440] == 0x79
    wait_until(condtion, True)
    
    # にらみつけるを選択
    def condition():
        rnd_push("down")
        return pyboy.memory[0xccdc] == 0x2b
    wait_until(condition, True)
    def condition():
        rnd_push("a")
        return pyboy.memory[0xcd2f] == 0x06
    wait_until(condition, True)
    
    # つのでつくを選択
    def condition():
        rnd_push("a")
        return pyboy.memory[0xc440] == 0x79
    wait_until(condition, True)
    def condition():
        rnd_push("down")
        return pyboy.memory[0xccdc] == 0x1e
    wait_until(condition, True)
    def condition():
        rnd_push("a")
        return pyboy.memory[0xcfcc] != 0x6a
    wait_until(condition, True)

    # あばれるを選択
    def condition():
        rnd_push("a")
        return pyboy.memory[0xc440] == 0x79
    wait_until(condition, True)
    def condition():
        rnd_push("down")
        return pyboy.memory[0xccdc] == 0x25
    wait_until(condition, True)
    event_abareru()


# 試行
# event_type: 0:あばれる, 1:にらみつける
def trial(A, B, HP, event_type=0):
    global pyboy

    win = 0
    state = nid_states(A, B, 15, 15)
    tqbar = tqdm([], position=0, bar_format="{desc}")
    for i in range(N):
        # ステートを読み込む
        with open(f"{romPath}.state", "rb") as f:
            pyboy.load_state(f)

        # ステータスをセットする
        for j, v in enumerate(STATES_TYPE):
            pyboy.memory[0xd14d + j * 2 + 1] = state[v]
        pyboy.memory[0xd12d] = HP # HPをセットする

        # 乱数を書き込む
        pyboy.memory[0xffd3] = random.randrange(0, 256)
        pyboy.memory[0xffd4] = random.randrange(0, 256)
        for j in range(random.randint(1, 5)):
            pyboy.tick() # 乱数を進める
        
        # イベントを実行する
        if event_type == 0: event_abareru()
        else : event_nirami()

        if pyboy.memory[0xcffd] != 0:
            win += 1
        tqbar.set_description(f"A{A}B{B}HP{HP}, win_rate: {win}/{i + 1}={win / (i + 1) * 100:.2f}%")
    return win

with open("result.csv", "w", newline="") as csvfile:
    csvwriter = csv.DictWriter(csvfile, fieldnames=["A", "B", "HP", "Win", "Type"])
    csvwriter.writeheader()
    total = 16 * 16 * 30 * 2 # A, B, HP, event_type
    cnt = 0
    allStartTime = time.time()
    for ET in range(2):
        for A in range(16):
            for B in range(16):
                state = nid_states(A, B, 15, 15)
                for HP in range(30):
                    cnt += 1
                    HP += 1
                    startTime = time.time()
                    win = trial(A, B, HP, event_type=ET)
                    endTime = time.time()
                    csvwriter.writerow({"A": A, "B": B, "HP": HP, "Win": win, "Type": ET})
                    csvfile.flush()
                    print(f"\033[32mA{A}B{B}HP{HP}, win_rate:{100 * win / N}%, time:{endTime - startTime: 0.2f}s progress:{100 * cnt / total: .2f}%\033[0m\n")
    print(f"Total time: {time.time() - allStartTime: 0.2f}s")



# ステートを保存する場合はsave=Trueを指定する
if save:
    with open(f"{romPath}.state", "wb") as f:
        pyboy.save_state(f)
pyboy.stop()
