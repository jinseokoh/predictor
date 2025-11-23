"""
입력 데이터 전처리 모듈
POST 요청으로 받은 원본 데이터를 모델이 예측할 수 있는 형태로 변환
"""
import pandas as pd
from typing import Dict, Any, Optional


def validate_input(data: Dict[str, Any]) -> Dict[str, str]:
    """
    입력 데이터 유효성 검사
    
    Args:
        data: POST 요청으로 받은 데이터
        
    Returns:
        에러 딕셔너리 (에러가 없으면 빈 딕셔너리)
    """
    errors = {}
    
    required_fields = ['type', 'genre', 'e1', 'b1', 'p1', 'e2', 'b2', 'p2']
    
    for field in required_fields:
        if field not in data:
            errors[field] = f"{field} is required"
    
    if errors:
        return errors
    
    # 타입 및 범위 검증
    try:
        type_val = int(data['type'])
        genre_val = int(data['genre'])
        
        # Type 범위 검증: 1(ARTIST1), 2(ARTIST2), 3(ARTIST3)
        if type_val not in [1, 2, 3]:
            errors['type'] = "type must be 1, 2, or 3"
        
        # Genre 범위 검증: 1~7
        if genre_val not in [1, 2, 3, 4, 5, 6, 7]:
            errors['genre'] = "genre must be between 1 and 7"
        
        # 숫자형 필드 검증
        for field in ['e1', 'b1', 'p1', 'e2', 'b2', 'p2']:
            val = float(data[field])
            if val < 0:
                errors[field] = f"{field} must be non-negative"
                
    except (ValueError, TypeError) as e:
        errors['validation'] = f"Invalid data type: {str(e)}"
    
    return errors


def standardize_features(df: pd.DataFrame, mean_std: Optional[Dict[str, Dict[str, float]]] = None) -> pd.DataFrame:
    """
    6개 지수 변수에 표준화 적용: (값 - 평균) / 표준편차
    
    Args:
        df: 전처리 전 DataFrame (In_Engagement, In_History, In_Popularity, 
            Ex_Engagement, Ex_History, Ex_Popularity 컬럼 포함)
        mean_std: 평균과 표준편차 딕셔너리
            {
                'In_Engagement': {'mean': float, 'std': float},
                'In_History': {'mean': float, 'std': float},
                'In_Popularity': {'mean': float, 'std': float},
                'Ex_Engagement': {'mean': float, 'std': float},
                'Ex_History': {'mean': float, 'std': float},
                'Ex_Popularity': {'mean': float, 'std': float}
            }
            None이면 표준화를 수행하지 않음 (기존 동작)
    
    Returns:
        표준화된 DataFrame
    """
    if mean_std is None:
        return df
    
    # 표준화가 필요한 컬럼들
    columns_to_standardize = [
        'In_Engagement', 'In_History', 'In_Popularity',
        'Ex_Engagement', 'Ex_History', 'Ex_Popularity'
    ]
    
    # 각 컬럼에 대해 표준화 적용
    for col in columns_to_standardize:
        if col in df.columns and col in mean_std:
            mean = mean_std[col]['mean']
            std = mean_std[col]['std']
            
            # 표준편차가 0이면 나누기 오류 방지
            if std > 0:
                df[col] = (df[col] - mean) / std
            else:
                # 표준편차가 0이면 평균으로 빼기만 수행
                df[col] = df[col] - mean
    
    return df


def preprocess_input(data: Dict[str, Any], mean_std: Optional[Dict[str, Dict[str, float]]] = None) -> tuple[pd.DataFrame, Dict[str, float]]:
    """
    입력 데이터를 모델이 사용할 수 있는 형태로 전처리
    
    Args:
        data: POST 요청 데이터
        {
          "type": 1,        # 1=ARTIST1, 2=ARTIST2, 3=ARTIST3
          "genre": 3,       # 1=PAINTER, 2=DRAWER, 3=ETC, 4=GALLERY, 5=PHOTOGRAPHER, 6=SCULPTOR, 7=VISUAL_ARTIST
          "e1": 111,        # In_Engagement
          "b1": 111,        # In_History
          "p1": 10000,      # In_Popularity
          "e2": 222,        # Ex_Engagement
          "b2": 222,        # Ex_History
          "p2": 20000       # Ex_Popularity
        }
        mean_std: 평균과 표준편차 딕셔너리
        
    Returns:
        (전처리된 DataFrame, 표준화된 지수 값 딕셔너리)
    """
    # 입력 데이터를 DataFrame으로 변환
    # 노트북과 동일한 컬럼명 사용
    input_dict = {
        'Type': [int(data['type'])],
        'Genre': [int(data['genre'])],
        'In_Engagement': [float(data['e1'])],
        'In_History': [float(data['b1'])],
        'In_Popularity': [float(data['p1'])],
        'Ex_Engagement': [float(data['e2'])],
        'Ex_History': [float(data['b2'])],
        'Ex_Popularity': [float(data['p2'])]
    }
    
    df = pd.DataFrame(input_dict)
    
    # 표준화 적용
    df = standardize_features(df, mean_std)
    
    # 표준화된 지수 값 추출
    standardized_values = {
        'e1': round(float(df['In_Engagement'].iloc[0]), 4),
        'b1': round(float(df['In_History'].iloc[0]), 4),
        'p1': round(float(df['In_Popularity'].iloc[0]), 4),
        'e2': round(float(df['Ex_Engagement'].iloc[0]), 4),
        'b2': round(float(df['Ex_History'].iloc[0]), 4),
        'p2': round(float(df['Ex_Popularity'].iloc[0]), 4)
    }
    
    # NaN 처리
    df = df.fillna(0)
    
    return df, standardized_values


def align_columns_with_model(df: pd.DataFrame, model_features: list = None) -> pd.DataFrame:
    """
    입력 DataFrame 반환 (sklearn 모델은 컬럼 순서 자동 처리)
    
    Args:
        df: 전처리된 입력 DataFrame
        model_features: 사용하지 않음 (호환성 유지용)
        
    Returns:
        입력 DataFrame (변경 없음)
    """
    # sklearn LogisticRegression은 학습 시 컬럼 순서를 기억하므로
    # 별도의 정렬이 필요 없음
    return df

