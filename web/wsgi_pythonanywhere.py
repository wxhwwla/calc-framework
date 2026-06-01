# SPDX-License-Identifier: AGPL-3.0
"""
PythonAnywhere WSGI 入口（免费套餐：WSGI + 同步 API，不用裸 FastAPI app）。

部署步骤（Bash，将 wxhwwla / calc-framework 换成你的用户名与目录）:
  workon calc-framework
  pip install -r ~/calc-framework/web/backend/requirements.txt
  pip install -e ~/calc-framework/framework/
  cp ~/calc-framework/web/wsgi_pythonanywhere.py /var/www/wxhwwla_pythonanywhere_com_wsgi.py
  # Web 页面 → Reload
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# ── 按账号修改 ─────────────────────────────────────────────────────────────
PA_USERNAME = "wxhwwla"
PA_PROJECT = "calc-framework"
PA_VENV = "calc-framework"
# ────────────────────────────────────────────────────────────────────────────

_BASE = Path(f"/home/{PA_USERNAME}/{PA_PROJECT}")
_FRAMEWORK_SRC = _BASE / "framework" / "src"
_BACKEND = _BASE / "web" / "backend"
_DATA = _BASE / "games" / "endfield" / "data"
_DIST = _BASE / "web" / "frontend" / "dist"
_DONATION = _BASE / "resources" / "donation"

for _p in (str(_FRAMEWORK_SRC), str(_BASE), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_VENV_ACTIVATE = Path(f"/home/{PA_USERNAME}/.virtualenvs/{PA_VENV}/bin/activate_this.py")
if _VENV_ACTIVATE.is_file():
    exec(open(_VENV_ACTIVATE, encoding="utf-8").read(), {"__file__": str(_VENV_ACTIVATE)})

# 勿使用 application = app（会报 missing argument 'send'）
# 关键 API 在下方同步处理；其余功能在 PA 免费版上可能不可用。

_DONATION_FILES = frozenset({"donation_qr.png", "afdian_qr.png"})

_MIME = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".html": "text/html",
    ".json": "application/json",
    ".woff2": "font/woff2",
    ".webp": "image/webp",
}


def _fix_path(path: str) -> str:
    path = unquote(path)
    try:
        path = path.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return path


def _read_json(path: Path):
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_body(environ) -> bytes:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    if length <= 0:
        return b""
    return environ["wsgi.input"].read(length)


def _json(start_response, data, status: str = "200 OK"):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _bytes(start_response, body: bytes, content_type: str, status: str = "200 OK"):
    start_response(
        status,
        [("Content-Type", content_type), ("Content-Length", str(len(body)))],
    )
    return [body]


def _http_error(start_response, detail, code: int = 400):
    status = f"{code} {'Error' if code >= 400 else 'OK'}"
    return _json(start_response, {"detail": detail}, status)


def _handle_donation(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    if not path.startswith("/api/donation/"):
        return None
    name = path[len("/api/donation/") :].lstrip("/")
    if name not in _DONATION_FILES:
        return _http_error(start_response, "not found", 404)
    fp = _DONATION / name
    if not fp.is_file():
        return _http_error(start_response, "not found", 404)
    return _bytes(start_response, fp.read_bytes(), "image/png")


def _handle_layout_compute(environ, start_response):
    """计算页依赖的 layout / evaluate / snapshot API。"""
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")

    try:
        from fastapi import HTTPException

        from api.layout import get_layout_payload, get_variables_payload
        from api.compute import EvaluateRequest, SnapshotRequest, evaluate_payload, snapshot_payload
    except Exception as e:
        return _json(start_response, {"error": f"layout/compute import failed: {e}"}, "500 Internal Server Error")

    try:
        if path == "/api/layout" and method == "GET":
            return _json(start_response, get_layout_payload())

        if path == "/api/layout/variables" and method == "GET":
            return _json(start_response, get_variables_payload())

        if path == "/api/compute/evaluate" and method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))
            result = evaluate_payload(EvaluateRequest(**payload))
            return _json(start_response, result.model_dump())

        if path == "/api/compute/snapshot" and method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))
            return _json(start_response, snapshot_payload(SnapshotRequest(**payload)))
    except HTTPException as exc:
        return _json(start_response, {"detail": exc.detail}, f"{exc.status_code} Error")
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _json(start_response, {"error": str(e)}, "500 Internal Server Error")

    return None


def _handle_arknights(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/arknights"):
        return None

    try:
        from fastapi import HTTPException

        from api.arknights import (
            ComputeRequest,
            compute_damage_payload,
            list_operators_payload,
            operator_summary_payload,
        )
    except Exception as e:
        return _json(start_response, {"error": f"arknights import failed: {e}"}, "500 Internal Server Error")

    try:
        if path == "/api/arknights/operators" and method == "GET":
            return _json(start_response, list_operators_payload())

        if path == "/api/arknights/compute" and method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))
            result = compute_damage_payload(ComputeRequest(**payload))
            return _json(start_response, result.model_dump())

        m = re.match(r"^/api/arknights/operators/(.+)$", path)
        if m and method == "GET":
            name = m.group(1).strip()
            return _json(start_response, operator_summary_payload(name))
    except HTTPException as exc:
        return _json(start_response, {"detail": exc.detail}, f"{exc.status_code} Error")
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _json(start_response, {"error": str(e)}, "500 Internal Server Error")

    return _http_error(start_response, "unknown arknights endpoint", 404)


def _handle_data_api(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/api/health":
        return _json(start_response, {"status": "ok", "version": "1.0.0"})

    if path == "/api/search/catalog":
        try:
            from games.endfield.data_loading.equipment_catalog import get_equipment_catalog

            catalog = get_equipment_catalog()
            result = {
                k: [
                    {
                        "名称": e.get("名称", ""),
                        "部位": e.get("部位", ""),
                        "所属套组": e.get("所属套组", ""),
                        "稀有度": e.get("稀有度", ""),
                    }
                    for e in v
                ]
                for k, v in catalog.items()
            }
            return _json(start_response, result)
        except Exception as e:
            return _json(start_response, {"error": str(e)}, "500 Internal Server Error")

    if not path.startswith("/api/data/"):
        return None
    if method != "GET":
        return _http_error(start_response, "not supported", 501)

    sub = path[len("/api/data/") :]

    if sub == "summary":
        c = _read_json(_DATA / "characters.json") or []
        w = _read_json(_DATA / "weapons.json") or []
        e = _read_json(_DATA / "equipments.json") or []
        return _json(
            start_response,
            {
                "characters_count": len(c),
                "weapons_count": len(w),
                "equipments_count": len(e),
                "equipment_sets": list({x.get("所属套组") for x in e if x.get("所属套组")}),
                "character_types": list({x.get("类型") for x in c if x.get("类型")}),
                "weapon_types": list({x.get("类型") for x in w if x.get("类型")}),
            },
        )

    if sub == "characters/detail/all":
        d = _read_json(_DATA / "characters.json")
        return _json(start_response, d) if d else _http_error(start_response, "not found", 404)
    if sub == "characters":
        raw = _read_json(_DATA / "characters.json") or []
        return _json(
            start_response,
            [
                {
                    "名称": c.get("名称"),
                    "类型": c.get("类型"),
                    "星级": c.get("星级"),
                    "武器": c.get("武器"),
                    "主能力": c.get("主能力"),
                    "副能力": c.get("副能力"),
                }
                for c in raw
            ],
        )
    m = re.match(r"^characters/(.+)$", sub)
    if m:
        n = m.group(1).strip()
        for c in _read_json(_DATA / "characters.json") or []:
            if c.get("名称") == n:
                return _json(start_response, c)
        return _http_error(start_response, f"not found: {n}", 404)

    if sub == "weapons/detail/all":
        d = _read_json(_DATA / "weapons.json")
        return _json(start_response, d) if d else _http_error(start_response, "not found", 404)
    if sub == "weapons":
        raw = _read_json(_DATA / "weapons.json") or []
        result = []
        for w in raw:
            e = {"名称": w.get("名称"), "类型": w.get("类型"), "星级": w.get("星级")}
            for k in ("附加属性", "武器技能", "普通技能", "特殊技能"):
                if k in w:
                    e[k] = w[k]
            result.append(e)
        return _json(start_response, result)
    m = re.match(r"^weapons/(.+)$", sub)
    if m:
        n = m.group(1).strip()
        for w in _read_json(_DATA / "weapons.json") or []:
            if w.get("名称") == n:
                return _json(start_response, w)
        return _http_error(start_response, f"not found: {n}", 404)

    if sub == "equipments/detail/all":
        d = _read_json(_DATA / "equipments.json")
        return _json(start_response, d) if d else _http_error(start_response, "not found", 404)
    if sub == "equipments":
        raw = _read_json(_DATA / "equipments.json") or []
        return _json(
            start_response,
            [
                {
                    "名称": e.get("名称"),
                    "装备种类": e.get("装备种类"),
                    "部位": e.get("部位"),
                    "稀有度": e.get("稀有度"),
                    "所属套组": e.get("所属套组"),
                    "属性词条": e.get("属性词条", []),
                    "三件套效果": e.get("三件套效果", []),
                }
                for e in raw
            ],
        )
    m = re.match(r"^equipments/set/(.+)$", sub)
    if m:
        s = m.group(1)
        raw = _read_json(_DATA / "equipments.json") or []
        return _json(start_response, [e for e in raw if e.get("所属套组") == s])
    m = re.match(r"^equipments/slot/(.+)$", sub)
    if m:
        s = m.group(1)
        raw = _read_json(_DATA / "equipments.json") or []
        return _json(start_response, [e for e in raw if e.get("部位") == s])
    m = re.match(r"^equipments/(.+)$", sub)
    if m:
        n = m.group(1).strip()
        for e in _read_json(_DATA / "equipments.json") or []:
            if e.get("名称") == n:
                return _json(start_response, e)
        return _http_error(start_response, f"not found: {n}", 404)

    return _http_error(start_response, "unknown endpoint", 404)


def application(environ, start_response):
    for handler in (_handle_donation, _handle_layout_compute, _handle_arknights, _handle_data_api):
        result = handler(environ, start_response)
        if result is not None:
            return result

    path = environ.get("PATH_INFO", "")
    fp = _DIST / (path.lstrip("/") if path not in ("", "/") else "index.html")
    if not fp.is_file():
        fp = _DIST / "index.html"
    if fp.is_file():
        return _bytes(start_response, fp.read_bytes(), _MIME.get(fp.suffix, "application/octet-stream"))
    start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
    return [b"Not Found"]
