#!/usr/bin/env bash
set -euo pipefail

ROLE_NAME="lambda-execution-role"

# Trust policy
cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
if aws iam get-role --role-name "${ROLE_NAME}" >/dev/null 2>&1; then
  echo "✓ Role '${ROLE_NAME}' already exists"
else
  aws iam create-role \
    --role-name "${ROLE_NAME}" \
    --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
    --output text >/dev/null
  echo "✓ Role '${ROLE_NAME}' created"
fi

# Attach policy
POLICY_ARN="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
if aws iam list-attached-role-policies --role-name "${ROLE_NAME}" --query "AttachedPolicies[?PolicyArn=='${POLICY_ARN}']" --output text | grep -q "${POLICY_ARN}"; then
  echo "✓ Policy already attached"
else
  aws iam attach-role-policy --role-name "${ROLE_NAME}" --policy-arn "${POLICY_ARN}"
  echo "✓ Policy attached"
fi

ROLE_ARN=$(aws iam get-role --role-name "${ROLE_NAME}" --query 'Role.Arn' --output text)
echo ""
echo "Role ARN: ${ROLE_ARN}"

rm -f /tmp/lambda-trust-policy.json

