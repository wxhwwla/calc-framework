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

import gzip
import json
import logging
import os
import re
import secrets
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote

logger = logging.getLogger(__name__)

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
_STATIC = _BASE / "web" / "static"
_DONATION = _BASE / "resources" / "donation"

# 与 utils/donation_assets.py 保持一致（WSGI 不依赖 utils 包，避免 PA 未上传 utils 时 500）
_DONATION_SLOTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "微信赞赏码",
        (
            "donation_qr.jpg",
            "donation_qr.jpeg",
            "donation_q.jpg",
            "donation_qr.png",
            "donation_qr.webp",
        ),
    ),
    (
        "爱发电",
        (
            "afdian_qr.png",
            "afdian_qr.jpg",
            "afdian_qr.jpeg",
            "afdian_qr.webp",
        ),
    ),
)


def _is_allowed_donation_filename(name: str) -> bool:
    if not name or "/" in name or "\\" in name or ".." in name:
        return False
    lower = name.lower()
    if not lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return False
    stem = Path(lower).stem
    return stem.startswith("donation") or stem.startswith("afdian")


def _donation_manifest() -> list[dict[str, str]]:
    """扫描 _DONATION 目录，按槽位返回可用图片。"""
    found: list[dict[str, str]] = []
    for label, candidates in _DONATION_SLOTS:
        for name in candidates:
            fp = _DONATION / name
            if fp.is_file():
                found.append(
                    {"file": name, "label": label, "rel": f"resources/donation/{name}"},
                )
                break
    return found


