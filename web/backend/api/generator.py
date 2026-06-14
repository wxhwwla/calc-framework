# SPDX-License-Identifier: AGPL-3.0
"""AI 计算器生成器 API。"""

from __future__ import annotations

import ipaddress
import json
import socket
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/generator", tags=["generator"])

# 导入生成器引擎
try:
    from tools.generator import GeneratorEngine
    from tools.generator import list_templates as list_gen_templates

    engine = GeneratorEngine()
    _HAS_ENGINE = True
except ImportError:
    engine = None
    list_gen_templates = None  # type: ignore[assignment]
    _HAS_ENGINE = False


class FormulaStep(BaseModel):
    id: str
    op: str  # + - * / condition expr
    lhs: str = ""
    rhs: str = ""
    cond: str = ""
    true_val: str = ""
    false_val: str = ""
    expr: str = ""
    input_map: dict[str, str] = {}
    label: str = ""


class VariableDef(BaseModel):
    name: str
    type: str = "float"
    source: str = "user_input"
    default: float | bool = 0
    description: str = ""


class OutputDef(BaseModel):
    name: str
    node: str = ""
    label: str = ""
    format: str = ""
    is_primary: bool = True


class GenerateRequest(BaseModel):
    template_id: str
    game_name: str
    variables: list[VariableDef] = []
    formula_steps: list[FormulaStep] = []
    outputs: list[OutputDef] = []


class AIFormulaRequest(BaseModel):
    """AI 公式解析请求。"""

    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    formula_description: str
    template_id: str = "simple"
    variables_context: list[dict] = []  # 模板已有的变量上下文


class AIFormulaResponse(BaseModel):
    """AI 公式解析响应。"""

    variables: list[dict]
    formula_steps: list[dict]
    outputs: list[dict]
    raw_response: str = ""
    validation_warnings: list[str] = []


class AITestRequest(BaseModel):
    """AI API 连接测试请求。"""

    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"


# AI 系统提示词
AI_SYSTEM_PROMPT = """你是一个游戏伤害计算器的 DAG 公式解析专家。用户会描述一个游戏的伤害公式，你需要将其解析为结构化的 DAG 节点数据。

框架说明：
- variables：输入变量，每个包含 name/type/source/default/description
  - type: float / int / bool / percent
  - source: character / weapon / enemy / user_input
- formula_steps：公式步骤，每步一个运算，包含 id/op/lhs/rhs/label
  - op: + - * / condition expr
  - condition 需要 cond/true_val/false_val
  - expr 需要 expr/input_map
- outputs：计算结果输出，包含 name/node/label/is_primary

请只输出 JSON，不要额外的解释文字。JSON 格式必须严格符合 Python json.loads 可解析。"""


@router.get("/templates")
def get_templates():
    """获取所有可用模板。"""
    if not _HAS_ENGINE:
        # fallback: 读取目录
        adapters_dir = Path(__file__).resolve().parents[3] / "framework" / "adapters"
        templates = {}
        for d in adapters_dir.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                meta_fp = d / "meta.json"
                if meta_fp.exists():
                    meta = json.loads(meta_fp.read_text(encoding="utf-8"))
                    templates[d.name] = {
                        "name": meta.get("name", d.name),
                        "description": meta.get("description", ""),
                    }
        return templates
    assert list_gen_templates is not None  # _HAS_ENGINE=True 时保证已导入
    return list_gen_templates()


