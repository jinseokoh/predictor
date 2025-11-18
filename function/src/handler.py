"""
AWS Lambda Handler
API Gateway와 통합되어 POST 요청을 받아 예측 결과를 반환
"""
import json
import traceback
import logging
from typing import Dict, Any

from inference.preprocessing import validate_input, preprocess_input, align_columns_with_model
from inference.predictor import load_model, predict

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
        event: API Gateway 또는 Function URL에서 전달된 이벤트
        context: Lambda context 객체
        
    Returns:
        API Gateway/Function URL 응답
    """
    logger.info(f"Lambda invoked. Request ID: {context.aws_request_id if context else 'N/A'}")
    logger.debug(f"Event: {json.dumps(event)}")
    
    try:
        # HTTP 메소드 추출 (API Gateway와 Function URL 모두 지원)
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
        
        # OPTIONS 요청 처리 (CORS preflight)
        if http_method == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # POST 요청인지 확인
        if http_method != 'POST':
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
        logger.info("Validating input data")
        validation_errors = validate_input(data)
        if validation_errors:
            logger.warning(f"Validation failed: {validation_errors}")
            return create_response(400, {
                'error': 'Validation failed',
                'details': validation_errors
            })
        
        # 모델 로드 (표준화 통계값을 가져오기 위해 먼저 로드)
        logger.info("Loading model")
        model_package = load_model()
        feature_names = model_package['feature_names']
        mean_std = model_package.get('mean_std', None)  # 표준화 통계값 (선택적)
        logger.info(f"Model loaded. Features: {len(feature_names)}")
        if mean_std:
            logger.info("Standardization statistics found in model package")
        else:
            logger.warning("No standardization statistics found in model package. Standardization will be skipped.")
        
        # 데이터 전처리 (표준화 포함)
        logger.info("Preprocessing input data")
        df = preprocess_input(data, mean_std)
        
        # 모델 feature와 정렬
        df = align_columns_with_model(df, feature_names)
        
        # 예측 수행
        logger.info("Performing prediction")
        result, percentage = predict(df)
        logger.info(f"Prediction result: {result}, percentage: {percentage}")
        
        # 성공 응답
        return create_response(200, {
            'result': result,
            'percentage': round(percentage, 2)
        })
        
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {str(e)}", exc_info=True)
        return create_response(500, {
            'error': 'Model not found',
            'message': 'Prediction model is not available'
        })
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
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
