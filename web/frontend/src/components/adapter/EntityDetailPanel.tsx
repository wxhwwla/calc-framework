import { Box, Paper, Typography } from "@mui/material";
import type { EntityDetailMeta, EntityRecord } from "../../utils/adapterEntity";
import { formatDetailValue } from "../../utils/adapterEntity";

interface EntityDetailPanelProps {
  detail: EntityDetailMeta;
  record: EntityRecord | undefined;
}

/** 选中实体字段明细 — 按 meta.entity_detail 分组与分列展示。 */
export default function EntityDetailPanel({ detail, record }: EntityDetailPanelProps) {
  if (!record) return null;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        {detail.title || detail.source}
      </Typography>
      {detail.sections.map((section) => (
        <Box key={section.title || section.fields[0]?.field} sx={{ mt: 1.5 }}>
          <Typography variant="caption" color="primary" display="block" gutterBottom>
            {section.title || ""}
          </Typography>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: `repeat(${section.columns || 1}, minmax(0, 1fr))`,
              columnGap: 2,
              rowGap: 0.75,
            }}
          >
            {section.fields.map((field) => (
              <Box key={field.field} sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {field.label || field.field}
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500, textAlign: "right" }}>
                  {formatDetailValue(record[field.field], field.format)}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      ))}
    </Paper>
  );
}