@router.get("/templates/{template_id}")
def get_template_detail(template_id: str):
    """获取模板详情，包括文件结构预览。"""
    adapters_dir = Path(__file__).resolve().parents[3] / "framework" / "adapters"
    d = adapters_dir / template_id
    if not d.is_dir():
        raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")

    meta_fp = d / "meta.json"
    if not meta_fp.exists():
        raise HTTPException(status_code=404, detail="模板缺少 meta.json")

    meta = json.loads(meta_fp.read_text(encoding="utf-8"))
    info: dict[str, Any] = {
        "id": template_id,
        "meta": meta,
        "files": [f.name for f in d.iterdir() if f.is_file()],
    }

    # 读取 ui/ 子目录文件
    ui_dir = d / "ui"
    if ui_dir.is_dir():
        info["files"].extend([f"ui/{f.name}" for f in ui_dir.iterdir()])

    # 读取 dag 预览
    entry_dag = meta.get("entry_dag", "")
    if entry_dag:
        dag_paths = [d / entry_dag, d / "dag" / entry_dag]
        for dp in dag_paths:
            if dp.exists():
                dag = json.loads(dp.read_text(encoding="utf-8"))
                info["dag_preview"] = {
                    "variables": len(dag.get("variables", {})),
                    "nodes": len(dag.get("nodes", {})),
                    "outputs": len(dag.get("outputs", {})),
                }
                break

    return info


