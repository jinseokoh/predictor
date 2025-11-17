# Predictor Lambda Function

AWS Lambda 기반 머신러닝 예측 API

## 📋 개요

이 프로젝트는 statsmodels 로지스틱 회귀 모델을 사용하여 potential_disc (상승/하락)을 예측하는 Lambda Function입니다.

### 주요 기능
- POST API를 통한 실시간 예측
- 정규화되지 않은 원본 데이터 입력 (Lambda 내부에서 전처리 수행)
- Lambda Layer를 통한 ML 라이브러리 및 모델 관리
- CORS 지원

## 🏗️ 프로젝트 구조

```
predictor/
├── function/
│   ├── src/
│   │   ├── handler.py                # Lambda 진입점
│   │   ├── inference/
│   │   │   ├── __init__.py
│   │   │   ├── preprocessing.py      # 데이터 전처리
│   │   │   └── predictor.py          # 예측 로직
│   │   └── models/
│   │       └── __init__.py
│   ├── build.sh                      # Function 빌드 스크립트
│   └── predictor-function.zip        # (빌드 후 생성)
│
├── layer/
│   ├── python/
│   │   ├── Model_LogitRegression.pkl # 학습된 모델
│   │   └── (site-packages/)          # pip 패키지들 (빌드 후)
│   ├── build.sh                      # Layer 빌드 스크립트
│   ├── requirements.txt              # Python 의존성
│   └── predictor-layer.zip           # (빌드 후 생성)
│
└── README.md
```

## 📦 요구사항

### 로컬 빌드 환경
- Python 3.11
- bash
- zip

### Lambda Runtime
- Python 3.11
- x86_64 아키텍처 (기본) 또는 arm64 (Graviton)

## 🚀 빌드 및 배포

### 1. Layer 빌드

Lambda Layer에는 ML 라이브러리와 모델 파일이 포함됩니다.

```bash
cd layer/
./build.sh
```

**출력**: `predictor-layer.zip` (약 150-200MB)

**Graviton (arm64) 빌드**:
```bash
ARCH=arm64 ./build.sh
```

### 2. Function 빌드

Lambda Function 코드를 패키징합니다.

```bash
cd function/
./build.sh
```

**출력**: `predictor-function.zip` (약 10KB)

### 3. AWS Lambda 배포

#### Layer 배포

```bash
aws lambda publish-layer-version \
  --layer-name predictor-dependencies \
  --description "ML dependencies and model for predictor" \
  --zip-file fileb://layer/predictor-layer.zip \
  --compatible-runtimes python3.11 \
  --compatible-architectures x86_64
```

Layer ARN을 기록해둡니다 (예: `arn:aws:lambda:ap-northeast-2:123456789012:layer:predictor-dependencies:1`)

#### Function 배포

```bash
aws lambda create-function \
  --function-name predictor-api \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function/predictor-function.zip \
  --timeout 30 \
  --memory-size 512 \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:predictor-dependencies:1 \
  --architectures x86_64
```

#### Function 업데이트 (재배포)

```bash
aws lambda update-function-code \
  --function-name predictor-api \
  --zip-file fileb://function/predictor-function.zip
```

### 4. API Gateway 설정 (선택사항)

Lambda Function URL을 사용하는 경우:

```bash
aws lambda create-function-url-config \
  --function-name predictor-api \
  --auth-type NONE \
  --cors AllowOrigins="*",AllowMethods="POST,OPTIONS",AllowHeaders="Content-Type"
```

또는 API Gateway REST API/HTTP API를 생성하여 Lambda와 연동할 수 있습니다.

## 📡 API 사용법

### Endpoint

POST 요청을 Lambda Function URL 또는 API Gateway endpoint로 전송합니다.

### Request Format

```json
{
  "type": 1,
  "genre": 3,
  "e1": 111,
  "b1": 111,
  "p1": 10000,
  "e2": 222,
  "b2": 222,  
  "p2": 20000,
  "channel": 1
}
```

