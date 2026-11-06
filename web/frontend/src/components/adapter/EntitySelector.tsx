import { Box, MenuItem, TextField } from "@mui/material";
import type { EntityRecord, EntitySelections, EntitySelector as EntitySelectorConfig } from "../../utils/adapterEntity";
import { optionDisplays, stepOptions } from "../../utils/adapterEntity";

interface EntitySelectorProps {
  records: readonly EntityRecord[];
  selector: EntitySelectorConfig;
  selections: EntitySelections;
  onChange: (index: number, value: string) => void;
}

/** 级联实体下拉 — 上级变化后由页面重建下级选项。 */
export default function EntitySelector({ records, selector, selections, onChange }: EntitySelectorProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      {selector.steps.map((step, index) => {
        const options = stepOptions(records, selector.steps, selections, index);
        const displays = optionDisplays(records, selector.steps, selections, index);
        const selected = selections[index];
        const value = selected && options.includes(selected) ? selected : "";
        return (
          <TextField
            key={step.field}
            select
            size="small"
            fullWidth
            label={step.label || step.field}
            value={value}
            onChange={(e) => onChange(index, e.target.value)}
          >
            {options.map((option) => (
              <MenuItem key={option} value={option}>
                {displays[option] ?? option}
              </MenuItem>
            ))}
          </TextField>
        );
      })}
    </Box>
  );
}
