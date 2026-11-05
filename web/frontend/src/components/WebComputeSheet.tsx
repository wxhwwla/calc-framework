import { useMemo, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableRow,
  TableContainer,
  Tabs,
  Tab,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import type { DagVariable, ControlSpec } from "../utils/controlInference";
import { defaultInputValues, inferControl } from "../utils/controlInference";
import { formatOutputValue } from "../utils/outputFormat";
import InputControl from "./adapter/InputControl";
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
  /** 所有 section 都声明 tab 时，按页签分组渲染。 */
  tab?: string;
  widget_type?: string;
  widget_config?: Record<string, unknown>;
}

export interface LayoutDefinition {
  schema_version: string;
  name: string;
  description?: string;
  sections: LayoutSection[];
}

export interface OutputMeta {
  label?: string;
  format?: string;
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
  /** DAG outputs 的显示名与格式；传入时输出改为多列网格 + 格式化。 */
  outputMeta?: Record<string, OutputMeta>;
  /** 路径 → 禁用原因；命中时灰显对应输入。 */
  disabledPaths?: Record<string, string>;
  /** 加载状态 */
  loading?: boolean;
}

interface TabGroup {
  tab: string;
  sections: LayoutSection[];
}

export default function WebComputeSheet({
  layout,
  variables,
  onInputChange,
  onEvaluate,
  outputValues,
  outputMeta,
  disabledPaths,
  loading = false,
}: WebComputeSheetProps) {
  const { t } = useTranslation();

  const [inputValues, setInputValues] = useState<Record<string, number | boolean | string>>(() =>
    defaultInputValues(variables),
  );
  const [donationOpen, setDonationOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

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

  const tabGroups = useMemo<TabGroup[] | null>(() => {
    if (layout.sections.length === 0 || !layout.sections.every((section) => section.tab)) {
      return null;
    }
    const groups: TabGroup[] = [];
    for (const section of layout.sections) {
      const tab = section.tab as string;
      let group = groups.find((item) => item.tab === tab);
      if (!group) {
        group = { tab, sections: [] };
        groups.push(group);
      }
      group.sections.push(section);
    }
    return groups;
  }, [layout.sections]);

  const firstSectionId = layout.sections[0]?.id;
  const safeActiveTab = tabGroups ? Math.min(activeTab, tabGroups.length - 1) : 0;

  const renderSection = (section: LayoutSection) => {
    const isFirst = section.id === firstSectionId;
    const shouldLazy = !isFirst && section.type !== "inputs" && tabGroups === null;

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
                gridTemplateColumns: `repeat(${section.columns || 2}, minmax(0, 1fr))`,
                gap: 2,
              }}
            >
              {(section.variables || []).map((varPath) => {
                const spec = specCache[varPath];
                if (!spec || spec.widget === "none") return null;
                const value = inputValues[varPath] ?? spec.default;
                const label = spec.description || varPath.split(".").pop() || varPath;
                const disabledReason = disabledPaths?.[varPath];
                return (
                  <Box key={varPath}>
                    <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                      {label}
                    </Typography>
                    <InputControl
                      spec={spec}
                      value={value as number | boolean | string}
                      onChange={(v) => handleChange(varPath, v)}
                      disabled={disabledReason !== undefined}
                    />
                    {disabledReason !== undefined && (
                      <Typography variant="caption" color="text.disabled" display="block" sx={{ mt: 0.5 }}>
                        {disabledReason
                          ? t("compute.inputDisabledReason", { reason: disabledReason })
                          : t("compute.inputDisabled")}
                      </Typography>
                    )}
                  </Box>
                );
              })}
            </Box>
          </Paper>
        );
      }

      if (section.type === "outputs") {
        const outNames = section.outputs || [];
        return (
          <Paper key={section.id} sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              {section.title}
            </Typography>
            {outputMeta ? (
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: `repeat(${section.columns || 2}, minmax(0, 1fr))`,
                  gap: 1.5,
                }}
              >
                {outNames.map((outName) => {
                  const meta = outputMeta[outName];
                  return (
                    <Box
                      key={outName}
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "baseline",
                        gap: 1,
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        bgcolor: "action.hover",
                      }}
                    >
                      <Typography variant="body2" color="text.secondary" noWrap title={outName}>
                        {meta?.label || outName}
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: "bold", whiteSpace: "nowrap" }}>
                        {formatOutputValue(outputValues?.[outName], meta?.format)}
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    {outNames.map((outName) => {
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
            )}
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
                {t("donation.dialogTitle")}
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
      const sectionHeight =
        section.type === "outputs" ? Math.min(60 * (section.outputs?.length || 3) + 80, 400) : 100;

      return (
        <LazySection key={section.id} height={sectionHeight}>
          {sectionContent}
        </LazySection>
      );
    }

    return sectionContent;
  };

  const visibleSections = tabGroups ? tabGroups[safeActiveTab]?.sections || [] : layout.sections;

  return (
    <Box>
      {tabGroups && (
        <Tabs
          value={safeActiveTab}
          onChange={(_e, value: number) => setActiveTab(value)}
          variant="scrollable"
          allowScrollButtonsMobile
          sx={{ mb: 2, borderBottom: 1, borderColor: "divider" }}
        >
          {tabGroups.map((group) => (
            <Tab key={group.tab} label={group.tab} />
          ))}
        </Tabs>
      )}

      {visibleSections.map(renderSection)}

      <Button
        variant="contained"
        fullWidth
        startIcon={<PlayArrowIcon />}
        onClick={handleEvaluate}
        disabled={loading}
        sx={{ mb: 2 }}
      >
        {loading ? t("compute.calculating") : t("common.submit")}
      </Button>

      <DonationDialog open={donationOpen} onClose={() => setDonationOpen(false)} />
    </Box>
  );
}