**필드 설명**:
- `type`: 타입 (정수)
- `genre`: 장르 (정수)
- `e1`: In_Engagement (숫자)
- `b1`: In_History (숫자)
- `p1`: In_Popularity (숫자)
- `e2`: Ex_Engagement (숫자)
- `b2`: Ex_History (숫자)
- `p2`: Ex_Popularity (숫자)
- `channel`: sale_channel (정수: 0=정찰제, 1=옥션, 2=둘다)

**주의**: 모든 값은 **정규화 전** 원본 값으로 전달합니다.

### Response Format

**성공 (200 OK)**:
```json
{
  "result": "up",
  "percentage": 75.23
}
```

- `result`: `"up"` (상승) 또는 `"down"` (하락)
- `percentage`: 상승 확률 (0.0 ~ 100.0)

**에러 (400 Bad Request)**:
```json
{
  "error": "Validation failed",
  "details": {
    "type": "type is required"
  }
}
```

**에러 (500 Internal Server Error)**:
```json
{
  "error": "Internal server error",
  "message": "..."
}
```

### cURL 예제

```bash
curl -X POST https://YOUR_FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "type": 1,
    "genre": 3,
    "e1": 111,
    "b1": 111,
    "p1": 10000,
    "e2": 222,
    "b2": 222,
    "p2": 20000,
    "channel": 1
  }'
```

### Python 예제

```python
import requests
import json

url = "https://YOUR_FUNCTION_URL"
data = {
    "type": 1,
    "genre": 3,
    "e1": 111,
    "b1": 111,
    "p1": 10000,
    "e2": 222,
    "b2": 222,
    "p2": 20000,
    "channel": 1
}

response = requests.post(url, json=data)
result = response.json()

print(f"Result: {result['result']}")
print(f"Percentage: {result['percentage']}%")
```

## 🧪 로컬 테스트

### 직접 테스트

```bash
cd function/src/
python3.11 handler.py
```

이 명령은 하드코딩된 테스트 데이터로 handler를 실행합니다.

**주의**: 로컬 테스트 시 `/opt/python/Model_LogitRegression.pkl` 경로를 임시로 변경해야 할 수 있습니다.

### SAM Local 테스트 (권장)

AWS SAM CLI를 사용하여 Lambda 환경을 로컬에서 에뮬레이션:

```bash
sam local invoke -e test-event.json
```

## 🔧 커스터마이징

### 모델 교체

1. 새 모델을 학습하고 `.pkl` 파일 생성
2. `layer/python/Model_LogitRegression.pkl`에 복사
3. Layer 재빌드 및 재배포

### Feature 변경

`preprocessing.py`의 `preprocess_input()` 함수를 수정하여 새로운 feature를 추가하거나 변경할 수 있습니다.

### 응답 형식 변경

`handler.py`의 응답 부분을 수정하거나, `predictor.py`의 `predict_with_details()` 함수를 사용하여 더 상세한 정보를 반환할 수 있습니다.

## ⚙️ 환경 변수 (선택사항)

Lambda 함수에 다음 환경 변수를 설정할 수 있습니다:

- `MODEL_PATH`: 모델 파일 경로 (기본: `/opt/python/Model_LogitRegression.pkl`)

## 📊 성능

- **Cold Start**: 약 3-5초 (Layer 크기에 따라 다름)
- **Warm Invocation**: 약 50-200ms
- **권장 메모리**: 512MB 이상
- **권장 타임아웃**: 30초

## 🐛 문제 해결

### 모델 파일을 찾을 수 없음

```
Model file not found: /opt/python/Model_LogitRegression.pkl
```

**해결책**: Layer 빌드 시 모델 파일이 `layer/python/`에 있는지 확인하고 Layer를 재배포합니다.

### 메모리 부족

```
Task timed out after X seconds
```

**해결책**: Lambda 함수의 메모리를 512MB 이상으로 설정합니다.

### 더미 변수 불일치

모델 학습 시와 다른 카테고리 값이 입력되면 예측이 부정확할 수 있습니다. `preprocessing.py`의 `align_columns_with_model()` 함수가 이를 처리합니다.

## 📝 주요 변경사항

- **v1.0**: 초기 릴리스 (statsmodels 로지스틱 회귀)

## 📄 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.
