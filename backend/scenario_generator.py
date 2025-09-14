from typing import List, Dict

# Branch Point A: 현재 젬의 소모 의지력 범위를 3~9로 가정.
MIN_COST = 3
MAX_COST = 9

memo: Dict[tuple, List[List[int]]] = {}

def _generate_recursive(target_sum: int, num_items: int, min_val: int) -> List[List[int]]:
    """
    재귀적으로 target_sum을 num_items개의 정수로 나누는 모든 조합을 찾는다.
    """
    if (target_sum, num_items, min_val) in memo:
        return memo[(target_sum, num_items, min_val)]
    if num_items == 1:
        if min_val <= target_sum <= MAX_COST: return [[target_sum]]
        else: return []
    result = []
    for i in range(min_val, MAX_COST + 1):
        remaining_sum = target_sum - i
        remaining_items = num_items - 1
        if remaining_sum < remaining_items * i: break
        if remaining_sum > remaining_items * MAX_COST: continue
        sub_solutions = _generate_recursive(remaining_sum, remaining_items, i)
        for solution in sub_solutions:
            result.append([i] + solution)
    memo[(target_sum, num_items, min_val)] = result
    return result

def generate_scenarios(total_willpower: int, num_slots: int) -> List[List[int]]:
    """
    주어진 총 의지력을 '정확하게' 모두 사용하는 '의지력 소모량 조합'만 생성합니다.
    Branch Point A: 이 함수는 의지력을 남기는 시나리오를 의도적으로 제외합니다.
    """
    if num_slots == 0:
        return [[]] if total_willpower == 0 else []
    
    memo.clear()
    
    # ===================================================================
    # *** 수정된 핵심 로직: for 루프를 제거하고 직접 호출 ***
    # ===================================================================
    # 이전에는 total_willpower '이하'의 모든 합계를 탐색했지만,
    # 이제는 정확히 total_willpower와 일치하는 조합만 찾습니다.
    min_possible_sum = num_slots * MIN_COST
    max_possible_sum = num_slots * MAX_COST

    if not (min_possible_sum <= total_willpower <= max_possible_sum):
        return [] # 물리적으로 불가능한 경우 즉시 빈 리스트 반환
        
    return _generate_recursive(total_willpower, num_slots, MIN_COST)
    # ===================================================================

# 개발 및 테스트용 코드
if __name__ == "__main__":
    print("--- 시나리오 생성기 테스트 (의지력 최대 활용 버전) ---")
    
    # 테스트 1: Willpower = 8, Slots = 2
    # 이전 결과: [[3, 3], [3, 4], [3, 5], [4, 4]]
    # 예상 결과: [[3, 5], [4, 4]]
    willpower_1, slots_1 = 8, 2
    scenarios_1 = generate_scenarios(willpower_1, slots_1)
    print(f"\nWillpower = {willpower_1}, Slots = {slots_1}:")
    print(f"  - 생성된 시나리오 개수: {len(scenarios_1)}")
    print(f"  - 결과: {scenarios_1}")

    # 테스트 2: Willpower = 17, Slots = 4
    # 이전 결과: 18개
    # 예상 결과: 합계가 정확히 17인 조합만 나옴 (개수 감소 예상)
    willpower_2, slots_2 = 17, 4
    scenarios_2 = generate_scenarios(willpower_2, slots_2)
    print(f"\nWillpower = {willpower_2}, Slots = {slots_2}:")
    print(f"  - 생성된 시나리오 개수: {len(scenarios_2)}")

    print(f"  - 결과 (전체): {scenarios_2}")
