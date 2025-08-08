import csv
from io import BytesIO
import logging
from multiprocessing import Pool
import os
import random
import signal
import time
from pyboy import PyBoy 

os.chdir(os.path.dirname(__file__))

# logging の設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(process)d - %(levelname)s - %(message)s')

rom_path = "./pokemonGold.gb"
render = False
multi_process = True # マルチプロセスで実行する場合はTrueにする
log = False

# 1サンプル当たりの試行回数
N = 1000

def signal_handler(signum, frame):
    print("Exiting...")
    # pyboy.stop()
    os._exit(0)

# Ctrl+Cで終了するための処理
signal.signal(signal.SIGINT, signal_handler)

def init_pyboy():
    ret = PyBoy(rom_path, sound_volume=0, window="SDL2" if render else "null", no_input=not render)
    ret.set_emulation_speed(2 if render else 0)
    return ret

def pyboy_tick(pyboy: PyBoy, frames=1):
    pyboy.tick(frames, render, False)

# 条件が満たされていれば待機させる関数
# triggerがTrueならば条件が満たされるまで待機
def wait_until(pyboy: PyBoy, condition_fn, trigger=False):
    while True:
        pyboy_tick(pyboy, 1)
        c = condition_fn()
        if (c and trigger) or ((not trigger) and (not c)):
            break

LV = 16 # レベル
# ワニノコのステータス
def totodile_states(a, b, s, c): # 個体値とレベルを渡す
    IV = (a, b, s, c) # 個体値
    base = (50, 65, 64, 43, 44, 48) # 種族値
    exp = (7, 8, 7, 7, 7, 8) # 努力レベル
    return poke_states(LV, base, IV, exp)

