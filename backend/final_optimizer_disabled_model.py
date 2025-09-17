# final_optimizer.py 
import tensorflow as tf
import numpy as np
from typing import Dict, Optional, Any, List
import os
import re
from tqdm import tqdm
import logging

from gem_simulator import GemSimulator, GEM_GRADES, GEM_INFO
from scenario_generator import generate_scenarios

# ==========================================================================
# *** 해당 코드는 final_optimizer의 초기 모델로 실제 서비스와 관련이 없습니다***
# ==========================================================================


# --- 상수 정의 ---
GEM_TYPES_ORDER = ["안정", "견고", "불변", "침식", "왜곡", "붕괴"]
GEM_GRADES_ORDER = ["고급", "희귀", "영웅"]
PEON_COST_PER_GEM = {"고급": 3, "희귀": 6, "영웅": 12}
CRYSTALS_PER_PEON = 8.5
GRADE_MAP_KR_TO_EN = { "고급": "advanced", "희귀": "rare", "영웅": "heroic" }

logger = logging.getLogger(__name__)

class FinalOptimizer:
    """
    훈련된 다수의 전문가 AI 모델을 사용하여 최적의 젬 제작 전략을 찾는 최종 클래스.
    """
    def __init__(self, models_dir='./models/'):
        self.models = self._load_specialist_models(models_dir)
        self.cost_cache: Dict[tuple, Optional[Dict]] = {}
        self.rng = np.random.default_rng()

    def _load_specialist_models(self, models_dir: str) -> Dict[tuple, tf.keras.Model]:
        """
        주어진 디렉토리에서 'gem_model_c...e....h5' 패턴의 모든 모델을 로드합니다.
        """
        models = {}
        logger.info(f"Loading specialist AI models from '{models_dir}'...")
        
        pattern = re.compile(r"gem_model_c(\d+)_e(\d+)\.h5")
        
        for filename in os.listdir(models_dir):
            match = pattern.match(filename)
            if match:
                core_point = int(match.group(1))
                efficiency = int(match.group(2))
                
                model_path = os.path.join(models_dir, filename)
                logger.info(f"  - Loading model for target ({core_point}, {efficiency}) from {filename}...")
                model = tf.keras.models.load_model(model_path, compile=False)
                
                models[(core_point, efficiency)] = model
        
        if not models:
            logger.error(f"No specialist models found in '{models_dir}'. Please run train_specialist.py first.")
            raise RuntimeError(f"No specialist models found in '{models_dir}'. Please run train_specialist.py first.")
        
        logger.info(f"Successfully loaded {len(models)} specialist models.")
        return models

    def _get_action(self, model: tf.keras.Model, state_array: np.ndarray) -> int:
        """주어진 모델과 상태로 최적의 행동을 결정합니다."""
        state_tensor = tf.convert_to_tensor(state_array, dtype=tf.float32)
        q_values = model(tf.expand_dims(state_tensor, axis=0), training=False)
        return tf.argmax(q_values[0]).numpy()

    # ===================================================================
    # *** 수정: 현실적인 제약조건과 경제적 판단이 포함된 시뮬레이션 ***
    # ===================================================================

    def _simulate_until_success(self, model: tf.keras.Model, target_spec: Dict, material_gem_grade_en: str, material_price: int, peon_gold_value: int, crystal_price: int) -> Dict[str, int]:
        """
        목표 스펙을 달성할 때까지, 현실적인 규칙에 따라 시뮬레이션하고 비용을 누적합니다.
        """
        costs = { "gem_cost": 0, "craft_cost": 0, "peon_cost": 0, "initialize_cost": 0 }
        simulator = GemSimulator(gem_grade=material_gem_grade_en, rng=self.rng)
        target_cp, target_eff = target_spec.get('core_point'), target_spec.get('efficiency')
        
        max_attempts = 2000 # 무한 루프 방지
        for _ in range(max_attempts):
            # 1. 새로운 젬 구매
            costs["gem_cost"] += material_price
            costs["peon_cost"] += peon_gold_value
            simulator.reset_gem() # 새 젬이므로 상태 초기화

            # 2. 젬 하나의 생애주기 (가공 횟수가 0이 될 때까지)
            while simulator.state['remaining_crafts'] > 0:
                if simulator.state['core'] >= target_cp and simulator.state['efficiency'] >= target_eff:
                    return costs # 성공!

                # --- 경제적 초기화 판단 (Heuristic Rule) ---
                # 조건: 코어나 효율이 1로 떨어지고, 초기화가 새 젬보다 저렴할 때
                should_initialize = (simulator.state['core'] == 1 or simulator.state['efficiency'] == 1) and (crystal_price < material_price + peon_gold_value)
                
                if should_initialize:
                    costs["initialize_cost"] += crystal_price
                    simulator.state['remaining_crafts'] -= 1 # 초기화 시 가공 횟수 1 소모 규칙
                    
                    # 젬 상태만 초기화 (남은 횟수는 유지, 리롤 횟수는 초기화)
                    # simulator.reset_gem()은 모든 것을 초기화하므로 직접 필요한 부분만 수정
                    temp_remaining_crafts = simulator.state['remaining_crafts']
                    temp_remaining_rerolls = simulator.state['remaining_rerolls']
                    
                    new_state = simulator.create_gem()
                    simulator.state = new_state
                    
                    simulator.state['remaining_crafts'] = temp_remaining_crafts
                    simulator.state['remaining_rerolls'] = temp_remaining_rerolls
                    
                    continue # 다음 가공 단계로 넘어감

                # AI의 행동 결정 (수락 또는 리롤)
                state_array = np.array([simulator.state['efficiency'], simulator.state['core'], 1, 1, simulator.state['remaining_crafts'], simulator.state['remaining_rerolls']])
                action = self._get_action(model, state_array)
                
                if action == 1 and simulator.state['remaining_rerolls'] > 0:
                    simulator.state['remaining_rerolls'] -= 1

                # 가공 실행
                options = simulator.generate_craft_options()
                if options:
                    selected_option = self.rng.choice(options)
                    simulator.apply_craft_option(selected_option)
                    costs["craft_cost"] += 900 * simulator.state['cost_modifier']
                else: # 옵션이 없는 예외적인 경우
                    simulator.state['remaining_crafts'] -= 1
            
            # 가공 횟수를 모두 소모한 후 마지막으로 성공 여부 체크
            if simulator.state['core'] >= target_cp and simulator.state['efficiency'] >= target_eff:
                return costs
        
        # 최대 시도 횟수 초과
        return { "gem_cost": float('inf'), "craft_cost": float('inf'), "peon_cost": float('inf'), "initialize_cost": float('inf') }

    def get_true_expected_cost(self, target_spec: Dict, material_gem_grade_en: str, material_price: int, peon_gold_value: int, crystal_price: int, simulations: int) -> Dict[str, int]:
        """
        '성공할 때까지 시뮬레이션'을 여러 번 반복하여 평균 상세 비용 내역(기댓값)을 계산합니다.
        """
        target_key = (target_spec['core_point'], target_spec['efficiency'])
        model = self.models.get(target_key)
        if model is None:
            return { "gem_cost": float('inf'), "craft_cost": float('inf'), "peon_cost": float('inf'), "initialize_cost": float('inf') }

        all_costs_list = []
        for _ in range(simulations):
            cost_breakdown = self._simulate_until_success(model, target_spec, material_gem_grade_en, material_price, peon_gold_value, crystal_price)
            if cost_breakdown["gem_cost"] != float('inf'):
                all_costs_list.append(cost_breakdown)
        
        if not all_costs_list:
            return { "gem_cost": float('inf'), "craft_cost": float('inf'), "peon_cost": float('inf'), "initialize_cost": float('inf') }

        # 각 비용 항목별로 평균을 계산
        avg_costs = {
            "gem_cost": int(np.mean([c["gem_cost"] for c in all_costs_list])),
            "craft_cost": int(np.mean([c["craft_cost"] for c in all_costs_list])),
            "peon_cost": int(np.mean([c["peon_cost"] for c in all_costs_list])),
            "initialize_cost": int(np.mean([c["initialize_cost"] for c in all_costs_list]))
        }
        return avg_costs

    def _calculate_min_cost_for_willpower(self, willpower_cost: int, gem_prices: Dict, crystal_price: int, core_type: str, simulations: int) -> Optional[Dict]:
        """
        주어진 소모 의지력을 만드는 가장 저렴한 방법을 찾습니다.
        """
        cache_key = (willpower_cost, core_type, simulations)
        if cache_key in self.cost_cache: return self.cost_cache[cache_key]
        
        best_option = {"total_cost": float('inf')}

        candidate_specs = []
        for gem_type, base_cost in GEM_INFO.items():
            is_order_gem = gem_type in ["안정", "견고", "불변"]
            if (core_type == "질서" and not is_order_gem) or (core_type == "혼돈" and is_order_gem): continue
            efficiency = base_cost - willpower_cost
            if 1 <= efficiency <= 5: candidate_specs.append({'type': gem_type, 'core_point': 5, 'efficiency': efficiency})

        for spec in candidate_specs:
            spec_type = spec['type']
            for material_grade_kr in GEM_GRADES_ORDER:
                material_full_name = next((name for name in gem_prices if spec_type in name and material_grade_kr in name), None)
                if not material_full_name: continue
                
                material_price = gem_prices.get(material_full_name)
                if material_price is None: continue
                
                material_grade_en = GRADE_MAP_KR_TO_EN.get(material_grade_kr)
                if not material_grade_en: continue
                
                required_peons = PEON_COST_PER_GEM.get(material_grade_kr, 0)
                required_crystals = required_peons * CRYSTALS_PER_PEON
                peon_gold_value = (required_crystals / 100) * crystal_price
                
                # 상세 비용 내역(Dict)을 받음
                expected_costs_breakdown = self.get_true_expected_cost(spec, material_grade_en, material_price, peon_gold_value, crystal_price, simulations)
                
                # 상세 비용의 합으로 총 비용 계산
                total_expected_cost = sum(expected_costs_breakdown.values())

                if total_expected_cost < best_option["total_cost"]:
                    best_option = {
                        "target_spec_str": f"({spec['type']}, {spec['core_point']}, {spec['efficiency']})",
                        "material_gem": material_full_name,
                        "willpower_cost": willpower_cost,
                        "total_cost": total_expected_cost,
                        "breakdown": {
                            "gem_cost": expected_costs_breakdown["gem_cost"],
                            "craft_cost": expected_costs_breakdown["craft_cost"],
                            "peon_cost": expected_costs_breakdown["peon_cost"],
                            "initialize_cost": expected_costs_breakdown["initialize_cost"]
                        }
                    }
        
        result = best_option if best_option["total_cost"] != float('inf') else None
        self.cost_cache[cache_key] = result
        return result

    def find_best_strategy(self, remaining_info: List[Dict], gem_prices: Dict, crystal_price: int, simulations: int) -> Dict:
        """
        모든 시나리오를 탐색하여 최종 최적 전략을 찾습니다.
        """
        self.cost_cache.clear()
        final_strategy = {"total_cost": 0, "details_per_core": []}
        for core in tqdm(remaining_info, desc="Optimizing Cores"):
            core_type = core['core'].split(' ')[1]
            scenarios = generate_scenarios(core['remaining_willpower'], core['remaining_slots'])
            best_scenario_for_core = {"cost": float('inf'), "combination": []}
            for scenario in scenarios:
                current_scenario_cost = 0; current_scenario_details = []; is_possible = True
                for willpower_cost in scenario:
                    min_cost_option = self._calculate_min_cost_for_willpower(willpower_cost, gem_prices, crystal_price, core_type, simulations)
                    if min_cost_option is None: is_possible = False; break
                    current_scenario_cost += min_cost_option['total_cost']
                    current_scenario_details.append(min_cost_option)
                if is_possible and current_scenario_cost < best_scenario_for_core['cost']:
                    best_scenario_for_core['cost'] = current_scenario_cost
                    best_scenario_for_core['combination'] = current_scenario_details
            if best_scenario_for_core['cost'] != float('inf'):
                final_strategy['total_cost'] += best_scenario_for_core['cost']
                final_strategy['details_per_core'].append({ "core": core['core'], "best_combination": best_scenario_for_core['combination'] })

        return final_strategy
