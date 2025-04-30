# ゴミ箱の計測
# 条件なし
from pyboy import PyBoy
import os

os.chdir(os.path.dirname(__file__))

render = False

pyboy = PyBoy("pokemonBlue.gb", sound_volume=0, window="SDL2" if render else "null", no_input=True)
pyboy.set_emulation_speed(0)
with open("./pokemonBlue.gb.state", "rb") as f:
    pyboy.load_state(f)

def wait_until(condition_fn):
    while not condition_fn():
        pyboy.tick(1, render, False)


repeat = 50000
gomibako = [0 for _ in range(8)]

def event_01():
    for i in range(repeat):
        def condition():
            pyboy.button("up")
            return pyboy.memory[0xd2dd] != 0x05
        wait_until(condition)


        def condition2():
            pyboy.button("down")
            return pyboy.memory[0xd2dd] == 0x05
        wait_until(condition2)

        gomibako[pyboy.memory[0xd6c2] // 2] += 1
        if (i % 100 == 0):
            print(i, gomibako)

event_01()
print(gomibako)
pyboy.stop(save=True)

# 計測結果(50000回)
# [6241, 6230, 6250, 6270, 6241, 6256, 6262, 6250]