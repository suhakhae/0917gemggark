# gem_env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple

from gem_simulator import GemSimulator, GEM_GRADES

class GemCraftingEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, gem_grade: str, targets: Dict[str, int]):
        super().__init__()
        self.gem_grade = gem_grade
        # *** 수정: 목표를 인자로 받아 저장 ***
        self.targets = targets 
        self.simulator = None
        self.action_space = spaces.Discrete(2)
        grade_info = GEM_GRADES[self.gem_grade]
        low = np.array([1, 1, 1, 1, 0, 0], dtype=np.float32)
        high = np.array([5, 5, 5, 5, grade_info['craft_count'], grade_info['reroll_count'] + 20], dtype=np.float32)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)

    def _get_obs(self) -> np.ndarray:
        # ... (이전과 동일)
        state = self.simulator.state
        return np.array([state['efficiency'], state['core'], state['effect1'], state['effect2'], state['remaining_crafts'], state['remaining_rerolls']], dtype=np.float32)

    def _is_target_reached(self) -> bool:
        """환경이 자신의 목표 달성 여부를 직접 판단"""
        state = self.simulator.state
        return (state['efficiency'] >= self.targets.get('efficiency', 1) and
                state['core'] >= self.targets.get('core', 1))

    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, Dict]:
        # ... (이전과 동일)
        super().reset(seed=seed)
        self.simulator = GemSimulator(gem_grade=self.gem_grade, rng=self.np_random)
        return self._get_obs(), {}

    def step(self, action: int) -> Tuple[np.ndarray, Dict]:
        # ... (이전과 동일, is_target_reached만 내부 함수로 변경)
        reward = -1.0
        if action == 1:
            if self.simulator.state['remaining_rerolls'] > 0:
                reward -= 2.0; self.simulator.state['remaining_rerolls'] -= 1
            else:
                reward -= 10.0
        options = self.simulator.generate_craft_options()
        if options:
            selected_option = self.np_random.choice(options)
            self.simulator.apply_craft_option(selected_option)
        terminated = False
        if self._is_target_reached():
            reward += 100.0; terminated = True
        elif self.simulator.state['remaining_crafts'] <= 0:
            reward -= 100.0; terminated = True
        truncated = False
        return self._get_obs(), reward, terminated, truncated, {}
