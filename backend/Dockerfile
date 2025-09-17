FROM tensorflow/tensorflow:2.15.0-gpu

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 복사 및 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. 나머지 프로젝트 파일들을 작업 디렉토리로 복사
COPY . .

# 5. 컨테이너 실행 시 uvicorn 서버를 실행하도록 CMD 설정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
