#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
LAYER_ROOT="${SCRIPT_DIR}"
WORKDIR="${LAYER_ROOT}"
PYDIR="${WORKDIR}/python"
ARCH="${ARCH:-x86_64}"  # set ARCH=arm64 for Graviton

if [[ "${ARCH}" == "arm64" ]]; then
  TARGET_PLATFORM="manylinux2014_aarch64"
else
  TARGET_PLATFORM="manylinux2014_x86_64"
fi

echo "Building Lambda Layer for architecture: ${ARCH}"
echo "Target platform: ${TARGET_PLATFORM}"

# 기존 python 폴더와 zip 파일 삭제
rm -rf "${PYDIR}" "${WORKDIR}/predictor-layer.zip"
mkdir -p "${PYDIR}"

# Python 3.11 필요 (Lambda runtime python3.11 사용)
python3.11 -m pip install --upgrade pip >/dev/null

echo "Installing Python dependencies..."
# Linux 호환 wheel 설치 (manylinux2014, cp311)
# AWS Lambda (AL2023)에서 동작하도록 darwin 바이너리 제외
python3.11 -m pip install \
  --only-binary=:all: \
  --platform "${TARGET_PLATFORM}" \
  --implementation cp \
  --python-version 311 \
  --abi cp311 \
  -r "${LAYER_ROOT}/requirements.txt" \
  -t "${PYDIR}"

echo "Copying model file..."
# 모델 파일 복사 확인
if [ -f "${PYDIR}/Model_LogitRegression.pkl" ]; then
  echo "Model file found: ${PYDIR}/Model_LogitRegression.pkl"
else
  echo "[WARN] Model file not found at ${PYDIR}/Model_LogitRegression.pkl" >&2
  echo "[INFO] Make sure to copy the model file before deployment" >&2
fi

# 바이너리 검증 (선택사항)
if command -v file >/dev/null 2>&1; then
  echo "Verifying binary compatibility..."
  if ls "${PYDIR}"/numpy/core/*.so >/dev/null 2>&1; then
    echo "Sample binary check (numpy):"
    file "${PYDIR}"/numpy/core/_multiarray_umath*.so 2>/dev/null | head -1 || true
  fi
fi

# Layer zip 생성
cd "${WORKDIR}" && zip -qr "${WORKDIR}/predictor-layer.zip" python

echo ""
echo "✅ Layer build complete!"
echo "Output: ${WORKDIR}/predictor-layer.zip"
echo ""
echo "Layer structure:"
echo "  python/"
echo "    └── Model_LogitRegression.pkl"
echo "    └── numpy/"
echo "    └── pandas/"
echo "    └── statsmodels/"
echo "    └── sklearn/"
echo "    └── ... (other dependencies)"
