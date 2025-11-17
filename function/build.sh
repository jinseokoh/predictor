#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
FUNCTION_ROOT="${SCRIPT_DIR}"
SRC_DIR="${FUNCTION_ROOT}/src"

echo "Building Lambda Function package..."

# 기존 zip 파일 삭제
rm -rf "${FUNCTION_ROOT}/predictor-function.zip"

# src 디렉토리로 이동하여 zip 생성
cd "${SRC_DIR}"

# 모든 Python 파일을 zip으로 압축
zip -qr "${FUNCTION_ROOT}/predictor-function.zip" . \
  -x "*.pyc" \
  -x "__pycache__/*" \
  -x "*/__pycache__/*" \
  -x "*/*/__pycache__/*"

echo ""
echo "✅ Function build complete!"
echo "Output: ${FUNCTION_ROOT}/predictor-function.zip"
echo ""
echo "Function structure:"
echo "  handler.py"
echo "  inference/"
echo "    ├── __init__.py"
echo "    ├── preprocessing.py"
echo "    └── predictor.py"
echo "  models/"
echo "    └── __init__.py"

