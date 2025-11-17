#!/usr/bin/env bash
set -euo pipefail

# 배포 스크립트
# Layer와 Function을 순차적으로 빌드합니다

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "${SCRIPT_DIR}"

echo "========================================="
echo "  Lambda Predictor 배포 빌드"
echo "========================================="
echo ""

# Layer 빌드
echo "1️⃣  Lambda Layer 빌드 중..."
cd layer/
./build.sh
cd ..

echo ""
echo "2️⃣  Lambda Function 빌드 중..."
cd function/
./build.sh
cd ..

echo ""
echo "========================================="
echo "✅ 빌드 완료!"
echo "========================================="
echo ""
echo "다음 파일들이 생성되었습니다:"
echo "  📦 layer/predictor-layer.zip"
echo "  📦 function/predictor-function.zip"
echo ""
echo "배포 방법:"
echo "  1. Layer 배포:"
echo "     aws lambda publish-layer-version \\"
echo "       --layer-name predictor-dependencies \\"
echo "       --zip-file fileb://layer/predictor-layer.zip \\"
echo "       --compatible-runtimes python3.11"
echo ""
echo "  2. Function 배포 (신규):"
echo "     aws lambda create-function \\"
echo "       --function-name predictor-api \\"
echo "       --runtime python3.11 \\"
echo "       --role <YOUR_ROLE_ARN> \\"
echo "       --handler handler.lambda_handler \\"
echo "       --zip-file fileb://function/predictor-function.zip \\"
echo "       --layers <LAYER_ARN>"
echo ""
echo "  3. Function 업데이트 (재배포):"
echo "     aws lambda update-function-code \\"
echo "       --function-name predictor-api \\"
echo "       --zip-file fileb://function/predictor-function.zip"
echo ""

