# ゴミ箱の計測
# -----条件-----
# 1. スプライトの方向ごとに測定する

from pyboy import PyBoy
import os

os.chdir(os.path.dirname(__file__))

render = False

# 入力を受け付けたい場合はno_input=Falseにする
pyboy = PyBoy("pokemonBlue.gb", sound_volume=0, window="SDL2" if render else "null", no_input=True)
pyboy.set_emulation_speed(0)
with open("./pokemonBlue.gb.state", "rb") as f:
    pyboy.load_state(f)

def wait_until(condition_fn):
    while condition_fn():
        pyboy.tick(1, render, False)


repeat = 50000
gomibako = [[0 for _ in range(8)] for _ in range(8)]

# 上に移動
def event_up():
    def condition():
        pyboy.button("up")
        return pyboy.memory[0xd2dd] == 0x05
    wait_until(condition)

# 下に移動
def event_down():
    def condition():
        pyboy.button("down")
        return pyboy.memory[0xd2dd] != 0x05
    wait_until(condition)

# スプライトが描画されるまで待つ
def event_sprite():
    def condition():
        return pyboy.memory[0xc111] != 0x02
    wait_until(condition)


for i in range(repeat):
    event_up()
    event_sprite()
    sprite1 = pyboy.memory[0xc129] // 4
    sprite2 = 0 if pyboy.memory[0xc139] == 8 else 1
    event_down()

    gomibako[sprite2 * 4 + sprite1][pyboy.memory[0xd6c2] // 2] += 1
    if (i % 100 == 0):
        print(i, gomibako)
    
print(gomibako)
pyboy.stop(save=True)

# 計測結果(50000回)
# ←↓ [756, 757, 758, 762, 756, 757, 761, 756], 
# ←↑ [804, 799, 805, 807, 812, 807, 810, 808], 
# ←← [632, 636, 639, 641, 636, 637, 632, 635], 
# ←→ [636, 631, 637, 635, 637, 640, 633, 636], 
# →↓ [901, 900, 905, 906, 899, 899, 906, 907], 
# →↑ [945, 946, 952, 950, 945, 954, 952, 952], 
# →← [781, 782, 778, 782, 778, 784, 781, 779], 
# →→ [786, 779, 776, 787, 778, 778, 787, 777],

# 計測結果(50000回)
# ←↓ [732, 733, 734, 737, 731, 732, 736, 733], 
# ←↑ [753, 751, 756, 760, 764, 757, 762, 761], 
# ←← [656, 660, 663, 663, 660, 660, 656, 658], 
# ←→ [685, 679, 687, 683, 687, 688, 680, 683], 
# →↓ [852, 852, 857, 857, 849, 853, 858, 857], 
# →↑ [1019, 1018, 1022, 1025, 1017, 1026, 1027, 1023], 
# →← [781, 781, 779, 783, 781, 784, 780, 780], 
# →→ [763, 756, 752, 762, 752, 756, 763, 755]

# 計測結果(50000回)
# ←↓ [732, 733, 734, 737, 731, 732, 736, 733], 
# ←↑ [753, 751, 756, 760, 764, 757, 762, 761], 
# ←← [656, 660, 663, 663, 660, 660, 656, 658], 
# ←→ [685, 679, 687, 683, 687, 688, 680, 683], 
# →↓ [852, 852, 857, 857, 849, 853, 858, 857], 
# →↑ [1019, 1018, 1022, 1025, 1017, 1026, 1027, 1023],
# →← [781, 781, 779, 783, 781, 784, 780, 780], 
# →→ [763, 756, 752, 762, 752, 756, 763, 755]