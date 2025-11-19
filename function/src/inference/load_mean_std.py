"""
표준화 통계값 로드 모듈
"""
import json
import os
from typing import Dict, Optional

_MEAN_STD_CACHE = None

# 하드코딩된 표준화 통계값 (모델 학습 시점의 통계)
HARDCODED_MEAN_STD = {
    'In_Engagement': {'mean': 41.82938, 'std': 65.669176},
    'In_History': {'mean': 362.88374, 'std': 610.10993},
    'In_Popularity': {'mean': 908.04684, 'std': 6431.8375},
    'Ex_Engagement': {'mean': 109.32793, 'std': 120.94698},
    'Ex_History': {'mean': 9.2596876, 'std': 9.9536345},
    'Ex_Popularity': {'mean': 7775.3163, 'std': 9912.7047}
}


def load_mean_std() -> Optional[Dict[str, Dict[str, float]]]:
    """
    표준화 통계값을 로드
    
    우선순위:
    1. 하드코딩된 값 (HARDCODED_MEAN_STD)
    2. JSON 파일 (mean_std_config.json)
    3. None (표준화 스킵)
    
    Returns:
        mean_std 딕셔너리 또는 None
        {
            'In_Engagement': {'mean': float, 'std': float},
            'In_History': {'mean': float, 'std': float},
            'In_Popularity': {'mean': float, 'std': float},
            'Ex_Engagement': {'mean': float, 'std': float},
            'Ex_History': {'mean': float, 'std': float},
            'Ex_Popularity': {'mean': float, 'std': float}
        }
    """
    global _MEAN_STD_CACHE
    
    # 캐시된 값이 있으면 반환
    if _MEAN_STD_CACHE is not None:
        return _MEAN_STD_CACHE
    
    # 1. 하드코딩된 값 확인
    if HARDCODED_MEAN_STD and len(HARDCODED_MEAN_STD) == 6:
        _MEAN_STD_CACHE = HARDCODED_MEAN_STD
        return HARDCODED_MEAN_STD
    
    # 2. JSON 파일에서 로드 시도
    json_path = os.path.join(os.path.dirname(__file__), 'mean_std_config.json')
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                mean_std = json.load(f)
            
            _MEAN_STD_CACHE = mean_std
            return mean_std
        except Exception as e:
            print(f"Error loading mean_std config: {e}")
    
    # 3. 둘 다 없으면 None 반환
    return None

