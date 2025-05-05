# カスミ勝率
# 個体値を変化させたときのカスミの勝率を計算する
from pyboy import PyBoy
import os
import math
import random
from tqdm import tqdm
import time
from PIL import Image
import signal
import time
import csv

# ffmpeg -i src/python/kasumi/output.gif -vf "scale=20*8*8:18*8*8:flags=neighbor,setpts=0.2*PTS" -movflags faststart -pix_fmt yuv420p output.mp4

os.chdir(os.path.dirname(__file__))

# ROMのパスを指定
romPath = "./pokemonBlue.gb"
# 画面を表示させる場合はrender=Trueにする
render = False
# saveする場合はTrueにする
save = False
# GIFを保存する場合はTrueにする
record = False 

def signal_handler(sig, frame):
    print("Exiting...")
    pyboy.stop()
    exit(0)

# Ctrl+Cで終了するための処理
signal.signal(signal.SIGINT, signal_handler)

def reset_pyboy():
    pyboy.stop()
    ret = PyBoy(romPath, sound_volume=0, window="SDL2" if render else "null", no_input=not render)
    ret.set_emulation_speed(0)
    return ret

# 入力を受け付けたい場合はno_input=Falseにする
pyboy = PyBoy(romPath, sound_volume=0, window="SDL2" if render else "null", no_input=not render)
# エミュレーション速度を最速にする 1で等速になる
pyboy.set_emulation_speed(0)



# 条件が満たされていれば待機させる関数
# triggerがTrueならば条件が満たされるまで待機
def wait_until(condition_fn, trigger=False):
    while True:
        pyboy.tick(1, render, False)
        c = condition_fn()
        if (c and trigger) or ((not trigger) and (not c)):
            break

