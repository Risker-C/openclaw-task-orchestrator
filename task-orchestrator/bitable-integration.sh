#!/usr/bin/env bash

# Bitable Integration Module for Task Orchestrator
# Version: V0.0.4
# Purpose: Provide connection management + CRUD persistence for orchestrator runtime data

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

BITABLE_BACKEND="${BITABLE_BACKEND:-auto}"                     # auto|local|api
BITABLE_API_BASE="${BITABLE_API_BASE:-https://open.feishu.cn/open-apis}"
BITABLE_APP_ID="${BITABLE_APP_ID:-}"
BITABLE_APP_SECRET="${BITABLE_APP_SECRET:-}"
BITABLE_APP_TOKEN="${BITABLE_APP_TOKEN:-}"

# API tuning
BITABLE_HTTP_TIMEOUT="${BITABLE_HTTP_TIMEOUT:-15}"
BITABLE_MAX_RETRIES="${BITABLE_MAX_RETRIES:-3}"
BITABLE_PAGE_SIZE="${BITABLE_PAGE_SIZE:-200}"

# Local persistence paths
BITABLE_DATA_ROOT="${BITABLE_DATA_ROOT:-/tmp/task-orchestrator/bitable}"
BITABLE_CACHE_DIR="${BITABLE_CACHE_DIR:-/tmp/task-orchestrator/cache}"
LOG_DIR="${LOG_DIR:-/tmp/task-orchestrator/logs}"
BITABLE_LOG="${LOG_DIR}/bitable-integration.log"

# Table IDs (for API mode). Defaults are stable logical names for local/mock usage.
BITABLE_TABLE_TASK_RECORDS="${BITABLE_TABLE_TASK_RECORDS:-tbl_task_records}"
BITABLE_TABLE_WORKFLOW_EXECUTIONS="${BITABLE_TABLE_WORKFLOW_EXECUTIONS:-tbl_workflow_executions}"
BITABLE_TABLE_PERFORMANCE_METRICS="${BITABLE_TABLE_PERFORMANCE_METRICS:-tbl_performance_metrics}"
BITABLE_TABLE_ERROR_PATTERNS="${BITABLE_TABLE_ERROR_PATTERNS:-tbl_error_patterns}"
BITABLE_TABLE_OPTIMIZATION_SUGGESTIONS="${BITABLE_TABLE_OPTIMIZATION_SUGGESTIONS:-tbl_optimization_suggestions}"

ACTIVE_BACKEND=""
TOKEN_CACHE_FILE="${BITABLE_CACHE_DIR}/tenant-token.json"

# shellcheck disable=SC2034
declare -A TABLE_ID_MAP=(
    [task_records]="${BITABLE_TABLE_TASK_RECORDS}"
    [workflow_executions]="${BITABLE_TABLE_WORKFLOW_EXECUTIONS}"
    [performance_metrics]="${BITABLE_TABLE_PERFORMANCE_METRICS}"
    [error_patterns]="${BITABLE_TABLE_ERROR_PATTERNS}"
    [optimization_suggestions]="${BITABLE_TABLE_OPTIMIZATION_SUGGESTIONS}"
)

# ============================================================================
# Logging
# ============================================================================

log_info() {
    local message="$1"
    mkdir -p "${LOG_DIR}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] ${message}" | tee -a "${BITABLE_LOG}"
}

log_error() {
    local message="$1"
    mkdir -p "${LOG_DIR}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] ${message}" | tee -a "${BITABLE_LOG}" >&2
}

log_debug() {
    local message="$1"
    if [[ "${DEBUG:-0}" == "1" ]]; then
        mkdir -p "${LOG_DIR}"
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] [DEBUG] ${message}" | tee -a "${BITABLE_LOG}"
    fi
}

# ============================================================================
# Utility
# ============================================================================

now_iso_utc() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

now_epoch_ms() {
    python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
}

require_dependency() {
    local bin="$1"
    if ! command -v "$bin" >/dev/null 2>&1; then
        log_error "Required dependency missing: $bin"
        return 1
    fi
}

urlencode() {
    local value="$1"
    python3 - "$value" <<'PY'
import sys
from urllib.parse import quote
print(quote(sys.argv[1], safe=""))
PY
}

json_validate_object() {
    local payload="$1"
    python3 - "$payload" <<'PY'
import json
import sys

try:
    value = json.loads(sys.argv[1])
except json.JSONDecodeError:
    raise SystemExit(1)

if not isinstance(value, dict):
    raise SystemExit(1)
PY
}

json_merge_objects() {
    local base_json="$1"
    local patch_json="$2"

    python3 - "$base_json" "$patch_json" <<'PY'
import json
import sys

base = json.loads(sys.argv[1])
patch = json.loads(sys.argv[2])

if not isinstance(base, dict) or not isinstance(patch, dict):
    raise SystemExit("Both base and patch must be JSON objects")

base.update(patch)
print(json.dumps(base, ensure_ascii=False, separators=(",", ":")))
PY
}

csv_to_json_array() {
    local csv_value="$1"
    python3 - "$csv_value" <<'PY'
import json
import sys

items = [item.strip() for item in sys.argv[1].split(",") if item.strip()]
print(json.dumps(items, ensure_ascii=False, separators=(",", ":")))
PY
}

