#!/usr/bin/env bash
set -euo pipefail

FUNCTION_NAME="${FUNCTION_NAME:-predictor-api}"
REGION="${REGION:-ap-northeast-2}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME="${FUNCTION_NAME}"
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest"

echo "Building and deploying ${FUNCTION_NAME}..."

# ECR login
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Create ECR repo if needed
aws ecr describe-repositories --repository-names ${REPO_NAME} --region ${REGION} >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name ${REPO_NAME} --region ${REGION} >/dev/null

# Build and push
docker build --platform linux/amd64 -t ${REPO_NAME}:latest .
docker tag ${REPO_NAME}:latest ${IMAGE_URI}
docker push ${IMAGE_URI} >/dev/null

# Deploy Lambda
if aws lambda get-function --function-name ${FUNCTION_NAME} --region ${REGION} >/dev/null 2>&1; then
  aws lambda update-function-code \
    --function-name ${FUNCTION_NAME} \
    --image-uri ${IMAGE_URI} \
    --region ${REGION} \
    --output text >/dev/null
  echo "✓ Function updated"
else
  ROLE_ARN=$(aws iam get-role --role-name lambda-execution-role --query 'Role.Arn' --output text)
  aws lambda create-function \
    --function-name ${FUNCTION_NAME} \
    --package-type Image \
    --code ImageUri=${IMAGE_URI} \
    --role ${ROLE_ARN} \
    --timeout 30 \
    --memory-size 1024 \
    --region ${REGION} \
    --output text >/dev/null
  echo "✓ Function created"
fi

# Create Function URL if needed
if ! aws lambda get-function-url-config --function-name ${FUNCTION_NAME} --region ${REGION} >/dev/null 2>&1; then
  aws lambda add-permission \
    --function-name ${FUNCTION_NAME} \
    --statement-id FunctionURLAllowPublicAccess \
    --action lambda:InvokeFunctionUrl \
    --principal "*" \
    --function-url-auth-type NONE \
    --region ${REGION} >/dev/null 2>&1 || true
  
  aws lambda create-function-url-config \
    --function-name ${FUNCTION_NAME} \
    --auth-type NONE \
    --region ${REGION} \
    --output text >/dev/null
  echo "✓ Function URL created"
fi

FUNCTION_URL=$(aws lambda get-function-url-config --function-name ${FUNCTION_NAME} --region ${REGION} --query 'FunctionUrl' --output text)

echo ""
echo "Deployment complete!"
echo "Function URL: ${FUNCTION_URL}"

