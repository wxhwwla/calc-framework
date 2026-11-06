import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert, Box, CircularProgress, Paper, Typography } from "@mui/material";
import type { PackExportBundle } from "../api/adapterPack";
import { fetchAdapterPackBundle } from "../api/adapterPack";
import type { EvaluateResult } from "../api/compute";
import { evaluate } from "../api/compute";
import type {
  EntityDetailMeta,
  EntityInputRule,
  EntityRecord,
  EntitySelections,
  EntitySelector as EntitySelectorConfig,
  EntityValue,
} from "../utils/adapterEntity";
import {
  buildEntityContext,
  computeDisabledPaths,
  initialSelections,
  matchingRecords,
  stepOptions,
} from "../utils/adapterEntity";
import type { DagVariable } from "../utils/controlInference";
import { defaultInputValues } from "../utils/controlInference";
import WebComputeSheet from "../components/WebComputeSheet";
import type { LayoutDefinition, OutputMeta } from "../components/WebComputeSheet";
import EntitySelector from "../components/adapter/EntitySelector";
import EntityDetailPanel from "../components/adapter/EntityDetailPanel";

interface AdapterMeta {
  name?: string;
  description?: string;
  entity_selectors?: EntitySelectorConfig[];
  entity_detail?: EntityDetailMeta;
  entity_input_rules?: EntityInputRule[];
}

interface DagDefinition {
  variables?: Record<string, DagVariable>;
  outputs?: Record<string, OutputMeta>;
}

interface AdapterGamePageProps {
  adapterId: string;
}

/**
 * 通用适配器计算页 — 由 meta/layout/DAG 驱动，无需为每个游戏单独写页面。
 *
 * 左栏：级联实体选择 + 明细；右栏：通用计算表。
 */
export default function AdapterGamePage({ adapterId }: AdapterGamePageProps) {
  const [bundle, setBundle] = useState<PackExportBundle | null>(null);
  const [selections, setSelections] = useState<EntitySelections>([]);
  const [outputValues, setOutputValues] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 与 WebComputeSheet 内部的输入状态保持镜像，供切换实体后自动重算。
  const inputValuesRef = useRef<Record<string, EntityValue>>({});
  // 只采用最后一次请求的结果，避免快速切换时旧响应覆盖新结果。
  const requestSeq = useRef(0);

  const evaluateRecord = useCallback(
    async (
      record: EntityRecord | undefined,
      values: Record<string, EntityValue>,
      selectorConfig: EntitySelectorConfig,
      adapterName: string,
    ) => {
      if (!record) {
        setError("没有可计算的实体记录");
        return;
      }
      const seq = requestSeq.current + 1;
      requestSeq.current = seq;
      setLoading(true);
      setError(null);
      try {
        const context = buildEntityContext(record, selectorConfig.source, values);
        const result: EvaluateResult = await evaluate(adapterName, context);
        if (seq === requestSeq.current) setOutputValues(result.outputs);
      } catch (e: unknown) {
        if (seq === requestSeq.current) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (seq === requestSeq.current) setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    let cancelled = false;
    requestSeq.current += 1;
    setBundle(null);
    setSelections([]);
    setOutputValues({});
    setLoading(false);
    setError(null);

    fetchAdapterPackBundle(adapterId)
      .then((data) => {
        if (cancelled) return;
        const meta = data.meta as AdapterMeta;
        const selector = meta.entity_selectors?.[0];
        const records = selector ? data.data_files[selector.data_file] || [] : [];
        const initial = selector ? initialSelections(records, selector.steps) : [];

        // 与桌面查看器一致：加载完成后按默认输入直接求值一次。
        const dagData = data.dag as DagDefinition;
        const defaults: Record<string, EntityValue> = defaultInputValues(dagData.variables || {});
        inputValuesRef.current = defaults;

        setBundle(data);
        setSelections(initial);
        if (selector) {
          void evaluateRecord(
            matchingRecords(records, selector.steps, initial)[0],
            defaults,
            selector,
            String(meta.name || adapterId),
          );
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });

    return () => {
      cancelled = true;
    };
  }, [adapterId, evaluateRecord]);

  const meta = (bundle?.meta || {}) as AdapterMeta;
  const selector = meta.entity_selectors?.[0];
  const records: EntityRecord[] = useMemo(
    () => (selector ? bundle?.data_files[selector.data_file] || [] : []),
    [bundle, selector],
  );

  const selectedRecord = useMemo(() => {
    if (!selector) return undefined;
    return matchingRecords(records, selector.steps, selections)[0];
  }, [records, selections, selector]);

  const disabledPaths = useMemo(() => {
    if (!meta.entity_input_rules || !selector || !selectedRecord) return {};
    return computeDisabledPaths(meta.entity_input_rules, selectedRecord, selector.source);
  }, [meta.entity_input_rules, selector, selectedRecord]);

  const adapterName = String(meta.name || adapterId);

  const handleSelectionChange = useCallback(
    (index: number, value: string) => {
      if (!selector) return;
      const next: EntitySelections = selections.slice(0, index + 1);
      next[index] = value;
      for (let stepIndex = index + 1; stepIndex < selector.steps.length; stepIndex += 1) {
        const options = stepOptions(records, selector.steps, next, stepIndex);
        next.push(options[0] ?? null);
      }
      setSelections(next);
      const record = matchingRecords(records, selector.steps, next)[0];
      void evaluateRecord(record, inputValuesRef.current, selector, adapterName);
    },
    [adapterName, evaluateRecord, records, selections, selector],
  );

  const handleEvaluate = useCallback(
    (inputValues: Record<string, EntityValue>) => {
      inputValuesRef.current = inputValues;
      if (!selector) return;
      void evaluateRecord(selectedRecord, inputValues, selector, adapterName);
    },
    [adapterName, evaluateRecord, selectedRecord, selector],
  );

  const handleInputChange = useCallback((path: string, value: EntityValue) => {
    inputValuesRef.current = { ...inputValuesRef.current, [path]: value };
  }, []);

  const layout = bundle ? (bundle.layout as unknown as LayoutDefinition) : null;
  const dag = bundle ? (bundle.dag as unknown as DagDefinition) : null;
  const variables: Record<string, DagVariable> = dag?.variables || {};
  const outputMeta = dag?.outputs;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {meta.name || adapterId}
      </Typography>
      {meta.description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {meta.description}
        </Typography>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {!bundle ? (
        error ? null : (
          <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
            <CircularProgress />
          </Box>
        )
      ) : (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "minmax(0, 1fr)", md: "minmax(0, 4fr) minmax(0, 8fr)" },
            gap: 2,
            alignItems: "start",
          }}
        >
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {selector && (
              <Paper sx={{ p: 2 }}>
                <EntitySelector
                  records={records}
                  selector={selector}
                  selections={selections}
                  onChange={handleSelectionChange}
                />
              </Paper>
            )}
            {meta.entity_detail && <EntityDetailPanel detail={meta.entity_detail} record={selectedRecord} />}
          </Box>

          <Box>
            {layout && (
              <WebComputeSheet
                layout={layout}
                variables={variables}
                outputValues={outputValues}
                outputMeta={outputMeta}
                disabledPaths={disabledPaths}
                onInputChange={handleInputChange}
                onEvaluate={handleEvaluate}
                loading={loading}
              />
            )}
          </Box>
        </Box>
      )}
    </Box>
  );
}
