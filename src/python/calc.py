import math


def get_exp(lv, real, bace, IV):
    return (4 * ((100 / lv) * (real - 5) - 2 * (bace + IV))) ** 2

def get_explevel(exp):
    return math.ceil((math.sqrt(exp))) // 4

if __name__ == "__main__":
    # lv = 17
    # real = 24
    # bace = 58
    # IV = 14
    # print(f"exp: {get_exp(lv, real, bace, IV)}")
    print(f"explevel: {[get_explevel(x) for x in [868, 1108, 1019, 800, 895, 1243]]}")