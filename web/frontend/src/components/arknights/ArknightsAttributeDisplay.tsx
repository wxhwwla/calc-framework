import { useTranslation } from "react-i18next";
import {
  Box,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Tooltip,
  TableContainer,
} from "@mui/material";
import type { OperatorSummary } from "../../api/arknights";

interface Props {
  operator: OperatorSummary;
}

const STAR_MAP: Record<number, number> = { 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6 };

export default function ArknightsAttributeDisplay({ operator }: Props) {
  const { t } = useTranslation();
  const baseStats = operator.基础属性 || {};

  const STAT_LABELS: Record<string, string> = {
    生命: t("attr.baseHP", "生命上限"),
    攻击: t("arknights.atk", "攻击力"),
    防御: t("arknights.defense", "防御力"),
    法术抗性: t("arknights.res", "法术抗性"),
    部署费用: t("arknights.extraBonus_cost", "部署费用"),
    再部署: t("arknights.extraBonus_redeploy", "再部署时间"),
    阻挡数: t("arknights.extraBonus_block", "阻挡数"),
    攻击间隔: t("arknights.extraBonus_interval", "攻击间隔"),
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1, flexWrap: "wrap" }}>
        <Typography variant="h6">{operator.名称}</Typography>
        <Chip
          label={`${operator.职业} · ${operator.分支}`}
          size="small"
          variant="outlined"
        />
        <Box sx={{ display: "flex", gap: 0.25 }}>
          {Array.from({ length: STAR_MAP[operator.星级] ?? operator.星级 }, (_, i) => (
            <Typography key={i} variant="body2" color="warning.main" sx={{ lineHeight: 1 }}>
              ★
            </Typography>
          ))}
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {operator.特性}
      </Typography>

      <Typography variant="subtitle2" gutterBottom color="text.secondary">
        {t("api.arknightsProps.baseAttr")}
      </Typography>
      <TableContainer sx={{ overflowX: 'auto' }}>
        <Table size="small" sx={{ mb: 1 }}>
          <TableBody>
            {Object.entries(baseStats).map(([key, val]) => (
              <TableRow key={key} sx={{ "&:last-child td": { borderBottom: 0 } }}>
                <TableCell sx={{ pl: 0, py: 0.25 }}>
                  <Typography variant="body2" color="text.secondary">
                    {STAT_LABELS[key] || key}
                  </Typography>
                </TableCell>
                <TableCell sx={{ pr: 0, py: 0.25 }} align="right">
                  <Typography variant="body2">
                    {typeof val === "number" ? val.toLocaleString() : String(val)}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {operator.信赖加成 && Object.keys(operator.信赖加成).length > 0 && (
        <>
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            {t("api.arknightsProps.trustBonus")}
          </Typography>
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1 }}>
            {Object.entries(operator.信赖加成).map(([key, val]) => (
              <Chip
                key={key}
                label={`${STAT_LABELS[key] || key} +${val >= 0 ? "" : ""}${val}`}
                size="small"
                variant="outlined"
                color="success"
              />
            ))}
          </Box>
        </>
      )}

      {operator.天赋 && operator.天赋.length > 0 && (
        <>
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            {t("api.arknightsProps.talent")}
          </Typography>
          {operator.天赋.map((t, i) => (
            <Tooltip key={i} title={t.description} arrow>
              <Chip
                label={`${t.name}（${t.unlock}）`}
                size="small"
                variant="outlined"
                sx={{ mr: 0.5, mb: 0.5, maxWidth: "100%" }}
              />
            </Tooltip>
          ))}
        </>
      )}
    </Box>
  );
}
