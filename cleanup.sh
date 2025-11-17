#!/usr/bin/env bash
set -euo pipefail

FUNCTION_NAME="${FUNCTION_NAME:-predictor-api}"
REGION="${REGION:-ap-northeast-2}"
ROLE_NAME="lambda-execution-role"

echo "Cleaning up AWS resources..."

# Delete Function URL
aws lambda delete-function-url-config \
  --function-name ${FUNCTION_NAME} \
  --region ${REGION} 2>/dev/null && echo "✓ Function URL deleted" || true

# Delete Lambda function
aws lambda delete-function \
  --function-name ${FUNCTION_NAME} \
  --region ${REGION} 2>/dev/null && echo "✓ Lambda function deleted" || true

# Delete ECR repository
aws ecr delete-repository \
  --repository-name ${FUNCTION_NAME} \
  --region ${REGION} \
  --force 2>/dev/null && echo "✓ ECR repository deleted" || true

# Delete IAM role
aws iam detach-role-policy \
  --role-name ${ROLE_NAME} \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null || true

aws iam delete-role \
  --role-name ${ROLE_NAME} 2>/dev/null && echo "✓ IAM role deleted" || true

echo ""
echo "Cleanup complete!"