for _p in (str(_FRAMEWORK_SRC), str(_BASE), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── 模块预热：在重载时提前加载耗时的 API 模块 ──────────────────────────
# 避免首次请求时加载 zip 中 422 个干员 JSON 导致超时（PA 免费版 1 worker）。
# 每个 try/except 独立，防止一个模块失败导致整个 app 不可用。
_WARMUP_OK: dict[str, bool] = {}
for _mod_name in ("api.arknights", "api.generator"):
    try:
        __import__(_mod_name, fromlist=["router"])
        _WARMUP_OK[_mod_name] = True
    except Exception as _exc:
        _WARMUP_OK[_mod_name] = False


def _warmup_status() -> dict[str, bool]:
    """返回预热状态（可被 /api/health 消费）。"""
    return dict(_WARMUP_OK)


_VENV_ACTIVATE = Path(f"/home/{PA_USERNAME}/.virtualenvs/{PA_VENV}/bin/activate_this.py")
if _VENV_ACTIVATE.is_file():
    with open(_VENV_ACTIVATE, encoding="utf-8") as _f:
        exec(_f.read(), {"__file__": str(_VENV_ACTIVATE)})

# 勿使用 application = app（会报 missing argument 'send'）
# 关键 API 在下方同步处理；其余功能在 PA 免费版上可能不可用。

_MIME = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".html": "text/html",
    ".json": "application/json",
    ".woff2": "font/woff2",
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


def _bytes(start_response, body: bytes, content_type: str, status: str = "200 OK", extra_headers=None):
    headers = [("Content-Type", content_type), ("Content-Length", str(len(body)))]
    if extra_headers:
        headers.extend(extra_headers)
    start_response(status, headers)
    return [body]


def _serve_static_file(environ, start_response, fp: Path):
    """静态资源；对 js/css 启用 gzip 与长期缓存（Vite 带 hash 文件名）。"""
    body = fp.read_bytes()
    suffix = fp.suffix.lower()
    content_type = _MIME.get(suffix, "application/octet-stream")
    headers: list[tuple[str, str]] = []
    if fp.name == "index.html":
        headers.append(("Cache-Control", "no-cache"))
    elif suffix in (".js", ".css", ".woff", ".woff2"):
        headers.append(("Cache-Control", "public, max-age=31536000, immutable"))
    accept = environ.get("HTTP_ACCEPT_ENCODING", "")
    if suffix in (".js", ".css", ".html", ".svg") and "gzip" in accept and len(body) > 512:
        body = gzip.compress(body, compresslevel=6)
        headers.append(("Content-Encoding", "gzip"))
    return _bytes(start_response, body, content_type, extra_headers=headers)


def _http_error(start_response, detail, code: int = 400):
    status = f"{code} {'Error' if code >= 400 else 'OK'}"
    return _json(start_response, {"detail": detail}, status)


def _handle_donation(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    if not path.startswith("/api/donation/"):
        return None
    name = path[len("/api/donation/") :].lstrip("/")
    if not name:
        return None
    if name == "manifest":
        return _json(start_response, _donation_manifest())
    if not _is_allowed_donation_filename(name):
        return _http_error(start_response, "not found", 404)
    fp = _DONATION / name
    if not fp.is_file():
        return _http_error(start_response, "not found", 404)
    ext = fp.suffix.lower()
    mime = _MIME.get(ext, "application/octet-stream")
    return _bytes(start_response, fp.read_bytes(), mime)


def _parse_qs(environ) -> dict[str, str]:
    parsed = parse_qs(environ.get("QUERY_STRING", ""))
    return {k: (v[0] if v else "") for k, v in parsed.items()}


def _post_json_handler(start_response, payload: dict, handler):
    """调用 FastAPI 路由函数；async 路由用 asyncio.run。"""
    import asyncio
    import inspect

    from fastapi import HTTPException

    try:
        result = handler(payload)
        if inspect.isawaitable(result):
            result = asyncio.run(result)
        if hasattr(result, "model_dump"):
            return _json(start_response, result.model_dump())
        return _json(start_response, result)
    except HTTPException as exc:
        return _json(start_response, {"detail": exc.detail}, f"{exc.status_code} Error")
    except Exception as e:
        return _safe_error_response(start_response, e)


def _handle_layout_compute(environ, start_response):
    """计算页依赖的 layout / evaluate / loadout API。"""
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not (path.startswith("/api/layout") or path.startswith("/api/compute")):
        return None

    try:
        from api.adapter_lib.layout import get_dag_payload, get_layout_payload, get_variables_payload
        from api.compute import (
            CompareRequest,
            EvaluateRequest,
            LoadoutPreviewRequest,
            LoadoutSnapshotRequest,
            PresetExportRequest,
            SnapshotRequest,
            compare,
            evaluate_loadout,
            evaluate_payload,
            loadout_context,
            loadout_preview,
            loadout_snapshot,
            preset_export,
            snapshot_payload,
        )
        from fastapi import HTTPException
    except Exception as e:
        return _json(start_response, {"error": f"layout/compute import failed: {e}"}, "500 Internal Server Error")

    try:
        if path == "/api/layout" and method == "GET":
            return _json(start_response, get_layout_payload())

        if path == "/api/layout/variables" and method == "GET":
            return _json(start_response, get_variables_payload())

        if path == "/api/layout/dag" and method == "GET":
            return _json(start_response, get_dag_payload())

        if method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))

            if path == "/api/compute/evaluate":
                result = evaluate_payload(EvaluateRequest(**payload))
                return _json(start_response, result.model_dump())

            if path == "/api/compute/evaluate-loadout":
                result = evaluate_loadout(LoadoutPreviewRequest(**payload))
                return _json(start_response, result.model_dump())

            if path == "/api/compute/loadout-context":
                result = loadout_context(LoadoutPreviewRequest(**payload))
                return _json(start_response, result.model_dump())

            if path == "/api/compute/preview":
                return _json(start_response, loadout_preview(LoadoutPreviewRequest(**payload)))

            if path == "/api/compute/snapshot-full":
                return _json(start_response, loadout_snapshot(LoadoutSnapshotRequest(**payload)))

            if path == "/api/compute/snapshot":
                return _json(start_response, snapshot_payload(SnapshotRequest(**payload)))

            if path == "/api/compute/compare":
                return _json(start_response, compare(CompareRequest(**payload)))

            if path == "/api/compute/preset-export":
                return _json(start_response, preset_export(PresetExportRequest(**payload)))
    except HTTPException as exc:
        return _json(start_response, {"detail": exc.detail}, f"{exc.status_code} Error")
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _safe_error_response(start_response, e)

    return None


def _handle_search_api(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/search"):
        return None

    try:
        from api.search import (
            EstimateRequest,
            SearchRequest,
            estimate_search,
            get_enemy_choices,
            list_search_history,
            run_search,
            save_search_history,
        )
    except Exception as e:
        return _json(start_response, {"error": f"search import failed: {e}"}, "500 Internal Server Error")

    try:
        if path == "/api/search/catalog" and method == "GET":
            scope = _parse_qs(environ).get("scope", "全部装备")
            from games.endfield.data_loading.equipment_catalog import get_equipment_catalog as load_catalog

            catalog = load_catalog(scope_label=scope)
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

        if path == "/api/search/enemies" and method == "GET":
            return _json(start_response, get_enemy_choices())

        if path == "/api/search/history" and method == "GET":
            return _json(start_response, list_search_history())

        if path == "/api/search/history" and method == "POST":
            raw = _read_body(environ)
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            return _json(start_response, save_search_history(payload))

        if method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))

            if path == "/api/search/estimate":
                return _post_json_handler(start_response, payload, lambda p: estimate_search(EstimateRequest(**p)))

            if path == "/api/search/run":
                return _post_json_handler(start_response, payload, lambda p: run_search(SearchRequest(**p)))

            if path == "/api/search/run_stream":
                return _json(
                    start_response,
                    {
                        "error": (
                            "run_stream not supported on PythonAnywhere; use local backend or POST /api/search/run"
                        ),
                        "code": "pa_stream_unsupported",
                    },
                    "501 Not Implemented",
                )
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown search endpoint", 404)


