# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 服务器 — stdio 端到端测试。"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parents[5]


def _write_template(root: Path) -> None:
    template = root / "framework" / "adapters" / "simple"
    template.mkdir(parents=True)
    (template / "meta.json").write_text(
        json.dumps(
            {"name": "简单模板", "schema_version": "dag-v1", "description": "测试模板", "functions": {}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    docs = root / "docs"
    docs.mkdir()
    (docs / "quickstart.md").write_text("# 快速开始\n\n三步创建计算器。", encoding="utf-8")


def _server_params(project_dir: Path) -> StdioServerParameters:
    env = dict(os.environ)
    paths = [str(REPO_ROOT), str(REPO_ROOT / "framework" / "src")]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "tools.calc_mcp", "--project-dir", str(project_dir)],
        env=env,
        cwd=str(REPO_ROOT),
    )


def _payload(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        if set(structured) == {"result"} and isinstance(structured["result"], dict):
            return structured["result"]
        return structured
    return json.loads(result.content[0].text)


async def _call(session: ClientSession, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    result = await session.call_tool(name, arguments or {})
    payload = _payload(result)
    assert payload.get("ok", True) is not False, f"{name} 失败: {payload}"
    return payload


async def _scenario(project_dir: Path) -> None:
    async with stdio_client(_server_params(project_dir)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            assert len(tools.tools) == 13

            templates = await _call(session, "list_templates")
            assert templates["templates"][0]["id"] == "simple"

            schemas = await _call(session, "describe_schemas")
            assert any(item["type"] == "binary" for item in schemas["nodes"])

            guide = await _call(session, "read_guide", {"topic": "quickstart"})
            assert "三步" in guide["content"]

            generated = await _call(
                session,
                "generate_adapter",
                {
                    "adapter_id": "demo",
                    "display_name": "演示计算器",
                    "game": "演示游戏",
                    "template_id": "simple",
                    "variables": [
                        {"name": "atk", "type": "float", "source": "user_input", "default": 100},
                        {"name": "mult", "type": "float", "source": "user_input", "default": 2},
                        {"name": "def", "type": "float", "source": "enemy", "default": 10},
                    ],
                    "formula_steps": [
                        {"id": "raw", "op": "mul", "lhs": "atk", "rhs": "mult"},
                        {"id": "damage", "op": "sub", "lhs": "raw", "rhs": "def"},
                    ],
                    "outputs": [{"name": "damage", "node": "damage", "label": "伤害"}],
                    "data_files": {"enemy": [{"名称": "测试敌人", "def": 10}]},
                },
            )
            assert generated["adapter_id"] == "demo"

            validated = await _call(session, "validate_adapter", {"adapter_id": "demo"})
            assert validated["valid"] is True, validated["errors"]

            smoke = await _call(
                session,
                "smoke_test_adapter",
                {
                    "adapter_id": "demo",
                    "context": {"user_input": {"atk": 50}, "enemy": {"def": 10}},
                },
            )
            assert smoke["outputs"]["damage"] == 90.0

            files = await _call(session, "list_adapter_files", {"adapter_id": "demo"})
            paths = {item["path"] for item in files["files"]}
            assert "meta.json" in paths
            assert "data/enemies.json" in paths

            meta_file = await _call(session, "read_adapter_file", {"adapter_id": "demo", "path": "meta.json"})
            meta_content = json.loads(meta_file["content"])
            assert meta_content["name"] == "演示计算器"
            assert meta_content["entry_data"] == ["data/enemies.json"]

            written = await _call(
                session,
                "write_adapter_file",
                {"adapter_id": "demo", "path": "notes.md", "content": "# 备注\n测试"},
            )
            assert written["bytes"] > 0

            exported = await _call(
                session,
                "export_calcpack",
                {"adapter_id": "demo", "output_path": "dist/demo.calcpack"},
            )
            assert exported["size_bytes"] > 0
            with zipfile.ZipFile(project_dir / "dist" / "demo.calcpack") as pack:
                assert "data/enemies.json" in pack.namelist()

            imported = await _call(
                session,
                "import_calcpack",
                {"calcpack_path": "dist/demo.calcpack", "adapter_id": "demo_copy"},
            )
            assert imported["validation"]["valid"] is True
            assert (project_dir / "framework" / "adapters" / "demo_copy" / "data" / "enemies.json").is_file()

            revalidated = await _call(session, "validate_adapter", {"adapter_id": "demo_copy"})
            assert revalidated["valid"] is True

            adapters = await _call(session, "list_adapters")
            assert {"demo", "demo_copy"} <= {item["id"] for item in adapters["adapters"]}


def test_stdio_end_to_end(tmp_path: Path) -> None:
    _write_template(tmp_path)

    asyncio.run(asyncio.wait_for(_scenario(tmp_path), timeout=120))
