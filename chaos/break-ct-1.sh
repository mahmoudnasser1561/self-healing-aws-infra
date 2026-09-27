#!/bin/bash
# CT-1: CloudTrail logging stopped.
set -euo pipefail
cd "$(dirname "$0")" && source lib.sh

trail=${TRAIL_NAME:-self-healing-aws-infra}

compliant() {
  local logging
  logging=$(aws cloudtrail get-trail-status --name "$trail" \
    --query IsLogging --output text 2>/dev/null) || return 1
  [[ $logging == True ]]
}

break_it() {
  aws cloudtrail stop-logging --name "$trail"
}

run CT-1