def _handle_manual_buff(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/manual-buff"):
        return None

    try:
        from api.endfield.manual_buff import (
            ActiveKeysRequest,
            ApplyConsumableRequest,
            abnormal_matrix_specs,
            active_keys,
            apply_consumable,
            list_consumable_presets,
            list_zone_options,
        )
    except Exception as e:
        return _json(start_response, {"error": f"manual-buff import failed: {e}"}, "500 Internal Server Error")

    try:
        if path == "/api/manual-buff/zone-options" and method == "GET":
            return _json(start_response, list_zone_options())

        if path == "/api/manual-buff/abnormal-matrix-specs" and method == "GET":
            return _json(start_response, abnormal_matrix_specs())

        if path == "/api/manual-buff/consumable-presets" and method == "GET":
            return _json(start_response, list_consumable_presets())

        if method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))

            if path == "/api/manual-buff/active-keys":
                return _json(start_response, active_keys(ActiveKeysRequest(**payload)))

            if path == "/api/manual-buff/apply-consumable":
                return _json(start_response, apply_consumable(ApplyConsumableRequest(**payload)))
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown manual-buff endpoint", 404)


def _handle_survival(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if path != "/api/survival/estimate" or method != "POST":
        return None

    try:
        from api.endfield.survival import SurvivalEstimateRequest, survival_estimate
    except Exception as e:
        return _json(start_response, {"error": f"survival import failed: {e}"}, "500 Internal Server Error")

    try:
        raw = _read_body(environ)
        if not raw:
            return _http_error(start_response, "empty body", 400)
        payload = json.loads(raw.decode("utf-8"))
        return _json(start_response, survival_estimate(SurvivalEstimateRequest(**payload)))
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _safe_error_response(start_response, e)


def _parse_multipart_file(environ) -> tuple[str, bytes]:
    """从 multipart/form-data 读取上传文件（字段名 file）。"""
    import cgi

    content_type = environ.get("CONTENT_TYPE", "")
    if "multipart/form-data" not in content_type:
        return "upload.calcpack", b""
    form = cgi.FieldStorage(
        fp=environ["wsgi.input"],
        environ=environ,
        keep_blank_values=True,
    )
    if "file" not in form:
        return "upload.calcpack", b""
    item = form["file"]
    if isinstance(item, list):
        item = item[0]
    filename = getattr(item, "filename", None) or "upload.calcpack"
    file_obj = getattr(item, "file", None)
    return filename, file_obj.read() if file_obj else b""


def _handle_hub(environ, start_response):
    """配置包市场 API（SQLite + 文件存储，PA 可写目录）。"""
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/hub"):
        return None

    try:
        from hub.storage import (
            create_pack,
            delete_pack,
            get_pack,
            get_pack_file_path,
            increment_download,
            list_packs,
            rate_pack,
            save_pack_file,
            update_pack,
            validate_calcpack_archive,
        )
    except Exception as e:
        return _json(start_response, {"error": f"hub import failed: {e}"}, "500 Internal Server Error")

    try:
        # ── 写操作（POST/DELETE）需要管理员认证 ──
        if method in ("POST", "DELETE"):
            err = _verify_admin_token_wsgi(environ)
            if err:
                return _json(start_response, {"detail": err}, "401 Unauthorized")

        if path == "/api/hub/stats" and method == "GET":
            _packs, total = list_packs(limit=0)
            return _json(start_response, {"total_packs": total})

        if path == "/api/hub/packs" and method == "GET":
            qs = _parse_qs(environ)
            packs, total = list_packs(
                search=qs.get("search", ""),
                tag=qs.get("tag", ""),
                sort=qs.get("sort", "updated_at"),
                order=qs.get("order", "desc"),
                offset=int(qs.get("offset", "0") or 0),
                limit=int(qs.get("limit", "20") or 20),
            )
            return _json(
                start_response,
                {
                    "packs": packs,
                    "total": total,
                    "offset": int(qs.get("offset", "0") or 0),
                    "limit": int(qs.get("limit", "20") or 20),
                },
            )

        if path == "/api/hub/packs" and method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))
            result = create_pack(
                name=str(payload.get("name", "")).strip(),
                version=str(payload.get("version", "")).strip(),
                description=str(payload.get("description", "")),
                author=str(payload.get("author", "")),
                tags=list(payload.get("tags") or []),
            )
            return _json(
                start_response,
                {
                    "id": result.id,
                    "name": result.name,
                    "version": result.version,
                    "message": "上传成功",
                },
                "201 Created",
            )

        m = re.match(r"^/api/hub/packs/([^/]+)$", path)
        if m and method == "GET":
            pack = get_pack(m.group(1))
            if pack is None:
                return _http_error(start_response, "包不存在", 404)
            return _json(start_response, pack)

        if m and method == "PUT":
            pack_id = m.group(1)
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))
            update_pack(
                pack_id,
                name=str(payload.get("name", "")).strip() or None,
                version=str(payload.get("version", "")).strip() or None,
                description=str(payload.get("description", "")) or None,
            )
            return _json(start_response, {"status": "updated", "id": pack_id})

        if m and method == "DELETE":
            pack_id = m.group(1)
            delete_pack(pack_id)
            return _json(start_response, {"status": "deleted", "id": pack_id})

        m = re.match(r"^/api/hub/packs/([^/]+)/upload$", path)
        if m and method == "POST":
            pack_id = m.group(1)
            if get_pack(pack_id) is None:
                return _http_error(start_response, "包不存在", 404)
            filename, content = _parse_multipart_file(environ)
            if not content:
                return _http_error(start_response, "未收到文件", 400)
            ok, err, meta = validate_calcpack_archive(content)
            if not ok:
                return _http_error(start_response, f"配置包无效: {err}", 400)
            saved = save_pack_file(pack_id, content, filename)
            pack = get_pack(pack_id) or {}
            game = str(meta.get("game") or "").strip()
            tags = list(pack.get("tags") or [])
            if game and game not in tags:
                tags.append(game)
            update_pack(pack_id, file_size=saved.stat().st_size, tags=tags)
            return _json(start_response, {"filename": filename, "size": saved.stat().st_size, "game": game})

        m = re.match(r"^/api/hub/packs/([^/]+)/download/(.+)$", path)
        if m and method == "GET":
            pack_id = m.group(1)
            filename = unquote(m.group(2))
            if get_pack(pack_id) is None:
                return _http_error(start_response, "包不存在", 404)
            file_path = get_pack_file_path(pack_id, filename)
            if file_path is None:
                return _http_error(start_response, "文件不存在", 404)
            increment_download(pack_id)
            body = file_path.read_bytes()
            headers = [
                ("Content-Type", "application/octet-stream"),
                ("Content-Disposition", f'attachment; filename="{filename}"'),
                ("Content-Length", str(len(body))),
            ]
            start_response("200 OK", headers)
            return [body]

        m = re.match(r"^/api/hub/packs/([^/]+)/rate$", path)
        if m and method == "POST":
            pack_id = m.group(1)
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))
            result = rate_pack(
                pack_id,
                score=int(payload.get("score", 0)),
                comment=str(payload.get("comment", "")),
            )
            if result is None:
                return _http_error(start_response, "包不存在", 404)
            return _json(
                start_response,
                {"rating": result["rating"], "rating_count": result["rating_count"]},
            )
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown hub endpoint", 404)


