import tensorflow as tf
import numpy as np
import collections
from tqdm import tqdm
import argparse

from gem_env import GemCraftingEnv
from dqn_model import create_dqn_model

# ===================================================================
# *** 수정된 부분: 하이퍼파라미터를 클래스 외부 상수로 정의 ***
# ===================================================================
# DQN 하이퍼파라미터
DEFAULT_GAMMA = 0.99
DEFAULT_LEARNING_RATE = 0.001

# 경험 리플레이 버퍼 설정
DEFAULT_BUFFER_LIMIT = 50000
DEFAULT_BATCH_SIZE = 64

# 엡실론-그리디 정책 설정
DEFAULT_EPSILON_START = 1.0
DEFAULT_EPSILON_END = 0.01
DEFAULT_EPSILON_DECAY = 0.999

# 학습 제어
DEFAULT_TARGET_UPDATE_FREQ = 10
# ===================================================================

class DQNAgent:
    # ===================================================================
    # *** 수정된 부분: __init__에서 하이퍼파라미터를 인자로 받음 ***
    # ===================================================================
    def __init__(self, state_shape, num_actions, buffer_limit, batch_size, gamma, learning_rate):
        self.state_shape = state_shape
        self.num_actions = num_actions
        self.batch_size = batch_size
        self.gamma = gamma

        self.replay_buffer = collections.deque(maxlen=buffer_limit)
        
        self.main_network = create_dqn_model(state_shape, num_actions)
        self.target_network = create_dqn_model(state_shape, num_actions)
        
        self.optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        self.update_target_network()
    # ===================================================================

    def update_target_network(self):
        self.target_network.set_weights(self.main_network.get_weights())

    def get_action(self, state, epsilon):
        if np.random.rand() < epsilon:
            return np.random.randint(self.num_actions)
        else:
            state_tensor = tf.convert_to_tensor(state, dtype=tf.float32)
            q_values = self.main_network(tf.expand_dims(state_tensor, axis=0))
            return tf.argmax(q_values[0]).numpy()

    def store_experience(self, state, action, reward, next_state, done):
        self.replay_buffer.append((state, action, reward, next_state, done))

    @tf.function
    def _train_step_graph(self, states, actions, rewards, next_states, dones):
        next_q_values = self.target_network(next_states, training=False)
        max_next_q = tf.reduce_max(next_q_values, axis=1)
        dones_float = tf.cast(dones, tf.float32)
        target_q_values = rewards + (1.0 - dones_float) * self.gamma * max_next_q

        with tf.GradientTape() as tape:
            current_q_values = self.main_network(states, training=True)
            action_indices = tf.stack([tf.range(tf.shape(actions)[0], dtype=tf.int32), actions], axis=1)
            action_q_values = tf.gather_nd(current_q_values, action_indices)
            loss = tf.keras.losses.MSE(target_q_values, action_q_values)
        
        grads = tape.gradient(loss, self.main_network.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.main_network.trainable_variables))

    def train_step(self):
        if len(self.replay_buffer) < self.batch_size:
            return
        minibatch_indices = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
        minibatch = [self.replay_buffer[i] for i in minibatch_indices]
        states, actions, rewards, next_states, dones = map(lambda x: tf.convert_to_tensor(np.array(x), dtype=tf.float32), zip(*minibatch))
        actions = tf.cast(actions, tf.int32)
        self._train_step_graph(states, actions, rewards, next_states, dones)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train a specialist DQN agent for a specific gem target.")
    parser.add_argument('--core_point', type=int, required=True, help="Target core point level (1-5)")
    parser.add_argument('--efficiency', type=int, required=True, help="Target efficiency level (1-5)")
    parser.add_argument('--episodes', type=int, default=10000, help="Total number of episodes to train")
    args = parser.parse_args()

    print(f"Starting training for target (core: {args.core_point}, efficiency: {args.efficiency})")
    
    GEM_GRADE = 'heroic'
    TARGETS = {'core': args.core_point, 'efficiency': args.efficiency}
    MODEL_SAVE_PATH = f'gem_model_c{args.core_point}_e{args.efficiency}.h5'

    env = GemCraftingEnv(gem_grade=GEM_GRADE, targets=TARGETS)
    
    # ===================================================================
    # *** 수정된 부분: 에이전트 생성 시 하이퍼파라미터 전달 ***
    # ===================================================================
    agent = DQNAgent(
        state_shape=env.observation_space.shape,
        num_actions=env.action_space.n,
        buffer_limit=DEFAULT_BUFFER_LIMIT,
        batch_size=DEFAULT_BATCH_SIZE,
        gamma=DEFAULT_GAMMA,
        learning_rate=DEFAULT_LEARNING_RATE
    )
    # ===================================================================
    
    epsilon = DEFAULT_EPSILON_START
    all_rewards = []

    for episode in tqdm(range(args.episodes), desc=f"Training C{args.core_point}/E{args.efficiency}"):
        state, _ = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action = agent.get_action(state, epsilon)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            agent.store_experience(state, action, reward, next_state, done)
            agent.train_step()
            state = next_state
            episode_reward += reward
        
        all_rewards.append(episode_reward)
        epsilon = max(DEFAULT_EPSILON_END, epsilon * DEFAULT_EPSILON_DECAY)
        
        if (episode + 1) % DEFAULT_TARGET_UPDATE_FREQ == 0:
            agent.update_target_network()

        if (episode + 1) % 100 == 0:
            last_100_avg_reward = np.mean(all_rewards[-100:])
            print(f"\nEpisode {episode + 1}/{args.episodes} | "
                  f"Last 100 Avg Reward: {last_100_avg_reward:.2f} | "
                  f"Epsilon: {epsilon:.4f}")

    agent.main_network.save(MODEL_SAVE_PATH)
    print(f"\nTraining complete! Model saved to '{MODEL_SAVE_PATH}'")
    
    env.close()