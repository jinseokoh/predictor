"""
예측 수행 모듈
모델을 로드하고 전처리된 데이터로 예측을 수행
"""
import pickle
import pandas as pd
from typing import Dict, Tuple
import os


# 전역 변수로 모델 캐싱 (Lambda cold start 최적화)
_MODEL_CACHE = None
# Container Image에서는 LAMBDA_TASK_ROOT에 모델이 위치
_MODEL_PATH = os.environ.get("MODEL_PATH", "/var/task/Model_LogitRegression.pkl")


def load_model():
    """
    학습된 sklearn LogisticRegression 모델을 로드
    
    Returns:
        sklearn LogisticRegression 모델 객체
    """
    global _MODEL_CACHE
    
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {_MODEL_PATH}")
    
    with open(_MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    
    _MODEL_CACHE = model
    return model


def predict(df: pd.DataFrame) -> Tuple[str, float]:
    """
    전처리된 데이터로 예측 수행
    
    Args:
        df: 전처리된 입력 DataFrame
            컬럼: Type, Genre, In_Engagement, In_History, In_Popularity,
                  Ex_Engagement, Ex_History, Ex_Popularity
        
    Returns:
        (result, percentage) 튜플
        - result: "up" 또는 "down"
        - percentage: 예측 확률 (0.0 ~ 100.0)
    """
    # 모델 로드
    model = load_model()
    
    # 예측 수행 (sklearn LogisticRegression)
    # predict_proba()는 [class=0 확률, class=1 확률] 반환
    prob_array = model.predict_proba(df)
    prob = prob_array[0][1]  # class=1일 확률
    
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

