# dqn_model.py
import tensorflow as tf
from tensorflow.keras import layers


# ===================================================================
# 아크그리드 젬 기댓값 계산기 2.0 - DQN 신경망 모델
#
# AI 에이전트의 '두뇌' 역할을 하는 신경망 모델을 정의합니다.
# 이 모델은 현재 젬의 상태(6차원 벡터)를 입력받아,
# 각 행동('수락', '리롤')의 기대 가치(Q-value)를 출력합니다.
# ===================================================================

def create_dqn_model(input_shape, num_actions):
    """
    DQN 에이전트를 위한 Keras Sequential 모델을 생성합니다.

    Args:
        input_shape (tuple): 모델의 입력 형태 (상태 공간의 차원). 예: (6,)
        num_actions (int): 모델의 출력 뉴런 수 (행동 공간의 크기). 예: 2

    Returns:
        tf.keras.Model: 컴파일되지 않은 Keras 모델.
    """
    model = tf.keras.Sequential([
        # 입력층: 상태 벡터(6개 숫자)를 받습니다.
        layers.Input(shape=input_shape),

        # 첫 번째 은닉층: 64개의 뉴런과 ReLU 활성화 함수.
        # 상태 벡터의 특징(feature)을 학습합니다.
        layers.Dense(64, activation='relu'),

        # 두 번째 은닉층: 64개의 뉴런과 ReLU 활성화 함수.
        # 더 복잡한 특징 조합을 학습합니다.
        layers.Dense(64, activation='relu'),

        # 출력층: 행동의 개수(2개)만큼의 뉴런.
        # 각 뉴런은 해당 행동을 선택했을 때의 기대 보상(Q-값)을 예측합니다.
        # 활성화 함수가 없는 선형(linear) 레이어로, Q-값은 어떤 값이든 될 수 있습니다.
        layers.Dense(num_actions, activation='linear')
    ])

    return model


# ===================================================================
# 모델 생성 및 구조 확인용 테스트 코드
# ===================================================================
if __name__ == '__main__':
    print("DQN 모델 생성 테스트 시작")

    # 상태 공간과 행동 공간의 크기를 정의
    # GemCraftingEnv의 스펙과 일치해야 합니다.
    STATE_SHAPE = (6,)
    NUM_ACTIONS = 2

    # 모델 생성
    dqn_model = create_dqn_model(STATE_SHAPE, NUM_ACTIONS)

    # 모델의 구조를 요약하여 출력
    print("\n생성된 모델 구조:")
    dqn_model.summary()

    # 임의의 상태 데이터로 예측 테스트
    # (배치 크기 1, 상태 벡터 6) 형태의 더미 데이터 생성
    dummy_state = tf.random.uniform(shape=(1, 6))
    q_values = dqn_model(dummy_state)

    print(f"\n더미 상태 입력: {dummy_state.numpy()}")
    print(f"모델의 Q-값 예측 (행동 0, 행동 1): {q_values.numpy()}")

    print("\n테스트 완료.")
