"""
예측 수행 모듈
모델을 로드하고 전처리된 데이터로 예측을 수행
"""
import pickle
import statsmodels.api as sm
import pandas as pd
from typing import Dict, Tuple
import os


# 전역 변수로 모델 캐싱 (Lambda cold start 최적화)
_MODEL_CACHE = None
_MODEL_PATH = "/opt/python/Model_LogitRegression.pkl"


def load_model() -> Dict:
    """
    학습된 모델을 로드
    
    Returns:
        모델 패키지 딕셔너리
        {
            "model_type": "statsmodels_logit",
            "model": 학습된 모델 객체,
            "feature_names": 학습에 사용된 feature 리스트
        }
    """
    global _MODEL_CACHE
    
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {_MODEL_PATH}")
    
    with open(_MODEL_PATH, "rb") as f:
        model_package = pickle.load(f)
    
    _MODEL_CACHE = model_package
    return model_package


def predict(df: pd.DataFrame) -> Tuple[str, float]:
    """
    전처리된 데이터로 예측 수행
    
    Args:
        df: 전처리된 입력 DataFrame (상수항 없음)
        
    Returns:
        (result, percentage) 튜플
        - result: "up" 또는 "down"
        - percentage: 예측 확률 (0.0 ~ 100.0)
    """
    # 모델 로드
    model_package = load_model()
    model = model_package['model']
    feature_names = model_package['feature_names']
    
    # 상수항 추가
    df_with_const = sm.add_constant(df, has_constant='add')
    
    # 상수항이 먼저 오도록 컬럼 순서 조정
    if 'const' in feature_names:
        # feature_names와 동일한 순서로 컬럼 정렬
        df_with_const = df_with_const[feature_names]
    
    # float 타입으로 변환
    df_with_const = df_with_const.astype(float)
    
    # 예측 수행
    # predict()는 class=1일 확률을 반환
    prob = model.predict(df_with_const)[0]
    
    # 확률이 0.5 이상이면 "up" (potential_disc=1), 미만이면 "down" (potential_disc=0)
    result = "up" if prob >= 0.5 else "down"
    
    # 백분율로 변환
    percentage = prob * 100.0
    
    return result, percentage


def predict_with_details(df: pd.DataFrame) -> Dict:
    """
    예측 수행 및 상세 정보 반환
    
    Args:
        df: 전처리된 입력 DataFrame
        
    Returns:
        상세 예측 결과 딕셔너리
        {
            "result": "up" | "down",
            "percentage": float,
            "probability_up": float,
            "probability_down": float,
            "confidence": float
        }
    """
    result, percentage = predict(df)
    
    prob_up = percentage / 100.0
    prob_down = 1.0 - prob_up
    
    # 신뢰도 = max(prob_up, prob_down) - 결정 경계(0.5)와의 거리
    confidence = abs(prob_up - 0.5) * 2.0 * 100.0  # 0~100% 스케일
    
    return {
        "result": result,
        "percentage": round(percentage, 2),
        "probability_up": round(prob_up * 100, 2),
        "probability_down": round(prob_down * 100, 2),
        "confidence": round(confidence, 2)
    }

