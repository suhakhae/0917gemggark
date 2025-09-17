
# Gemggark: AI 기반 아크그리드 젬 세공 기댓값 계산기

## 1. Back-end Part

## 📖 프로젝트 개요

Gemggark는 로스트아크의 '아크그리드' 시스템에 대한 최적의 젬 제작 전략을 AI를 통해 추천하는 웹 서비스의 백엔드 API입니다. 실시간 시장 데이터를 반영하여 사용자에게 가장 경제적인 선택지를 제공하는 것을 목표로 합니다. 
사용자가 보유하고 있는 코어와 젬을 입력하고 최적화를 시작하면 거래소 가격을 반영하여 각 코어별 20코어 포인트를 달성하기 위한 최적 소모 골드의 기댓값을 계산하여 제공합니다.

---

## 🚀 주요 기능

- **AI 최적화 엔진:** TensorFlow(DQN)로 훈련된 전문가 AI 모델이 복잡한 확률을 시뮬레이션하여 최적의 젬 제작 전략을 도출합니다.
- **실시간 데이터 연동:** 로스트아크 Open API를 통해 실시간 젬 시세를 반영합니다.
- **고성능 캐싱:** Redis를 도입하여 반복적인 계산 요청에 대해 수 초 내에 즉시 응답합니다.
- **실시간 진행률 피드백:** WebSocket을 통해 프론트엔드에 계산 진행 상황을 실시간으로 전송하여 UX를 향상시킵니다.

---

## 🛠️ 기술 스택

- **언어/프레임워크:** Python, FastAPI
- **AI/데이터:** TensorFlow, NumPy
- **데이터베이스:** Redis (캐싱용)
- **실시간 통신:** WebSocket
- **서버 환경:** Docker, Docker Compose, Uvicorn

---

## ⚙️ 실행 방법

**사전 준비:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) 설치 (NVIDIA GPI 필수)
- 로스트아크 Open API Key 발급

**실행 순서:**
1.  **`.env` 파일 생성:**
    -   프로젝트 루트에 `.env` 파일에 있는 API키를 발급받은 본인의 API 키로 교체합니다.
    ```
    LOSTARK_API_KEY=여기에_발급받은_API_키를_입력하세요
    ```

2. **터미널에서 백엔드 프로젝트 경로를 지정하세요**
    - 윈도우 파일 관리자에서 쉽게 경로를 복사할 수 있습니다
    ```
    cd './backend'
    ```

2.  **Docker Compose 실행:**
    -   터미널에서 아래 명령어를 실행하여 백엔드 서버와 Redis를 동시에 시작합니다.
    ```bash
    docker-compose up --build
    ```

3.  **서버 접속:**
    -   서버가 성공적으로 시작되면, API 문서는 `http://localhost:8000/docs` 에서 확인할 수 있습니다.

---

## 2. Front-end Part

## 📖 프로젝트 개요

Gemggark 백엔드 API와 연동하여, 사용자가 웹 브라우저를 통해 직관적으로 아크그리드 최적화 기능을 사용할 수 있도록 하는 사용자 인터페이스(UI)입니다.

---

## 🚀 주요 기능

- **동적 입력 폼:** 사용자가 자신의 코어, 보유 젬, 시장 상황을 쉽게 입력할 수 있습니다.
- **실시간 젬 시세 대시보드:** 페이지 접속 시 현재 18종 젬의 시세를 한눈에 보여줍니다.
- **실시간 진행률 피드백:** WebSocket과 연동된 로딩 바와 상태 메시지를 통해 긴 계산 시간 동안의 진행 상황을 시각적으로 보여줍니다.
- **결과 데이터 시각화:** 백엔드로부터 받은 복잡한 JSON 결과를 표와 툴팁을 이용해 보기 쉽게 표현합니다.

---

## 🛠️ 기술 스택

- **언어/프레임워크:** JavaScript, React.js
- **UI 라이브러리:** Material-UI (MUI)
- **API 통신:** axios
- **개발 환경:** Node.js, npm

---

## ⚙️ 실행 방법

**사전 준비:**
- [Node.js](https://nodejs.org/) (LTS 버전) 설치
- 백엔드 서버가 `http://localhost:8000`에서 실행 중이어야 합니다. (새 터미널을 열어서 프론트 작업을 수행하세요)

**실행 순서:**
1.  **라이브러리 설치:**
    -   터미널에서 프로젝트 루트 폴더로 이동한 후(백엔드와 동일하게 cd 이용), 아래 명령어를 실행합니다.
    ```bash
    npm install
    ```

2.  **개발 서버 시작:**
    -   아래 명령어를 실행하여 React 개발 서버를 시작합니다.
    -   실행 후 웹 브라우저에서 자동으로 `http://localhost:3000` 페이지가 열립니다.
    ```bash
    npm start
    ```

---


