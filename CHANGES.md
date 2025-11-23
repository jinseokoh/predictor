# 변경사항 요약 (2025-11-23)

## 모델 업데이트: statsmodels → sklearn LogisticRegression

주피터 노트북 (`/Users/chuck/Downloads/data-test.ipynb`)을 기반으로 Lambda 프로젝트를 업데이트했습니다.

## 주요 변경사항

### 1. 모델 타입 변경
- **이전**: `statsmodels.Logit` 모델
- **현재**: `sklearn.linear_model.LogisticRegression` 모델
- **파일**: `function/src/inference/predictor.py`

### 2. 입력 파라미터 변경
- **제거된 변수**: `channel` (판매채널)
- **유지된 변수**: 
  - `type`: 작가타입 (1=ARTIST1, 2=ARTIST2, 3=ARTIST3)
  - `genre`: 장르 (1=PAINTER, 2=DRAWER, 3=ETC, 4=GALLERY, 5=PHOTOGRAPHER, 6=SCULPTOR, 7=VISUAL_ARTIST)
  - `e1`, `b1`, `p1`: 내부 참여/이력/인기 지수
  - `e2`, `b2`, `p2`: 외부 참여/이력/인기 지수

### 3. 전처리 방식 변경
- **더미 변수 제거**: Type과 Genre를 정수 값으로 직접 사용
- **파일**: `function/src/inference/preprocessing.py`
- 노트북의 `get_test_data()` 함수 로직을 반영

### 4. 수정된 파일 목록
1. `function/src/inference/predictor.py`
   - sklearn LogisticRegression 사용
   - `predict_proba()` 메서드로 예측
   - 상수항 추가 로직 제거

2. `function/src/inference/preprocessing.py`
   - `channel` 변수 제거
   - 더미 변수 생성 로직 제거
   - Type과 Genre를 정수로 직접 사용
   - validation에 Type(1-3), Genre(1-7) 범위 검증 추가

3. `function/src/handler.py`
   - `channel` 필드 validation 제거
   - 모델 로딩 방식 단순화

4. `test.sh`
   - 테스트 payload에서 `channel` 제거

5. `README.md`
   - API 스펙 업데이트
   - 파라미터 설명 추가
   - 예제 코드 업데이트

## 테스트 방법

### 로컬 테스트 (선택)
```bash
cd function/src
python3 handler.py
```

### AWS Lambda 배포 및 테스트
```bash
# 배포
./deploy.sh

# 테스트
./test.sh
```

### 예제 요청
```bash
curl -X POST https://lbjf3q2ludatcmrthdkjeq72740mllta.lambda-url.ap-northeast-2.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"type":1,"genre":3,"e1":111,"b1":111,"p1":10000,"e2":222,"b2":222,"p2":20000}'
```

### 예제 응답
```json
{
  "result": "up",
  "percentage": 87.34,
  "e1": -0.5234,
  "b1": -0.3421,
  "p1": 1.2345,
  "e2": 0.8765,
  "b2": 0.4321,
  "p2": -0.1234
}
```

## 주의사항

1. **모델 파일 업데이트**: `model/Model_LogitRegression.pkl` 파일이 sklearn 모델로 업데이트되어야 합니다 (현재 파일 크기: 971바이트)

2. **표준화 통계값**: 6개 지수의 평균/표준편차는 여전히 `mean_std_config.json` 또는 `load_mean_std.py`에서 설정해야 합니다

3. **호환성**: 이전 API 요청 중 `channel` 파라미터를 포함한 요청은 실패합니다. 클라이언트 코드도 함께 업데이트해야 합니다

## 다음 단계

1. 변경사항 커밋
   ```bash
   git add .
   git commit -m "Update model to sklearn LogisticRegression and remove channel parameter"
   ```

2. Lambda 재배포
   ```bash
   ./deploy.sh
   ```

3. 통합 테스트 수행
   ```bash
   ./test.sh
   ```