@router.post("/generate")
def generate_adapter(req: GenerateRequest):
    """生成适配器包。"""
    if not _HAS_ENGINE:
        raise HTTPException(status_code=500, detail="生成器引擎不可用")

    try:
        variables = [v.model_dump() for v in req.variables]
        steps = [s.model_dump() for s in req.formula_steps]
        outputs = [o.model_dump() for o in req.outputs]

        with tempfile.TemporaryDirectory() as tmpdir:
            files = engine.generate(
                req.template_id,
                req.game_name,
                variables=variables if variables else None,
                formula_steps=steps if steps else None,
                outputs=outputs if outputs else None,
                output_dir=tmpdir,
            )

            # 读取生成的文件内容
            result = {}
            for filepath, content in files.items():
                result[filepath] = content

            return {
                "success": True,
                "files": result,
                "file_count": len(result),
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── SSRF 防护 ──────────────────────────────────────

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _validate_api_url(url: str) -> str:
    """校验 API URL 防止 SSRF 攻击。

    Raises:
        HTTPException: URL 指向内网地址、使用非 http(s) 协议、或无法解析。
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail=f"不支持的协议: {parsed.scheme}，仅允许 http/https")

    hostname = parsed.hostname or ""
    if hostname in _LOCAL_HOSTNAMES:
        raise HTTPException(status_code=400, detail=f"禁止访问内部地址: {hostname}")

    # 如果是 IP 地址，检查是否在私有网段
    try:
        ip = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETWORKS:
            if ip in net:
                raise HTTPException(status_code=400, detail=f"禁止访问内网地址: {hostname}")
    except ValueError:
        # 不是 IP 地址（是域名），尝试 DNS 解析（SSRF 防护：验证域名不指向内网）
        try:
            addrs = socket.getaddrinfo(hostname, 80, family=socket.AF_INET)
            for addr in addrs:
                ip_str = addr[4][0]
                ip = ipaddress.ip_address(ip_str)
                for net in _PRIVATE_NETWORKS:
                    if ip in net:
                        raise HTTPException(status_code=400, detail=f"域名 {hostname} 解析到内网地址 {ip_str}，已阻止")
        except socket.gaierror:
            # DNS 解析失败 — 阻止（SSRF 防护：无法验证目标地址安全）
            raise HTTPException(
                status_code=400,
                detail=f"无法解析域名 {hostname}，请检查 API 地址是否正确",
            )

    return url.rstrip("/")


@router.post("/ai/parse")
async def ai_parse_formula(req: AIFormulaRequest):
    """用 AI 解析自然语言公式描述，返回结构化 DAG 数据。"""
    if not req.formula_description:
        raise HTTPException(status_code=400, detail="公式描述不能为空")

    # 构建用户消息
    context_info = ""
    if req.variables_context:
        context_info = f"\n模板已有变量上下文：\n{json.dumps(req.variables_context, ensure_ascii=False, indent=2)}"

    user_message = f"""模板类型：{req.template_id}{context_info}

用户描述的公式：
{req.formula_description}

请解析为 DAG 节点。输出 JSON 格式：
{{
  "variables": [{{"name": "ATK", "type": "float", "source": "character", "default": 100, "description": "攻击力"}}],
  "formula_steps": [{{"id": "step1", "op": "*", "lhs": "ATK", "rhs": "skill_mult", "label": "攻击力×技能倍率"}}],
  "outputs": [{{"name": "最终伤害", "node": "step1", "label": "最终伤害", "is_primary": true}}]
}}"""

    # 调用 LLM API
    if not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API Key 不能为空")
    if not req.api_key.strip().startswith("sk-"):
        raise HTTPException(status_code=400, detail="API Key 格式似乎不正确，应以 sk- 开头")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {req.api_key}",
    }
    payload = {
        "model": req.model,
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    safe_base = _validate_api_url(req.api_base)
    api_url = safe_base + "/chat/completions"
    # 二次验证：确保最终 URL 的 hostname 未被 SSRF 绕过
    _validate_api_url(api_url)

    try:
        # SSRF: api_url 已经 _validate_api_url 校验，确保仅允许 https 外网地址
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(api_url, json=payload, headers=headers)  # nosec: SSRF-checked
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="无法连接到 AI API，请检查 API 地址是否正确")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI 请求超时，请检查网络连接或换用更快的模型")
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 401:
            raise HTTPException(status_code=502, detail="API Key 认证失败，请检查密钥是否正确")
        elif status == 429:
            raise HTTPException(status_code=502, detail="API 请求频率过高，请稍后再试")
        else:
            raise HTTPException(status_code=502, detail=f"AI API 返回错误 (HTTP {status})")
    except Exception:
        raise HTTPException(status_code=502, detail="AI 请求失败，请稍后重试")

    # 解析返回内容
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=502, detail=f"AI 返回格式异常，缺少 choices/content: {e!s}")

    # 尝试提取 JSON
    import re

    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"AI 返回的 JSON 格式无效: {e!s}。原始返回: {content[:200]}")
    else:
        raise HTTPException(status_code=502, detail=f"AI 返回内容中未找到 JSON 数据。原始返回: {content[:200]}")

    # 验证返回的数据结构
    variables = parsed.get("variables", [])
    formula_steps = parsed.get("formula_steps", [])
    outputs = parsed.get("outputs", [])

    if not formula_steps:
        # AI 可能没理解要生成公式步骤，尝试给更友好的提示
        pass

    return AIFormulaResponse(
        variables=variables,
        formula_steps=formula_steps,
        outputs=outputs,
        raw_response=content,
        validation_warnings=_validate_ai_result(variables, formula_steps, outputs),
    )


def _validate_ai_result(variables: list, formula_steps: list, outputs: list) -> list[str]:
    """验证 AI 解析结果，返回警告列表。"""
    warnings = []
    if not variables:
        warnings.append("AI 未识别到任何变量")
    if not formula_steps:
        warnings.append("AI 未识别到任何公式步骤")
    if not outputs:
        warnings.append("AI 未识别到任何输出")

    # 检查 formula_steps 引用的变量是否都在 variables 中
    var_names = {v.get("name", "") for v in variables}
    for step in formula_steps:
        for ref in [
            step.get("lhs", ""),
            step.get("rhs", ""),
            step.get("cond", ""),
            step.get("true_val", ""),
            step.get("false_val", ""),
        ]:
            if ref and ref not in var_names and not ref.replace(".", "").isdigit():
                warnings.append(f"公式步骤 '{step.get('label', step.get('id', ''))}' 引用了未定义的变量 '{ref}'")

    return warnings


@router.post("/ai/test")
async def ai_test_connection(req: AITestRequest):
    """测试 AI API 连接是否正常。"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {req.api_key}",
    }
    payload = {
        "model": req.model,
        "messages": [{"role": "user", "content": "回复 OK 表示连接正常"}],
        "max_tokens": 10,
    }
    safe_base = _validate_api_url(req.api_base)
    api_url = safe_base + "/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(api_url, json=payload, headers=headers)  # nosec: SSRF-checked via _validate_api_url
            resp.raise_for_status()
            data = resp.json()
            return {"status": "ok", "model": data.get("model", "")}
    except Exception as e:
        from web.backend.bridge import get_logger

        get_logger(__name__).warning("AI 连接测试失败: %s", e)
        return {"status": "error", "message": "连接测试失败，请检查 API 地址和密钥"}
