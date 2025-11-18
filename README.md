# Predictor API

Lambda Container Image 기반 머신러닝 예측 API

## 목표

전달받은 로지스틱 회귀 기반 예측 모델을 기반으로 작가가치 예측 API 제작.
  - 6개 지수는 DB record 값을 그대로 전달하여 API 에서 전처리(표준화) 후 사용
  - 지수 e1, b1, p1, e2, b2, p2 (참여지수, 이력지수, 인기지수, 참여지수2, 이력지수2, 인기지수2)
  - 표준화 공식: (값 - 평균) / 표준편차
  - 표준화된 6개 지수 값을 응답에 포함하여 반환
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
  "percentage": 100.0,
  "e1": -0.5234,
  "b1": -0.3421,
  "p1": 1.2345,
  "e2": 0.8765,
  "b2": 0.4321,
  "p2": -0.1234
}
```

**참고:** e1, b1, p1, e2, b2, p2는 표준화된 지수 값입니다. 표준화 공식: (값 - 평균) / 표준편차

## 표준화 통계값 설정

6개 지수를 표준화하려면 **한 번만** 평균/표준편차를 계산하여 설정해야 합니다.

### 방법 1: JSON 파일 사용 (권장)

1. DB에서 통계 계산:
```bash
# Bastion host를 통한 SSH 터널 생성
ssh -i key.pem -N -L 3307:RDS_ENDPOINT:3306 ec2-user@BASTION_IP

# 스크립트 실행 (DB 정보 입력 필요)
python3 calculate_stats_via_bastion.py
# → mean_std_config.json 파일 생성
```

2. JSON 파일을 배포에 포함:
```bash
# mean_std_config.json을 function/src/inference/ 디렉토리에 복사
cp mean_std_config.json function/src/inference/

# 재배포
./deploy.sh
```

### 방법 2: 코드에 직접 입력

`function/src/inference/load_mean_std.py` 파일의 `HARDCODED_MEAN_STD`를 수정:

```python
HARDCODED_MEAN_STD = {
    'In_Engagement': {'mean': 123.45, 'std': 67.89},
    'In_History': {'mean': 234.56, 'std': 78.90},
    'In_Popularity': {'mean': 12345.67, 'std': 890.12},
    'Ex_Engagement': {'mean': 345.67, 'std': 89.01},
    'Ex_History': {'mean': 456.78, 'std': 90.12},
    'Ex_Popularity': {'mean': 23456.78, 'std': 901.23}
}
```

## 프로젝트 구조

```
predictor/
├── Dockerfile                          # Lambda Container Image 정의
├── requirements.txt                    # Python 의존성
├── setup.sh                            # IAM 역할 생성
├── deploy.sh                           # 빌드 및 배포
├── test.sh                             # 테스트
├── cleanup.sh                          # 리소스 삭제
├── calculate_stats_via_bastion.py      # DB 통계 계산 스크립트
├── check_model.py                      # 모델 파일 분석 스크립트
├── model/                              # ML 모델 파일
│   └── Model_LogitRegression.pkl
└── function/
    └── src/
        ├── handler.py                  # Lambda 핸들러
        └── inference/                  # 추론 로직
            ├── preprocessing.py        # 전처리 (표준화 포함)
            ├── predictor.py            # 예측
            ├── load_mean_std.py        # 표준화 통계값 로드
            └── mean_std_config.json    # 표준화 통계값 (선택적)
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
