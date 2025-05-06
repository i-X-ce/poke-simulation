# イシツブテ戦の勝率を調べる
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
# saveする場合はTrueにする
save = False
# マルチスレッドで実行する場合はTrueにする
multi_thread = True

# 1サンプル当たりの試行回数
N = 200

def signal_handler(sig, frame):
    print("Exiting...")
    # pyboy.stop()
    os._exit(0)

# Ctrl+Cで終了するための処理
signal.signal(signal.SIGINT, signal_handler)

def init_pyboy():
    while True:
        try:
            ret = PyBoy(romPath, sound_volume=0, window="SDL2" if render else "null", no_input=not render)
            ret.set_emulation_speed(0)
            break
        except Exception as e:
            logging.error(f"Error initializing PyBoy: {e}", exc_info=True)
            time.sleep(0.01)  
    return ret



# 条件が満たされていれば待機させる関数
# triggerがTrueならば条件が満たされるまで待機
def wait_until(pyboy, condition_fn, trigger=False):
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
def event_abareru(pyboy: PyBoy):
    cnt = 0
    def condition():
        nonlocal cnt
        cnt -= 1
        if cnt <= 0:
            pyboy.button("a")
            cnt = random.randint(1, 5)
        return pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)

# にらみつける
def event_nirami(pyboy: PyBoy):
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
        return pyboy.memory[0xc440] == 0x79 or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condtion, True)
    
    # にらみつけるを選択
    def condition():
        rnd_push("down")
        return pyboy.memory[0xccdc] == 0x2b or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)
    def condition():
        rnd_push("a")
        return pyboy.memory[0xcd2f] == 0x06 or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)
    
    # つのでつくを選択
    def condition():
        rnd_push("a")
        return pyboy.memory[0xc440] == 0x79 or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)
    def condition():
        rnd_push("down")
        return pyboy.memory[0xccdc] == 0x1e or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)
    def condition():
        rnd_push("a")
        return pyboy.memory[0xcfcc] != 0x6a or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)

    # あばれるを選択
    def condition():
        rnd_push("a")
        return pyboy.memory[0xc440] == 0x79 or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)
    def condition():
        rnd_push("down")
        return pyboy.memory[0xccdc] == 0x25 or pyboy.memory[0xd034] != 2
    wait_until(pyboy, condition, True)
    event_abareru(pyboy)


# 試行
# event_type: 0:あばれる, 1:にらみつける
def trial(A, B, HP, event_type):
    process_id = os.getpid() # プロセスIDを取得
    # logging.info(f"[PID:{process_id}] Starting trial: A={A}, B={B}, HP={HP}, event_type={event_type}")
    try:
        new_pyboy = init_pyboy()
        # logging.info(f"[PID:{process_id}] PyBoy initialized for A={A}, B={B}, HP={HP}, event_type={event_type}")

        win = 0
        state = nid_states(A, B, 15, 15)
        # tqbar はマルチプロセスでは表示が乱れる可能性があるためコメントアウト推奨
        if not multi_thread: tqbar = tqdm([], position=0, bar_format="{desc}")

        with open(f"{romPath}.state", "rb") as f:
            state_data = f.read()
        # logging.info(f"[PID:{process_id}] State file read for A={A}, B={B}, HP={HP}, event_type={event_type}")

        for i in range(N):
            logging.debug(f"[PID:{process_id}] Starting iteration {i+1}/{N} for A={A}, B={B}, HP={HP}, event_type={event_type}")
            # ステートを読み込む
            new_pyboy.load_state(BytesIO(state_data))
            logging.debug(f"[PID:{process_id}] State loaded for iteration {i+1}")

            # ステータスをセットする
            for j, v in enumerate(STATES_TYPE):
                new_pyboy.memory[0xd14d + j * 2 + 1] = state[v]
            new_pyboy.memory[0xd12d] = HP # HPをセットする
            logging.debug(f"[PID:{process_id}] Status set for iteration {i+1}")

            # 乱数を書き込む
            new_pyboy.memory[0xffd3] = random.randrange(0, 256)
            new_pyboy.memory[0xffd4] = random.randrange(0, 256)
            for j in range(random.randint(1, 5)):
                new_pyboy.tick() # 乱数を進める
            logging.debug(f"[PID:{process_id}] Random numbers set for iteration {i+1}")

            # イベントを実行する
            # logging.info(f"[PID:{process_id}] Executing event {event_type} for iteration {i+1}")
            if event_type == 0:
                event_abareru(new_pyboy)
            else : # event_type == 1
                event_nirami(new_pyboy)
            # logging.info(f"[PID:{process_id}] Event {event_type} finished for iteration {i+1}")

            if new_pyboy.memory[0xcffd] != 0:
                win += 1
            if i % 10 == 0 and not multi_thread: tqbar.set_description(f"Type{event_type}, A{A}B{B}HP{HP}, win_rate: {win}/{i + 1} = {win / (i + 1) * 100:.2f}%")

        # logging.info(f"[PID:{process_id}] Finished trial: A={A}, B={B}, HP={HP}, event_type={event_type}, result={win}")
        new_pyboy.stop() # PyBoyインスタンスを停止
        return win
    except Exception as e:
        logging.error(f"[PID:{process_id}] Error in trial: A={A}, B={B}, HP={HP}, event_type={event_type} - {e}", exc_info=True)
        # エラーが発生した場合、Noneを返すか例外を再送出する
        return None # または raise

