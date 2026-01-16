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

    while queue:
        curr = queue.popleft()
        if all(costs[t] != -1 for t in target_byte):
            pass

        curr_step = costs[curr]
        for op in operations:
            nxt = (curr + op) % 256
            if costs[nxt] == -1:
                costs[nxt] = curr_step + 1
                queue.append(nxt)

    if any(costs[t] == -1 for t in target_byte):
        return 99999
    
    return sum(costs[t] for t in target_byte)


def genetic_algorithm(target_bytes):
    population_size = 100  # 集団のサイズ
    generations = 1000  # 世代数
    mutation_rate = 0.1  # 突然変異率
    OPERATE_RANGE = 6  # 操作ボタンの数

    # 初期集団の生成
    population = []
    for _ in range(population_size):
        individual = [random.randint(0, 256) for _ in range(OPERATE_RANGE)]
        individual.sort()
        population.append(individual)

    best_solution = None
    best_energy = float('inf')

    for generation in range(generations):
        new_population = []
        for i in range(population_size):
            # 親の選択
            parent1 = random.choice(population)
            parent2 = random.choice(population)

            # 交叉
            crossover_point = random.randint(1, OPERATE_RANGE - 1)
            child = parent1[:crossover_point] + parent2[crossover_point:]
            child.sort()

            # 突然変異
            if random.random() < mutation_rate:
                mutation_index = random.randint(0, OPERATE_RANGE - 1)
                child[mutation_index] = random.randint(0, 256)
                child.sort()

            new_population.append(child)

        population = new_population

        # 最良の解を更新
        for individual in population:
            energy = get_total_steps(individual, target_bytes)
            if energy < best_energy:
                best_energy = energy
                best_solution = individual
                print(f"Generation {generation}: 更新 {best_solution} Energy: {best_energy}")

    return best_solution, best_energy

BINARY_DATA = [
                                                          0xCD, 0x67, 0x38, 0xF0, 0xB3, 0x01, 0x01,
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
    best_solution, best_energy = genetic_algorithm(BINARY_DATA)
    print("Best Solution:", best_solution)
    print("Best Energy:", best_energy)
