# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""AI 智能推荐 API — 自然语言搜装 + AI 解释结果。"""

from __future__ import annotations

import json
import logging
import re

from api.internal.safe_http import post_chat_completions
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from api.internal.json_utils import ADAPTER_ROOT, ENDFIELD_DATA_ROOT, load_json

router = APIRouter(prefix="/api/ai", tags=["ai"])

_CHARS_PATH = ENDFIELD_DATA_ROOT / "characters.json"
_WEAPONS_PATH = ENDFIELD_DATA_ROOT / "weapons.json"

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
    """AI 配装推荐响应。"""

    character_name: str
    query: str
    ai_intent: str = ""
    ai_hint: str = ""
    total_combinations: int = 0
    top_results: list[dict] = Field(default_factory=list)


def _list_chars() -> list[dict]:
    """加载角色 JSON 数据。"""
    return load_json(_CHARS_PATH) or []


def _list_weapons() -> list[dict]:
    """加载武器 JSON 数据。"""
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
            char_info = f"角色: {req.character_name}"
            if weapon_data:
                char_info += f", 当前武器: {req.weapon_name}"

            user_msg = (
                f"{char_info}\n可用武器: {weapon_count} 把\n可用装备: {equipment_count} 件\n\n用户需求: {req.query}"
            )

            resp = await post_chat_completions(
                req.api_base,
                json_body={
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
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            json_match = re.search(r"\{[^{}]*\}", content)
            if json_match:
                parsed = json.loads(json_match.group())
                ai_intent = parsed.get("intent", "")
                ai_hint = parsed.get("search_hint", "")
        except Exception as exc:
            logger.warning("AI 意图理解失败: %s", exc)
            ai_intent = ""
            ai_hint = ""

    if not ai_intent and req.query:
        ai_intent = f"根据「{req.query}」搜索最优配装"

    # 构建推荐结果（从搜索 API 获取或提供估算）
    top_results: list[dict] = []
    try:
        from calc_framework.config.manager import AdapterManager

        manager = AdapterManager(ADAPTER_ROOT)
        pkg = manager.load("终末地伤害计算（Calc Framework）")
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
    except Exception as exc:
        logger.warning("DAG 基线求值失败: %s", exc)

    return AiRecommendResponse(
        character_name=req.character_name,
        query=req.query,
        ai_intent=ai_intent,
        ai_hint=ai_hint,
        total_combinations=total_combinations,
        top_results=top_results,
    )


# ── AI 结果解释 ──────────────────────────────────────


class ExplainRequest(BaseModel):
    """AI 结果解释请求。"""

    query: str = Field(description="用户的原始查询")
    character_name: str = Field(default="", description="角色名")
    results: list[dict] = Field(description="搜索结果列表 [{label, damage, ...}]")
    api_key: str = Field(default="", description="API Key")
    api_base: str = Field(default="https://api.openai.com/v1")
    model: str = Field(default="gpt-4o-mini")


class ExplainResponse(BaseModel):
    """AI 结果解释响应。"""

    explanation: str
    suggestions: list[str] = Field(default_factory=list)


_EXPLAIN_PROMPT = """你是一个游戏伤害计算器的配装分析专家。用户搜索了最优配装，你需要用通俗易懂的语言解释：

1. 为什么排名第一的配装伤害最高
2. 它相比其他配装的优势在哪里
3. 给用户的下一步建议（可以微调哪些参数获得更好的结果）

输出 JSON：
{
  "explanation": "详细解释（2-3句话）",
  "suggestions": ["建议1", "建议2"]
}"""


@router.post("/explain", response_model=ExplainResponse)
async def ai_explain(req: ExplainRequest):
    """AI 解释搜索结果——为什么这个配装最好，如何进一步优化。"""
    if not req.api_key.strip():
        if not req.results:
            return ExplainResponse(
                explanation=f"共搜索到 {len(req.results)} 个配装方案。",
                suggestions=["填入 API Key 可获得 AI 详细解释"],
            )
        return ExplainResponse(
            explanation=(
                f"共搜索到 {len(req.results)} 个配装方案。"
                f"排名第一:「{req.results[0].get('label', '?')}」"
                f"伤害 {req.results[0].get('damage', 0)}。"
            ),
            suggestions=["填入 API Key 可获得 AI 详细解释"],
        )

    results_text = "\n".join(
        f"#{i + 1} {r.get('label', '?')}: 伤害 {r.get('damage', 0)}" for i, r in enumerate(req.results[:5])
    )

    user_msg = f"角色: {req.character_name}\n用户查询: {req.query}\n\n搜索结果:\n{results_text}"

    try:
        resp = await post_chat_completions(
            req.api_base,
            json_body={
                "model": req.model,
                "messages": [
                    {"role": "system", "content": _EXPLAIN_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.5,
                "response_format": {"type": "json_object"},
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {req.api_key}",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        json_match = re.search(r"\{[^{}]*\}", content)
        if json_match:
            parsed = json.loads(json_match.group())
            return ExplainResponse(
                explanation=parsed.get("explanation", ""),
                suggestions=parsed.get("suggestions", []),
            )
    except Exception as e:
        top_info = (
            f"排名第一: {req.results[0].get('label', '?')} (伤害 {req.results[0].get('damage', 0)})"
            if req.results
            else "无结果"
        )
        logger.warning("AI 解释失败: %s", e)
        return ExplainResponse(
            explanation=top_info,
            suggestions=["AI 解释失败，请稍后重试"],
        )

    return ExplainResponse(explanation="", suggestions=[])


# ── AI 语义搜索 ──────────────────────────────────────


class SearchRequest(BaseModel):
    """AI 语义搜索请求。"""

    query: str = Field(description="自然语言搜索，如'暴击率最高的单手剑'")
    category: str = Field(default="weapons", description="搜索类别: characters / weapons / equipments")
    api_key: str = Field(default="", description="API Key（可选，不填则用关键词匹配）")
    api_base: str = Field(default="https://api.openai.com/v1")
    model: str = Field(default="gpt-4o-mini")


class SearchResponse(BaseModel):
    """AI 语义搜索响应。"""

    query: str
    category: str
    results: list[dict] = Field(default_factory=list)
    ai_refined: bool = False


_SEARCH_PROMPT = """你是一个游戏数据搜索助手。根据用户的自然语言查询，从给出的数据列表中筛选最匹配的条目。

输出 JSON:
{
  "matches": ["条目名称1", "条目名称2"],
  "reasoning": "为什么这些最匹配"
}"""


@router.post("/search", response_model=SearchResponse)
async def ai_search(req: SearchRequest):
    """AI 语义搜索——用人话搜索角色/武器/装备。"""
    # 加载数据
    if req.category == "characters":
        items = _list_chars()
    elif req.category == "weapons":
        items = _list_weapons()
    else:
        equip_path = ENDFIELD_DATA_ROOT / "equipments.json"
        items = (load_json(equip_path) or []) if equip_path.exists() else []

    names = [it.get("名称", "") for it in items if it.get("名称")]
    if not names:
        return SearchResponse(query=req.query, category=req.category)

    results: list[dict] = []
    ai_refined = False

    # 先用关键词做基础匹配
    keywords = req.query.replace("的", " ").replace("最", " ").split()
    for it in items:
        name = it.get("名称", "")
        type_str = str(it.get("类型", ""))
        star_str = str(it.get("星级", ""))
        score = sum(1 for kw in keywords if kw in name or kw in type_str or kw in star_str)
        if score > 0:
            results.append({**it, "_score": score})

    results.sort(key=lambda x: x.get("_score", 0), reverse=True)

    # 如果有 API key，用 AI 精排
    if req.api_key.strip() and len(names) <= 50:
        try:
            item_list = "\n".join(f"- {n}" for n in names[:50])
            user_msg = f"数据列表:\n{item_list}\n\n用户查询: {req.query}"

            resp = await post_chat_completions(
                req.api_base,
                json_body={
                    "model": req.model,
                    "messages": [
                        {"role": "system", "content": _SEARCH_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {req.api_key}",
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            json_match = re.search(r"\{[^{}]*\}", content)
            if json_match:
                parsed = json.loads(json_match.group())
                ai_matches = parsed.get("matches", [])
                # AI 结果排到最前
                ai_results = [it for m in ai_matches for it in items if it.get("名称") == m]
                existing_names = {r.get("名称") for r in results}
                for ar in ai_results:
                    if ar.get("名称") not in existing_names:
                        results.insert(0, {**ar, "_score": 99})
                ai_refined = True
        except Exception as exc:
            logger.warning("AI 搜索精排失败: %s", exc)

    return SearchResponse(
        query=req.query,
        category=req.category,
        results=results[:20],
        ai_refined=ai_refined,
    )


# ── AI 对话配装（多轮）───────────────────────────────


class ConversationRequest(BaseModel):
    """AI 多轮对话请求。"""

    messages: list[dict] = Field(description="对话历史 [{role, content}]")
    character_name: str = Field(default="", description="当前角色")
    api_key: str = Field(default="", description="API Key")
    api_base: str = Field(default="https://api.openai.com/v1")
    model: str = Field(default="gpt-4o-mini")


class ConversationResponse(BaseModel):
    """AI 多轮对话响应。"""

    reply: str
    action: str = ""  # "search" / "adjust" / "explain" / "none"


_CONVERSATION_PROMPT = """你是一个游戏伤害计算器的配装顾问。你可以帮用户：
- 推荐配装方向（暴击流、攻击流、均衡流）
- 解释为什么某种配装更好
- 建议下一步搜索参数

当前可用功能：搜索最优配装、对比方案、查看伤害明细。

输出 JSON:
{
  "reply": "自然语言回复",
  "action": "none"
}
action 可以是: none（纯对话）/ search（建议用户搜索）/ explain（解释结果）"""


@router.post("/chat", response_model=ConversationResponse)
async def ai_chat(req: ConversationRequest):
    """AI 多轮对话配装咨询。"""
    if not req.api_key.strip():
        return ConversationResponse(
            reply="请填入 OpenAI API Key 以使用 AI 对话功能。支持 OpenAI 兼容 API（如 DeepSeek）。",
            action="none",
        )

    system_msg = _CONVERSATION_PROMPT
    if req.character_name:
        system_msg += f"\n当前选中的角色: {req.character_name}"

    try:
        messages = [{"role": "system", "content": system_msg}, *req.messages[-10:]]

        resp = await post_chat_completions(
            req.api_base,
            json_body={
                "model": req.model,
                "messages": messages,
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {req.api_key}",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        json_match = re.search(r"\{[^{}]*\}", content)
        if json_match:
            parsed = json.loads(json_match.group())
            return ConversationResponse(
                reply=parsed.get("reply", content),
                action=parsed.get("action", "none"),
            )
    except Exception as e:
        return ConversationResponse(reply=f"AI 服务暂时不可用: {e}", action="none")

    return ConversationResponse(reply="", action="none")


__all__: list[str] = []
