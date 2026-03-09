#!/usr/bin/env python3

import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DB = {
    "tables": {}
}


def ensure_table(table_id: str):
    if table_id not in DB["tables"]:
        DB["tables"][table_id] = {}
    return DB["tables"][table_id]


def extract_filter(query: str):
    # Supports: CurrentValue.[field]="value"
    m = re.match(r'CurrentValue\.\[(?P<field>[^\]]+)]="(?P<value>.*)"', query)
    if not m:
        return None, None
    return m.group("field"), m.group("value")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # noqa: A003
        return

    def _send(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/open-apis/auth/v3/tenant_access_token/internal":
            self._send({
                "code": 0,
                "msg": "success",
                "tenant_access_token": "mock-tenant-token",
                "expire": 7200,
            })
            return

        m = re.match(r"^/open-apis/bitable/v1/apps/[^/]+/tables/([^/]+)/records$", parsed.path)
        if m:
            table_id = m.group(1)
            table = ensure_table(table_id)
            payload = self._read_json()
            fields = payload.get("fields", {})
            record_id = f"rec_{int(time.time() * 1000)}_{len(table) + 1}"
            table[record_id] = {
                "record_id": record_id,
                "fields": fields,
            }
            self._send({
                "code": 0,
                "msg": "success",
                "data": {
                    "record": table[record_id]
                }
            })
            return

        self._send({"code": 404, "msg": "not found"}, status=404)

    def do_GET(self):
        parsed = urlparse(self.path)

        m_table = re.match(r"^/open-apis/bitable/v1/apps/[^/]+/tables/([^/]+)$", parsed.path)
        if m_table:
            table_id = m_table.group(1)
            ensure_table(table_id)
            self._send({
                "code": 0,
                "msg": "success",
                "data": {
                    "table": {
                        "table_id": table_id
                    }
                }
            })
            return

        m_record = re.match(r"^/open-apis/bitable/v1/apps/[^/]+/tables/([^/]+)/records/([^/]+)$", parsed.path)
        if m_record:
            table_id, record_id = m_record.group(1), m_record.group(2)
            table = ensure_table(table_id)
            record = table.get(record_id)
            if not record:
                self._send({"code": 9702001, "msg": "record not found"})
                return
            self._send({
                "code": 0,
                "msg": "success",
                "data": {
                    "record": record
                }
            })
            return

        m_list = re.match(r"^/open-apis/bitable/v1/apps/[^/]+/tables/([^/]+)/records$", parsed.path)
        if m_list:
            table_id = m_list.group(1)
            table = ensure_table(table_id)
            query = parse_qs(parsed.query)

            items = list(table.values())

            filter_values = query.get("filter", [])
            if filter_values:
                field, value = extract_filter(filter_values[0])
                if field is not None:
                    filtered = []
                    for item in items:
                        fv = item.get("fields", {}).get(field)
                        if isinstance(fv, list):
                            joined = ",".join(str(v) for v in fv)
                            if joined == value:
                                filtered.append(item)
                        elif str(fv) == value:
                            filtered.append(item)
                    items = filtered

            page_size = int(query.get("page_size", [200])[0])
            items = items[:page_size]

            self._send({
                "code": 0,
                "msg": "success",
                "data": {
                    "items": items,
                    "has_more": False,
                    "page_token": "",
                }
            })
            return

        self._send({"code": 404, "msg": "not found"}, status=404)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        m = re.match(r"^/open-apis/bitable/v1/apps/[^/]+/tables/([^/]+)/records/([^/]+)$", parsed.path)
        if not m:
            self._send({"code": 404, "msg": "not found"}, status=404)
            return

        table_id, record_id = m.group(1), m.group(2)
        table = ensure_table(table_id)
        record = table.get(record_id)
        if not record:
            self._send({"code": 9702001, "msg": "record not found"})
            return

        payload = self._read_json()
        patch = payload.get("fields", {})
        record["fields"].update(patch)

        self._send({
            "code": 0,
            "msg": "success",
            "data": {
                "record": record
            }
        })

    def do_DELETE(self):
        parsed = urlparse(self.path)
        m = re.match(r"^/open-apis/bitable/v1/apps/[^/]+/tables/([^/]+)/records/([^/]+)$", parsed.path)
        if not m:
            self._send({"code": 404, "msg": "not found"}, status=404)
            return

        table_id, record_id = m.group(1), m.group(2)
        table = ensure_table(table_id)
        table.pop(record_id, None)
        self._send({"code": 0, "msg": "success", "data": {}})


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