def _handle_pack(environ, start_response):
    """Web 配置包设计器：主题默认值 + .calcpack 导出。"""
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/pack"):
        return None

    try:
        from api.packaging.pack import (
            DEFAULT_THEME,
            ExportRequest,
            export_calcpack_bytes,
            export_preview,
        )
    except Exception as e:
        return _json(start_response, {"error": f"pack import failed: {e}"}, "500 Internal Server Error")

    try:
        if path == "/api/pack/theme/default" and method == "GET":
            return _json(start_response, DEFAULT_THEME)

        if method == "POST":
            raw = _read_body(environ)
            if not raw:
                return _http_error(start_response, "empty body", 400)
            payload = json.loads(raw.decode("utf-8"))
            req = ExportRequest(**payload)

            if path == "/api/pack/export/preview":
                return _json(start_response, export_preview(req))

            if path == "/api/pack/export":
                body, filename = export_calcpack_bytes(req)
                headers = [
                    ("Content-Type", "application/zip"),
                    ("Content-Disposition", f'attachment; filename="{filename}"'),
                    ("Content-Length", str(len(body))),
                ]
                start_response("200 OK", headers)
                return [body]
    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown pack endpoint", 404)


def _handle_adapters(environ, start_response):
    """适配器列表与 meta.json（Web 配置包设计器导出模板）。"""
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/adapters"):
        return None

    adapter_root = _BASE / "framework" / "adapters"
    try:
        if path == "/api/adapters" and method == "GET":
            results = []
            for apath in adapter_root.iterdir():
                meta_file = apath / "meta.json"
                if not meta_file.is_file():
                    continue
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                results.append(
                    {
                        "id": apath.name,
                        "name": meta.get("name", apath.name),
                        "game": meta.get("game", ""),
                        "version": meta.get("version", ""),
                        "description": meta.get("description", ""),
                    }
                )
            return _json(start_response, results)

        m = re.match(r"^/api/adapters/([^/]+)/meta$", path)
        if m and method == "GET":
            meta_file = adapter_root / m.group(1) / "meta.json"
            if not meta_file.is_file():
                return _http_error(start_response, f"adapter not found: {m.group(1)}", 404)
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            return _json(start_response, {"id": m.group(1), "meta": meta})

        m = re.match(r"^/api/adapters/([^/]+)/(layout|dag|data-summary|pack-bundle)$", path)
        if m and method == "GET":
            from api.adapter_lib.assets import (
                data_entity_summary,
                get_adapter_dag,
                get_adapter_layout,
                get_pack_export_bundle,
            )

            aid = m.group(1)
            action = m.group(2)
            if action == "layout":
                return _json(start_response, get_adapter_layout(aid))
            if action == "dag":
                return _json(start_response, get_adapter_dag(aid))
            if action == "data-summary":
                return _json(start_response, {"entities": data_entity_summary(aid)})
            if action == "pack-bundle":
                return _json(start_response, get_pack_export_bundle(aid))
    except Exception as e:
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown adapters endpoint", 404)