json_extract_code() {
    local body="$1"
    python3 - "$body" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("-1")
    raise SystemExit(0)

print(payload.get("code", -1))
PY
}

json_extract_message() {
    local body="$1"
    python3 - "$body" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("invalid-json")
    raise SystemExit(0)

print(payload.get("msg", ""))
PY
}

json_extract_first_record_id() {
    local body="$1"
    python3 - "$body" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("")
    raise SystemExit(0)

record = payload.get("data", {}).get("record")
if isinstance(record, dict):
    print(record.get("record_id", ""))
    raise SystemExit(0)

items = payload.get("data", {}).get("items", [])
if items and isinstance(items[0], dict):
    print(items[0].get("record_id", ""))
else:
    print("")
PY
}

# ============================================================================
# Runtime / Backend Selection
# ============================================================================

resolve_backend() {
    case "${BITABLE_BACKEND}" in
        local|api)
            printf '%s' "${BITABLE_BACKEND}"
            ;;
        auto)
            if [[ -n "${BITABLE_APP_ID}" && -n "${BITABLE_APP_SECRET}" && -n "${BITABLE_APP_TOKEN}" ]]; then
                printf '%s' "api"
            else
                printf '%s' "local"
            fi
            ;;
        *)
            log_error "Invalid BITABLE_BACKEND: ${BITABLE_BACKEND} (expected auto|local|api)"
            return 1
            ;;
    esac
}

ensure_runtime() {
    mkdir -p "${LOG_DIR}" "${BITABLE_CACHE_DIR}" "${BITABLE_DATA_ROOT}"
    if [[ -z "${ACTIVE_BACKEND}" ]]; then
        ACTIVE_BACKEND="$(resolve_backend)"
        log_debug "Selected backend: ${ACTIVE_BACKEND}"
    fi
}

table_id_for() {
    local logical_table="$1"
    if [[ -z "${TABLE_ID_MAP[$logical_table]:-}" ]]; then
        log_error "Unknown logical table: ${logical_table}"
        return 1
    fi
    printf '%s' "${TABLE_ID_MAP[$logical_table]}"
}

# ============================================================================
# API Backend (Feishu REST)
# ============================================================================

http_request_with_retry() {
    local method="$1"
    local url="$2"
    local token="${3:-}"
    local payload="${4:-}"

    local attempt=1
    local delay=1

    while (( attempt <= BITABLE_MAX_RETRIES )); do
        local body_file
        body_file="$(mktemp)"

        local -a curl_cmd=(
            curl --silent --show-error --location
            --request "$method"
            --connect-timeout "${BITABLE_HTTP_TIMEOUT}"
            --max-time "${BITABLE_HTTP_TIMEOUT}"
            --write-out "%{http_code}"
            --output "${body_file}"
            --header "Content-Type: application/json; charset=utf-8"
        )

        if [[ -n "$token" ]]; then
            curl_cmd+=(--header "Authorization: Bearer ${token}")
        fi

        if [[ -n "$payload" ]]; then
            curl_cmd+=(--data "$payload")
        fi

        curl_cmd+=("$url")

        local http_code
        local curl_status=0

        if ! http_code="$("${curl_cmd[@]}")"; then
            curl_status=$?
            http_code="000"
        fi

        local response_body
        response_body="$(cat "${body_file}")"
        rm -f "${body_file}"

        log_debug "HTTP ${method} ${url} -> status=${http_code} (attempt ${attempt})"

        if [[ "${curl_status}" -ne 0 ]]; then
            if (( attempt == BITABLE_MAX_RETRIES )); then
                log_error "HTTP request failed after ${attempt} attempts: ${method} ${url}"
                return 1
            fi
        elif [[ "${http_code}" =~ ^2[0-9][0-9]$ ]]; then
            printf '%s' "$response_body"
            return 0
        elif [[ "${http_code}" == "429" || "${http_code}" =~ ^5[0-9][0-9]$ ]]; then
            if (( attempt == BITABLE_MAX_RETRIES )); then
                log_error "Server error after retries: HTTP ${http_code}, body=${response_body}"
                return 1
            fi
        else
            log_error "Unexpected HTTP status ${http_code}, body=${response_body}"
            return 1
        fi

        sleep "$delay"
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done

    return 1
}

fetch_tenant_access_token() {
    local auth_payload
    auth_payload=$(cat <<EOF
{"app_id":"${BITABLE_APP_ID}","app_secret":"${BITABLE_APP_SECRET}"}
EOF
)

    local body
    body="$(http_request_with_retry "POST" "${BITABLE_API_BASE}/auth/v3/tenant_access_token/internal" "" "${auth_payload}")"

    local code
    code="$(json_extract_code "$body")"
    if [[ "$code" != "0" ]]; then
        log_error "Failed to get tenant access token: code=${code}, msg=$(json_extract_message "$body")"
        return 1
    fi

    python3 - "${TOKEN_CACHE_FILE}" "$body" <<'PY'
import json
import time
import sys
from pathlib import Path

out_file = Path(sys.argv[1])
payload = json.loads(sys.argv[2])
out_file.parent.mkdir(parents=True, exist_ok=True)

token = payload["tenant_access_token"]
expire_seconds = int(payload.get("expire", 7200))
expires_at = int(time.time()) + max(60, expire_seconds - 60)

out_file.write_text(json.dumps({
    "tenant_access_token": token,
    "expires_at": expires_at,
}, ensure_ascii=False), encoding="utf-8")

print(token)
PY
}

