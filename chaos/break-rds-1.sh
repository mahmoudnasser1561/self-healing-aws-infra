#!/bin/bash
# RDS-1: the database made publicly accessible.
set -euo pipefail
cd "$(dirname "$0")" && source lib.sh

dbid=${DB_ID:-self-healing-aws-infra-postgres}

compliant() {
  local public
  public=$(aws rds describe-db-instances --db-instance-identifier "$dbid" \
    --query 'DBInstances[0].PubliclyAccessible' --output text 2>/dev/null) || return 1
  [[ $public == False ]]
}

break_it() {
  aws rds modify-db-instance --db-instance-identifier "$dbid" \
    --publicly-accessible --apply-immediately >/dev/null
}

run RDS-1