STATES_TYPE = ("h", "a", "b", "s", "c")
# ニドキングのステータス
def nid_states(a, b, s, c): # 個体値とレベルを渡す
    lv = 25
    h = (a % 2 << 3) + (b % 2 << 2) + (s % 2 << 1) + c % 2
    IV = {"h":h, "a": a, "b":b, "s":s, "c":c} # 個体値
    base = {"h":81, "a":92, "b":77, "s":85, "c":75} # 種族値
    exp = {"h":1871, "a":2094, "b":2376, "s":2283, "c":2559} # 努力値
    ret = {x: (((2 *(base[x] + IV[x]) + math.ceil((math.sqrt(exp[x]))) // 4) * lv) // 100)
            + (5 if x != "h" else (lv + 10)) for x in IV}
    return ret


frames = []
def event_01():
    cnt = 0
    def condition():
        nonlocal cnt
        global frames
        if cnt <= 0:
            pyboy.button("a")
            cnt = random.randrange(0, 5)
        cnt -= 1
        if record:
            frames.append(pyboy.screen.image.copy())

        
        return pyboy.memory[0xd034] != 2

    wait_until(condition, True)

ACSet = {"a": set(), "c": set()}
ACs = {x: [] for x in ACSet.keys()}
for key in ACSet.keys(): 
    for j in range(16):
        if key == "a" and j < 5:
            continue
        v = nid_states(j, j, j, j)[key]
        if v in ACSet[key]:
            continue
        ACSet[key].add(v)
        ACs[key].append(j)

print(ACs)


N = 10000 if not record else 10 # 1サンプル当たりの試行回数
result = []
total = 3 * len(ACs["a"]) * len(ACs["c"]) 
cnt = 0
tqbar = tqdm([], position=0, bar_format="{desc}")


def trial(A, B, S, C, HP):
        global pyboy
        global cnt
        global frames
        global tqbar
        global result
        global total
        global record
        global N
        win = 0
        frames = []
        # new_state = {"h": h, "a": a, "b": b, "s": s, "c": c}
        new_state = nid_states(A, B, S, C)
        for i in range(N):
            if i % 500 == 0:
                pyboy = reset_pyboy()
            with open(f"{romPath}.state", "rb") as f:
                pyboy.load_state(f)
            # pyboy.memory[0xff04] = random.randrange(0, 256)
            # print([hex(x) for x in pyboy.memory[0xd858:0xd858 + 4]])
            pyboy.memory[0xffd3] = random.randrange(0, 256)
            pyboy.memory[0xffd4] = random.randrange(0, 256)
            for j in range(random.randrange(0, 5)):
                pyboy.tick() # 乱数を進める
            
            for j, v in enumerate(STATES_TYPE):
                pyboy.memory[0xd14d + j * 2 + 1] = new_state[v]
            # print([hex(x) for x in pyboy.memory[0xd14d:0xd14d + 10]])
            pyboy.memory[0xd12d] = HP
            event_01()
            if pyboy.memory[0xcffd] != 0:
                win += 1
            tqbar.set_description_str(f"    A{A},B8,S{S},C{C},HP{HP}, win_rate: {win}/{i + 1}={100 * win / (i + 1): .2f}%")
        
        if record:
            frames[0].save("output.gif", save_all=True, append_images=frames[1:], duration=1, loop=0)
            print(len(frames))
        return win

trial(0, 8, 15, 15, 83)

# with open("result.csv", "w", newline="") as csvfile:
#     csvwriter = csv.DictWriter(csvfile, fieldnames=["A", "B", "S", "C", "HP", "Win"])
#     csvwriter.writeheader()

#     for S in [10, 11, 15][::-1]:
#         for A in ACs["a"][::-1]:
#             for C in ACs["c"][::-1]:
#                 state = nid_states(A, 8, S, C)
#                 samples = []
#                 for HP in range(40, state["h"] + 1)[::-1]:
                    
#                     # for i in range(N):
#                     #     if i % 500 == 0:
#                     #         pyboy = reset_pyboy()
#                     #     with open(f"{romPath}.state", "rb") as f:
#                     #         pyboy.load_state(f)
#                     #     # pyboy.memory[0xff04] = random.randrange(0, 256)
#                     #     # print([hex(x) for x in pyboy.memory[0xd858:0xd858 + 4]])

#                     #     # pyboy.memory[0xffd3] = random.randrange(0, 256)
#                     #     # pyboy.memory[0xffd4] = random.randrange(0, 256)
#                     #     # for j in range(random.randrange(0, 5)):
#                     #     #     pyboy.tick() # 乱数を進める
                        
#                     #     # for j, (k, v) in enumerate(state.items()):
#                     #     #     pyboy.memory[0xd14d + j * 2 + 1] = v
#                     #     # pyboy.memory[0xd12d] = HP
#                     #     # event_01()
#                     startTime = time.time()
#                     win = trial(A, 8, S, C, HP)
#                     endTime = time.time()
#                     print(f"\nA{A},B8,S{S},C{C},HP{HP}, win_rate:{100 * win / N}%, time:{endTime - startTime: 0.2f}s progress: {100 * (cnt / total + (HP - 40) / ((state['h'] - 40) * total)): .2f}%")
#                     csvwriter.writerow({"A": A, "B": 8, "S": S, "C": C, "HP": HP, "Win": win})
#                     csvfile.flush()
#                     if record:
#                         frames[0].save("output.gif", save_all=True, append_images=frames[1:], duration=1, loop=0)
#                         print(len(frames))
#                 add = (f"A{A},B8,S{S},C{C}", samples)
#                 result.append(add)
#                 print(add)
#                 cnt += 1

# ステートを保存する場合はsave=Trueを指定する
if save:
    with open(f"{romPath}.state", "wb") as f:
        pyboy.save_state(f)
pyboy.stop()

# ('A15,B8,S15,C15', [1870, 1870, 1864, 1830, 1837, 1824, 1838, 1790, 1777, 1795, 1800, 1768, 1739, 1749, 1729, 1708, 1736, 1667, 1694, 1656, 1623, 1622, 1597, 1606, 1531, 1551, 1561, 1573, 1542, 1560, 1577, 1550, 1555, 1559, 1565, 1548, 1573, 1560, 1589, 1552, 1546, 1469, 1363, 1281])