get_tenant_access_token() {
    if [[ -f "${TOKEN_CACHE_FILE}" ]]; then
        local cached
        cached="$(python3 - "${TOKEN_CACHE_FILE}" <<'PY'
import json
import time
import sys

try:
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        payload = json.load(f)
except Exception:
    print("")
    raise SystemExit(0)

if int(payload.get("expires_at", 0)) > int(time.time()):
    print(payload.get("tenant_access_token", ""))
else:
    print("")
PY
)"
        if [[ -n "$cached" ]]; then
            printf '%s' "$cached"
            return 0
        fi
    fi

    fetch_tenant_access_token
}

api_call() {
    local method="$1"
    local path="$2"
    local payload="${3:-}"

    local token
    token="$(get_tenant_access_token)"

    local body
    body="$(http_request_with_retry "$method" "${BITABLE_API_BASE}${path}" "$token" "$payload")"

    local code
    code="$(json_extract_code "$body")"

    if [[ "$code" == "0" ]]; then
        printf '%s' "$body"
        return 0
    fi

    # Token expired / invalid token: refresh once
    if [[ "$code" == "99991663" || "$code" == "99991664" ]]; then
        rm -f "${TOKEN_CACHE_FILE}"
        token="$(get_tenant_access_token)"
        body="$(http_request_with_retry "$method" "${BITABLE_API_BASE}${path}" "$token" "$payload")"
        code="$(json_extract_code "$body")"
        if [[ "$code" == "0" ]]; then
            printf '%s' "$body"
            return 0
        fi
    fi

    log_error "Feishu API failed: code=${code}, msg=$(json_extract_message "$body")"
    return 1
}

validate_api_config() {
    if [[ -z "${BITABLE_APP_ID}" || -z "${BITABLE_APP_SECRET}" || -z "${BITABLE_APP_TOKEN}" ]]; then
        log_error "API mode requires BITABLE_APP_ID, BITABLE_APP_SECRET, BITABLE_APP_TOKEN"
        return 1
    fi

    local logical_table
    for logical_table in "${!TABLE_ID_MAP[@]}"; do
        if [[ -z "${TABLE_ID_MAP[$logical_table]}" ]]; then
            log_error "Missing table mapping for ${logical_table}"
            return 1
        fi
    done

    return 0
}

api_verify_tables() {
    local logical_table
    for logical_table in "${!TABLE_ID_MAP[@]}"; do
        local table_id
        table_id="$(table_id_for "$logical_table")"
        api_call "GET" "/bitable/v1/apps/${BITABLE_APP_TOKEN}/tables/${table_id}" >/dev/null
        log_debug "Verified table: ${logical_table} (${table_id})"
    done
}

api_create_record() {
    local logical_table="$1"
    local fields_json="$2"

    local table_id
    table_id="$(table_id_for "$logical_table")"

    local payload
    payload=$(cat <<EOF
{"fields":${fields_json}}
EOF
)

    api_call "POST" "/bitable/v1/apps/${BITABLE_APP_TOKEN}/tables/${table_id}/records" "$payload"
}

api_get_record() {
    local logical_table="$1"
    local record_id="$2"

    local table_id
    table_id="$(table_id_for "$logical_table")"

    api_call "GET" "/bitable/v1/apps/${BITABLE_APP_TOKEN}/tables/${table_id}/records/${record_id}"
}

api_update_record() {
    local logical_table="$1"
    local record_id="$2"
    local fields_json="$3"

    local table_id
    table_id="$(table_id_for "$logical_table")"

    local payload
    payload=$(cat <<EOF
{"fields":${fields_json}}
EOF
)

    api_call "PATCH" "/bitable/v1/apps/${BITABLE_APP_TOKEN}/tables/${table_id}/records/${record_id}" "$payload"
}

api_delete_record() {
    local logical_table="$1"
    local record_id="$2"

    local table_id
    table_id="$(table_id_for "$logical_table")"

    api_call "DELETE" "/bitable/v1/apps/${BITABLE_APP_TOKEN}/tables/${table_id}/records/${record_id}"
}

api_list_records_all() {
    local logical_table="$1"
    local table_id
    table_id="$(table_id_for "$logical_table")"

    local page_token=""
    local all_items='[]'

    while true; do
        local path
        path="/bitable/v1/apps/${BITABLE_APP_TOKEN}/tables/${table_id}/records?page_size=${BITABLE_PAGE_SIZE}"
        if [[ -n "$page_token" ]]; then
            path+="&page_token=$(urlencode "$page_token")"
        fi

        local body
        body="$(api_call "GET" "$path")"

        local parsed
        parsed="$(python3 - "$body" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
data = payload.get("data", {})
print(json.dumps({
    "items": data.get("items", []),
    "has_more": bool(data.get("has_more", False)),
    "page_token": data.get("page_token", ""),
}, ensure_ascii=False, separators=(",", ":")))
PY
)"

        all_items="$(python3 - "$all_items" "$parsed" <<'PY'
import json
import sys

