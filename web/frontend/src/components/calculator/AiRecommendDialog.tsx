import { useState } from "react";
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SmartToyIcon from "@mui/icons-material/SmartToy";

interface Props {
  open: boolean;
  onClose: () => void;
  characterName: string;
  weaponName?: string;
}

interface RecommendResult {
  character_name: string;
  query: string;
  ai_intent: string;
  ai_hint: string;
  total_combinations: number;
  top_results: { label: string; damage: number; note: string }[];
}

export default function AiRecommendDialog({ open, onClose, characterName, weaponName }: Props) {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendResult | null>(null);
  const [error, setError] = useState("");

  const handleRecommend = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const body: Record<string, unknown> = {
        character_name: characterName,
        weapon_name: weaponName || "",
        query: query.trim(),
      };
      if (apiKey.trim()) {
        body.api_key = apiKey.trim();
      }
      const r = await fetch("/api/ai/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e: any) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    setQuery("");
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <SmartToyIcon sx={{ mr: 1, verticalAlign: "middle" }} />
        {t("ai.recommendTitle", "AI 智能配装推荐")}
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t("ai.recommendHint", "用自然语言描述你的配装需求，如"暴击率越高越好"、「推荐最高伤害配装」")}
        </Typography>

        <Chip
          label={`${t("compute.character")}: ${characterName}`}
          size="small"
          color="primary"
          sx={{ mb: 1 }}
        />

        <TextField
          fullWidth
          size="small"
          label={t("ai.yourQuery", "你的需求")}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("ai.queryPlaceholder", "例：我想要暴击率超过50%的配装")}
          onKeyDown={(e) => e.key === "Enter" && handleRecommend()}
          sx={{ mb: 1 }}
        />

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="caption">
              {t("ai.apiSettings", "AI API 设置（可选，不填则只搜索不解释）")}
            </Typography>
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
              helperText={t("ai.apiKeyHint", "支持 OpenAI 兼容 API")}
            />
          </AccordionDetails>
        </Accordion>

        <Button
          variant="contained"
          onClick={handleRecommend}
          disabled={loading || !query.trim()}
          fullWidth
          sx={{ mt: 2 }}
        >
          {loading ? <CircularProgress size={20} /> : t("ai.recommend", "开始分析")}
        </Button>

        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

        {result && (
          <Box sx={{ mt: 2 }}>
            {result.ai_intent && (
              <Alert severity="info" icon={<SmartToyIcon />} sx={{ mb: 1 }}>
                <strong>AI:</strong> {result.ai_intent}
              </Alert>
            )}
            {result.ai_hint && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                💡 {result.ai_hint}
              </Typography>
            )}

            <Typography variant="caption" color="text.secondary">
              {t("ai.searchSpace", "搜索空间")}: {result.total_combinations.toLocaleString()} {t("common.items")}
            </Typography>

            {result.top_results.length > 0 && (
              <TableContainer sx={{ mt: 1 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t("common.plan")}</TableCell>
                      <TableCell align="right">{t("common.totalDamageShort")}</TableCell>
                      <TableCell>{t("common.description")}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.top_results.map((r, i) => (
                      <TableRow key={i} sx={i === 0 ? { bgcolor: "success.light" } : undefined}>
                        <TableCell>{r.label}</TableCell>
                        <TableCell align="right"><strong>{r.damage.toLocaleString()}</strong></TableCell>
                        <TableCell>
                          <Typography variant="caption">{r.note}</Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t("common.close")}</Button>
      </DialogActions>
    </Dialog>
  );
}
