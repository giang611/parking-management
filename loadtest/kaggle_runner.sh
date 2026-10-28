#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
USERS="${USERS:-10}"
SPAWN_RATE="${SPAWN_RATE:-2}"
RUN_TIME="${RUN_TIME:-60s}"
RESULTS_ROOT="${RESULTS_DIR:-$PROJECT_ROOT/docs/benchmarks}"
RUN_TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

: "${ADMIN_USERNAME:?Set ADMIN_USERNAME in the Kaggle environment.}"
: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD in the Kaggle environment.}"
command -v python >/dev/null || { echo "python is required." >&2; exit 2; }
command -v locust >/dev/null || {
    echo "Locust is missing. Install with: python -m pip install -r requirements-loadtest.txt" >&2
    exit 2
}
[[ "$USERS" =~ ^[1-9][0-9]*$ ]] || { echo "USERS must be a positive integer." >&2; exit 2; }
python - "$SPAWN_RATE" <<'PY'
import sys

try:
    value = float(sys.argv[1])
except ValueError:
    raise SystemExit("SPAWN_RATE must be a positive number.")
if value <= 0:
    raise SystemExit("SPAWN_RATE must be a positive number.")
PY

if [[ "$RESULTS_ROOT" != /* ]]; then
    RESULTS_ROOT="$PROJECT_ROOT/$RESULTS_ROOT"
fi
mkdir -p "$RESULTS_ROOT"
RUN_DIR="$(mktemp -d "$RESULTS_ROOT/${RUN_TIMESTAMP}-XXXXXXXX")"
RUN_ID="${RUN_DIR##*/}"

python - "$BASE_URL" <<'PY'
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen

url = sys.argv[1].rstrip("/") + "/health"
try:
    with urlopen(url, timeout=5) as response:
        body = json.loads(response.read().decode("utf-8"))
except (OSError, URLError, ValueError) as error:
    raise SystemExit(f"Backend health check failed at {url}: {error}")
if body.get("status") != "ok":
    raise SystemExit(f"Backend returned an unexpected health response: {body}")
PY

python - "$RUN_DIR/environment.txt" "$RUN_ID" "$BASE_URL" "$USERS" "$SPAWN_RATE" "$RUN_TIME" <<'PY'
import os
import platform
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

output_path, run_id, base_url, users, spawn_rate, run_time = sys.argv[1:]
parsed = urlsplit(base_url)
safe_url = f"{parsed.scheme}://{parsed.hostname or ''}"
if parsed.port:
    safe_url += f":{parsed.port}"
safe_url += parsed.path
revision = "unavailable"
if shutil.which("git"):
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    if result.returncode == 0:
        revision = result.stdout.strip()
lines = [
    f"Run ID UTC: {run_id}",
    f"Target: {safe_url}",
    f"Users: {users}",
    f"Spawn rate (users/sec): {spawn_rate}",
    f"Run time: {run_time}",
    f"Python: {platform.python_version()}",
    f"Locust: {subprocess.check_output(['locust', '--version'], text=True).strip()}",
    f"Platform: {platform.platform()}",
    f"CPU count: {os.cpu_count()}",
    f"Git revision: {revision}",
]
try:
    lines.extend(["", "CPU details:", subprocess.check_output(["lscpu"], text=True).strip()])
except (OSError, subprocess.CalledProcessError):
    pass
try:
    with open("/proc/meminfo", encoding="utf-8") as memory:
        lines.extend(["", "Memory:", memory.read().strip()])
except OSError:
    pass
with open(output_path, "w", encoding="utf-8") as output:
    output.write("\n".join(lines) + "\n")
PY

CSV_PREFIX="$RUN_DIR/locust"
set +e
locust \
    --locustfile "$PROJECT_ROOT/loadtest/locustfile.py" \
    --host "$BASE_URL" \
    --headless \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --stop-timeout 10 \
    --only-summary \
    --csv "$CSV_PREFIX" \
    --csv-full-history \
    --html "$RUN_DIR/report.html" \
    --exit-code-on-error 1 \
    2>&1 | tee "$RUN_DIR/locust.log"
LOCUST_EXIT_CODE=${PIPESTATUS[0]}
set -e

python - "$RUN_DIR/locust_stats.csv" "$RUN_DIR/summary.md" "$RUN_ID" "$RUN_DIR" <<'PY'
import csv
import os
import sys

csv_path, summary_path, run_id, run_dir = sys.argv[1:]
with open(csv_path, newline="", encoding="utf-8") as source:
    rows = list(csv.DictReader(source))
aggregate = next((row for row in rows if row.get("Name", "").lower() == "aggregated"), None)
if aggregate is None:
    raise SystemExit(f"Locust aggregate row missing from {csv_path}")
metrics = [
    ("Requests", "Request Count"),
    ("Failures", "Failure Count"),
    ("Throughput (requests/sec)", "Requests/s"),
    ("Failure rate (failures/sec)", "Failures/s"),
    ("Average response time (ms)", "Average Response Time"),
    ("Median response time (ms)", "Median Response Time"),
    ("95th percentile (ms)", "95%"),
    ("Maximum response time (ms)", "Max Response Time"),
]
lines = [
    f"# Kaggle CPU baseline {run_id}",
    "",
    "See `environment.txt` for hardware, runtime, and load settings.",
    "The API and Locust load generator run on the same Kaggle runtime unless the run configuration says otherwise.",
    "",
    "| Metric | Result |",
    "|---|---:|",
]
lines.extend(f"| {label} | {aggregate.get(column, 'n/a')} |" for label, column in metrics)
lines.extend(["", "Artifacts: `locust_stats.csv`, `locust_stats_history.csv`, `locust_failures.csv`, `report.html`, `locust.log`."])
with open(summary_path, "w", encoding="utf-8") as output:
    output.write("\n".join(lines) + "\n")
print(f"Benchmark artifacts saved to {os.path.abspath(run_dir)}")
PY

exit "$LOCUST_EXIT_CODE"