all_items = json.loads(sys.argv[1])
parsed = json.loads(sys.argv[2])
all_items.extend(parsed.get("items", []))
print(json.dumps(all_items, ensure_ascii=False, separators=(",", ":")))
PY
)"

        local has_more
        has_more="$(python3 - "$parsed" <<'PY'
import json
import sys
print("true" if json.loads(sys.argv[1]).get("has_more") else "false")
PY
)"

        if [[ "$has_more" != "true" ]]; then
            break
        fi

        page_token="$(python3 - "$parsed" <<'PY'
import json
import sys
print(json.loads(sys.argv[1]).get("page_token", ""))
PY
)"
    done

    cat <<EOF
{"code":0,"msg":"success","data":{"items":${all_items},"has_more":false,"page_token":""}}
EOF
}

api_find_record_id_by_field() {
    local logical_table="$1"
    local field_name="$2"
    local field_value="$3"

    local table_id
    table_id="$(table_id_for "$logical_table")"

    local escaped_value
    escaped_value="${field_value//\"/\\\"}"
    local filter_expr="CurrentValue.[${field_name}]=\"${escaped_value}\""

    local path
    path="/bitable/v1/apps/${BITABLE_APP_TOKEN}/tables/${table_id}/records?page_size=1&filter=$(urlencode "$filter_expr")"

    local body
    body="$(api_call "GET" "$path")"

    local record_id
    record_id="$(json_extract_first_record_id "$body")"

    if [[ -z "$record_id" ]]; then
        return 1
    fi

    printf '%s' "$record_id"
}

# ============================================================================
# Local Backend (File-based persistence)
# ============================================================================

local_table_dir() {
    local logical_table="$1"
    printf '%s' "${BITABLE_DATA_ROOT}/${logical_table}"
}

local_init_tables() {
    local logical_table
    for logical_table in "${!TABLE_ID_MAP[@]}"; do
        mkdir -p "$(local_table_dir "$logical_table")"
    done
}

local_generate_record_id() {
    python3 - <<'PY'
import time
print(f"rec_{int(time.time() * 1000)}")
PY
}

local_record_path() {
    local logical_table="$1"
    local record_id="$2"
    printf '%s' "$(local_table_dir "$logical_table")/${record_id}.json"
}

