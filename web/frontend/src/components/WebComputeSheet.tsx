import { useMemo, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Slider,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Table,
  TableBody,
  TableCell,
  TableRow,
  TableContainer,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import type { DagVariable, ControlSpec } from "../utils/controlInference";
import { inferControl, getUserInputVariables } from "../utils/controlInference";
import type { SelectChangeEvent } from "@mui/material/Select";
import LazySection from "./LazySection";
import DonationDialog from "./calculator/DonationDialog";
import { DONATION_TEXT } from "../constants/donation";

/** layout.json Section 类型 */
export interface LayoutSection {
  id: string;
  type: "inputs" | "outputs" | "widget";
  title: string;
  variables?: string[];
  outputs?: string[];
  columns?: number;
  widget_type?: string;
  widget_config?: Record<string, unknown>;
}

export interface LayoutDefinition {
  schema_version: string;
  name: string;
  description?: string;
  sections: LayoutSection[];
}

interface WebComputeSheetProps {
  layout: LayoutDefinition;
  variables: Record<string, DagVariable>;
  /** 当用户修改 input 值时回调 */
  onInputChange?: (path: string, value: number | boolean | string) => void;
  /** 当用户点击计算按钮时回调 */
  onEvaluate?: (inputValues: Record<string, number | boolean | string>) => void;
  /** 外部传入的输出值（可选） */
  outputValues?: Record<string, number>;
  /** 加载状态 */
  loading?: boolean;
}

function InputControl({
  spec,
  value,
  onChange,
}: {
  spec: ControlSpec;
  value: number | boolean | string;
  onChange: (v: number | boolean | string) => void;
}) {
  const numValue = typeof value === "number" ? value : (typeof spec.default === "number" ? spec.default : 0);
  const boolValue = typeof value === "boolean" ? value : Boolean(spec.default);

  switch (spec.widget) {
    case "spinbox":
    case "text":
      return (
        <TextField
          type="number"
          size="small"
          fullWidth
          value={numValue}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            const v = parseFloat(e.target.value);
            onChange(isNaN(v) ? 0 : v);
          }}
          inputProps={{
            step: spec.step,
            min: spec.minVal ?? undefined,
            max: spec.maxVal ?? undefined,
          }}
        />
      );

    case "slider":
      return (
        <Box sx={{ px: 1 }}>
          <Slider
            value={numValue}
            min={spec.minVal ?? 0}
            max={spec.maxVal ?? 100}
            step={spec.step}
            onChange={(_e, v) => onChange(v as number)}
            valueLabelDisplay="auto"
          />
        </Box>
      );

    case "switch":
      return (
        <FormControlLabel
          control={
            <Switch
              checked={boolValue}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.checked)}
            />
          }
          label={spec.description || spec.label.split(".").pop() || ""}
        />
      );

    case "dropdown":
      return (
        <FormControl fullWidth size="small">
          <InputLabel>{spec.description || spec.label}</InputLabel>
          <Select
            value={String(value)}
            label={spec.description || spec.label}
            onChange={(e: SelectChangeEvent) => onChange(e.target.value)}
          >
            {spec.options.map((opt) => (
              <MenuItem key={opt} value={opt}>
                {opt}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      );

    default:
      return <Typography variant="body2" color="text.secondary">{String(value)}</Typography>;
  }
}

export default function WebComputeSheet({
  layout,
  variables,
  onInputChange,
  onEvaluate,
  outputValues,
  loading = false,
}: WebComputeSheetProps) {
  const userInputVars = useMemo(() => getUserInputVariables(variables), [variables]);

  const [inputValues, setInputValues] = useState<Record<string, number | boolean | string>>(() => {
    const init: Record<string, number | boolean | string> = {};
    for (const [path, varDef] of Object.entries(userInputVars)) {
      const spec = inferControl(path, varDef);
      init[path] = spec.default as number | boolean | string;
    }
    return init;
  });
  const [donationOpen, setDonationOpen] = useState(false);

  const handleChange = useCallback(
    (path: string, value: number | boolean | string) => {
      setInputValues((prev) => ({ ...prev, [path]: value }));
      onInputChange?.(path, value);
    },
    [onInputChange],
  );

  const handleEvaluate = useCallback(() => {
    onEvaluate?.(inputValues);
  }, [inputValues, onEvaluate]);

  const specCache = useMemo(() => {
    const cache: Record<string, ControlSpec> = {};
    for (const [path, varDef] of Object.entries(variables)) {
      cache[path] = inferControl(path, varDef);
    }
    return cache;
  }, [variables]);

  const firstSectionId = layout.sections[0]?.id;

  return (
    <Box>
      {layout.sections.map((section) => {
        const isFirst = section.id === firstSectionId;
        const shouldLazy = !isFirst && section.type !== "inputs";

        const sectionContent = (() => {
          if (section.type === "inputs") {
            return (
              <Paper key={section.id} sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom color="text.secondary">
                  {section.title}
                </Typography>
                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${section.columns || 2}, 1fr)`,
                    gap: 2,
                  }}
                >
                  {(section.variables || []).map((varPath) => {
                    const spec = specCache[varPath];
                    if (!spec || spec.widget === "none") return null;
                    const value = inputValues[varPath] ?? spec.default;
                    const label = spec.description || varPath.split(".").pop() || varPath;
                    return (
                      <Box key={varPath}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          {label}
                        </Typography>
                        <InputControl spec={spec} value={value as number | boolean | string} onChange={(v) => handleChange(varPath, v)} />
                      </Box>
                    );
                  })}
                </Box>
              </Paper>
            );
          }

          if (section.type === "outputs") {
            return (
              <Paper key={section.id} sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom color="text.secondary">
                  {section.title}
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      {(section.outputs || []).map((outName) => {
                        const val = outputValues?.[outName];
                        return (
                          <TableRow key={outName}>
                            <TableCell sx={{ border: "none", pl: 0 }}>{outName}</TableCell>
                            <TableCell sx={{ border: "none", textAlign: "right", fontWeight: "bold" }}>
                              {val !== undefined ? val.toFixed(4) : "--"}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            );
          }

          if (section.type === "widget") {
            if (section.widget_type === "donation") {
              return (
                <Paper key={section.id} sx={{ p: 2, mb: 2, textAlign: "center" }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {(section.widget_config?.text as string) || DONATION_TEXT.split("\n\n")[0]}
                  </Typography>
                  <Button variant="outlined" color="secondary" onClick={() => setDonationOpen(true)}>
                    自愿捐赠
                  </Button>
                </Paper>
              );
            }
            return null;
          }

          return null;
        })();

        if (sectionContent === null) return null;

        if (shouldLazy) {
          const sectionHeight = section.type === "outputs"
            ? Math.min(60 * (section.outputs?.length || 3) + 80, 400)
            : 100;

          return (
            <LazySection key={section.id} height={sectionHeight}>
              {sectionContent}
            </LazySection>
          );
        }

        return sectionContent;
      })}

      <Button
        variant="contained"
        fullWidth
        startIcon={<PlayArrowIcon />}
        onClick={handleEvaluate}
        disabled={loading}
        sx={{ mb: 2 }}
      >
        {loading ? "计算中..." : "计算"}
      </Button>

      <DonationDialog open={donationOpen} onClose={() => setDonationOpen(false)} />
    </Box>
  );
}
