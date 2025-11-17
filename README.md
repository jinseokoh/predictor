# Predictor API

Lambda Container Image 기반 머신러닝 예측 API

## 목표

전달받은 로지스틱 회귀 기반 예측 모델을 기반으로 작가가치 예측 API 제작.
  - 6개지수는 표준화하지 않고 DB record 값을 그대로 전달하여 API 에서 전처리 후 사용하도록 진행
  - 지수 e1, b1, p1, e2, b2, p2 (참여지수, 이력지수, 인기지수, 참여지수2 이력지수2 인기지수2)
  - 변수 type, genre, channel (작가타입, 장르, 판매채널)

### 1. 배포된 Function URL:

```
Function URL: https://lbjf3q2ludatcmrthdkjeq72740mllta.lambda-url.ap-northeast-2.on.aws/
```

### 2. 테스트

```bash
./test.sh
```

또는 직접 호출:

```bash
curl -X POST https://lbjf3q2ludatcmrthdkjeq72740mllta.lambda-url.ap-northeast-2.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"type":1,"genre":3,"e1":111,"b1":111,"p1":10000,"e2":222,"b2":222,"p2":20000,"channel":1}'
```

응답 예시:

```json
{
  "result": "up",
  "percentage": 100.0
}
```

## 프로젝트 구조

```
predictor/
├── Dockerfile             # Lambda Container Image 정의
├── requirements.txt       # Python 의존성
├── setup.sh               # IAM 역할 생성
├── deploy.sh              # 빌드 및 배포
├── test.sh                # 테스트
├── cleanup.sh             # 리소스 삭제
├── model/                 # ML 모델 파일
│   └── Model_LogitRegression.pkl
└── function/
    └── src/
        ├── handler.py     # Lambda 핸들러
        └── inference/     # 추론 로직
```

## 리소스 정리

모든 AWS 리소스를 삭제하려면:

```bash
./cleanup.sh
```

## 환경 변수

스크립트 실행 시 환경 변수로 설정 변경 가능:

```bash
FUNCTION_NAME=predictor-api REGION=ap-northeast-2 ./deploy.sh
```

- `FUNCTION_NAME`: Lambda 함수 이름 (default: `predictor-api`)
- `REGION`: AWS 리전 (default: `ap-northeast-2`)
