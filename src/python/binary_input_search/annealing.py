from collections import deque
import math
import random

def get_total_steps(operations, target_byte):
    """
    操作回数を計算する
    
    :param operations: [v1, v2, ...] の操作量リスト
    :param target_byte: 作りたいバイト列
    """
    costs = [-1] * 256
    costs[0] = 0
    queue = deque([0])
    histories = {0: []}

    while queue:
        curr = queue.popleft()
        if all(costs[t] != -1 for t in target_byte):
            pass

        curr_step = costs[curr]
        for op in operations:
            nxt = (curr + op) % 256
            if costs[nxt] == -1:
                costs[nxt] = curr_step + 1
                histories[nxt] = histories[curr] + [op]
                queue.append(nxt)

    if any(costs[t] == -1 for t in target_byte):
        return 99999, histories
    
    return sum(costs[t] for t in target_byte), histories

def simulated_annealing(target_bytes, print_progress=True):
    T = 1000 # 初期温度
    T_min = .1 # 最低温度
    cooling_rate = 0.9995 # 冷却率
    OPERATE_RANGE = 6 # 操作ボタンの数
    fixed_operations = []  # 固定操作ボタン

    history = set()

    # 配列が履歴に存在しないか & 重複が存在しないかチェック
    def check_array(arr):
        arr = sorted(arr)
        if tuple(arr) in history:
            return False
        for i in range(OPERATE_RANGE - 1):
            if arr[i] == arr[i + 1]:
                return False
        return True

    current_solution = []
    while True:
        current_solution = [random.randint(0, 256) for _ in range(OPERATE_RANGE - len(fixed_operations))]
        # current_solution = [3, 11, 56, 205, 229, 254]
        current_solution.sort()
        if check_array(current_solution + fixed_operations):
            break
    current_energy = get_total_steps(current_solution + fixed_operations, target_bytes)[0]

    best_solution = current_solution[:]
    best_energy = current_energy

    history.add(tuple(current_solution))

    step = 0
    while T > T_min:
        new_solution = current_solution[:]
        idx = random.randint(0, OPERATE_RANGE - len(fixed_operations) - 1)

        def get_new_value():
            if random.random() < .7:
                change = random.randint(-3, 3)
            else: 
                change = random.randint(-50, 50)

            new_value = new_solution[idx] + change
            new_value = new_value % 256
            return new_value

        while True:
            _new_solution = current_solution[:]
            new_value = get_new_value()
            _new_solution[idx] = new_value
            _new_solution.sort()
            
            if not check_array(_new_solution + fixed_operations):
                continue
            
            if new_value != new_solution[idx]:
                
                new_solution = _new_solution
                break

        new_energy = get_total_steps(new_solution + fixed_operations, target_bytes)[0]
        delta_energy = new_energy - current_energy

        if delta_energy < 0:
            accept = True
        else:
            prob = math.exp(-delta_energy / T)
            accept = random.random() < prob
        
        if accept:
            current_solution = new_solution
            current_energy = new_energy

            if new_energy < best_energy:
                best_solution = new_solution
                best_energy = new_energy

                if print_progress:
                    print("\033[33m", end="")
                    print(f"Step {step}: 更新 {new_solution + fixed_operations} Energy: {best_energy} T: {T:.2f}")
                    print("\033[0m", end="")

        T *= cooling_rate
        step += 1
    return best_solution + fixed_operations, best_energy

BINARY_DATA = [
                                                          0xCD, 0x3F, 0x38, 0xF0, 0xB3, 0x01, 0x01,
    0x00, 0x07, 0x38, 0x18, 0x0B, 0x0B, 0x07, 0x38, 0x13, 0x0E, 0xF0, 0x07, 0x38, 0x0E, 0x01, 0x10,
    0x00, 0x07, 0x38, 0x08, 0x07, 0x38, 0x03, 0x07, 0xD0, 0xE9, 0xE1, 0xC9, 0x79, 0xCB, 0x43, 0x20,
    0x06, 0xCB, 0x4B, 0x20, 0x05, 0x09, 0xC9, 0x86, 0x77, 0xC9, 0x84, 0x67, 0xC9, 0xF5, 0xCB, 0x37,
    0xCD, 0x24, 0xD6, 0xF1, 0xE6, 0x0F, 0xC6, 0xF6, 0xF6, 0x60, 0x22, 0xC9, 0x21, 0x00, 0xD0, 0xCD,
    0xE9, 0xD5, 0xE5, 0x11, 0xF8, 0xFF, 0x19, 0xE5, 0xD1, 0x21, 0xAB, 0xC3, 0x01, 0x0C, 0x00, 0x36,
    0x7C, 0x23, 0x7A, 0xCD, 0x1D, 0xD6, 0x7B, 0xCD, 0x1D, 0xD6, 0x36, 0x7F, 0x23, 0x1A, 0xCD, 0x1D,
    0xD6, 0x13, 0x36, 0x7C, 0x09, 0x7C, 0xFE, 0xC5, 0x20, 0xE5, 0x3E, 0xED, 0xEA, 0x4B, 0xC4, 0xE1,
    0x18, 0xCD
]

if __name__ == "__main__":
    
    # target_bytes = BINARY_DATA
    # final_solution, final_score = simulated_annealing(target_bytes)

    # print("-----")
    # step, histories = get_total_steps(final_solution, target_bytes)
    # for t in BINARY_DATA:
    #     print(f"byte {t:02X}: 操作履歴 {histories[t]}")
    # sum_steps = sum(len(histories[t]) for t in BINARY_DATA)
    # print(f"総操作数: {sum_steps} 平均操作数: {sum_steps / len(BINARY_DATA):.2f}")

    # print("-----")
    # print(f"最終結果: {final_solution}")
    # print(f"最終操作数: {final_score}")

    target_bytes = BINARY_DATA
    N = 100

    print("---計測開始---")
    results = []
    for i in range(N):
        final_solution, final_score = simulated_annealing(target_bytes, print_progress=False)
        results.append((final_solution, final_score))
        print(f"試行 {i+1}/{N} 完了 最終操作数: {final_score} 操作: {final_solution}")
    
    scores = [res[1] for res in results]
    sum_score = sum(scores)
    avg_score = sum_score / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    median_score = sorted(scores)[len(results)//2]
    print(f"平均操作数: {avg_score:.2f} 最大操作数: {max_score} 最小操作数: {min_score} 中央操作数: {median_score}")

    results.sort(key=lambda x: x[1])
    for res in results[:3]:
        print(f"操作: {res[0]} 最終操作数: {res[1]}")


# [-2, 7, 34, -51, 28, -55]

# 最終結果: [7, 11, 32, 198, 222, 248]
# 最終操作数: 351

# 最終結果: [1, 7, 25, 28, 201, 205]
# 最終操作数: 343

# 最終結果: [7, 28, 36, 205, 229, 254]
# 最終操作数: 340

# 最終結果: [4, 7, 24, 25, 201, 233]
# 最終操作数: 337

# 最終結果: [1, 32, 62, 201, 213, 248]
# 最終操作数: 337

# 最終結果: [3, 11, 56, 205, 229, 254]
# 最終操作数: 335

# 最終結果: [1, 7, 19, 28, 117, 201, 205, 246]
# 最終操作数: 288

# 最終結果: [7, 25, 33, 56, 201, 205, 229, 240]
# 最終操作数: 280