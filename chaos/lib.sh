# Shared by the break-*.sh scripts: time a resource from broken to fixed.
# Each script defines compliant() and break_it(), then calls run <rule-id>.

log=results.log

now() { date -u +%FT%TZ; }

run() {
  local rule=$1 timeout=${TIMEOUT:-60}

  compliant || { echo "not compliant before the run" >&2; exit 1; }

  local run_id t0
  run_id=$(date -u +%Y%m%dT%H%M%SZ)
  t0=$(now)
  echo "run ${run_id} rule ${rule} broken at ${t0}"
  break_it

  SECONDS=0
  until compliant; do
    if (( SECONDS > timeout )); then
      echo "result run=${run_id} rule=${rule} outcome=timeout seconds=${SECONDS}" | tee -a "$log"
      exit 1
    fi
    sleep 1
  done

  echo "result run=${run_id} rule=${rule} outcome=remediated t0=${t0} t2=$(now) seconds=${SECONDS}" | tee -a "$log"
}
