"""
AWS Lambda Handler
API Gateway와 통합되어 POST 요청을 받아 예측 결과를 반환
"""
import json
import traceback
from typing import Dict, Any

from inference.preprocessing import validate_input, preprocess_input, align_columns_with_model
from inference.predictor import load_model, predict


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    API Gateway 응답 형식 생성
    
    Args:
        status_code: HTTP 상태 코드
        body: 응답 본문 딕셔너리
        
    Returns:
        API Gateway 응답 딕셔너리
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # CORS 설정
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda 진입점
    
    Args:
        event: API Gateway에서 전달된 이벤트
        context: Lambda context 객체
        
    Returns:
        API Gateway 응답
    """
    try:
        # OPTIONS 요청 처리 (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # POST 요청인지 확인
        if event.get('httpMethod') != 'POST':
            return create_response(405, {
                'error': 'Method not allowed',
                'message': 'Only POST method is supported'
            })
        
        # 요청 본문 파싱
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return create_response(400, {
                    'error': 'Invalid JSON',
                    'message': 'Request body must be valid JSON'
                })
        else:
            data = body
        
        # 입력 유효성 검사
        validation_errors = validate_input(data)
        if validation_errors:
            return create_response(400, {
                'error': 'Validation failed',
                'details': validation_errors
            })
        
        # 데이터 전처리
        df = preprocess_input(data)
        
        # 모델 feature와 정렬
        model_package = load_model()
        feature_names = model_package['feature_names']
        df = align_columns_with_model(df, feature_names)
        
        # 예측 수행
        result, percentage = predict(df)
        
        # 성공 응답
        return create_response(200, {
            'result': result,
            'percentage': round(percentage, 2)
        })
        
    except FileNotFoundError as e:
        print(f"[ERROR] Model file not found: {str(e)}")
        traceback.print_exc()
        return create_response(500, {
            'error': 'Model not found',
            'message': 'Prediction model is not available'
        })
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        traceback.print_exc()
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })


# 로컬 테스트용
if __name__ == '__main__':
    # 테스트 이벤트
    test_event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            "type": 1,
            "genre": 3,
            "e1": 111,
            "b1": 111,
            "p1": 10000,
            "e2": 222,
            "b2": 222,  
            "p2": 20000,
            "channel": 1
        })
    }
    
    response = lambda_handler(test_event, None)
    print(json.dumps(response, indent=2, ensure_ascii=False))