local_create_record() {
    local logical_table="$1"
    local fields_json="$2"

    local record_id
    record_id="$(local_generate_record_id)"

    local record_path
    record_path="$(local_record_path "$logical_table" "$record_id")"

    local now
    now="$(now_iso_utc)"

    python3 - "$record_path" "$record_id" "$fields_json" "$now" <<'PY'
import json
import sys
from pathlib import Path

record_path = Path(sys.argv[1])
record_id = sys.argv[2]
fields = json.loads(sys.argv[3])
now = sys.argv[4]

record_path.parent.mkdir(parents=True, exist_ok=True)
record_path.write_text(json.dumps({
    "record_id": record_id,
    "fields": fields,
    "created_at": now,
    "updated_at": now,
    "synced_to_api": False,
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({
    "code": 0,
    "msg": "success",
    "data": {
        "record": {
            "record_id": record_id,
            "fields": fields,
        }
    }
}, ensure_ascii=False))
PY
}

local_get_record() {
    local logical_table="$1"
    local record_id="$2"

    local record_path
    record_path="$(local_record_path "$logical_table" "$record_id")"

    if [[ ! -f "$record_path" ]]; then
        cat <<EOF
{"code":404,"msg":"record not found","data":{}}
EOF
        return 1
    fi

    python3 - "$record_path" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    payload = json.load(f)

print(json.dumps({
    "code": 0,
    "msg": "success",
    "data": {
        "record": {
            "record_id": payload["record_id"],
            "fields": payload.get("fields", {}),
        }
    }
}, ensure_ascii=False))
PY
}

local_update_record() {
    local logical_table="$1"
    local record_id="$2"
    local patch_fields_json="$3"

    local record_path
    record_path="$(local_record_path "$logical_table" "$record_id")"

    if [[ ! -f "$record_path" ]]; then
        cat <<EOF
{"code":404,"msg":"record not found","data":{}}
EOF
        return 1
    fi

    local now
    now="$(now_iso_utc)"

    python3 - "$record_path" "$patch_fields_json" "$now" <<'PY'
import json
import sys

record_path = sys.argv[1]
patch = json.loads(sys.argv[2])
now = sys.argv[3]

with open(record_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

fields = payload.get("fields", {})
fields.update(patch)
payload["fields"] = fields
payload["updated_at"] = now
payload["synced_to_api"] = False

with open(record_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "code": 0,
    "msg": "success",
    "data": {
        "record": {
            "record_id": payload["record_id"],
            "fields": fields,
        }
    }
}, ensure_ascii=False))
PY
}

local_delete_record() {
    local logical_table="$1"
    local record_id="$2"

    local record_path
    record_path="$(local_record_path "$logical_table" "$record_id")"

    if [[ ! -f "$record_path" ]]; then
        cat <<EOF
{"code":404,"msg":"record not found","data":{}}
EOF
        return 1
    fi

    rm -f "$record_path"
    cat <<EOF
{"code":0,"msg":"success","data":{}}
EOF
}

local_list_records() {
    local logical_table="$1"

    local table_dir
    table_dir="$(local_table_dir "$logical_table")"

    python3 - "$table_dir" <<'PY'
import json
import sys
from pathlib import Path

table_dir = Path(sys.argv[1])
items = []

if table_dir.exists():
    for path in sorted(table_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            items.append({
                "record_id": payload.get("record_id"),
                "fields": payload.get("fields", {}),
            })
        except Exception:
            continue

print(json.dumps({
    "code": 0,
    "msg": "success",
    "data": {
        "items": items,
        "has_more": False,
        "page_token": "",
    }
}, ensure_ascii=False))
PY
}

local_find_record_id_by_field() {
    local logical_table="$1"
    local field_name="$2"
    local field_value="$3"

    local table_dir
    table_dir="$(local_table_dir "$logical_table")"

    python3 - "$table_dir" "$field_name" "$field_value" <<'PY'
import json
import sys
from pathlib import Path

table_dir = Path(sys.argv[1])
field_name = sys.argv[2]
field_value = sys.argv[3]

if not table_dir.exists():
    raise SystemExit(1)

for path in sorted(table_dir.glob("*.json")):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue

    value = payload.get("fields", {}).get(field_name)
    if value is None:
        continue

    if isinstance(value, list):
        normalized = ",".join(str(v) for v in value)
        if normalized == field_value:
            print(payload.get("record_id", ""))
            raise SystemExit(0)

    if str(value) == field_value:
        print(payload.get("record_id", ""))
        raise SystemExit(0)

raise SystemExit(1)
PY
}

local_mark_record_synced() {
    local logical_table="$1"
    local record_id="$2"

    local record_path
    record_path="$(local_record_path "$logical_table" "$record_id")"

    if [[ ! -f "$record_path" ]]; then
        return 0
    fi

    local now
    now="$(now_iso_utc)"

    python3 - "$record_path" "$now" <<'PY'
import json
import sys

path = sys.argv[1]
now = sys.argv[2]

with open(path, "r", encoding="utf-8") as f:
    payload = json.load(f)

payload["synced_to_api"] = True
payload["synced_at"] = now

with open(path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
PY
}

# ============================================================================
# Backend-Agnostic Record API
# ============================================================================

create_record() {
    local logical_table="$1"
    local fields_json="$2"

    json_validate_object "$fields_json"

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        api_create_record "$logical_table" "$fields_json"
    else
        local_create_record "$logical_table" "$fields_json"
    fi
}

get_record() {
    local logical_table="$1"
    local record_id="$2"

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        api_get_record "$logical_table" "$record_id"
    else
        local_get_record "$logical_table" "$record_id"
    fi
}

update_record() {
    local logical_table="$1"
    local record_id="$2"
    local patch_fields_json="$3"

    json_validate_object "$patch_fields_json"

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        api_update_record "$logical_table" "$record_id" "$patch_fields_json"
    else
        local_update_record "$logical_table" "$record_id" "$patch_fields_json"
    fi
}

delete_record() {
    local logical_table="$1"
    local record_id="$2"

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        api_delete_record "$logical_table" "$record_id"
    else
        local_delete_record "$logical_table" "$record_id"
    fi
}

list_records() {
    local logical_table="$1"

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        api_list_records_all "$logical_table"
    else
        local_list_records "$logical_table"
    fi
}

find_record_id_by_field() {
    local logical_table="$1"
    local field_name="$2"
    local field_value="$3"

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        api_find_record_id_by_field "$logical_table" "$field_name" "$field_value"
    else
        local_find_record_id_by_field "$logical_table" "$field_name" "$field_value"
    fi
}

# ============================================================================
# Business Functions
# ============================================================================

init_bitable() {
    ensure_runtime
    require_dependency curl
    require_dependency python3

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        validate_api_config
        fetch_tenant_access_token >/dev/null
        api_verify_tables
        log_info "Bitable integration initialized (backend=api)"
    else
        local_init_tables
        log_info "Bitable integration initialized (backend=local, data_root=${BITABLE_DATA_ROOT})"
    fi
}

init_tables() {
    ensure_runtime
    if [[ "$ACTIVE_BACKEND" == "local" ]]; then
        local_init_tables
        log_info "Local table directories are ready"
    else
        api_verify_tables
        log_info "Remote Bitable tables verified"
    fi
}

create_task_record() {
    local task_id="$1"
    local workflow_name="$2"
    local status="$3"
    local assigned_agents_csv="$4"
    local token_usage="${5:-0}"

    local created_at
    created_at="$(now_epoch_ms)"

    local assigned_agents_json
    assigned_agents_json="$(csv_to_json_array "$assigned_agents_csv")"

    local fields_json
    fields_json=$(cat <<EOF
{"task_id":"${task_id}","workflow_name":"${workflow_name}","status":"${status}","created_at":${created_at},"assigned_agents":${assigned_agents_json},"token_usage":${token_usage}}
EOF
)

    local created
    created="$(create_record "task_records" "$fields_json")"

    log_info "Task record created: ${task_id}"
    printf '%s\n' "$created"
}

get_task_record() {
    local task_id="$1"

    local record_id
    if ! record_id="$(find_record_id_by_field "task_records" "task_id" "$task_id")"; then
        log_error "Task record not found for task_id=${task_id}"
        return 1
    fi

    get_record "task_records" "$record_id"
}

update_task_status() {
    local task_id="$1"
    local status="$2"
    local result_summary="${3:-}"
    local error_message="${4:-}"

    local record_id
    if ! record_id="$(find_record_id_by_field "task_records" "task_id" "$task_id")"; then
        log_error "Task record not found for task_id=${task_id}"
        return 1
    fi

    local timestamp
    timestamp="$(now_epoch_ms)"

    local patch_json='{}'

    patch_json="$(json_merge_objects "$patch_json" "{\"status\":\"${status}\"}")"

    if [[ "$status" == "running" ]]; then
        patch_json="$(json_merge_objects "$patch_json" "{\"started_at\":${timestamp}}")"
    fi

    if [[ "$status" == "completed" || "$status" == "failed" || "$status" == "cancelled" ]]; then
        patch_json="$(json_merge_objects "$patch_json" "{\"completed_at\":${timestamp}}")"
    fi

    if [[ -n "$result_summary" ]]; then
        patch_json="$(json_merge_objects "$patch_json" "{\"result_summary\":\"${result_summary}\"}")"
    fi

    if [[ -n "$error_message" ]]; then
        patch_json="$(json_merge_objects "$patch_json" "{\"error_message\":\"${error_message}\"}")"
    fi

    local updated
    updated="$(update_record "task_records" "$record_id" "$patch_json")"

    log_info "Task status updated: ${task_id} -> ${status}"
    printf '%s\n' "$updated"
}

delete_task_record() {
    local task_id="$1"

    local record_id
    if ! record_id="$(find_record_id_by_field "task_records" "task_id" "$task_id")"; then
        log_error "Task record not found for task_id=${task_id}"
        return 1
    fi

    delete_record "task_records" "$record_id" >/dev/null
    log_info "Task record deleted: ${task_id}"
}

list_task_records() {
    list_records "task_records"
}

record_workflow_execution() {
    local execution_id="$1"
    local workflow_name="$2"
    local phase_id="$3"
    local agent_id="$4"
    local status="$5"
    local duration="$6"
    local output_path="${7:-}"
    local success_criteria="${8:-}"
    local actual_output="${9:-}"

    local start_time end_time
    start_time="$(now_epoch_ms)"
    end_time="$(now_epoch_ms)"

    local fields_json
    fields_json=$(cat <<EOF
{"execution_id":"${execution_id}","workflow_name":"${workflow_name}","phase_id":"${phase_id}","agent_id":"${agent_id}","status":"${status}","start_time":${start_time},"end_time":${end_time},"duration":${duration},"output_path":"${output_path}","success_criteria":"${success_criteria}","actual_output":"${actual_output}"}
EOF
)

    create_record "workflow_executions" "$fields_json" >/dev/null
    log_info "Workflow execution recorded: ${execution_id}"
}

record_performance_metrics() {
    local workflow_name="$1"
    local execution_time="$2"
    local agent_count="$3"
    local parallel_agents="$4"
    local token_usage="$5"
    local error_count="$6"
    local success_rate="$7"
    local retry_count="${8:-0}"

    local metric_id
    metric_id="METRIC-$(date +%s%N)"

    local timestamp
    timestamp="$(now_epoch_ms)"

    local fields_json
    fields_json=$(cat <<EOF
{"metric_id":"${metric_id}","timestamp":${timestamp},"workflow_name":"${workflow_name}","execution_time":${execution_time},"agent_count":${agent_count},"parallel_agents":${parallel_agents},"token_usage":${token_usage},"error_count":${error_count},"retry_count":${retry_count},"success_rate":${success_rate}}
EOF
)

    create_record "performance_metrics" "$fields_json" >/dev/null
    log_info "Performance metrics recorded: ${metric_id}"
}

record_error_pattern() {
    local error_type="$1"
    local error_message="$2"
    local affected_workflows_csv="$3"
    local affected_agents_csv="$4"

    local pattern_id
    pattern_id="PATTERN-$(date +%s%N)"

    local affected_workflows_json
    affected_workflows_json="$(csv_to_json_array "$affected_workflows_csv")"

    local affected_agents_json
    affected_agents_json="$(csv_to_json_array "$affected_agents_csv")"

    local timestamp
    timestamp="$(now_epoch_ms)"

    local fields_json
    fields_json=$(cat <<EOF
{"pattern_id":"${pattern_id}","error_type":"${error_type}","error_message":"${error_message}","occurrence_count":1,"last_occurrence":${timestamp},"affected_workflows":${affected_workflows_json},"affected_agents":${affected_agents_json},"status":"open"}
EOF
)

    create_record "error_patterns" "$fields_json" >/dev/null
    log_info "Error pattern recorded: ${pattern_id}"
}

add_optimization_suggestion() {
    local category="$1"
    local title="$2"
    local description="$3"
    local impact="$4"
    local effort="$5"
    local priority="$6"

    local suggestion_id
    suggestion_id="SUGG-$(date +%s%N)"

    local created_at
    created_at="$(now_epoch_ms)"

    local fields_json
    fields_json=$(cat <<EOF
{"suggestion_id":"${suggestion_id}","created_at":${created_at},"category":"${category}","title":"${title}","description":"${description}","impact":"${impact}","effort":"${effort}","priority":${priority},"status":"pending"}
EOF
)

    create_record "optimization_suggestions" "$fields_json" >/dev/null
    log_info "Optimization suggestion added: ${suggestion_id}"
}

get_all_task_records() {
    list_task_records
}

get_performance_summary() {
    local workflow_name="${1:-}"
    local payload
    payload="$(list_records "performance_metrics")"

    python3 - "$workflow_name" "$payload" <<'PY'
import json
import sys

workflow = sys.argv[1]
payload = json.loads(sys.argv[2])
items = payload.get("data", {}).get("items", [])

filtered = []
for item in items:
    fields = item.get("fields", {})
    if workflow and fields.get("workflow_name") != workflow:
        continue
    filtered.append(fields)

total = len(filtered)

def to_number(value):
    try:
        return float(value)
    except Exception:
        return 0.0

execution_total = sum(to_number(m.get("execution_time", 0)) for m in filtered)
error_total = sum(to_number(m.get("error_count", 0)) for m in filtered)
token_total = sum(to_number(m.get("token_usage", 0)) for m in filtered)
retry_total = sum(to_number(m.get("retry_count", 0)) for m in filtered)

avg_execution = execution_total / total if total else 0
avg_success = sum(to_number(m.get("success_rate", 0)) for m in filtered) / total if total else 0

print(json.dumps({
    "total_executions": total,
    "total_execution_time": round(execution_total, 3),
    "average_execution_time": round(avg_execution, 3),
    "total_error_count": round(error_total, 3),
    "total_token_usage": round(token_total, 3),
    "total_retry_count": round(retry_total, 3),
    "average_success_rate": round(avg_success, 3),
}, ensure_ascii=False))
PY
}

analyze_error_patterns() {
    local payload
    payload="$(list_records "error_patterns")"

    python3 - "$payload" <<'PY'
import json
import sys
from collections import defaultdict

payload = json.loads(sys.argv[1])
items = payload.get("data", {}).get("items", [])

count_by_type = defaultdict(int)
status_by_type = defaultdict(lambda: defaultdict(int))

for item in items:
    fields = item.get("fields", {})
    error_type = fields.get("error_type", "unknown")
    occurrence = fields.get("occurrence_count", 1)
    status = fields.get("status", "open")

    try:
        occurrence = int(occurrence)
    except Exception:
        occurrence = 1

    count_by_type[error_type] += occurrence
    status_by_type[error_type][status] += occurrence

patterns = []
for error_type in sorted(count_by_type.keys()):
    patterns.append({
        "error_type": error_type,
        "total_occurrences": count_by_type[error_type],
        "status_breakdown": dict(status_by_type[error_type]),
    })

print(json.dumps({
    "total_patterns": len(patterns),
    "analysis_timestamp": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "patterns": patterns,
}, ensure_ascii=False))
PY
}

generate_optimization_recommendations() {
    local perf_summary
    perf_summary="$(get_performance_summary)"
    local error_summary
    error_summary="$(analyze_error_patterns)"

    python3 - "$perf_summary" "$error_summary" <<'PY'
import json
import sys

perf = json.loads(sys.argv[1])
errors = json.loads(sys.argv[2])
recommendations = []

if perf.get("average_execution_time", 0) > 300:
    recommendations.append({
        "category": "performance",
        "title": "Reduce average workflow latency",
        "description": "Average execution time exceeds 300s. Consider splitting long phases and adding cached intermediate outputs.",
        "priority": 9,
    })

if perf.get("average_success_rate", 100) < 95:
    recommendations.append({
        "category": "reliability",
        "title": "Improve workflow success rate",
        "description": "Average success rate below 95%. Add retries with circuit breaker and fallback routing.",
        "priority": 8,
    })

if perf.get("total_retry_count", 0) > 0 and perf.get("total_executions", 0) > 0:
    recommendations.append({
        "category": "reliability",
        "title": "Investigate high retry usage",
        "description": "Retries are occurring in production flow. Analyze timeout thresholds and external API stability.",
        "priority": 7,
    })

if errors.get("total_patterns", 0) > 3:
    recommendations.append({
        "category": "quality",
        "title": "Consolidate recurring error classes",
        "description": "Multiple recurring error patterns detected. Add automated taxonomy and root-cause labels.",
        "priority": 6,
    })

if not recommendations:
    recommendations.append({
        "category": "maintenance",
        "title": "System health is stable",
        "description": "No major optimization bottleneck detected from current metrics.",
        "priority": 3,
    })

print(json.dumps({
    "generated_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "recommendations": recommendations,
}, ensure_ascii=False))
PY
}

sync_to_bitable() {
    ensure_runtime

    if [[ "$ACTIVE_BACKEND" == "api" ]]; then
        log_info "sync command skipped: backend already api"
        return 0
    fi

    # If local backend but credentials are present, push non-synced records to API.
    if [[ -z "${BITABLE_APP_ID}" || -z "${BITABLE_APP_SECRET}" || -z "${BITABLE_APP_TOKEN}" ]]; then
        log_info "sync command skipped: API credentials not configured"
        return 0
    fi

    validate_api_config

    local synced_count=0
    local logical_table
    for logical_table in "${!TABLE_ID_MAP[@]}"; do
        local table_dir
        table_dir="$(local_table_dir "$logical_table")"
        mkdir -p "$table_dir"

        local file
        while IFS= read -r file; do
            local state
            state="$(python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    payload = json.load(f)

print("true" if payload.get("synced_to_api") else "false")
PY
)"

            if [[ "$state" == "true" ]]; then
                continue
            fi

            local fields_json
            fields_json="$(python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    payload = json.load(f)

print(json.dumps(payload.get("fields", {}), ensure_ascii=False, separators=(",", ":")))
PY
)"

            api_create_record "$logical_table" "$fields_json" >/dev/null

            local local_record_id
            local_record_id="$(python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    payload = json.load(f)

print(payload.get("record_id", ""))
PY
)"

            if [[ -n "$local_record_id" ]]; then
                local_mark_record_synced "$logical_table" "$local_record_id"
            fi

            synced_count=$((synced_count + 1))
        done < <(find "$table_dir" -type f -name '*.json' 2>/dev/null)
    done

    log_info "Synced ${synced_count} local records to Bitable API"
}

