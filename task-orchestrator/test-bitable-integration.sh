#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BITABLE_SCRIPT="${PROJECT_ROOT}/bitable-integration.sh"
MOCK_SERVER="${PROJECT_ROOT}/tests/integration/mock_feishu_bitable_server.py"

PORT="${BITABLE_MOCK_PORT:-18080}"
TEST_TMP="$(mktemp -d)"
MOCK_PID=""

cleanup() {
    if [[ -n "$MOCK_PID" ]]; then
        kill "$MOCK_PID" >/dev/null 2>&1 || true
    fi
    rm -rf "$TEST_TMP"
}
trap cleanup EXIT

start_mock_server() {
    python3 "$MOCK_SERVER" --port "$PORT" >"${TEST_TMP}/mock.log" 2>&1 &
    MOCK_PID=$!

    # wait until server is up
    for _ in $(seq 1 30); do
        if curl -s "http://127.0.0.1:${PORT}/open-apis/auth/v3/tenant_access_token/internal" >/dev/null 2>&1; then
            return 0
        fi
        sleep 0.2
    done

    echo "Failed to start mock Feishu server" >&2
    return 1
}

run_cmd() {
    local cmd="$1"
    shift
    bash "$BITABLE_SCRIPT" "$cmd" "$@"
}

run_json_cmd() {
    local cmd="$1"
    shift

    local raw
    raw="$(run_cmd "$cmd" "$@")"

    python3 - "$raw" <<'PY'
import sys

text = sys.argv[1].strip().splitlines()
for line in reversed(text):
    line = line.strip()
    if line.startswith("{") and line.endswith("}"):
        print(line)
        raise SystemExit(0)

raise SystemExit(1)
PY
}

assert_json() {
    local json_input="$1"
    local py_expr="$2"
    local message="$3"

    if python3 - "$py_expr" "$json_input" <<'PY'
import json
import sys

expr = sys.argv[1]
payload = json.loads(sys.argv[2])
if not eval(expr):
    raise SystemExit(1)
PY
    then
        echo "[PASS] ${message}"
    else
        echo "[FAIL] ${message}" >&2
        echo "       JSON=${json_input}" >&2
        exit 1
    fi
}

main() {
    start_mock_server

    export BITABLE_BACKEND="api"
    export BITABLE_API_BASE="http://127.0.0.1:${PORT}/open-apis"
    export BITABLE_APP_ID="cli_a"
    export BITABLE_APP_SECRET="cli_s"
    export BITABLE_APP_TOKEN="app_mock"
    export BITABLE_HTTP_TIMEOUT="5"
    export BITABLE_MAX_RETRIES="3"
    export BITABLE_CACHE_DIR="${TEST_TMP}/cache"
    export LOG_DIR="${TEST_TMP}/logs"

    run_cmd init >/dev/null

    # CRUD
    create_out="$(run_json_cmd create-task TASK-IT-001 document_analysis pending "agent1,agent2" 200)"
    assert_json "$create_out" 'payload["code"] == 0' "create-task should succeed in API mode"

    get_out="$(run_json_cmd get-task TASK-IT-001)"
    assert_json "$get_out" 'payload["data"]["record"]["fields"]["task_id"] == "TASK-IT-001"' "get-task should fetch API record"

    run_cmd update-task TASK-IT-001 completed "ok" >/dev/null
    get_updated="$(run_json_cmd get-task TASK-IT-001)"
    assert_json "$get_updated" 'payload["data"]["record"]["fields"]["status"] == "completed"' "update-task should patch API record"

    list_out="$(run_json_cmd list-tasks)"
    assert_json "$list_out" 'len(payload["data"]["items"]) == 1' "list-tasks should list API records"

    run_cmd delete-task TASK-IT-001 >/dev/null
    if run_cmd get-task TASK-IT-001 >/dev/null 2>&1; then
        echo "[FAIL] get-task should fail after delete" >&2
        exit 1
    fi
    echo "[PASS] delete-task should remove API record"

    # Persistence models
    run_cmd record-execution EXEC-IT-001 document_analysis phase-2 agent2 completed 45 "/tmp/out" "ok" "result" >/dev/null
    run_cmd record-metrics document_analysis 45 3 2 600 0 100 0 >/dev/null
    run_cmd record-metrics document_analysis 60 3 2 700 1 90 1 >/dev/null
    run_cmd record-error timeout "phase timeout" "document_analysis" "agent2" >/dev/null

    summary_out="$(run_json_cmd get-summary document_analysis)"
    assert_json "$summary_out" 'payload["total_executions"] == 2' "summary should aggregate API metrics"

    analysis_out="$(run_json_cmd analyze-errors)"
    assert_json "$analysis_out" 'payload["total_patterns"] >= 1' "analyze-errors should work in API mode"

    # Performance benchmark
    local n=50
    local start_ms end_ms elapsed_ms
    start_ms="$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)"

    for i in $(seq 1 "$n"); do
        run_cmd record-metrics benchmark_flow "$i" 2 2 100 0 100 0 >/dev/null
    done

    end_ms="$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)"
    elapsed_ms=$((end_ms - start_ms))

    if [[ "$elapsed_ms" -le 0 ]]; then
        echo "[FAIL] invalid benchmark elapsed time" >&2
        exit 1
    fi

    local throughput
    throughput="$(python3 - "$n" "$elapsed_ms" <<'PY'
import sys
n = float(sys.argv[1])
elapsed_ms = float(sys.argv[2])
print(round((n * 1000.0) / elapsed_ms, 2))
PY
)"

    echo "[PASS] benchmark: ${n} metric writes in ${elapsed_ms} ms (${throughput} ops/sec)"

    if [[ "$elapsed_ms" -gt 15000 ]]; then
        echo "[FAIL] benchmark exceeded threshold (15s)" >&2
        exit 1
    fi

    echo "Integration test completed successfully"
}

main "$@"
