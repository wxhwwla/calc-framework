import { Box, Typography, Paper, Table, TableBody, TableCell, TableRow, Accordion, AccordionSummary, AccordionDetails, TableContainer } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

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

const ZONE_GROUPS: Record<string, string[]> = {
  "基础属性": ["基础攻击力", "最终攻击力", "技能倍率"],
  "攻击倍率": ["攻击倍率乘区"],
  "增伤": ["增伤乘区"],
  "防御/抗性": ["防御乘区", "抗性乘区"],
  "暴击": ["暴击乘区"],
  "易伤": ["易伤乘区", "失衡易伤乘区"],
  "其他": ["伤害类型乘区", "精英伤乘区", "额外伤害乘区", "元素反应乘区", "其他乘区"],
};

function formatValue(v: unknown): string {
  if (v == null) return "--";
  if (typeof v === "number") return v.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
  return String(v);
}

function getZoneGroup(key: string): string {
  for (const [group, keys] of Object.entries(ZONE_GROUPS)) {
    if (keys.includes(key)) return group;
  }
  return "其他";
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

  const grouped = zoneRows.reduce<Record<string, typeof zoneRows>>((acc, row) => {
    const g = getZoneGroup(row.label);
    if (!acc[g]) acc[g] = [];
    acc[g].push(row);
    return acc;
  }, {});

  const groupOrder = Object.keys(ZONE_GROUPS).filter((g) => grouped[g]?.length > 0);
  const otherGroup = Object.keys(grouped).filter((g) => !(g in ZONE_GROUPS));
  const allGroups = [...groupOrder, ...otherGroup];

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        伤害预览
      </Typography>

      {outputValues && Object.keys(outputValues).length > 0 && (
        <TableContainer sx={{ overflowX: 'auto' }}>
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
        </TableContainer>
      )}

      {allGroups.length > 0 && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: "block" }}>
            乘区明细
          </Typography>
          {allGroups.map((group) => (
            <Accordion key={group} disableGutters sx={{ boxShadow: "none", "&:before": { display: "none" } }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: 36, "& .MuiAccordionSummary-content": { my: 0.5 } }}>
                <Typography variant="body2">{group}</Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ py: 0 }}>
                <TableContainer sx={{ overflowX: 'auto' }}>
                  <Table size="small">
                    <TableBody>
                      {grouped[group].map((row) => (
                        <TableRow key={row.label}>
                          <TableCell sx={{ border: "none", pl: 1, fontSize: "0.8rem", color: "text.secondary" }}>
                            {row.label}
                          </TableCell>
                          <TableCell sx={{ border: "none", textAlign: "right", fontSize: "0.8rem" }}>
                            {row.value}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
    </Paper>
  );
}