# ============================================================================
# CLI
# ============================================================================

show_help() {
    cat <<'EOF'
Bitable Integration Module for Task Orchestrator (V0.0.4)

Usage:
  bitable-integration.sh <command> [arguments]

Connection / bootstrap:
  init
  sync

Task records (CRUD):
  create-task <task_id> <workflow_name> <status> <assigned_agents_csv> [token_usage]
  get-task <task_id>
  update-task <task_id> <status> [result_summary] [error_message]
  delete-task <task_id>
  list-tasks

Workflow / metrics / quality:
  record-execution <execution_id> <workflow_name> <phase_id> <agent_id> <status> <duration> [output_path] [success_criteria] [actual_output]
  record-metrics <workflow_name> <execution_time> <agent_count> <parallel_agents> <token_usage> <error_count> <success_rate> [retry_count]
  record-error <error_type> <error_message> <affected_workflows_csv> <affected_agents_csv>
  add-suggestion <category> <title> <description> <impact> <effort> <priority>

Analysis:
  get-summary [workflow_name]
  analyze-errors
  generate-recommendations

Compatibility aliases:
  get-all-tasks   -> list-tasks
  help

Environment:
  BITABLE_BACKEND=auto|local|api
  BITABLE_APP_ID / BITABLE_APP_SECRET / BITABLE_APP_TOKEN
  BITABLE_TABLE_TASK_RECORDS / BITABLE_TABLE_WORKFLOW_EXECUTIONS / ...
EOF
}

