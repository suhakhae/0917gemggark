# validator.py 
from typing import List, Dict, Tuple, Any
import copy
import numpy as np

CORE_INFO = {"유물": 15, "고대": 17}
GEM_INFO = { "안정": 8, "견고": 9, "불변": 10, "침식": 8, "왜곡": 9, "붕괴": 10 }
MIN_GEM_WILLPOWER_COST = 3
def _calculate_gem_cost(gem: Dict) -> int:
    for gem_type in GEM_INFO:
        if gem_type in gem['name']:
            base_cost = GEM_INFO[gem_type]
            return base_cost - gem['efficiency']
    return float('inf')

# ===================================================================
# *** 핵심 로직: 고도화된 백트래킹 알고리즘 ***
# ===================================================================

def check_feasibility(cores_input: Dict[str, List[str]], held_gems: List[Dict]) -> Tuple[bool, Any]:
    core_list = []
    for core_type, grades in cores_input.items():
        for grade in grades:
            core_list.append({
                "grade": grade, "type": core_type,
                "willpower": CORE_INFO[grade], "slots": 4, "held_gems": []
            })
    
    gems_with_cost = sorted(
        [{**gem, 'cost': _calculate_gem_cost(gem)} for gem in held_gems],
        key=lambda g: g['cost'], reverse=True
    )

    best_solution = {"state": None, "remaining_willpower": -1, "willpower_variance": float('inf')}

    def backtrack(gem_index: int, current_cores: List[Dict]):
        if gem_index == len(gems_with_cost):
            total_remaining_willpower = sum(c['willpower'] for c in current_cores)
            
            willpower_values = [c['willpower'] for c in current_cores]
            current_variance = np.var(willpower_values)

            is_better_solution = False
            if total_remaining_willpower > best_solution["remaining_willpower"]:
                is_better_solution = True
            elif total_remaining_willpower == best_solution["remaining_willpower"] and current_variance < best_solution["willpower_variance"]:
                is_better_solution = True

            if is_better_solution:
                is_viable = True
                for core in current_cores:
                    if core['willpower'] < core['slots'] * MIN_GEM_WILLPOWER_COST:
                        is_viable = False
                        break
                
                if is_viable:
                    best_solution["state"] = copy.deepcopy(current_cores)
                    best_solution["remaining_willpower"] = total_remaining_willpower
                    best_solution["willpower_variance"] = current_variance
            return

        gem_to_place = gems_with_cost[gem_index]
        
        last_tried_core_signature = None

        for i in range(len(current_cores)):
            core = current_cores[i]
            
            core_signature = (core['grade'], core['type'], core['willpower'], core['slots'])
            if core_signature == last_tried_core_signature:
                continue

            #  젬 이름에 코어 타입이 포함되어 있는지 직접 확인
            if core['type'] in gem_to_place['name'] and core['slots'] > 0 and core['willpower'] >= gem_to_place['cost']:
                last_tried_core_signature = core_signature
                
                core['slots'] -= 1
                core['willpower'] -= gem_to_place['cost']
                core['held_gems'].append(gem_to_place)
                
                backtrack(gem_index + 1, current_cores)
                
                core['held_gems'].pop()
                core['willpower'] += gem_to_place['cost']
                core['slots'] += 1

    backtrack(0, core_list)

    if best_solution["state"] is None:
        return False, {"reason": "보유한 젬들을 모든 코어에 활성화 가능하도록 배치하는 조합을 찾을 수 없습니다."}
    else:
        sorted_state = sorted(best_solution["state"], key=lambda c: (c['grade'], c['type']), reverse=True)
        remaining_info = [
            {
                "core": f"{core['grade']} {core['type']}",
                "remaining_willpower": core['willpower'],
                "remaining_slots": core['slots']
            }
            for core in sorted_state
        ]

        return True, remaining_info
