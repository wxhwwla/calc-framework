import { useEffect, useState, useCallback, useMemo, lazy, Suspense } from "react";
import { Box, Paper, Grid2 as Grid, Typography, Tabs, Tab, Button, Collapse, FormControl, InputLabel, Select, MenuItem, IconButton } from "@mui/material";
import { ExpandLess, ExpandMore } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import CharacterSelector from "../components/calculator/CharacterSelector";
import AttributeDisplay from "../components/calculator/AttributeDisplay";
import WebComputeSheet from "../components/WebComputeSheet";
import SearchPanel from "../components/calculator/SearchPanel";
import EnemyParamPanel from "../components/calculator/EnemyParamPanel";
import MultiSkillPanel from "../components/calculator/MultiSkillPanel";
import FixedLoadoutPanel from "../components/calculator/FixedLoadoutPanel";
import PresetDialog from "../components/calculator/PresetDialog";
import CritAndAbnormalPanel from "../components/calculator/CritAndAbnormalPanel";
import PreviewText from "../components/calculator/PreviewText";
import TotalDamagePanel from "../components/calculator/TotalDamagePanel";
import CalcHistoryDialog from "../components/calculator/CalcHistoryDialog";
import SearchHistoryDialog from "../components/calculator/SearchHistoryDialog";
import SkillLevelPanel from "../components/calculator/SkillLevelPanel";
import WeaponSkillPanel from "../components/calculator/WeaponSkillPanel";
import CalcModeSelector from "../components/calculator/CalcModeSelector";
import type { LayoutDefinition } from "../components/WebComputeSheet";
import type { DagVariable } from "../utils/controlInference";
import type { EnemyParams } from "../api/search";
import { DEFAULT_ENEMY_PARAMS, mergeEnemyParams } from "../api/search";
import type { MultiSkillSettings } from "../components/calculator/MultiSkillPanel";
import type { FixedLoadoutSelection } from "../components/calculator/FixedLoadoutPanel";
import type { CritAndAbnormalSettings } from "../components/calculator/CritAndAbnormalPanel";
import BuildIcon from "@mui/icons-material/Build";
import TuneIcon from "@mui/icons-material/Tune";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import CameraAltIcon from "@mui/icons-material/CameraAlt";
import SearchPreviewPanel from "../components/calculator/SearchPreviewPanel";
import SegmentManualBuffDialog, {
  type ManualBuffStore,
} from "../components/calculator/SegmentManualBuffDialog";
import { fetchEquipmentCatalog } from "../api/search";
import {
  buildWebLoadoutPayload,
  buildSearchRequestFromLoadout,
  evaluateLoadout,
  fetchLoadoutPreview,
  fetchLoadoutSnapshot,
} from "../api/loadout";
import SearchSettingsPanel from "../components/calculator/SearchSettingsPanel";
import BatchCompareDialog from "../components/calculator/BatchCompareDialog";
import SurvivalEstimateDialog from "../components/calculator/SurvivalEstimateDialog";
import OCRUploadDialog from "../components/calculator/OCRUploadDialog";
import DamageDashboardDialog from "../components/calculator/DamageDashboardDialog";
import HelpDialog from "../components/calculator/HelpDialog";
import DataSourceDialog from "../components/calculator/DataSourceDialog";
import DonationDialog from "../components/calculator/DonationDialog";
import { logOperation, exportLogsAsJson } from "../utils/operationLog";
import { useComputeStore } from "../store/computeStore";
import { fetchLayout, fetchVariables } from "../api/layout";
import type { DamageSnapshot } from "../api/compute";
import { fetchWeapons } from "../api/data";

const DamageChart = lazy(() => import("../components/calculator/DamageChart"));

