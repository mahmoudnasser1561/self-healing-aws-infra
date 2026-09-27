#!/bin/bash
# SG-1: port 22 opened to the world on the app tier's security group.
set -euo pipefail
cd "$(dirname "$0")" && source lib.sh

group=${GROUP_ID:-$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=self-healing-aws-infra-app \
  --query 'SecurityGroups[0].GroupId' --output text)}

compliant() {
  local open
  open=$(aws ec2 describe-security-group-rules \
    --filters Name=group-id,Values="$group" \
    --query 'length(SecurityGroupRules[?IsEgress==`false` && CidrIpv4==`0.0.0.0/0`])' \
    --output text 2>/dev/null) || return 1
  [[ $open == 0 ]]
}

break_it() {
  aws ec2 authorize-security-group-ingress \
    --group-id "$group" --protocol tcp --port 22 --cidr 0.0.0.0/0 >/dev/null
}

run SG-1
