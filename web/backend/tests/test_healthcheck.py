# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""容器健康检查脚本测试：状态目录可写 + HTTP 端点可用。"""

from __future__ import annotations

import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import healthcheck


class _OkHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b'{"status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


def _serve() -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    return server, f"http://127.0.0.1:{port}/api/health"


def test_check_state_dirs_ok(tmp_path: Path) -> None:
    dirs = [tmp_path / "hub", tmp_path / "admin"]

    assert healthcheck.check_state_dirs(dirs) is True
    assert all(d.is_dir() for d in dirs)
    assert not any((d / ".healthcheck").exists() for d in dirs)


def test_check_state_dirs_fails_when_not_writable(tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    assert healthcheck.check_state_dirs([blocker]) is False


def test_check_http_ok() -> None:
    server, url = _serve()
    try:
        assert healthcheck.check_http(url) is True
    finally:
        server.shutdown()
        server.server_close()


def test_check_http_fails_when_unreachable() -> None:
    assert healthcheck.check_http("http://127.0.0.1:1/api/health", timeout=1.0) is False


def test_main_returns_zero_when_all_checks_pass(tmp_path: Path, monkeypatch) -> None:
    server, url = _serve()
    try:
        monkeypatch.setenv(
            "CALC_STATE_DIRS",
            os.pathsep.join([str(tmp_path / "hub"), str(tmp_path / "admin")]),
        )
        monkeypatch.setenv("CALC_HEALTH_URL", url)
        assert healthcheck.main() == 0
    finally:
        server.shutdown()
        server.server_close()
