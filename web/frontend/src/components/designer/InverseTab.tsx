import { useState, useCallback } from "react";
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
      if (isNaN(v)) throw new Error(`无法解析数值: "${p}"`);
      return v;
    });
  }, []);

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
        公式反推
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        从等级属性数据反向推导成长公式参数
      </Typography>

      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
        <InputLabel>数据类型</InputLabel>
        <Select
          value={mode}
          label="数据类型"
          onChange={(e: SelectChangeEvent) => setMode(e.target.value as "attribute" | "skill")}
        >
          <MenuItem value="attribute">属性数据（90级）</MenuItem>
          <MenuItem value="skill">技能倍率（9/12级）</MenuItem>
        </Select>
      </FormControl>

      <TextField
        fullWidth
        multiline
        rows={6}
        placeholder={
          mode === "attribute"
            ? "输入90个属性数据（空格或换行分隔）…\n例如: 100 105 110 115 …"
            : "输入9或12个技能倍率数据（空格或换行分隔）…\n例如: 1.0 1.05 1.10 1.15 …"
        }
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        sx={{ mb: 2, fontFamily: "monospace", fontSize: 13 }}
      />

      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <Button variant="contained" onClick={handleCalculate} disabled={loading || !inputText.trim()}>
          {loading ? "计算中…" : "开始反推"}
        </Button>
        <Button variant="outlined" onClick={handleClear}>
          清除
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
            反推结果 {result.valid ? <Chip label="✓ 验证通过" size="small" color="success" /> : <Chip label="✗ 有误差" size="small" color="warning" />}
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
