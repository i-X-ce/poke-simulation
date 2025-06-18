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

LV = 19 # レベル
# アリゲイツのステータス
def croconaw_states(a, b, s, c): # 個体値とレベルを渡す
    IV = (a, b, s, c) # 個体値
    base = (65, 80, 80, 58, 59, 63) # 種族値
    exp = (8, 9, 9, 8, 8, 9) # 努力レベル
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
        value = croconaw_states(iv, iv, iv, iv)[state]
        if value in values:
            continue
        values.add(value)
        ivs.append(iv)
    return ivs


MIN_HP = croconaw_states(0, 0, 0, 0)["h"] - 5 # 最小HP
MAX_HP = croconaw_states(15, 15, 15, 15)["h"] # 最大HP
As = IVs("a", 5, 15) # 攻撃の個体値リスト
Bs = IVs("b", 0, 15) # 防御の個体値リスト
Cs = IVs("c", 6, 15) # 特殊の個体値リスト

def event(pyboy: PyBoy, type=0):
    end_type = 0 # 終了タイプ 0:続行, 1:勝利, 2:敗北, -1:強制終了
    frame_cnt = 0 # フレームカウント
    
    def end_check():
        nonlocal end_type
        nonlocal frame_cnt

        if frame_cnt > 60 * 100: 
            end_type = -1 
            return True # 100秒経過した場合は強制終了
        if end_type != 0:
            return True # すでに終了している場合は何もしない
        if pyboy.memory[0xcb15] == 0:
            return False # 戦闘が始まっていない場合は何もしない
        
        if pyboy.memory[0xd0e1] == 0xf1 and pyboy.memory[0xcb35] == 0x01 and pyboy.memory[0xd0f1] == 0 and pyboy.memory[0xd0f2] == 0x0:
            end_type = 1 # ミルタンクのHPが0になった場合勝利
        if (pyboy.memory[0xcb13] == 0 and pyboy.memory[0xcb14] == 0):
            end_type = 2 # アリゲイツのHPが0になった場合敗北
        return end_type != 0
    
    def push_button(button):
        nonlocal frame_cnt
        pyboy.button(button)
        addcnt = random.randint(1, 5)
        frame_cnt += addcnt
        pyboy_tick(pyboy, addcnt) # ボタンを押してから1フレーム待機

    # 操作と終了判定を行う関数
    # actions: (操作, 判定)のタプル
    def execute_actions(actions):
        for action, condition in actions:
            def wait_condition():
                nonlocal frame_cnt
                action()
                frame_cnt += 1
                return condition()
            wait_until(pyboy, wait_condition, True)
    
    # れんぞくぎり
    if type == 0:
        actions = [
            (
                lambda: push_button("a"), 
                lambda: end_check()
            ),
        ]
        execute_actions(actions)

    # いかり
    elif type == 1:
        actions = [
            (
                lambda: push_button("a"), 
                lambda: pyboy.memory[0xc440] == 0x79 or end_check()
            ),
            (
                lambda: push_button("down"), 
                lambda: pyboy.memory[0xcbb5] == 0x63 or end_check()
            ),
        ]
        execute_actions(actions)
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

def trial(A, B, S, C, HP, type=0):
    pyboy = init_pyboy()
    croconaw_state = croconaw_states(A, B, S, C)
    # print(croconaw_state)
    with open(f"{rom_path}.state", "rb") as f:
        state_data = f.read()
    
    win = 0
    total_frame_cnt = 0
    for _ in range(N):
        while True: 
            pyboy.load_state(BytesIO(state_data))

            START_ADDR = 0xda12
            for j, v in enumerate(STATES_TYPE):
                addr = START_ADDR + (j + 1) * 2
                pyboy.memory[addr] = 0
                pyboy.memory[addr + 1] = croconaw_state[v]
                # print(f"{v}: {croconaw_state[v]}")
            pyboy.memory[START_ADDR] = 0
            pyboy.memory[START_ADDR + 1] = HP
            pyboy.memory[0xda0f] = LV  

            pyboy.memory[0xffe3] = random.randrange(0, 256) # 乱数初期化
            pyboy.memory[0xffe4] = random.randrange(0, 256)
            pyboy_tick(pyboy, random.randint(1, 5))
            end_type, frame_cnt = event(pyboy, type)
            if render:
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
    return logging.info(f"\033[32mA{A}B{B}S{S}C{C}H{HP}T{type}, win: {win}/{N} ({100 * win / N:.2f}%), progress: {progress + 1}/{len(all_args)} ({(progress + 1) / len(all_args) * 100:.2f}%), frame: {frame}, ave_frame: {frame / max(1, win):.2f}f\033[0m")

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def trial_wrapper(args):
        No, (A, B, S, C, HP, type) = args
        return No, trial(A, B, S, C, HP, type)

if __name__ == "__main__":
    all_args = [(a, b, 5, c, hp, type) for type in range(2) for a in As for b in Bs for c in Cs for hp in range(MIN_HP, MAX_HP + 1)]
    all_args = [(i, args) for i, args in enumerate(all_args)]

    if multi_process:
        csvfile = open(f"result/result_{time.strftime('%Y%m%d_%H%M%S')}.csv", "w", newline="")
        csvwriter = csv.DictWriter(csvfile, fieldnames=["No", "A", "B", "S", "C", "HP", "Win", "Frame"])
        csvwriter.writeheader()

        totalStartTime = time.time()
        logging.info(f"Total trials: {len(all_args)}")
        logging.info(f"Starting trials... ")

        try:
            with Pool(initializer=init_worker) as pool:
                results_iterator = pool.imap_unordered(trial_wrapper, all_args)
                for i, result in enumerate(results_iterator):
                    No, (win, frame) = result 
                    A, B, S, C, HP, type = all_args[No][1]
                    csvwriter.writerow({
                        "No": No, "A": A, "B": B, "S": S, "C": C, "HP": HP, 
                        "Win": win, "Frame": frame
                    })
                    csvfile.flush()
                    result_rog(A, B, S, C, HP, type, i, win, frame)
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
        win, frame = trial(0, 0, 0, 0, MIN_HP, 1)
        print(f"win:{win}/{N}, frame:{frame}, average frame: {frame / max(1, win):.2f} frames")

        totalEndTime = time.time()
        logging.info(f"Total time: {totalEndTime - totalStartTime:.2f}s")