def _handle_history_and_download(environ, start_response):
    """计算历史 + 本地搜索服务器下载（PA 上 FastAPI 不跑，须 WSGI 处理）。"""
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/api/history":
        try:
            from api.history import list_history_payload, save_history_payload
        except Exception as e:
            return _json(start_response, {"error": f"history import failed: {e}"}, "500 Internal Server Error")
        try:
            if method == "GET":
                return _json(start_response, list_history_payload())
            if method == "POST":
                raw = _read_body(environ)
                if not raw:
                    return _http_error(start_response, "empty body", 400)
                payload = json.loads(raw.decode("utf-8"))
                return _json(start_response, save_history_payload(payload))
        except json.JSONDecodeError:
            return _http_error(start_response, "invalid JSON", 400)
        except Exception as e:
            return _safe_error_response(start_response, e)
        return _http_error(start_response, "method not allowed", 405)

    if path in ("/api/download/client", "/local-backend.zip") and method == "GET":
        try:
            from api.internal.download_client import build_client_download

            body, filename, ctype = build_client_download()
            return _bytes(
                start_response,
                body,
                ctype,
                extra_headers=[("Content-Disposition", f'attachment; filename="{filename}"')],
            )
        except Exception as e:
            return _safe_error_response(start_response, e)

    return None


