#!/usr/bin/env bash
set -euo pipefail

FUNCTION_NAME="${FUNCTION_NAME:-predictor-api}"
REGION="${REGION:-ap-northeast-2}"

# Test payload
PAYLOAD='{"type":1,"genre":3,"e1":111,"b1":111,"p1":10000,"e2":222,"b2":222,"p2":20000,"channel":1}'

# Get Function URL
FUNCTION_URL=$(aws lambda get-function-url-config \
  --function-name ${FUNCTION_NAME} \
  --region ${REGION} \
  --query 'FunctionUrl' \
  --output text 2>/dev/null || echo "")

if [[ -n "${FUNCTION_URL}" ]]; then
  echo "Testing Function URL..."
  echo ""
  curl -X POST ${FUNCTION_URL} \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}" 2>/dev/null | jq . 2>/dev/null || cat
  echo ""
else
  echo "No Function URL found. Testing via AWS CLI..."
  echo ""
  aws lambda invoke \
    --function-name ${FUNCTION_NAME} \
    --region ${REGION} \
    --cli-binary-format raw-in-base64-out \
    --payload "{\"httpMethod\":\"POST\",\"body\":\"${PAYLOAD}\"}" \
    /tmp/response.json >/dev/null
  cat /tmp/response.json | jq -r '.body' | jq .
  rm -f /tmp/response.json
fi