def trial_result2string(event_type, A, B, HP, win, time, progress):
    return f"\033[32mType{event_type}, A{A}B{B}HP{HP}, win_rate:{100 * win / N}%, time:{time: 0.2f}s progress:{100 * (progress) / total: .2f}%\033[0m"


# マルチスレッドで試行を実行する
def trial_wrapper(args):
    A, B, HP, ET = args
    return trial(A, B, HP, ET)

ABSet = {"a": set(), "b": set()}
ABs = {x: [] for x in ABSet.keys()}
for key in ABSet.keys():
    for j in range(16):
        v = nid_states(j, j, j, j)[key]
        if v in ABSet[key]:
            continue
        ABSet[key].add(v)
        ABs[key].append(j)
total = len(ABs["a"]) * len(ABs["b"]) * 30 * 2 # A, B, HP, event_type

if __name__ == "__main__":
    if multi_thread:
        with open("result.csv", "w", newline="") as csvfile:
            print(ABs, flush=True)
            csvwriter = csv.DictWriter(csvfile, fieldnames=["Type", "A", "B", "HP", "Win"])
            csvwriter.writeheader()
            all_args = [(A, B, HP + 1, ET) for ET in range(2) for A in ABs["a"] for B in ABs["b"] for HP in range(30)]
            totalStartTime = time.time()
            logging.info("Starting multiprocessing pool...")
            with Pool() as pool:
                try:
                    # pool.imap を使用
                    results_iterator = pool.imap(trial_wrapper, all_args)

                    for i, result_tuple in enumerate(zip(all_args, results_iterator)):
                        (A, B, HP, event_type), win = result_tuple
                        # エラーが発生した場合(win is Noneなど)の処理を追加
                        if win is None:
                            logging.warning(f"Skipping result due to error for A={A}, B={B}, HP={HP}, event_type={event_type}")
                            continue # またはエラーとして記録

                        csvwriter.writerow({"A": A, "B": B, "HP": HP, "Win": win, "Type": event_type})
                        csvfile.flush()
                        logging.info(trial_result2string(event_type, A, B, HP, win, 0, i + 1))

                except KeyboardInterrupt:
                    logging.warning("KeyboardInterrupt received. Terminating pool.")
                    print("Exiting...")
                    pool.terminate()
                    pool.join()
                except Exception as e:
                    logging.error(f"Error during multiprocessing execution: {e}", exc_info=True)
                    # プールを安全に終了させる
                    pool.terminate()
                    pool.join()
                else:
                    logging.info("Multiprocessing finished successfully.")
                    print("\nFinished") # 改行を追加
                    pool.close()
                    pool.join()
            print(f"Total time: {time.time() - totalStartTime: 0.2f}s", flush=True)
    else :
        with open("result.csv", "w", newline="") as csvfile:
            print(ABs)
            csvwriter = csv.DictWriter(csvfile, fieldnames=["Type", "A", "B", "HP", "Win"])
            csvwriter.writeheader()
            cnt = 0
            totalStartTime = time.time()

            for ET in range(2):
                for A in ABs["a"]:
                    for B in ABs["b"]:
                        state = nid_states(A, B, 15, 15)
                        for HP in range(30):
                            cnt += 1
                            HP += 1
                            startTime = time.time()
                            win = trial(A, B, HP, ET)
                            endTime = time.time()
                            csvwriter.writerow({"A": A, "B": B, "HP": HP, "Win": win, "Type": ET})
                            csvfile.flush()
                            print(trial_result2string(ET, A, B, HP, win, endTime - startTime, cnt), end="\n\n", flush=True)
            print(f"Total time: {time.time() - totalStartTime: 0.2f}s")


# ステートを保存する場合はsave=Trueを指定する
# if save:
#     with open(f"{romPath}.state", "wb") as f:
#         pyboy.save_state(f)
# pyboy.stop()
