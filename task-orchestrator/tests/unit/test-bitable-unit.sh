#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BITABLE_SCRIPT="${PROJECT_ROOT}/bitable-integration.sh"

TEST_TMP="$(mktemp -d)"
trap 'rm -rf "${TEST_TMP}"' EXIT

export BITABLE_BACKEND="local"
export BITABLE_DATA_ROOT="${TEST_TMP}/data"
export BITABLE_CACHE_DIR="${TEST_TMP}/cache"
export LOG_DIR="${TEST_TMP}/logs"
export DEBUG="0"

PASS=0
FAIL=0
TOTAL_FUNCTIONAL_COMMANDS=14
LAST_JSON=""

declare -A EXECUTED

mark_command() {
    local cmd="$1"
    EXECUTED["$cmd"]=1
}

run_cmd() {
    local cmd="$1"
    shift
    mark_command "$cmd"
    bash "${BITABLE_SCRIPT}" "$cmd" "$@"
}

run_json_cmd() {
    local cmd="$1"
    shift

    mark_command "$cmd"

    local raw
    raw="$(bash "${BITABLE_SCRIPT}" "$cmd" "$@")"

    LAST_JSON="$(python3 - "$raw" <<'PY'
import sys

text = sys.argv[1].strip().splitlines()
for line in reversed(text):
    line = line.strip()
    if line.startswith("{") and line.endswith("}"):
        print(line)
        raise SystemExit(0)

raise SystemExit(1)
PY
)"
}

assert_true() {
    local condition="$1"
    local message="$2"

    if eval "$condition"; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
        echo "[FAIL] ${message}" >&2
    fi
}

assert_json_expr() {
    local json_input="$1"
    local python_expr="$2"
    local message="$3"

    if python3 - "$python_expr" "$json_input" <<'PY'
import json
import sys

expr = sys.argv[1]
payload = json.loads(sys.argv[2])
if not eval(expr):
    raise SystemExit(1)
PY
    then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
        echo "[FAIL] ${message}" >&2
        echo "        JSON: ${json_input}" >&2
    fi
}

# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

run_cmd init >/dev/null

run_json_cmd create-task TASK-UT-001 document_analysis pending "agent-a,agent-b" 100
create_output="$LAST_JSON"
assert_json_expr "$create_output" 'payload["code"] == 0' "create-task should succeed"

run_json_cmd get-task TASK-UT-001
get_output="$LAST_JSON"
assert_json_expr "$get_output" 'payload["data"]["record"]["fields"]["task_id"] == "TASK-UT-001"' "get-task should return matching task_id"
assert_json_expr "$get_output" 'payload["data"]["record"]["fields"]["status"] == "pending"' "new task status should be pending"

run_cmd update-task TASK-UT-001 running "started" >/dev/null
run_cmd update-task TASK-UT-001 completed "done" >/dev/null

run_json_cmd get-task TASK-UT-001
updated_output="$LAST_JSON"
assert_json_expr "$updated_output" 'payload["data"]["record"]["fields"]["status"] == "completed"' "update-task should change status"
assert_json_expr "$updated_output" 'payload["data"]["record"]["fields"].get("completed_at", 0) > 0' "completed_at should be set"

run_json_cmd list-tasks
list_output="$LAST_JSON"
assert_json_expr "$list_output" 'len(payload["data"]["items"]) == 1' "list-tasks should return one task"

run_cmd record-execution EXEC-UT-001 document_analysis phase-1 agent-a completed 12 "/tmp/out" "ok" "result" >/dev/null
run_cmd record-metrics document_analysis 12 2 2 120 0 100 0 >/dev/null
run_cmd record-metrics tech_evaluation 20 3 2 180 1 80 1 >/dev/null
run_cmd record-error timeout "request timeout" "document_analysis" "agent-a" >/dev/null
run_cmd add-suggestion performance "parallelize" "split phases" high medium 8 >/dev/null

run_json_cmd get-summary
summary_output="$LAST_JSON"
assert_json_expr "$summary_output" 'payload["total_executions"] == 2' "get-summary should aggregate two metrics"
assert_json_expr "$summary_output" 'payload["total_error_count"] >= 1' "summary should include error counts"

run_json_cmd analyze-errors
analysis_output="$LAST_JSON"
assert_json_expr "$analysis_output" 'payload["total_patterns"] >= 1' "analyze-errors should find patterns"

run_json_cmd generate-recommendations
recommend_output="$LAST_JSON"
assert_json_expr "$recommend_output" 'len(payload["recommendations"]) >= 1' "generate-recommendations should output at least one recommendation"

run_cmd sync >/dev/null
run_cmd delete-task TASK-UT-001 >/dev/null

if bash "${BITABLE_SCRIPT}" get-task TASK-UT-001 >/dev/null 2>&1; then
    assert_true "false" "deleted task should not be retrievable"
else
    PASS=$((PASS + 1))
fi

functional_coverage=$(( ${#EXECUTED[@]} * 100 / TOTAL_FUNCTIONAL_COMMANDS ))
assert_true "[ ${functional_coverage} -ge 80 ]" "functional coverage must be >= 80%"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo "Unit test result: PASS=${PASS}, FAIL=${FAIL}, FunctionalCoverage=${functional_coverage}%"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
