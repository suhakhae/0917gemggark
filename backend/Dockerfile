# 1. 베이스 이미지를 NVIDIA CUDA와 TensorFlow GPU가 완벽하게 설정된 공식 이미지로 변경
FROM tensorflow/tensorflow:2.15.0-gpu

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 복사 및 라이브러리 설치
#    베이스 이미지에 tensorflow, numpy 등은 이미 포함되어 있으므로,
#    설치 과정이 매우 빨라집니다.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. 나머지 프로젝트 파일들을 작업 디렉토리로 복사
COPY . .

# 5. 컨테이너 실행 시 uvicorn 서버를 실행하도록 CMD 설정
#    (지금은 python 스크립트를 직접 실행하므로 이 부분은 사용되지 않음)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
