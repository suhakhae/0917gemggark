# final_optimizer.py (모든 변수 범위 문제 최종 해결 버전)
import tensorflow as tf
import numpy as np
from typing import Dict, Optional, Any, List
import os
import re
from tqdm import tqdm
import logging
import redis
import json

from gem_simulator import GemSimulator, GEM_GRADES
# GEM_INFO는 여기서 임포트하지 않고 클래스 내부로 이동
from scenario_generator import generate_scenarios

logger = logging.getLogger(__name__)

class FinalOptimizer:
    # 모든 관련 상수를 클래스 변수로 이동 및 선언 
    GEM_GRADES_ORDER = ["고급", "희귀", "영웅"]
    GRADE_MAP_KR_TO_EN = { "고급": "advanced", "희귀": "rare", "영웅": "heroic" }
    PEON_COST_PER_GEM = {"고급": 3, "희귀": 6, "영웅": 12}
    CRYSTALS_PER_PEON = 8.5
    GEM_INFO = {
        "안정": 8, "견고": 9, "불변": 10,
        "침식": 8, "왜곡": 9, "붕괴": 10,
    }
    
    def __init__(self, models_dir='./models/'):
        self.models = self._load_specialist_models(models_dir)
        self.rng = np.random.default_rng()
        try:
            self.redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}. Caching will be disabled.")
            self.redis_client = None

    def _load_specialist_models(self, models_dir: str) -> Dict[tuple, tf.keras.Model]:
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
        state_tensor = tf.convert_to_tensor(state_array, dtype=tf.float32)
        q_values = model(tf.expand_dims(state_tensor, axis=0), training=False)
        return tf.argmax(q_values[0]).numpy()

    def _simulate_one_gem_lifecycle(self, model: tf.keras.Model, target_spec: Dict, material_gem_grade_en: str, material_price: int, peon_gold_value: int, crystal_price: int) -> (bool, Dict[str, int]):
        costs = { "craft_cost": 0, "initialize_cost": 0 }
        simulator = GemSimulator(gem_grade=material_gem_grade_en, rng=self.rng)
        target_cp, target_eff = target_spec.get('core_point'), target_spec.get('efficiency')
        while simulator.state['remaining_crafts'] > 0:
            if simulator.state['core'] >= target_cp and simulator.state['efficiency'] >= target_eff: return True, costs
            should_initialize = (simulator.state['core'] == 1 or simulator.state['efficiency'] == 1) and (crystal_price < material_price + peon_gold_value)
            if should_initialize:
                costs["initialize_cost"] += crystal_price
                simulator.state['remaining_crafts'] -= 1
                temp_remaining_crafts = simulator.state['remaining_crafts']
                temp_remaining_rerolls = simulator.state['remaining_rerolls']
                new_state = simulator.create_gem()
                simulator.state = new_state
                simulator.state['remaining_crafts'] = temp_remaining_crafts
                simulator.state['remaining_rerolls'] = temp_remaining_rerolls
                continue
            state_array = np.array([simulator.state['efficiency'], simulator.state['core'], 1, 1, simulator.state['remaining_crafts'], simulator.state['remaining_rerolls']])
            action = self._get_action(model, state_array)
            if action == 1 and simulator.state['remaining_rerolls'] > 0: simulator.state['remaining_rerolls'] -= 1
            options = simulator.generate_craft_options()
            if options:
                selected_option = self.rng.choice(options)
                simulator.apply_craft_option(selected_option)
                costs["craft_cost"] += 900 * simulator.state['cost_modifier']
            else: simulator.state['remaining_crafts'] -= 1
        is_success = simulator.state['core'] >= target_cp and simulator.state['efficiency'] >= target_eff
        return is_success, costs

    def get_true_expected_cost(self, target_spec: Dict, material_gem_grade_en: str, material_price: int, peon_gold_value: int, crystal_price: int, simulations: int) -> Dict[str, int]:
        target_key = (target_spec['core_point'], target_spec['efficiency'])
        model = self.models.get(target_key)
        if model is None: return { "gem_cost": float('inf'), "craft_cost": float('inf'), "peon_cost": float('inf'), "initialize_cost": float('inf') }
        lifecycle_sims = max(simulations * 20, 2000)
        outcomes = [self._simulate_one_gem_lifecycle(model, target_spec, material_gem_grade_en, material_price, peon_gold_value, crystal_price) for _ in range(lifecycle_sims)]
        success_count = sum(1 for is_success, _ in outcomes if is_success)
        success_rate_per_gem = success_count / lifecycle_sims
        if success_rate_per_gem < 1e-9: return { "gem_cost": float('inf'), "craft_cost": float('inf'), "peon_cost": float('inf'), "initialize_cost": float('inf') }
        avg_craft_cost = np.mean([c["craft_cost"] for _, c in outcomes])
        avg_initialize_cost = np.mean([c["initialize_cost"] for _, c in outcomes])
        expected_attempts = 1 / success_rate_per_gem
        avg_costs = {
            "gem_cost": int(expected_attempts * material_price),
            "craft_cost": int(expected_attempts * avg_craft_cost),
            "peon_cost": int(expected_attempts * peon_gold_value),
            "initialize_cost": int(expected_attempts * avg_initialize_cost)
        }
        return avg_costs

    def _calculate_min_cost_for_willpower(self, willpower_cost: int, gem_prices: Dict, crystal_price: int, core_type: str, simulations: int) -> Optional[Dict]:
        cache_key = f"willpower_cost:{willpower_cost}:core_type:{core_type}:sims:{simulations}:crystal_price:{crystal_price}"
        if self.redis_client:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache HIT for key: {cache_key}")
                return json.loads(cached_result)
        logger.info(f"Cache MISS for key: {cache_key}. Calculating...")
        best_option = {"total_cost": float('inf')}
        candidate_specs = []
        # self.GEM_INFO 로 참조 방식 변경
        for gem_type, base_cost in self.GEM_INFO.items():
            is_order_gem = gem_type in ["안정", "견고", "불변"]
            if (core_type == "질서" and not is_order_gem) or (core_type == "혼돈" and is_order_gem): continue
            efficiency = base_cost - willpower_cost
            if 1 <= efficiency <= 5: candidate_specs.append({'type': gem_type, 'core_point': 5, 'efficiency': efficiency})
        for spec in candidate_specs:
            spec_type = spec['type']
            for material_grade_kr in self.GEM_GRADES_ORDER:
                material_full_name = next((name for name in gem_prices if spec_type in name and material_grade_kr in name), None)
                if not material_full_name: continue
                material_price = gem_prices.get(material_full_name)
                if material_price is None: continue
                material_grade_en = self.GRADE_MAP_KR_TO_EN.get(material_grade_kr)
                if not material_grade_en: continue
                required_peons = self.PEON_COST_PER_GEM.get(material_grade_kr, 0)
                # self.CRYSTALS_PER_PEON 으로 참조 방식 변경
                required_crystals = required_peons * self.CRYSTALS_PER_PEON
                peon_gold_value = (required_crystals / 100) * crystal_price
                expected_costs_breakdown = self.get_true_expected_cost(spec, material_grade_en, material_price, peon_gold_value, crystal_price, simulations)
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
        if self.redis_client and result:
            self.redis_client.set(cache_key, json.dumps(result), ex=21600)
            logger.info(f"Result for key {cache_key} stored in cache.")
        return result

    def find_best_strategy(self, remaining_info: List[Dict], gem_prices: Dict, crystal_price: int, simulations: int) -> Dict:
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
