# gem_simulator.py
import numpy as np
from typing import Dict, List, Any

# --- (상단 상수 정의 부분은 이전과 동일) ---
GEM_GRADES = {
    "advanced": {"craft_count": 5, "reroll_count": 0},
    "rare": {"craft_count": 7, "reroll_count": 1},
    "heroic": {"craft_count": 9, "reroll_count": 2},
}

GEM_INFO = {
    "안정": 8, "견고": 9, "불변": 10,
    "침식": 8, "왜곡": 9, "붕괴": 10,
}

CRAFT_POSSIBILITIES = [
    # ... (이전과 동일한 28개의 가능성 딕셔셔리 리스트) ...
    {'type': 'efficiency', 'value': 1, 'probability': 11.65, 'condition': lambda gem: gem['efficiency'] < 5},
    {'type': 'efficiency', 'value': 2, 'probability': 4.40, 'condition': lambda gem: gem['efficiency'] < 4},
    {'type': 'efficiency', 'value': 3, 'probability': 1.75, 'condition': lambda gem: gem['efficiency'] < 3},
    {'type': 'efficiency', 'value': 4, 'probability': 0.45, 'condition': lambda gem: gem['efficiency'] < 2},
    {'type': 'efficiency', 'value': -1, 'probability': 3.00, 'condition': lambda gem: gem['efficiency'] > 1},
    {'type': 'core', 'value': 1, 'probability': 11.65, 'condition': lambda gem: gem['core'] < 5},
    {'type': 'core', 'value': 2, 'probability': 4.40, 'condition': lambda gem: gem['core'] < 4},
    {'type': 'core', 'value': 3, 'probability': 1.75, 'condition': lambda gem: gem['core'] < 3},
    {'type': 'core', 'value': 4, 'probability': 0.45, 'condition': lambda gem: gem['core'] < 2},
    {'type': 'core', 'value': -1, 'probability': 3.00, 'condition': lambda gem: gem['core'] > 1},
    {'type': 'effect1', 'value': 1, 'probability': 11.65, 'condition': lambda gem: gem['effect1'] < 5},
    {'type': 'effect1', 'value': 2, 'probability': 4.40, 'condition': lambda gem: gem['effect1'] < 4},
    {'type': 'effect1', 'value': 3, 'probability': 1.75, 'condition': lambda gem: gem['effect1'] < 3},
    {'type': 'effect1', 'value': 4, 'probability': 0.45, 'condition': lambda gem: gem['effect1'] < 2},
    {'type': 'effect1', 'value': -1, 'probability': 3.00, 'condition': lambda gem: gem['effect1'] > 1},
    {'type': 'effect2', 'value': 1, 'probability': 11.65, 'condition': lambda gem: gem['effect2'] < 5},
    {'type': 'effect2', 'value': 2, 'probability': 4.40, 'condition': lambda gem: gem['effect2'] < 4},
    {'type': 'effect2', 'value': 3, 'probability': 1.75, 'condition': lambda gem: gem['effect2'] < 3},
    {'type': 'effect2', 'value': 4, 'probability': 0.45, 'condition': lambda gem: gem['effect2'] < 2},
    {'type': 'effect2', 'value': -1, 'probability': 3.00, 'condition': lambda gem: gem['effect2'] > 1},
    {'type': 'effect1_change', 'value': 0, 'probability': 3.25, 'condition': lambda gem: True},
    {'type': 'effect2_change', 'value': 0, 'probability': 3.25, 'condition': lambda gem: True},
    {'type': 'cost_increase', 'value': 0, 'probability': 1.75, 'condition': lambda gem: gem['cost_modifier'] == 1.0 and gem['remaining_crafts'] > 1},
    {'type': 'cost_decrease', 'value': 0, 'probability': 1.75, 'condition': lambda gem: gem['cost_modifier'] > 1.0 and gem['remaining_crafts'] > 1},
    {'type': 'maintain_state', 'value': 0, 'probability': 1.75, 'condition': lambda gem: True},
    {'type': 'reroll_1', 'value': 1, 'probability': 2.50, 'condition': lambda gem: gem['remaining_crafts'] > 1},
    {'type': 'reroll_2', 'value': 2, 'probability': 0.75, 'condition': lambda gem: gem['remaining_crafts'] > 1}
]


class GemSimulator:
    def __init__(self, gem_grade: str, rng: np.random.Generator):
        if gem_grade not in GEM_GRADES:
            raise ValueError(f"Invalid gem grade: {gem_grade}")
        self.gem_grade = gem_grade
        self.grade_info = GEM_GRADES[self.gem_grade]
        self.rng = rng
        self.state = self.create_gem()

    def create_gem(self) -> Dict[str, Any]:
        return {
            'efficiency': 1, 'core': 1, 'effect1': 1, 'effect2': 1,
            'remaining_crafts': self.grade_info['craft_count'],
            'remaining_rerolls': self.grade_info['reroll_count'],
            'cost_modifier': 1.0,
        }

    def reset_gem(self) -> Dict[str, Any]:
        self.state = self.create_gem()
        return self.state
    
    # ===================================================================
    # *** 수정된 로직 (결정성 보장 최종 버전) ***
    # ===================================================================
    def generate_craft_options(self) -> List[Dict[str, Any]]:
        """
        가장 견고한 방식으로 고유한 가공 옵션 4개를 확률적으로 생성합니다.
        """
        available_options = [opt for opt in CRAFT_POSSIBILITIES if opt['condition'](self.state)]
        selected_options = []
        
        num_to_sample = min(4, len(available_options))

        for _ in range(num_to_sample):
            probabilities = np.array([opt['probability'] for opt in available_options])
            probabilities /= probabilities.sum() # 확률 정규화

            # numpy RNG를 사용하여 하나의 인덱스를 선택
            chosen_index = self.rng.choice(len(available_options), p=probabilities)
            
            # 선택된 옵션을 결과에 추가하고, 다음 샘플링을 위해 풀(pool)에서 제거
            chosen_option = available_options.pop(chosen_index)
            selected_options.append(chosen_option)
            
        return selected_options
    # ===================================================================

    def apply_craft_option(self, option: Dict[str, Any]):
        option_type = option['type']
        value = option['value']

        if option_type in ['efficiency', 'core', 'effect1', 'effect2']:
            current_value = self.state[option_type]
            self.state[option_type] = max(1, min(5, current_value + value))
        elif option_type == 'reroll_1':
            self.state['remaining_rerolls'] += 1
        elif option_type == 'reroll_2':
            self.state['remaining_rerolls'] += 2
        elif option_type == 'cost_increase':
            self.state['cost_modifier'] = 2.0
        elif option_type == 'cost_decrease':
            self.state['cost_modifier'] = 1.0

        self.state['remaining_crafts'] -= 1

    def is_target_reached(self, targets: Dict[str, int]) -> bool:
        return (self.state['efficiency'] >= targets.get('efficiency', 1) and
                self.state['core'] >= targets.get('core', 1) and
                self.state['effect1'] >= targets.get('effect1', 1) and
                self.state['effect2'] >= targets.get('effect2', 1))

    def is_possible_to_reach_target(self, targets: Dict[str, int]) -> bool:
        needed_points = (
            max(0, targets.get('efficiency', 1) - self.state['efficiency']) +
            max(0, targets.get('core', 1) - self.state['core']) +
            max(0, targets.get('effect1', 1) - self.state['effect1']) +
            max(0, targets.get('effect2', 1) - self.state['effect2'])
        )
        max_potential = self.state['remaining_crafts'] * 4
        return max_potential >= needed_points