# ポケモンのステータス実数値
# lv:レベル, base:種族値, IVs:個体値, exp:努力レベル
STATES_TYPE = ("h", "a", "b", "s", "c", "d")
def poke_states(lv, base, IV, exp):
    a, b, s, c = IV
    d = c # 特防は特攻と同じ値を使用
    h = (a % 2 << 3) + (b % 2 << 2) + (s % 2 << 1) + c % 2 
    IV = {"h":h, "a": a, "b": b, "s": s, "c": c, "d": d} # 個体値
    base = {x: base[i] for i, x in enumerate(STATES_TYPE)} # 種族値
    exp = {x: exp[i] for i, x in enumerate(STATES_TYPE)} # 努力レベル
    return {x: (((2 *(base[x] + IV[x]) + exp[x]) * lv) // 100)
            + (5 if x != "h" else (lv + 10)) for x in IV}

# 同じ実数値になる個体値を省いた個体値リストを生成する
def IVs(state, min_IV, max_IV):
    values = set()
    ivs = []
    for iv in range(min_IV, max_IV + 1):
        value = totodile_states(iv, iv, iv, iv)[state]
        if value in values:
            continue
        values.add(value)
        ivs.append(iv)
    return ivs


MIN_HP = totodile_states(15, 15, 15, 15)["h"] - 10 # 最小HP
MAX_HP = totodile_states(15, 15, 15, 15)["h"] # 最大HP
As = IVs("a", 4, 15) # 攻撃の個体値リスト
Bs = IVs("b", 0, 15) # 防御の個体値リスト
if log:
    print(f"MIN_HP: {MIN_HP}, MAX_HP: {MAX_HP}")
    print(f"攻撃の個体値リスト: {As}")
    print(f"防御の個体値リスト: {Bs}")

def event(pyboy: PyBoy, type=0):
    end_type = 0 # 終了タイプ 0:続行, 1:勝利, 2:敗北, -1:強制終了
    frame_cnt = 0 # フレームカウント
    
    def end_check():
        nonlocal end_type
        nonlocal frame_cnt

        if frame_cnt > 60 * 300:
            end_type = -1
            return True
        if end_type != 0:
            return True
        if pyboy.memory[0xcb15] == 0:
            return False
        
        # 相手のポケモンが全滅した場合勝利
        if sum([pyboy.memory[0xdcf0 + x * 48] * 256 + pyboy.memory[0xdcf1 + x * 48] for x in range(6)]) == 0:
            end_type = 1
        # ワニノコのHPが0になった場合敗北
        if pyboy.memory[0xcb13] + pyboy.memory[0xcb14] == 0:
            end_type = 2
        return end_type != 0
    
    def push_button(button):
        nonlocal frame_cnt
        pyboy.button(button)
        addcnt = random.randint(1, 5)
        frame_cnt += addcnt
        pyboy_tick(pyboy, addcnt)

    # プラスパワーなし
    if type == 0:
        def condition():
            push_button("a")
            return end_check()
        wait_until(pyboy, condition, True)

    # プラスパワーあり
    elif type == 1:
        # カーソルを右に
        def condition():
            push_button("right")
            return pyboy.memory[0xcf15] == 0x02
        wait_until(pyboy, condition, True)
        # プラスパワーを使用
        def condition():
            push_button("a")
            return pyboy.memory[0xcb9e] == 0x08 or end_check()
        wait_until(pyboy, condition, True)
        # メニューに戻る
        def condition():
            push_button("b")
            return pyboy.memory[0xcf15] == 0x02 or end_check()
        wait_until(pyboy, condition, True)
        # カーソルを左に
        def condition():
            push_button("left")
            return pyboy.memory[0xcf15] == 0x01 or end_check()
        wait_until(pyboy, condition, True)
        # いかり連打
        def condition():
            push_button("a")
            return end_check()
        wait_until(pyboy, condition, True)

    if render:
        if end_type == 1:
            print("Win!")
        elif end_type == 2:
            print("Lose!")
        for _ in range(3 * 60):
            pyboy_tick(pyboy)
    
    return end_type, frame_cnt

def trial(A, B, HP, type, S=9, C=9):
    pyboy = init_pyboy()
    croconaw_state = totodile_states(A, B, S, C)
    # print(croconaw_state)
    with open(f"{rom_path}.state", "rb") as f:
        state_data = f.read()
    
    win = 0
    total_frame_cnt = 0
    for _ in range(N):
        while True: 
            pyboy.load_state(BytesIO(state_data))

            # 実数値を初期化
            ABILITY_ADDR = 0xda12
            for j, v in enumerate(STATES_TYPE):
                addr = ABILITY_ADDR + (j + 1) * 2
                pyboy.memory[addr] = 0
                pyboy.memory[addr + 1] = croconaw_state[v]
            pyboy.memory[ABILITY_ADDR] = 0
            pyboy.memory[ABILITY_ADDR + 1] = HP
            pyboy.memory[0xda05] = A * 0x10 + B # 個体値を設定
            pyboy.memory[0xda06] = S * 0x10 + C # 個体

            # 努力値を初期化
            # EXP_ADDR = 0xd9fb
            # for j, v in enumerate([0, 0, 0, 0, 0, 0]):
            #     addr = EXP_ADDR + j * 2
            #     pyboy.memory[addr] = v / 256
            #     pyboy.memory[addr + 1] = v % 256

            pyboy.memory[0xffe3] = random.randrange(0, 256) # 乱数初期化
            pyboy.memory[0xffe4] = random.randrange(0, 256)
            pyboy_tick(pyboy, random.randint(1, 5))
            end_type, frame_cnt = event(pyboy, type)

            if log:
                print(f"calc: {croconaw_state}")
                print(f"da14: {({x: pyboy.memory[0xda14 + i * 2 + 1] for i, x in enumerate(STATES_TYPE)})}")
                print(f"cb14: {({x: pyboy.memory[0xcb14 + i * 2 + 1] for i, x in enumerate(STATES_TYPE)})}")

            if end_type != -1:
                if end_type == 1:
                    win += 1
                    total_frame_cnt += frame_cnt
                break
    return win, total_frame_cnt


def result_rog(A, B, S, C, HP, type, progress, win, frame):
    return logging.info(f"\033[32mT{type}A{A}B{B}S{S}C{C}H{HP}, win: {win}/{N} ({100 * win / N:.2f}%), progress: {progress + 1}/{len(all_args)} ({(progress + 1) / len(all_args) * 100:.2f}%), frame: {frame}, ave_frame: {frame / max(1, win):.2f}f\033[0m")

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def trial_wrapper(args):
        No, (A, B, HP, type) = args
        return No, trial(A, B, HP, type)

if __name__ == "__main__":
    all_args = [(A, B, HP, type) for type in range(2) for A in As for B in Bs for HP in range(MIN_HP, MAX_HP + 1)]
    all_args = [(i, args) for i, args in enumerate(all_args)]

    if multi_process:
        csvfile = open(f"result/result_{time.strftime('%Y%m%d_%H%M%S')}.csv", "w", newline="")
        csvwriter = csv.DictWriter(csvfile, fieldnames=["No", "Type", "A", "B", "HP", "Win", "Frame"])
        csvwriter.writeheader()

        totalStartTime = time.time()
        logging.info(f"Total trials: {len(all_args)}")
        logging.info(f"Starting trials... ")

        try:
            with Pool(initializer=init_worker) as pool:
                results_iterator = pool.imap_unordered(trial_wrapper, all_args)
                for i, result in enumerate(results_iterator):
                    No, (win, frame) = result 
                    A, B, HP, type = all_args[No][1]
                    csvwriter.writerow({
                        "No": No, "Type": type, "A": A, "B": B, "HP": HP, 
                        "Win": win, "Frame": frame
                    })
                    csvfile.flush()
                    result_rog(A, B, 9, 9, HP, type, i, win, frame)
        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt received. Terminating pool...")
            pool.terminate()
            pool.join()
        else:
            pool.close()
            pool.join()
        
        totalEndTime = time.time()
        logging.info(f"Total time: {totalEndTime - totalStartTime:.2f}s")
        csvfile.close()
    else:
        totalStartTime = time.time()
        logging.info(f"Starting trials... ")
        
        win, frame = trial(15, 15, MIN_HP, type=0)
        print(f"win:{win}/{N}, frame:{frame}, average frame: {frame / max(1, win):.2f} frames")

        win, frame = trial(15, 15, MIN_HP, type=1)
        print(f"win:{win}/{N}, frame:{frame}, average frame: {frame / max(1, win):.2f} frames")
        
        totalEndTime = time.time()
        logging.info(f"Total time: {totalEndTime - totalStartTime:.2f}s")