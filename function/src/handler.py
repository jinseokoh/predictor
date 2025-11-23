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
from inference.load_mean_std import load_mean_std

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
        
        # 표준화 통계값 로드 (JSON 파일에서)
        logger.info("Loading standardization statistics")
        mean_std = load_mean_std()
        if mean_std:
            logger.info("Standardization statistics loaded from JSON config")
        else:
            logger.warning("No standardization statistics found. Standardization will be skipped.")
        
        # 모델 로드
        logger.info("Loading model")
        model = load_model()
        logger.info("Model loaded successfully")
        
        # 데이터 전처리 (표준화 포함)
        logger.info("Preprocessing input data")
        df, standardized_values = preprocess_input(data, mean_std)
        
        # 컬럼 정렬 (sklearn은 자동으로 처리하지만 호환성 유지)
        df = align_columns_with_model(df)
        
        # 예측 수행
        logger.info("Performing prediction")
        result, percentage = predict(df)
        logger.info(f"Prediction result: {result}, percentage: {percentage}")
        
        # 성공 응답 (표준화된 지수 값 포함)
        response_body = {
            'result': result,
            'percentage': round(percentage, 2)
        }
        
        # 표준화된 6종 지수 값 추가
        response_body.update(standardized_values)
        
        return create_response(200, response_body)
        
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
            "type": 1,         # 1=ARTIST1, 2=ARTIST2, 3=ARTIST3
            "genre": 3,        # 1=PAINTER, 2=DRAWER, 3=ETC, 4=GALLERY, 5=PHOTOGRAPHER, 6=SCULPTOR, 7=VISUAL_ARTIST
            "e1": 111,         # In_Engagement
            "b1": 111,         # In_History
            "p1": 10000,       # In_Popularity
            "e2": 222,         # Ex_Engagement
            "b2": 222,         # Ex_History
            "p2": 20000        # Ex_Popularity
        })
    }
    
    response = lambda_handler(test_event, None)
    print(json.dumps(response, indent=2, ensure_ascii=False))
