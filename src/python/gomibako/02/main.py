# ゴミ箱の計測
# -----条件-----
# 1. スプライトの方向ごとに測定する
# 2. ソフトリセットを組み込む

from pyboy import PyBoy
import os

os.chdir(os.path.dirname(__file__))

render = False
save = False

# 入力を受け付けたい場合はno_input=Falseにする
pyboy = PyBoy("pokemonBlue.gb", sound_volume=0, window="SDL2" if render else "null", no_input=True)
pyboy.set_emulation_speed(0)
with open("./pokemonBlue.gb.state", "rb") as f:
    pyboy.load_state(f)


def wait_until(condition_fn, trigger=False):
    while True:
        pyboy.tick(1, render, False)
        c = condition_fn()
        if (c and trigger) or ((not trigger) and (not c)):
            break


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

# ソフトリセット
def event_reset():
    def condition():
        pyboy.button("a")
        pyboy.button("b")
        pyboy.button("start")
        pyboy.button("select")
        return pyboy.memory[0xd11d] == 0x00
    def condition2():
        pyboy.button("up")
        pyboy.button("b")
        pyboy.button("select")
        return pyboy.memory[0xffb4] == 0x46 and pyboy.memory[0xd11d] == 0x08
    def condition3():
        pyboy.button("start")
        return pyboy.memory[0xffb4] == 0x08 and pyboy.memory[0xd11d] != 0x08
    def condition4():
        # print(pyboy.memory[0xffb4], pyboy.memory[0xff4a])
        pyboy.button("a")
        return pyboy.memory[0xff4a] == 0x90
    wait_until(condition, True)
    wait_until(condition2, True)
    wait_until(condition3, True)
    wait_until(condition4, True)

for i in range(repeat):
    event_reset()
    event_up()
    event_sprite()
    sprite1 = pyboy.memory[0xc129] // 4
    sprite2 = 0 if pyboy.memory[0xc139] == 8 else 1
    event_down()
    gomibako[sprite2 * 4 + sprite1][pyboy.memory[0xd6c2] // 2] += 1
    if (i % 100 == 0):
        print(i, gomibako)
    
print(gomibako)
if save:
    with open("./pokemonBlue.gb.state", "wb") as f:
        pyboy.save_state(f)
pyboy.stop()

# 計測結果(50000回)
# ←↓ [802, 789, 811, 740, 843, 790, 746, 724], 
# ←↑ [756, 775, 786, 738, 854, 734, 805, 794], 
# ←← [768, 874, 762, 786, 689, 855, 806, 711], 
# ←→ [806, 736, 788, 797, 719, 875, 775, 764], 
# →↓ [728, 740, 848, 831, 744, 775, 824, 766], 
# →↑ [829, 812, 750, 747, 787, 731, 808, 789], 
# →← [747, 771, 758, 818, 822, 750, 789, 791], 
# →→ [826, 774, 703, 848, 743, 766, 845, 742]