export default function ComputePage() {
  const { t } = useTranslation();
  const weaponScopeOptions = useMemo(() => [t("compute.currentWeapon"), t("compute.sameTypeStar"), t("compute.sameTypeAll")], [t]);
  const equipmentScopeOptions = useMemo(() => [t("compute.allEquipment"), t("compute.setOnly"), t("compute.pieceOnly")], [t]);

  const [tab, setTab] = useState(0);
  const loading = useComputeStore((s) => s.loading);
  const error = useComputeStore((s) => s.error);

  const [selectedChar, setSelectedChar] = useState("");
  const [selectedWeapon, setSelectedWeapon] = useState("");
  const [charData, setCharData] = useState<Record<string, unknown> | null>(null);
  const [weaponData, setWeaponData] = useState<Record<string, unknown> | null>(null);
  const [charLevel, setCharLevel] = useState(90);
  const [weaponLevel, setWeaponLevel] = useState(90);
  const [trustLevel, setTrustLevel] = useState(0);

  const [weaponScope, setWeaponScope] = useState("同类型全部");
  const [equipmentScope, setEquipmentScope] = useState("全部装备");

  const [charAdvancedExpanded, setCharAdvancedExpanded] = useState(true);
  const [weaponAdvancedExpanded, setWeaponAdvancedExpanded] = useState(true);

  const [layout, setLayout] = useState<LayoutDefinition | null>(null);
  const [variables, setVariables] = useState<Record<string, DagVariable> | null>(null);
  const [outputValues, setOutputValues] = useState<Record<string, number>>({});

  const [enemyParams, setEnemyParams] = useState<EnemyParams>({ ...DEFAULT_ENEMY_PARAMS });
  const [multiSkill, setMultiSkill] = useState<MultiSkillSettings>({
    useManualCounts: false,
    manualCounts: {},
    damageComponentMode: "skill_and_abnormal",
    useExpectedCrit: false,
  });
  const [fixedLoadout, setFixedLoadout] = useState<FixedLoadoutSelection | null>(null);
  const [critAbnormal, setCritAbnormal] = useState<CritAndAbnormalSettings>({
    extraCritRate: 0,
    extraCritDamage: 0,
    includeConditionalEquipmentCrit: false,
    physicalAbnormalCounts: {},
    spellAbnormalCounts: {},
  });
  const [presetDialogOpen, setPresetDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [searchHistoryOpen, setSearchHistoryOpen] = useState(false);
  const [historyEntry, setHistoryEntry] = useState<Record<string, unknown> | null>(null);
  const [skillLevels, setSkillLevels] = useState<Record<string, number>>({});
  const [weaponSkillValues, setWeaponSkillValues] = useState<Record<string, number>>({});
  const [calcMode, setCalcMode] = useState("zone_snapshot");
  const [damageSnapshot, setDamageSnapshot] = useState<DamageSnapshot | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [allWeapons, setAllWeapons] = useState<any[]>([]);
  const [equipmentCatalog, setEquipmentCatalog] = useState<Record<string, unknown[]>>({});
  const [manualBuffDialogOpen, setManualBuffDialogOpen] = useState(false);
  const [manualBuffStore, setManualBuffStore] = useState<ManualBuffStore>({});
  const [previewLines, setPreviewLines] = useState<string[] | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [batchCompareOpen, setBatchCompareOpen] = useState(false);
  const [survivalDialogOpen, setSurvivalDialogOpen] = useState(false);
  const [ocrDialogOpen, setOcrDialogOpen] = useState(false);
  const [dashboardOpen, setDashboardOpen] = useState(false);
  const [searchSettings, setSearchSettings] = useState({ topN: 10, workers: 4, damageComponent: "skill_and_abnormal" });
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);
  const [dataSourceOpen, setDataSourceOpen] = useState(false);
  const [donationOpen, setDonationOpen] = useState(false);

  useEffect(() => {
    fetchLayout().then(setLayout).catch(() => {});
    fetchVariables().then(setVariables).catch(() => {});
    fetchWeapons().then(setAllWeapons).catch(() => {});
  }, []);

  useEffect(() => {
    fetchEquipmentCatalog(equipmentScope).then(setEquipmentCatalog).catch(() => {});
  }, [equipmentScope]);

  const skillLevelsTuple = useMemo((): [number, number, number] => [
    (skillLevels.skill_1_level as number) ?? 8,
    (skillLevels.skill_2_level as number) ?? 8,
    (skillLevels.skill_3_level as number) ?? 8,
  ], [skillLevels]);

  const handleSelectCharacter = useCallback((name: string, data: Record<string, unknown>) => {
    setSelectedChar(name);
    setCharData(data);
  }, []);

  const handleSelectWeapon = useCallback((name: string, data: Record<string, unknown>) => {
    setSelectedWeapon(name);
    setWeaponData(data);
  }, []);

  const handleImportPreset = useCallback((data: Record<string, unknown>) => {
    const schema = String(data.schema || "");
    setSelectedChar(String(data.char_name || ""));
    setSelectedWeapon(String(data.weapon_name || ""));
    setCharLevel(Number(data.char_level ?? 90));
    setWeaponLevel(Number(data.weapon_level ?? 90));
    setTrustLevel(Number(data.trust_level ?? 0));

    if (schema === "endfield_loadout_preset_v2") {
      const levels = data.skill_levels as number[] | undefined;
      if (levels && levels.length >= 3) {
        setSkillLevels({
          skill_1_level: levels[0],
          skill_2_level: levels[1],
          skill_3_level: levels[2],
        });
      }
      setEnemyParams(mergeEnemyParams((data.enemy_params as Partial<EnemyParams>) ?? {}));
      setMultiSkill({
        useManualCounts: Boolean(data.use_manual_multi_skill_counts),
        manualCounts: (data.multi_skill_counts as Record<string, number>) ?? {},
        damageComponentMode: String(data.damage_component_mode ?? "skill_and_abnormal"),
        useExpectedCrit: Boolean(data.use_expected_crit),
      });
      setCritAbnormal({
        extraCritRate: Number(data.extra_crit_rate ?? 0),
        extraCritDamage: Number(data.extra_crit_damage ?? 0),
        includeConditionalEquipmentCrit: Boolean(data.include_conditional_equipment_crit),
        physicalAbnormalCounts: (data.physical_abnormal_counts as Record<string, number>) ?? {},
        spellAbnormalCounts: (data.spell_abnormal_counts as Record<string, number>) ?? {},
      });
      setManualBuffStore((data.manual_buffs as ManualBuffStore) ?? {});
      const fixed = data.fixed_equipment_names as Record<string, string | null> | undefined;
      if (fixed) {
        setFixedLoadout({
          chest: fixed.chest ?? null,
          gloves: fixed.gloves ?? null,
          accessory_a: fixed.accessory_a ?? null,
          accessory_b: fixed.accessory_b ?? null,
        });
      }
      const normal = (data.weapon_normal_levels as number[]) ?? [];
      const wsv: Record<string, number> = {};
      normal.forEach((lv, i) => {
        wsv[`normal_skill_${i + 1}_level`] = lv;
      });
      const specials = (data.weapon_special_states as { level: number; stack: number }[]) ?? [];
      specials.forEach((s, i) => {
        wsv[`special_skill_${i + 1}_level`] = s.level;
        wsv[`special_skill_${i + 1}_stack`] = s.stack;
      });
      if (Object.keys(wsv).length > 0) setWeaponSkillValues(wsv);
      if (data.weapon_scope) setWeaponScope(String(data.weapon_scope));
      if (data.equipment_scope) setEquipmentScope(String(data.equipment_scope));
      return;
    }

    const web = data as {
      enemy_params?: Partial<EnemyParams>;
      multi_skill?: {
        use_manual_multi_skill_counts?: boolean;
        manual_counts?: Record<string, number>;
        damage_component_mode?: string;
      };
      fixed_loadout?: FixedLoadoutSelection | null;
    };
    setEnemyParams(mergeEnemyParams(web.enemy_params ?? {}));
    setMultiSkill({
      useManualCounts: Boolean(web.multi_skill?.use_manual_multi_skill_counts),
      manualCounts: web.multi_skill?.manual_counts ?? {},
      damageComponentMode: web.multi_skill?.damage_component_mode ?? "skill_and_abnormal",
      useExpectedCrit: false,
    });
    if (web.fixed_loadout) {
      setFixedLoadout(web.fixed_loadout as unknown as FixedLoadoutSelection);
    }
  }, []);

  const makeLoadoutPayload = useCallback(() => {
    return buildWebLoadoutPayload({
      charData,
      weaponData,
      charLevel,
      weaponLevel,
      trustLevel,
      skillLevels,
      weaponSkillValues,
      weaponScope,
      equipmentScope,
      calcMode,
      multiSkill,
      critAbnormal,
      enemyParams,
      fixedLoadout,
      manualBuffStore,
      equipmentCatalog,
    });
  }, [
    charData,
    weaponData,
    charLevel,
    weaponLevel,
    trustLevel,
    skillLevels,
    weaponSkillValues,
    weaponScope,
    equipmentScope,
    calcMode,
    multiSkill,
    critAbnormal,
    enemyParams,
    fixedLoadout,
    manualBuffStore,
    equipmentCatalog,
  ]);

  const handleEvaluate = useCallback(async () => {
    const payload = makeLoadoutPayload();
    if (!payload) {
      useComputeStore.setState({ error: "请先选择角色与武器", loading: false });
      return;
    }

    logOperation("evaluate", `${selectedChar}+${selectedWeapon} Lv.${charLevel}/${weaponLevel}`);
    try {
      useComputeStore.setState({ loading: true, error: null });
      const evalResult = await evaluateLoadout(payload);
      setOutputValues(evalResult.outputs);

      setHistoryEntry({
        char_name: selectedChar,
        weapon_name: selectedWeapon,
        loadout: payload,
        outputs: evalResult.outputs,
        node_values: evalResult.node_values,
      });

      useComputeStore.setState({ result: evalResult, error: null, loading: false });

      setSnapshotLoading(true);
      setPreviewLoading(true);
      setPreviewError(null);
      fetchLoadoutSnapshot(payload)
        .then(setDamageSnapshot)
        .catch(() => {})
        .finally(() => setSnapshotLoading(false));
      fetchLoadoutPreview(payload)
        .then(setPreviewLines)
        .catch((e) => {
          setPreviewError(String(e));
          setPreviewLines(null);
        })
        .finally(() => setPreviewLoading(false));
    } catch (e: unknown) {
      useComputeStore.setState({ error: String(e), loading: false });
    }
  }, [makeLoadoutPayload, selectedChar, selectedWeapon, charLevel, weaponLevel]);

  const loadoutPayload = makeLoadoutPayload();
  const searchParams = loadoutPayload
    ? {
        ...buildSearchRequestFromLoadout(loadoutPayload, {
          all_weapons: allWeapons as Record<string, unknown>[],
          current_weapon: (weaponData ?? {}) as Record<string, unknown>,
          equipment_catalog: equipmentCatalog as Record<string, Record<string, unknown>[]>,
        }),
        top_n: searchSettings.topN,
        max_workers: searchSettings.workers,
      }
    : null;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        终末地伤害计算器
      </Typography>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)}>
          <Tab label="计算页" />
          <Tab label="高级页" />
        </Tabs>
      </Paper>

      {tab === 0 && (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 5 }}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <CharacterSelector
                selectedChar={selectedChar}
                selectedWeapon={selectedWeapon}
                onSelectCharacter={handleSelectCharacter}
                onSelectWeapon={handleSelectWeapon}
                charLevel={charLevel}
                weaponLevel={weaponLevel}
                onCharLevelChange={setCharLevel}
                onWeaponLevelChange={setWeaponLevel}
              />
            </Paper>

            <Box
              sx={{ display: "flex", alignItems: "center", cursor: "pointer", mb: 0.5 }}
              onClick={() => setCharAdvancedExpanded(!charAdvancedExpanded)}
            >
              <Typography variant="subtitle2" sx={{ flex: 1 }}>
                技能等级
              </Typography>
              <IconButton size="small">
                {charAdvancedExpanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>
            <Collapse in={charAdvancedExpanded}>
              <SkillLevelPanel charData={charData} onChange={setSkillLevels} />
            </Collapse>

            <Box
              sx={{ display: "flex", alignItems: "center", cursor: "pointer", mb: 0.5, mt: 1 }}
              onClick={() => setWeaponAdvancedExpanded(!weaponAdvancedExpanded)}
            >
              <Typography variant="subtitle2" sx={{ flex: 1 }}>
                武器技能
              </Typography>
              <IconButton size="small">
                {weaponAdvancedExpanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>
            <Collapse in={weaponAdvancedExpanded}>
              <WeaponSkillPanel weaponData={weaponData} onChange={setWeaponSkillValues} />
            </Collapse>

            <AttributeDisplay
              characterData={charData}
              weaponData={weaponData}
              charLevel={charLevel}
              weaponLevel={weaponLevel}
              trustLevel={trustLevel}
              onTrustLevelChange={setTrustLevel}
              skillLevels={skillLevels}
            />

            <EnemyParamPanel onParamsChange={setEnemyParams} />

            <Paper sx={{ p: 2, mb: 2 }}>
              <CalcModeSelector value={calcMode} onChange={setCalcMode} />
            </Paper>

            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom color="text.secondary">
                搜索范围
              </Typography>
              <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                <InputLabel>武器候选范围</InputLabel>
                <Select
                  value={weaponScope}
                  label="武器候选范围"
                  onChange={(e) => setWeaponScope(e.target.value)}
                >
                  {weaponScopeOptions.map((o) => (
                    <MenuItem key={o} value={o}>{o}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth size="small">
                <InputLabel>装备范围</InputLabel>
                <Select
                  value={equipmentScope}
                  label="装备范围"
                  onChange={(e) => setEquipmentScope(e.target.value)}
                >
                  {equipmentScopeOptions.map((o) => (
                    <MenuItem key={o} value={o}>{o}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, md: 7 }}>
            {layout && variables && (
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  {layout.name}
                </Typography>
                <WebComputeSheet
                  layout={layout}
                  variables={variables}
                  onInputChange={() => {}}
                  onEvaluate={handleEvaluate}
                  outputValues={outputValues}
                  loading={loading}
                />
              </Paper>
            )}

            {outputValues && Object.keys(outputValues).length > 0 && (
              <Box sx={{ mt: 2 }}>
                <TotalDamagePanel
                  snapshot={damageSnapshot}
                  loading={snapshotLoading}
                />
                <PreviewText
                  outputValues={outputValues}
                  nodeValues={null}
                />
                <SearchPreviewPanel
                  lines={previewLines}
                  loading={previewLoading}
                  error={previewError}
                />
                {Object.keys(outputValues).length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Suspense fallback={null}>
                      <DamageChart
                        outputValues={outputValues}
                        nodeValues={null}
                        zoneShare={
                          damageSnapshot?.zone_share_percent as Record<string, number> | undefined
                        }
                      />
                    </Suspense>
                  </Box>
                )}
              </Box>
            )}

            {error && (
              <Paper sx={{ p: 2, mt: 2 }}>
                <Typography color="error">{error}</Typography>
              </Paper>
            )}
          </Grid>
        </Grid>
      )}

      {tab === 1 && (
        <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 5 }}>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<BuildIcon />}
                    onClick={() => setPresetDialogOpen(true)}
                    fullWidth
                  >
                    工具与分享
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<TuneIcon />}
                    onClick={() => setManualBuffDialogOpen(true)}
                  >
                    Buff微调
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setSurvivalDialogOpen(true)}
                  >
                    处决/治疗
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<CompareArrowsIcon />}
                    onClick={() => setBatchCompareOpen(true)}
                  >
                    方案对比
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setDashboardOpen(true)}
                  >
                    伤害仪表盘
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<CameraAltIcon />}
                    onClick={() => setOcrDialogOpen(true)}
                  >
                    截图识装
                  </Button>
                </Box>
                <Box sx={{ display: "flex", gap: 1, mt: 1, flexWrap: "wrap" }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setHelpDialogOpen(true)}
                  >
                    使用说明
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setDataSourceOpen(true)}
                  >
                    数据来源
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setDonationOpen(true)}
                  >
                    捐赠
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => { logOperation("export_log"); exportLogsAsJson(); }}
                  >
                    导出日志
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setHistoryDialogOpen(true)}
                  >
                    历史
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setSearchHistoryOpen(true)}
                  >
                    搜索历史
                  </Button>
                </Box>
              </Paper>
              <FixedLoadoutPanel onChange={setFixedLoadout} equipmentScope={equipmentScope} />
              <MultiSkillPanel
                charData={charData}
                skillLevels={skillLevelsTuple}
                onChange={setMultiSkill}
              />
              <CritAndAbnormalPanel onChange={setCritAbnormal} />
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 7 }}>
            <SearchSettingsPanel settings={searchSettings} onChange={setSearchSettings} />
            <Paper sx={{ p: 3 }}>
              <SearchPanel currentParams={(searchParams ?? {}) as any} />
            </Paper>
          </Grid>
        </Grid>
      )}

      <PresetDialog
        open={presetDialogOpen}
        onClose={() => setPresetDialogOpen(false)}
        loadoutPayload={loadoutPayload}
        currentState={{
          charName: selectedChar,
          weaponName: selectedWeapon,
          charLevel,
          weaponLevel,
          enemyParams,
          multiSkill,
          fixedLoadout: fixedLoadout as Record<string, string | null> | null,
        }}
        onImport={handleImportPreset}
      />

      <CalcHistoryDialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        currentEntry={historyEntry as any}
        onRestore={(entry) => {
          setSelectedChar(String(entry.char_name || ""));
          setSelectedWeapon(String(entry.weapon_name || ""));
          setHistoryDialogOpen(false);
        }}
      />

      <SearchHistoryDialog
        open={searchHistoryOpen}
        onClose={() => setSearchHistoryOpen(false)}
      />

      <SegmentManualBuffDialog
        open={manualBuffDialogOpen}
        onClose={() => setManualBuffDialogOpen(false)}
        store={manualBuffStore}
        onApply={(store) => {
          setManualBuffStore(store);
          setManualBuffDialogOpen(false);
        }}
        manualCounts={multiSkill.manualCounts}
        physicalAbnormalCounts={critAbnormal.physicalAbnormalCounts}
        spellAbnormalCounts={critAbnormal.spellAbnormalCounts}
      />

      <BatchCompareDialog
        open={batchCompareOpen}
        onClose={() => setBatchCompareOpen(false)}
        enemyParams={enemyParams}
      />

      <SurvivalEstimateDialog
        open={survivalDialogOpen}
        onClose={() => setSurvivalDialogOpen(false)}
        charData={charData}
        weaponData={weaponData}
        charLevel={charLevel}
        weaponLevel={weaponLevel}
        trustLevel={trustLevel}
        enemyParams={enemyParams}
      />

      <OCRUploadDialog
        open={ocrDialogOpen}
        onClose={() => setOcrDialogOpen(false)}
        onResult={(data) => {
          if (data.preset) {
            handleImportPreset(data.preset);
          } else {
            if (data.char_name) setSelectedChar(data.char_name);
            if (data.weapon_name) setSelectedWeapon(data.weapon_name);
          }
          setOcrDialogOpen(false);
        }}
      />

      <DamageDashboardDialog
        open={dashboardOpen}
        onClose={() => setDashboardOpen(false)}
        snapshot={damageSnapshot}
      />

      <HelpDialog open={helpDialogOpen} onClose={() => setHelpDialogOpen(false)} />

      <DataSourceDialog open={dataSourceOpen} onClose={() => setDataSourceOpen(false)} />

      <DonationDialog open={donationOpen} onClose={() => setDonationOpen(false)} />
    </Box>
  );
}
