#!/bin/bash
set -euo pipefail

set -a
. /etc/app.env
set +a

exec 9>/var/lock/deploy-release.lock
flock 9

version="${1:-latest}"

aws s3 cp "s3://$RELEASE_BUCKET/releases/$version.tar.gz" /tmp/release.tar.gz --only-show-errors
rm -rf /opt/app/src
mkdir /opt/app/src
tar -xzf /tmp/release.tar.gz -C /opt/app/src
python3.11 -m venv /opt/app/venv
/opt/app/venv/bin/pip install --quiet --disable-pip-version-check -r /opt/app/src/requirements.txt
chown -R app:app /opt/app

systemctl restart app
for _ in $(seq 30); do
  curl -fs http://127.0.0.1:8000/api/health >/dev/null && exit 0
  sleep 2
done

echo "release failed its health check" >&2
exit 1
