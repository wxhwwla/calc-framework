import { Box, Typography, Paper, Table, TableBody, TableCell, TableRow } from "@mui/material";

interface PreviewTextProps {
  outputValues: Record<string, number> | null;
  nodeValues: Record<string, number | string | null> | null;
}

const KNOWN_ZONE_KEYS = [
  "基础攻击力",
  "最终攻击力",
  "技能倍率",
  "攻击倍率乘区",
  "增伤乘区",
  "防御乘区",
  "抗性乘区",
  "暴击乘区",
  "易伤乘区",
  "失衡易伤乘区",
  "伤害类型乘区",
  "精英伤乘区",
  "额外伤害乘区",
  "元素反应乘区",
  "其他乘区",
];

function formatValue(v: unknown): string {
  if (v == null) return "--";
  if (typeof v === "number") return v.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
  return String(v);
}

export default function PreviewText({ outputValues, nodeValues }: PreviewTextProps) {
  if (!outputValues && !nodeValues) {
    return (
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary" textAlign="center">
          尚无计算结果，请执行计算后查看预览
        </Typography>
      </Paper>
    );
  }

  const zoneRows: { label: string; value: string }[] = [];

  if (nodeValues) {
    for (const key of KNOWN_ZONE_KEYS) {
      if (key in nodeValues) {
        zoneRows.push({ label: key, value: formatValue(nodeValues[key]) });
      }
    }

    for (const [key, val] of Object.entries(nodeValues)) {
      if (!KNOWN_ZONE_KEYS.includes(key) && typeof val === "number") {
        zoneRows.push({ label: key, value: formatValue(val) });
      }
    }
  }

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        伤害预览
      </Typography>

      {outputValues && Object.keys(outputValues).length > 0 && (
        <Table size="small">
          <TableBody>
            {Object.entries(outputValues).map(([key, val]) => (
              <TableRow key={key}>
                <TableCell sx={{ border: "none", pl: 0, fontWeight: "bold" }}>
                  {key}
                </TableCell>
                <TableCell sx={{ border: "none", textAlign: "right", fontWeight: "bold", fontSize: "1.1rem" }}>
                  {formatValue(val)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {zoneRows.length > 0 && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            乘区明细
          </Typography>
          <Table size="small">
            <TableBody>
              {zoneRows.map((row) => (
                <TableRow key={row.label}>
                  <TableCell sx={{ border: "none", pl: 0, fontSize: "0.8rem" }}>
                    {row.label}
                  </TableCell>
                  <TableCell sx={{ border: "none", textAlign: "right", fontSize: "0.8rem" }}>
                    {row.value}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}
    </Paper>
  );
}
