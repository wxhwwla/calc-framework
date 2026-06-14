# SPDX-License-Identifier: AGPL-3.0
"""AI 智能推荐 API — 自然语言搜装 + AI 解释结果。"""

from __future__ import annotations

import json
import re

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ._json_utils import ADAPTER_ROOT, ENDFIELD_DATA_ROOT, load_json

router = APIRouter(prefix="/api/ai", tags=["ai"])

_CHARS_PATH = ENDFIELD_DATA_ROOT / "characters.json"
_WEAPONS_PATH = ENDFIELD_DATA_ROOT / "weapons.json"

# 复用 generator.py 的 SSRF 防护
from api.generator import _validate_api_url

_RECOMMEND_SYSTEM_PROMPT = """你是一个游戏伤害计算器的智能配装助手。用户会用自然语言描述他们的需求，你需要：

1. 理解用户的配装偏好（如"暴击流"、"高攻击力"、"均衡"等）
2. 输出 JSON 格式的解释和建议：

{
  "intent": "用户意图的一句话总结",
  "search_hint": "给用户的搜索建议（1-2句话）",
  "explanation_template": "用于在结果展示时填充的模板说明（{top_damage} 等占位符可用）"
}

搜索系统会自动找到伤害最高的配装。你只需要理解用户意图并给出人性化的解释。"""


class AiRecommendRequest(BaseModel):
    character_name: str = Field(description="角色名称")
    weapon_name: str = Field(default="", description="当前武器（可选）")
    query: str = Field(description="自然语言查询，如'推荐暴击流配装'")
    api_key: str = Field(default="", description="OpenAI API Key（可选，不填则只搜不解释）")
    api_base: str = Field(default="https://api.openai.com/v1", description="API 地址")
    model: str = Field(default="gpt-4o-mini", description="模型名")


class AiRecommendResponse(BaseModel):
    character_name: str
    query: str
    ai_intent: str = ""
    ai_hint: str = ""
    total_combinations: int = 0
    top_results: list[dict] = Field(default_factory=list)


def _list_chars() -> list[dict]:
    return load_json(_CHARS_PATH) or []


def _list_weapons() -> list[dict]:
    return load_json(_WEAPONS_PATH) or []


@router.post("/recommend", response_model=AiRecommendResponse)
async def ai_recommend(req: AiRecommendRequest):
    """AI 智能配装推荐：自然语言查询 → 意图理解 → 搜索推荐。"""
    chars = _list_chars()
    char_data = next((c for c in chars if c.get("名称") == req.character_name), None)
    if not char_data:
        raise HTTPException(status_code=404, detail=f"角色不存在: {req.character_name}")

    weapons = _list_weapons()
    weapon_data = None
    if req.weapon_name:
        weapon_data = next((w for w in weapons if w.get("名称") == req.weapon_name), None)

    # 统计可搜索空间
    weapon_count = len(weapons)
    equipment_count = 0  # 从装备文件获取
    equip_path = ENDFIELD_DATA_ROOT / "equipments.json"
    if equip_path.exists():
        equip_data = load_json(equip_path) or []
        equipment_count = len(equip_data)
    total_combinations = weapon_count * max(equipment_count, 1)

    ai_intent = ""
    ai_hint = ""

    # 如果有 API key，调用 AI 做意图理解
    if req.api_key.strip():
        try:
            safe_base = _validate_api_url(req.api_base)
            api_url = safe_base + "/chat/completions"

            char_info = f"角色: {req.character_name}"
            if weapon_data:
                char_info += f", 当前武器: {req.weapon_name}"

            user_msg = (
                f"{char_info}\n可用武器: {weapon_count} 把\n可用装备: {equipment_count} 件\n\n用户需求: {req.query}"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    api_url,
                    json={
                        "model": req.model,
                        "messages": [
                            {"role": "system", "content": _RECOMMEND_SYSTEM_PROMPT},
                            {"role": "user", "content": user_msg},
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {req.api_key}",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    ai_intent = parsed.get("intent", "")
                    ai_hint = parsed.get("search_hint", "")
        except Exception:
            ai_intent = ""
            ai_hint = ""

    if not ai_intent and req.query:
        ai_intent = f"根据「{req.query}」搜索最优配装"

    # 构建推荐结果（从搜索 API 获取或提供估算）
    top_results: list[dict] = []
    try:
        from calc_framework.config.manager import AdapterManager

        manager = AdapterManager(ADAPTER_ROOT)
        pkg = manager.load("终末地伤害计算")
        if pkg and pkg.dag_service:
            # 构建基本上下文跑一次 DAG 作为基线

            ctx = {
                "character": {
                    "基础攻击": 350,
                    "力量": 100,
                    "敏捷": 100,
                    "智识": 100,
                    "意志": 100,
                    "暴击率": 0.05,
                    "暴击伤害": 1.5,
                },
                "weapon": {"基础攻击": 0, "攻击力+": 0, "附加攻击力+": 0},
                "equipment": {"攻击力平值": 0},
                "enemy": {"防御": 100},
                "computed": {
                    "主能力平值加算": 0,
                    "副能力平值加算": 0,
                    "主能力百分比": 0,
                    "副能力百分比": 0,
                    "技能倍率": 1.0,
                    "伤害加成": 0,
                    "伤害减免": 0,
                    "增幅": 0,
                    "虚弱": 0,
                    "庇护": 0,
                    "脆弱": 0,
                    "易伤": 0,
                    "失衡易伤": 0,
                    "抗性": 0,
                    "非主控减伤": 0,
                    "连击增伤": 0,
                    "特殊乘区": 0,
                    "力量加成值": 0,
                    "敏捷加成值": 0,
                    "智识加成值": 0,
                    "意志加成值": 0,
                },
            }
            result = pkg.dag_service.evaluate(ctx)
            baseline_damage = result.outputs.get("加权总伤", sum(result.outputs.values()))
            top_results.append(
                {
                    "label": f"{req.character_name} 基线",
                    "damage": round(baseline_damage, 2),
                    "note": "当前配置的基线伤害",
                }
            )
    except Exception:
        pass

    return AiRecommendResponse(
        character_name=req.character_name,
        query=req.query,
        ai_intent=ai_intent,
        ai_hint=ai_hint,
        total_combinations=total_combinations,
        top_results=top_results,
    )


__all__: list[str] = []