def _handle_arknights(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/arknights"):
        return None

    try:
        from api.arknights import (
            ComputeRequest,
            compute_damage_payload,
            list_operators_payload,
            operator_summary_payload,
        )
        from fastapi import HTTPException
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
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown arknights endpoint", 404)


def _safe_error_response(start_response, exc: Exception) -> list:
    """日志记录异常并返回通用错误响应（不泄露内部信息）。"""
    logger.error("WSGI handler error: %s", exc, exc_info=exc)
    return _json(start_response, {"error": "服务器内部错误"}, "500 Internal Server Error")


def _verify_admin_token_wsgi(environ) -> str | None:
    """WSGI 版管理 Token 校验（FastAPI 路由用 Depends，WSGI 只能手动校验）。"""
    configured = os.environ.get("CALC_ADMIN_TOKEN", "").strip()
    if not configured:
        return "管理接口未配置，请联系管理员"
    token = environ.get("HTTP_X_ADMIN_TOKEN", "").strip()
    if not token:
        return "缺少管理 Token"
    if not secrets.compare_digest(token, configured):
        return "管理 Token 无效"
    return None


# ── WSGI 允许的来源（与 FastAPI cors.py / csrf.py 保持一致） ──
_WSGI_ALLOWED_ORIGINS = frozenset(
    {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # 生产环境可扩展：
        # "https://wxhwwla.pythonanywhere.com",
    }
)


def _check_csrf_wsgi(environ) -> str | None:
    """WSGI 版 CSRF 校验 — 校验 Origin/Referer 头是否在允许来源中。

    仅对非安全方法（POST/PUT/DELETE）且非已认证路径进行校验。
    返回 None 表示通过，返回字符串表示错误信息。
    """
    if os.environ.get("CALC_DISABLE_CSRF", "").strip().lower() in ("1", "true", "yes", "on"):
        return None

    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method in ("GET", "HEAD", "OPTIONS"):
        return None

    path = _fix_path(environ.get("PATH_INFO", ""))
    # 已受 Token 认证保护的路径跳过 CSRF（双重认证无意义）
    if any(path.startswith(p) for p in ("/api/admin", "/api/download", "/api/data")):
        return None

    origin = (environ.get("HTTP_ORIGIN", "") or "").strip().rstrip("/")
    if origin:
        if origin in _WSGI_ALLOWED_ORIGINS:
            return None
        return f"CSRF 校验失败：来源 {origin} 不被允许"

    referer = (environ.get("HTTP_REFERER", "") or "").strip().rstrip("/")
    if referer:
        for allowed in _WSGI_ALLOWED_ORIGINS:
            if referer.startswith(allowed):
                return None

    return "CSRF 校验失败：缺少 Origin/Referer 头或来源不被允许"


def _handle_data_write(environ, start_response, path: str, method: str) -> list | None:
    """POST/PUT/DELETE /api/data/* 与公式反推（PA WSGI）。"""
    if not path.startswith("/api/data"):
        return None
    if method == "GET":
        return None
    err = _verify_admin_token_wsgi(environ)
    if err:
        return _json(start_response, {"detail": err}, "401 Unauthorized")

    sub = path[len("/api/data/") :] if path.startswith("/api/data/") else ""

    try:
        from api.entity.mutations import (
            create_character,
            create_equipment,
            create_weapon,
            delete_character,
            delete_equipment,
            delete_weapon,
            inverse_formula_payload,
            inverse_milestones_payload,
            inverse_segment_payload,
            update_character,
            update_equipment,
            update_weapon,
        )
        from api.entity.profiles import (
            create_entity_row,
            delete_entity_row,
            update_entity_row,
        )

        if path == "/api/data/inverse/segment" and method == "POST":
            raw = _read_body(environ)
            payload = json.loads(raw.decode("utf-8"))
            return _json(
                start_response,
                inverse_segment_payload(
                    game=payload.get("game", "endfield"),
                    blueprint_id=payload["blueprint_id"],
                    segment_key=payload["segment_key"],
                    values=payload["values"],
                    rarity=int(payload.get("rarity", 6)),
                    max_error=float(payload.get("max_error", 0.05)),
                ),
            )

        if path == "/api/data/inverse/milestones" and method == "POST":
            raw = _read_body(environ)
            payload = json.loads(raw.decode("utf-8"))
            return _json(
                start_response,
                inverse_milestones_payload(
                    payload["operator"],
                    max_error=float(payload.get("max_error", 0.05)),
                ),
            )

        if path == "/api/data/inverse" and method == "POST":
            raw = _read_body(environ)
            payload = json.loads(raw.decode("utf-8"))
            return _json(
                start_response,
                inverse_formula_payload(
                    payload["type"],
                    payload["values"],
                    max_error=float(payload.get("max_error", 0.05)),
                ),
            )

        raw = _read_body(environ)
        if method in ("POST", "PUT", "DELETE") and not raw and not sub.startswith("profiles/"):
            return _http_error(start_response, "empty body", 400)
        payload = json.loads(raw.decode("utf-8")) if raw else {}

        if sub.startswith("profiles/"):
            m = re.match(r"^profiles/([^/]+)/([^/]+)$", sub)
            if method == "POST" and m:
                return _json(start_response, create_entity_row(m.group(1), m.group(2), payload))
            m = re.match(r"^profiles/([^/]+)/([^/]+)/(.+)$", sub)
            if m and method == "PUT":
                return _json(
                    start_response,
                    update_entity_row(m.group(1), m.group(2), unquote(m.group(3)), payload),
                )
            if m and method == "DELETE":
                return _json(
                    start_response,
                    delete_entity_row(m.group(1), m.group(2), unquote(m.group(3))),
                )

        if method == "POST":
            if sub == "characters":
                return _json(start_response, create_character(payload))
            if sub == "weapons":
                return _json(start_response, create_weapon(payload))
            if sub == "equipments":
                return _json(start_response, create_equipment(payload))

        if method == "PUT":
            m = re.match(r"^characters/(.+)$", sub)
            if m:
                return _json(start_response, update_character(unquote(m.group(1)), payload))
            m = re.match(r"^weapons/(.+)$", sub)
            if m:
                return _json(start_response, update_weapon(unquote(m.group(1)), payload))
            m = re.match(r"^equipments/(.+)$", sub)
            if m:
                return _json(start_response, update_equipment(unquote(m.group(1)), payload))

        if method == "DELETE":
            m = re.match(r"^characters/(.+)$", sub)
            if m:
                return _json(start_response, delete_character(unquote(m.group(1))))
            m = re.match(r"^weapons/(.+)$", sub)
            if m:
                return _json(start_response, delete_weapon(unquote(m.group(1))))
            m = re.match(r"^equipments/(.+)$", sub)
            if m:
                return _json(start_response, delete_equipment(unquote(m.group(1))))

    except json.JSONDecodeError:
        return _http_error(start_response, "invalid JSON", 400)
    except Exception as e:
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown data write endpoint", 404)


def _handle_data_api(environ, start_response):
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/api/health":
        return _json(start_response, {"status": "ok", "version": "1.0.0"})

    if path == "/api/search/catalog":
        return _handle_search_api(environ, start_response)

    if not path.startswith("/api/data/"):
        return None

    write_result = _handle_data_write(environ, start_response, path, method)
    if write_result is not None:
        return write_result

    if method != "GET":
        return _http_error(start_response, "not supported", 501)

    sub = path[len("/api/data/") :]

    if sub == "profiles":
        from api.entity.profiles import profiles_metadata

        return _json(start_response, profiles_metadata())

    m = re.match(r"^profiles/([^/]+)/([^/]+)/detail/all$", sub)
    if m:
        from api.entity.profiles import list_entity_rows

        return _json(start_response, list_entity_rows(m.group(1), m.group(2), full=True))

    m = re.match(r"^profiles/([^/]+)/([^/]+)$", sub)
    if m:
        from api.entity.profiles import list_entity_rows

        return _json(start_response, list_entity_rows(m.group(1), m.group(2)))

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
        if not d:
            return _http_error(start_response, "not found", 404)
        from urllib.parse import parse_qs

        from web.backend.data_materialize import format_entity_list, parse_entity_format

        fmt = parse_entity_format(parse_qs(environ.get("QUERY_STRING", "")).get("format", [None])[0])
        return _json(start_response, format_entity_list(d, fmt, kind="character"))
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
        from urllib.parse import parse_qs

        from web.backend.data_materialize import format_character_entity, parse_entity_format

        fmt = parse_entity_format(parse_qs(environ.get("QUERY_STRING", "")).get("format", [None])[0])
        for c in _read_json(_DATA / "characters.json") or []:
            if c.get("名称") == n:
                return _json(start_response, format_character_entity(c, fmt))
        return _http_error(start_response, f"not found: {n}", 404)

    if sub == "weapons/detail/all":
        d = _read_json(_DATA / "weapons.json")
        if not d:
            return _http_error(start_response, "not found", 404)
        from urllib.parse import parse_qs

        from web.backend.data_materialize import format_entity_list, parse_entity_format

        fmt = parse_entity_format(parse_qs(environ.get("QUERY_STRING", "")).get("format", [None])[0])
        return _json(start_response, format_entity_list(d, fmt, kind="weapon"))
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
        from urllib.parse import parse_qs

        from web.backend.data_materialize import format_weapon_entity, parse_entity_format

        fmt = parse_entity_format(parse_qs(environ.get("QUERY_STRING", "")).get("format", [None])[0])
        for w in _read_json(_DATA / "weapons.json") or []:
            if w.get("名称") == n:
                return _json(start_response, format_weapon_entity(w, fmt))
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


def _handle_generator_api(environ, start_response):
    """生成器 API：模板列表/详情/生成（PA 仅支持只读端点）。"""
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/generator"):
        return None

    try:
        from api.generator import get_template_detail, get_templates
    except Exception as e:
        return _json(start_response, {"error": f"generator import failed: {e}"}, "500 Internal Server Error")

    try:
        if path == "/api/generator/templates" and method == "GET":
            return _json(start_response, get_templates())

        m = re.match(r"^/api/generator/templates/([^/]+)$", path)
        if m and method == "GET":
            return _json(start_response, get_template_detail(m.group(1)))

        if method == "POST":
            return _json(
                start_response,
                {
                    "error": "generator POST endpoints require the local backend (FastAPI). "
                    "Use the desktop client or run the local search server.",
                    "code": "pa_generator_unsupported",
                },
                "501 Not Implemented",
            )
    except Exception as e:
        return _safe_error_response(start_response, e)

    return _http_error(start_response, "unknown generator endpoint", 404)


def _handle_admin_unpack(environ, start_response):
    """管理端点：解压 dist.zip（POST 启动 / GET 查询状态）。

    POST: 后台启动 unzip 子进程，立即返回。需要管理 Token。
    GET: 返回解压状态（done/count/error）。
    """
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if not path.startswith("/api/admin/unpack-dist"):
        return None

    import subprocess

    zip_path = _BASE / "web" / "frontend" / "dist.zip"
    dist_dir = _BASE / "web" / "frontend" / "dist"
    status_file = _BASE / "web" / "frontend" / ".unpack_status.json"

    if method == "GET":
        if status_file.is_file():
            try:
                status = json.loads(status_file.read_text(encoding="utf-8"))
                return _json(start_response, status)
            except Exception:
                return _json(start_response, {"done": False, "status": "error reading status"})
        # 检查是否已经解压过（dist/ 有文件且 dist.zip 不存在）
        if dist_dir.is_dir() and not zip_path.is_file():
            return _json(start_response, {"done": True, "files": "already extracted"})
        return _json(start_response, {"done": False, "status": "not started"})

    if method != "POST":
        return None

    # ── POST 写操作需要管理 Token ──
    err = _verify_admin_token_wsgi(environ)
    if err:
        return _json(start_response, {"detail": err}, "401 Unauthorized")

    if not zip_path.is_file():
        return _http_error(start_response, f"dist.zip not found: {zip_path}", 404)

    # 后台解压（避免 WSGI 超时）
    script = (
        f"rm -rf {dist_dir} && mkdir -p {dist_dir} && "
        f"cd {dist_dir} && unzip -oq {zip_path} && "
        f"rm -f {zip_path} && "
        f"echo '{{\"done\":true,\"files\":'$(ls -1 | wc -l)'}}' > {status_file}"
    )
    try:
        subprocess.Popen(["bash", "-c", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return _json(start_response, {"ok": True, "status": "unpack started in background"})
    except Exception as e:
        return _safe_error_response(start_response, e)


def _handle_admin_deploy(environ, start_response):
    """管理端点：git pull + npm build（POST 启动 / GET 查状态）。

    部署新版本只需两步：
      1. git push
      2. curl -X POST -H 'X-Admin-Token: xxx' https://xxx.pythonanywhere.com/api/admin/deploy
      3. 等待 2-3 分钟，在 PA Web 页面 Reload
    """
    path = _fix_path(environ.get("PATH_INFO", ""))
    method = environ.get("REQUEST_METHOD", "GET")
    if path != "/api/admin/deploy":
        return None

    import subprocess

    status_file = _BASE / ".deploy_status.json"

    if method == "GET":
        if status_file.is_file():
            try:
                return _json(start_response, json.loads(status_file.read_text(encoding="utf-8")))
            except Exception:
                pass
        return _json(start_response, {"done": False, "status": "idle"})

    if method != "POST":
        return None

    # ── POST 写操作需要管理 Token ──
    err = _verify_admin_token_wsgi(environ)
    if err:
        return _json(start_response, {"detail": err}, "401 Unauthorized")

    script = (
        f"cd {_BASE} && "
        f"git pull origin develop 2>&1 && "
        f"cd web/frontend && npm install --silent 2>&1 && npm run build 2>&1 && "
        f'echo \'{{"done":true,"status":"ok"}}\' > {status_file} || '
        f'echo \'{{"done":false,"status":"failed"}}\' > {status_file}'
    )
    try:
        subprocess.Popen(["bash", "-c", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return _json(start_response, {"ok": True, "status": "deploy started"})
    except Exception as e:
        return _safe_error_response(start_response, e)


def application(environ, start_response):
    # ── CSRF 校验（对所有非安全方法，例外路径跳过） ──
    csrf_err = _check_csrf_wsgi(environ)
    if csrf_err:
        logger.warning("WSGI CSRF 拒绝: %s", csrf_err)
        return _json(start_response, {"detail": csrf_err}, "403 Forbidden")

    for handler in (
        _handle_admin_deploy,
        _handle_donation,
        _handle_layout_compute,
        _handle_search_api,
        _handle_generator_api,
        _handle_admin_unpack,
        _handle_hub,
        _handle_pack,
        _handle_adapters,
        _handle_history_and_download,
        _handle_manual_buff,
        _handle_survival,
        _handle_arknights,
        _handle_data_api,
    ):
        result = handler(environ, start_response)
        if result is not None:
            return result

    path = environ.get("PATH_INFO", "")
    fp = _DIST / (path.lstrip("/") if path not in ("", "/") else "index.html")
    if not fp.is_file():
        fp = _DIST / "index.html"
    if fp.is_file():
        return _serve_static_file(environ, start_response, fp)
    start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
    return [b"Not Found"]