main() {
    ensure_runtime

    local command="${1:-help}"

    case "$command" in
        init)
            init_bitable
            init_tables
            ;;
        create-task)
            [[ $# -lt 5 ]] && { log_error "Usage: create-task <task_id> <workflow_name> <status> <assigned_agents_csv> [token_usage]"; exit 1; }
            create_task_record "$2" "$3" "$4" "$5" "${6:-0}"
            ;;
        get-task)
            [[ $# -lt 2 ]] && { log_error "Usage: get-task <task_id>"; exit 1; }
            get_task_record "$2"
            ;;
        update-task)
            [[ $# -lt 3 ]] && { log_error "Usage: update-task <task_id> <status> [result_summary] [error_message]"; exit 1; }
            update_task_status "$2" "$3" "${4:-}" "${5:-}"
            ;;
        delete-task)
            [[ $# -lt 2 ]] && { log_error "Usage: delete-task <task_id>"; exit 1; }
            delete_task_record "$2"
            ;;
        list-tasks|get-all-tasks)
            list_task_records
            ;;
        record-execution)
            [[ $# -lt 7 ]] && { log_error "Usage: record-execution <execution_id> <workflow_name> <phase_id> <agent_id> <status> <duration> [output_path] [success_criteria] [actual_output]"; exit 1; }
            record_workflow_execution "$2" "$3" "$4" "$5" "$6" "$7" "${8:-}" "${9:-}" "${10:-}"
            ;;
        record-metrics)
            [[ $# -lt 8 ]] && { log_error "Usage: record-metrics <workflow_name> <execution_time> <agent_count> <parallel_agents> <token_usage> <error_count> <success_rate> [retry_count]"; exit 1; }
            record_performance_metrics "$2" "$3" "$4" "$5" "$6" "$7" "$8" "${9:-0}"
            ;;
        record-error)
            [[ $# -lt 5 ]] && { log_error "Usage: record-error <error_type> <error_message> <affected_workflows_csv> <affected_agents_csv>"; exit 1; }
            record_error_pattern "$2" "$3" "$4" "$5"
            ;;
        add-suggestion)
            [[ $# -lt 7 ]] && { log_error "Usage: add-suggestion <category> <title> <description> <impact> <effort> <priority>"; exit 1; }
            add_optimization_suggestion "$2" "$3" "$4" "$5" "$6" "$7"
            ;;
        get-summary)
            get_performance_summary "${2:-}"
            ;;
        analyze-errors)
            analyze_error_patterns
            ;;
        generate-recommendations)
            generate_optimization_recommendations
            ;;
        sync)
            sync_to_bitable
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: ${command}"
            show_help
            exit 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
