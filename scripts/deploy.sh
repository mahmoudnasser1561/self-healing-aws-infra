#!/bin/bash
set -euo pipefail

: "${PROJECT:?PROJECT must be set}"
build="${1:-dist}"

if [ ! -d "${build}" ]; then
  echo "build directory ${build} not found" >&2
  exit 1
fi

account=$(aws sts get-caller-identity --query Account --output text)
bucket="${PROJECT}-frontend-${account}"

distribution=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='${PROJECT}'].Id | [0]" --output text)
if [ -z "${distribution}" ] || [ "${distribution}" = "None" ]; then
  echo "no CloudFront distribution found for ${PROJECT}" >&2
  exit 1
fi

aws s3 sync "${build}" "s3://${bucket}" --delete

invalidation=$(aws cloudfront create-invalidation \
  --distribution-id "${distribution}" --paths "/*" \
  --query Invalidation.Id --output text)
aws cloudfront wait invalidation-completed \
  --distribution-id "${distribution}" --id "${invalidation}"

domain=$(aws cloudfront get-distribution --id "${distribution}" \
  --query Distribution.DomainName --output text)
echo "deployed to https://${domain}"
