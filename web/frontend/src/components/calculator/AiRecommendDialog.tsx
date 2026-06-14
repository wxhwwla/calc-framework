import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
  Alert,
  Box,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Paper,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SendIcon from "@mui/icons-material/Send";
import SearchIcon from "@mui/icons-material/Search";

interface Props {
  open: boolean;
  onClose: () => void;
  characterName: string;
  weaponName?: string;
}

interface ChatMsg {
  role: "user" | "ai";
  content: string;
  results?: { label: string; damage: number; note: string }[];
  action?: string;
}

export default function AiRecommendDialog({ open, onClose, characterName, weaponName }: Props) {
  const { t } = useTranslation();
  const [apiKey, setApiKey] = useState("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [chat, setChat] = useState<ChatMsg[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && chat.length === 0 && characterName) {
      setChat([{
        role: "ai",
        content: t("ai.greeting", "你好！我是配装助手。你可以问我：\n• 「推荐最高伤害配装」\n• 「暴击率优先怎么配」\n• 「这把武器适合谁」"),
      }]);
    }
  }, [open, characterName, t]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [chat]);

  const baseBody = () => ({
    character_name: characterName,
    weapon_name: weaponName || "",
    api_key: apiKey.trim(),
  });

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput("");
    setChat((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);
    setError("");

    try {
      if (apiKey.trim()) {
        // 多轮对话模式
        const msgs = [
          ...chat.filter((c) => c.content).map((c) => ({ role: c.role, content: c.content })),
          { role: "user" as const, content: msg },
        ];
        const r = await fetch("/api/ai/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...baseBody(), messages: msgs }),
        });
        if (!r.ok) throw new Error(await r.text());
        const data = await r.json();
        setChat((prev) => [...prev, { role: "ai", content: data.reply, action: data.action }]);

        if (data.action === "search") {
          await handleQuickRecommend(msg);
        }
      } else {
        // 无 API key：直接调推荐
        await handleQuickRecommend(msg);
      }
    } catch (e: any) {
      setError(String(e));
      setChat((prev) => [...prev, { role: "ai", content: t("ai.error", "出错了，请稍后重试") }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickRecommend = async (query: string) => {
    const r = await fetch("/api/ai/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...baseBody(), query }),
    });
    if (!r.ok) return;
    const data = await r.json();
    const results = data.top_results || [];
    const summary = results.length > 0
      ? `${data.ai_intent || ""}\n\n搜索空间: ${data.total_combinations.toLocaleString()} 种组合\n${data.ai_hint || ""}`
      : t("ai.noResults", "暂无搜索结果");
    setChat((prev) => [...prev, { role: "ai", content: summary, results }]);
  };

  const handleExplain = async () => {
    const lastResult = [...chat].reverse().find((c) => c.results?.length);
    if (!lastResult?.results || !apiKey.trim()) return;
    setLoading(true);
    try {
      const lastQuery = [...chat].reverse().find((c) => c.role === "user")?.content || "";
      const r = await fetch("/api/ai/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...baseBody(),
          query: lastQuery,
          results: lastResult.results,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const text = data.explanation + (data.suggestions?.length ? "\n\n💡 " + data.suggestions.join("\n💡 ") : "");
      setChat((prev) => [...prev, { role: "ai", content: text }]);
    } catch (e: any) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (category: string) => {
    if (!input.trim() || loading) return;
    const query = input.trim();
    setInput("");
    setChat((prev) => [...prev, { role: "user", content: `${t("ai.searchPrefix", "搜索")}: ${query}` }]);
    setLoading(true);
    try {
      const body = { query, category, api_key: apiKey.trim() };
      const r = await fetch("/api/ai/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      const items = data.results?.slice(0, 10) || [];
      const summary = items.length > 0
        ? `${t("ai.found", "找到")} ${items.length} ${t("common.items")}:\n` + items.map((it: any) => `• ${it["名称"]} (${it["星级"] || ""}⭐ ${it["类型"] || ""})`).join("\n")
        : t("ai.notFound", "未找到匹配项");
      setChat((prev) => [...prev, {
        role: "ai",
        content: summary + (data.ai_refined ? `\n\n🤖 AI ${t("ai.refined", "精排")}` : ""),
      }]);
    } catch (e: any) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <SmartToyIcon sx={{ mr: 1, verticalAlign: "middle" }} />
        {t("ai.recommendTitle", "AI 配装助手")}
        <Chip label={characterName} size="small" color="primary" sx={{ ml: 1 }} />
      </DialogTitle>
      <DialogContent dividers>
        {/* 聊天区域 */}
        <Box
          ref={scrollRef}
          sx={{ height: 360, overflowY: "auto", mb: 1, display: "flex", flexDirection: "column", gap: 1 }}
        >
          {chat.map((msg, i) => (
            <Box key={i} sx={{ alignSelf: msg.role === "user" ? "flex-end" : "flex-start", maxWidth: "85%" }}>
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  bgcolor: msg.role === "user" ? "primary.main" : "grey.100",
                  color: msg.role === "user" ? "#fff" : "text.primary",
                  borderRadius: 2,
                  whiteSpace: "pre-wrap",
                  fontSize: "0.85rem",
                }}
              >
                {msg.content}
                {msg.results && msg.results.length > 0 && (
                  <Box sx={{ mt: 1, fontSize: "0.8rem" }}>
                    {msg.results.slice(0, 5).map((r, ri) => (
                      <Box key={ri} sx={{ display: "flex", justifyContent: "space-between", py: 0.3, borderBottom: "1px solid #ddd" }}>
                        <span>{r.label}</span>
                        <strong>{r.damage.toLocaleString()}</strong>
                      </Box>
                    ))}
                  </Box>
                )}
              </Paper>
              {msg.results && msg.results.length > 0 && apiKey.trim() && (
                <Button size="small" onClick={handleExplain} sx={{ mt: 0.5, fontSize: "0.7rem" }}>
                  🤖 {t("ai.explainResult", "AI 解释结果")}
                </Button>
              )}
            </Box>
          ))}
          {loading && <CircularProgress size={20} sx={{ alignSelf: "center" }} />}
          {error && <Alert severity="error" sx={{ fontSize: "0.8rem" }} onClose={() => setError("")}>{error}</Alert>}
        </Box>

        {/* 快捷操作 */}
        <Box sx={{ display: "flex", gap: 0.5, mb: 1, flexWrap: "wrap" }}>
          <Chip
            icon={<SearchIcon />}
            label={t("ai.searchWeapons", "搜武器")}
            size="small"
            onClick={() => handleSearch("weapons")}
            disabled={loading || !input.trim()}
          />
          <Chip
            icon={<SearchIcon />}
            label={t("ai.searchChars", "搜角色")}
            size="small"
            onClick={() => handleSearch("characters")}
            disabled={loading || !input.trim()}
          />
        </Box>

        {/* 输入区 */}
        <Box sx={{ display: "flex", gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t("ai.queryPlaceholder", "例：佩丽卡暴击流怎么配装？")}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            multiline
            maxRows={3}
          />
          <IconButton color="primary" onClick={handleSend} disabled={loading || !input.trim()}>
            <SendIcon />
          </IconButton>
        </Box>

        {/* API 设置 */}
        <Accordion sx={{ mt: 1 }} defaultExpanded={false}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="caption">{t("ai.apiSettings", "API 设置（可选）")}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TextField
              fullWidth
              size="small"
              type="password"
              label="OpenAI API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              helperText={t("ai.apiKeyHint", "填入后可多轮对话+AI解释。支持 DeepSeek 等兼容 API")}
            />
          </AccordionDetails>
        </Accordion>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
