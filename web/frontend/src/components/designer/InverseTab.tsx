import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableRow,
  TableContainer,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { inverseFormula, type InverseResponse } from "../../api/designer";

export default function InverseTab() {
  const { t } = useTranslation();
  const [mode, setMode] = useState<"attribute" | "skill">("attribute");
  const [inputText, setInputText] = useState("");
  const [result, setResult] = useState<InverseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const parseValues = useCallback((text: string): number[] => {
    const cleaned = text.replace(/%/g, "").replace(/，/g, ",");
    const parts = cleaned.split(/[\s,]+/).filter(Boolean);
    return parts.map((p) => {
      const v = parseFloat(p.trim());
      if (isNaN(v)) throw new Error(`${t("designer.inverseTab.parseError")}: "${p}"`);
      return v;
    });
  }, [t]);

  const handleCalculate = useCallback(async () => {
    setError(null);
    setResult(null);
    try {
      const values = parseValues(inputText);
      setLoading(true);
      const res = await inverseFormula(mode, values);
      setResult(res);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [inputText, mode, parseValues]);

  const handleClear = useCallback(() => {
    setInputText("");
    setResult(null);
    setError(null);
  }, []);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t("designer.inverseTab.title")}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {t("designer.inverseTab.description")}
      </Typography>

      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
        <InputLabel>{t("designer.inverseTab.dataType")}</InputLabel>
        <Select
          value={mode}
          label={t("designer.inverseTab.dataType")}
          onChange={(e: SelectChangeEvent) => setMode(e.target.value as "attribute" | "skill")}
        >
          <MenuItem value="attribute">{t("designer.inverseTab.attrData")}</MenuItem>
          <MenuItem value="skill">{t("designer.inverseTab.skillData")}</MenuItem>
        </Select>
      </FormControl>

      <TextField
        fullWidth
        multiline
        rows={6}
        placeholder={
          mode === "attribute"
            ? t("designer.inverseTab.attrPlaceholder")
            : t("designer.inverseTab.skillPlaceholder")
        }
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        sx={{ mb: 2, fontFamily: "monospace", fontSize: 13 }}
      />

      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <Button variant="contained" onClick={handleCalculate} disabled={loading || !inputText.trim()}>
          {loading ? t("designer.inverseTab.calculating") : t("designer.inverseTab.startInverse")}
        </Button>
        <Button variant="outlined" onClick={handleClear}>
          {t("designer.inverseTab.clear")}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom color="primary">
            {t("designer.inverseTab.inverseResult")} {result.valid ? <Chip label={t("designer.inverseTab.verifiedPass")} size="small" color="success" /> : <Chip label={t("designer.inverseTab.hasError")} size="small" color="warning" />}
          </Typography>

          <TableContainer>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>base</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>{result.base}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>growth</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>{result.growth}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>divisor</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>{result.divisor}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>offset</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>{result.offset}</TableCell>
                </TableRow>
                {result.special !== null && (
                  <TableRow>
                    <TableCell sx={{ border: "none", pl: 0 }}>special</TableCell>
                    <TableCell sx={{ border: "none", fontWeight: "bold" }}>{result.special}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <Divider sx={{ my: 1.5 }} />

          <Typography variant="body2" sx={{ fontFamily: "monospace", bgcolor: "grey.900", p: 1, borderRadius: 1 }}>
            公式: {result.formula}
          </Typography>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block", whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
            {result.details}
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
