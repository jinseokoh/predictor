# AWS Lambda Python 3.11 Base Image
FROM public.ecr.aws/lambda/python:3.11

# 작업 디렉토리 설정
WORKDIR ${LAMBDA_TASK_ROOT}

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 모델 파일 복사
COPY model/Model_LogitRegression.pkl ${LAMBDA_TASK_ROOT}/

# Lambda 함수 코드 복사
COPY function/src/ ${LAMBDA_TASK_ROOT}/

# Lambda handler 설정
CMD ["handler.lambda_handler"]

