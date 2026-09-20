#!/bin/bash
set -euo pipefail

: "${ASG_NAME:?ASG_NAME must be set}"
attempts="${ATTEMPTS:-90}"
interval="${INTERVAL:-10}"

command_id=$(aws ssm send-command \
  --document-name AWS-RunShellScript \
  --targets "Key=tag:aws:autoscaling:groupName,Values=${ASG_NAME}" \
  --parameters 'commands=["/usr/local/bin/deploy-release"]' \
  --max-concurrency 1 \
  --max-errors 0 \
  --query Command.CommandId --output text)
echo "command ${command_id}"

statuses=""
for _ in $(seq "${attempts}"); do
  statuses=$(aws ssm list-command-invocations \
    --command-id "${command_id}" \
    --query 'CommandInvocations[].Status' --output text)
  echo "statuses: ${statuses:-none yet}"
  if [ -n "${statuses}" ] && ! echo "${statuses}" | grep -q -E "Pending|InProgress|Delayed"; then
    break
  fi
  sleep "${interval}"
done

if [ -z "${statuses}" ] || echo "${statuses}" | tr '\t' '\n' | grep -q -v -x "Success"; then
  echo "deploy did not succeed on every instance" >&2
  exit 1
fi
