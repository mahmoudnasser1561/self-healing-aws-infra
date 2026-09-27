#!/bin/bash
# S3-1: Block Public Access removed on the frontend bucket.
set -euo pipefail
cd "$(dirname "$0")" && source lib.sh

account=$(aws sts get-caller-identity --query Account --output text)
bucket=${BUCKET:-self-healing-aws-infra-frontend-$account}

compliant() {
  local flags
  flags=$(aws s3api get-public-access-block --bucket "$bucket" \
    --query 'PublicAccessBlockConfiguration.*' --output text 2>/dev/null) || return 1
  [[ $flags != *False* ]]
}

break_it() {
  aws s3api delete-public-access-block --bucket "$bucket"
}

run S3-1
