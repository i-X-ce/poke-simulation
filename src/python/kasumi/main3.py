# カスミ勝率
# マルチプロセスに対応
from multiprocessing import Pool
import time
from pyboy import PyBoy
import os
import signal
import math
import random
from tqdm import tqdm
import csv
from io import BytesIO
import logging 

os.chdir(os.path.dirname(__file__))

# logging の設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(process)d - %(levelname)s - %(message)s')

# ROMのパスを指定
romPath = "./pokemonBlue.gb"
# 画面を表示させる場合はrender=Trueにする
render = False
# マルチプロセスで実行する場合はTrueにする
multi_process = True

# 1サンプル当たりの試行回数
N = 2

def signal_handler(sig, frame):
    print("Exiting...")
    # pyboy.stop()
    os._exit(0)

# Ctrl+Cで終了するための処理
# signal.signal(signal.SIGINT, signal_handler)

def init_pyboy():
    ret = PyBoy(romPath, sound_volume=0, window="SDL2" if render else "null", no_input=not render)
    ret.set_emulation_speed(0)
    return ret

# 条件が満たされていれば待機させる関数
# triggerがTrueならば条件が満たされるまで待機
def wait_until(pyboy: PyBoy, condition_fn, trigger=False):
    while True:
        pyboy.tick(1, render, False)
        c = condition_fn()
        if (c and trigger) or ((not trigger) and (not c)):
            break

# ニドキングのステータス
def nid_states(a, b, s, c): # 個体値とレベルを渡す
    lv = 25
    IV = (a, b, s, c) # 個体値
    base = (81, 92, 77, 85, 75) # 種族値
    exp = (1871, 2094, 2376, 2283, 2559) # 努力値
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

MAX_HP = nid_states(15, 15, 15, 15)["h"]
RHP_KEY = [f"{i}" for i in range(1, MAX_HP + 1)]
ACSet = {"a": set(), "c": set()}
ACs = {x: [] for x in ACSet.keys()}
for key in ACSet.keys(): 
    for j in range(16):
        if key == "a" and j < 8:
            continue
        v = nid_states(j, j, j, j)[key]
        if v in ACSet[key]:
            continue
        ACSet[key].add(v)
        ACs[key].append(j)
# print(ACs)

def abareru_event(pyboy: PyBoy):
    cnt = 0
    def condition():
        nonlocal cnt
        if cnt <= 0:
            pyboy.button("a")
            cnt = random.randrange(0, 5)
        cnt -= 1
        return pyboy.memory[0xd034] != 2

    wait_until(pyboy, condition, True)

def trial(A, B, S, C, HP):
    pyboy = init_pyboy()
    nid_state = nid_states(A, B, S, C)
    with open(f"{romPath}.state", "rb") as f:
        state_data = f.read()

    win = 0
    ret_HP = {i: 0 for i in RHP_KEY}
    for _ in range(N):
        pyboy.load_state(BytesIO(state_data))

        for j, v in enumerate(STATES_TYPE):
            pyboy.memory[0xd14d + j * 2 + 1] = nid_state[v]
        pyboy.memory[0xd12d] = HP

        pyboy.memory[0xffd3] = random.randrange(0, 256) # 乱数初期化
        pyboy.memory[0xffd4] = random.randrange(0, 256)
        for j in range(random.randint(1, 5)):
            pyboy.tick()
        abareru_event(pyboy)
        if pyboy.memory[0xcffd] != 0:
            ret_HP[RHP_KEY[pyboy.memory[0xcffd] - 1]] += 1
            win += 1
    return win, ret_HP

def trial_wrapper(args):
    No, (A, B, S, C, HP) = args
    return No, trial(A, B, S, C, HP)

def result_rog(A, B, S, C, HP, progress, win):
    return f"\033[32mA{A}B{B}S{S}C{C}HP{HP}, win: {win}/{N} ({100 * win / N:.2f}%), progress: {progress + 1}/{len(all_args)} ({(progress + 1) / len(all_args) * 100:.2f}%)\033[0m"

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

if __name__ == "__main__":
    csvfile = open(f"result/result_{time.strftime('%Y%m%d_%H%M%S')}.csv", "w", newline="")
    csvwriter = csv.DictWriter(csvfile, fieldnames=["No", "A", "B", "S", "C", "HP", "Win"] + RHP_KEY)
    csvwriter.writeheader()

    all_args = [(A, 8, S, C, HP) for A in ACs["a"] for S in [10, 11, 15] for C in ACs["c"] for HP in range(50, nid_states(A, 8, S, C)["h"] + 1)]
    all_args = [(No, args) for No, args in enumerate(all_args)]

    if multi_process:
        totalStartTime = time.time()
        logging.info(f"Total trials: {len(all_args)}")
        logging.info(f"Starting trials... ")
        try: 
            with Pool(initializer=init_worker) as pool:
                results_iterator = pool.imap_unordered(trial_wrapper, all_args)
                for i, result in enumerate(results_iterator):
                    No, (win, hps) = result
                    A, B, S, C, HP = all_args[No][1]
                    csvwriter.writerow({"No": No, "A": A, "B": B, "S": S, "C": C, "HP": HP, "Win": win, **hps})
                    csvfile.flush()
                    logging.info(result_rog(A, B, S, C, HP, i, win))
                    # logging.info(f"Progress: {i + 1}/{len(all_args)} ({(i + 1) / len(all_args) * 100:.2f}%)")
        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt received. Terminating pool...")
            pool.terminate()
            pool.join()
        else:
            pool.close()
            pool.join()
        
        totalEndTime = time.time()
        logging.info(f"Total time: {totalEndTime - totalStartTime:.2f}s")
    else :
        win, hps = trial(15, 15, 15, 15, 83)
        csvwriter.writerow({"A": 15, "B": 15, "S": 15, "C": 15, "HP": 40, "Win": win, **hps})
    
    csvfile.close()