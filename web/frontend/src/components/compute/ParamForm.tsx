import { useTranslation } from "react-i18next";
import { Box, FormControlLabel, Switch, Typography } from "@mui/material";
import NumberField from "../common/NumberField";
import { useComputeStore } from "../../store/computeStore";

export default function ParamForm() {
  const { t } = useTranslation();
  const schema = useComputeStore((s) => s.schema);
  const paramValues = useComputeStore((s) => s.paramValues);
  const setParam = useComputeStore((s) => s.setParam);
  const runCompute = useComputeStore((s) => s.runCompute);

  if (schema.length === 0) return null;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      runCompute();
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      <Typography variant="subtitle2" color="text.secondary">
        {t('compute.title', '参数输入')}
      </Typography>
      {schema.map((attr) => {
        const key = attr.name.includes(".")
          ? attr.name.split(".")[1]
          : attr.name;
        const label = attr.description || key;
        const value = paramValues[key];

        if (attr.type === "bool") {
          return (
            <FormControlLabel
              key={attr.name}
              control={
                <Switch
                  checked={!!value}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setParam(key, e.target.checked)}
                />
              }
              label={label}
            />
          );
        }

        return (
          <NumberField
            key={attr.name}
            label={label}
            value={typeof value === "number" ? value : 0}
            onChange={(v) => setParam(key, v)}
            onKeyDown={handleKeyDown}
          />
        );
      })}
    </Box>
  );
}
