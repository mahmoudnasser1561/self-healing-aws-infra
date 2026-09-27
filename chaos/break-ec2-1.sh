#!/bin/bash
# EC2-1: an instance's metadata service downgraded off IMDSv2.
set -euo pipefail
cd "$(dirname "$0")" && source lib.sh

instance=${INSTANCE_ID:-$(aws ec2 describe-instances \
  --filters Name=tag:aws:autoscaling:groupName,Values=self-healing-aws-infra-app \
            Name=instance-state-name,Values=running \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)}

compliant() {
  local tokens
  tokens=$(aws ec2 describe-instances --instance-ids "$instance" \
    --query 'Reservations[0].Instances[0].MetadataOptions.HttpTokens' \
    --output text 2>/dev/null) || return 1
  [[ $tokens == required ]]
}

break_it() {
  aws ec2 modify-instance-metadata-options --instance-id "$instance" \
    --http-tokens optional --http-endpoint enabled >/dev/null
}

run EC2-1
