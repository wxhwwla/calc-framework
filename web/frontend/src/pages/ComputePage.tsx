import { useEffect, useState, useCallback } from "react";
import { Box, Paper, Grid2 as Grid, Typography, Tabs, Tab } from "@mui/material";
import CharacterSelector from "../components/calculator/CharacterSelector";
import AttributeDisplay from "../components/calculator/AttributeDisplay";
import WebComputeSheet from "../components/WebComputeSheet";
import SearchPanel from "../components/calculator/SearchPanel";
import type { LayoutDefinition } from "../components/WebComputeSheet";
import type { DagVariable } from "../utils/controlInference";
import { useComputeStore } from "../store/computeStore";
import { fetchLayout, fetchVariables } from "../api/layout";
import { evaluate } from "../api/compute";
import { fetchWeapons } from "../api/data";

export default function ComputePage() {
  const [tab, setTab] = useState(0);
  const loading = useComputeStore((s) => s.loading);
  const error = useComputeStore((s) => s.error);

  const [selectedChar, setSelectedChar] = useState("");
  const [selectedWeapon, setSelectedWeapon] = useState("");
  const [charData, setCharData] = useState<Record<string, unknown> | null>(null);
  const [weaponData, setWeaponData] = useState<Record<string, unknown> | null>(null);

  const [layout, setLayout] = useState<LayoutDefinition | null>(null);
  const [variables, setVariables] = useState<Record<string, DagVariable> | null>(null);
  const [outputValues, setOutputValues] = useState<Record<string, number>>({});
  const [inputValues, _setInputValues] = useState<Record<string, number | boolean | string>>({});

  const [allWeapons, setAllWeapons] = useState<any[]>([]);
  const [equipmentCatalog, setEquipmentCatalog] = useState<Record<string, unknown[]>>({});

  useEffect(() => {
    fetchLayout().then(setLayout).catch(() => {});
    fetchVariables().then(setVariables).catch(() => {});
    fetchWeapons().then(setAllWeapons).catch(() => {});
    fetch("/api/search/catalog")
      .then((r) => r.json())
      .then(setEquipmentCatalog)
      .catch(() => {});
  }, []);

  const handleSelectCharacter = useCallback((name: string, data: Record<string, unknown>) => {
    setSelectedChar(name);
    setCharData(data);
  }, []);

  const handleSelectWeapon = useCallback((name: string, data: Record<string, unknown>) => {
    setSelectedWeapon(name);
    setWeaponData(data);
  }, []);

  const getAttr90 = useCallback((data: Record<string, unknown> | null, attr: string): number => {
    if (!data) return 0;
    const arr = data[attr];
    if (Array.isArray(arr)) {
      const idx = Math.min(89, arr.length - 1);
      return typeof arr[idx] === "number" ? (arr[idx] as number) : 0;
    }
    return typeof arr === "number" ? (arr as number) : 0;
  }, []);

  const handleEvaluate = useCallback(async () => {
    const adapter = "终末地伤害计算";
    const charBaseAtk = getAttr90(charData, "基础攻击力");
    const weaponBaseAtk = getAttr90(weaponData, "基础攻击力");
    const charStrength = getAttr90(charData, "力量");
    const charAgility = getAttr90(charData, "敏捷");
    const charIntellect = getAttr90(charData, "智识");
    const charWill = getAttr90(charData, "意志");

    const context: Record<string, Record<string, number | boolean | string>> = {
      character: {
        "基础攻击": charBaseAtk,
        "力量": charStrength,
        "敏捷": charAgility,
        "智识": charIntellect,
        "意志": charWill,
        "暴击率": 0.05,
        "暴击伤害": 0.5,
      },
      weapon: {
        "基础攻击": weaponBaseAtk,
        "攻击力+": 0,
        "附加攻击力+": 0,
      },
      enemy: {
        "防御": 100,
      },
      equipment: {
        "攻击力平值": 0,
      },
      computed: {
        "主能力平值加算": charStrength,
        "副能力平值加算": charAgility,
        "主能力百分比": 0,
        "副能力百分比": 0,
        "技能倍率": 1,
        "伤害加成": 0,
        "伤害减免": 0,
        "增幅": 0,
        "虚弱": 0,
        "庇护": 0,
        "脆弱": 0,
        "易伤": 0,
        "失衡易伤": 0,
        "抗性": 0,
        "非主控减伤": 0,
        "连击增伤": 0,
        "特殊乘区": 0,
        "力量加成值": 0,
        "敏捷加成值": 0,
        "智识加成值": 0,
        "意志加成值": 0,
      },
      user_input: {},
    };

    for (const [path, val] of Object.entries(inputValues)) {
      const parts = path.split(".");
      if (parts.length === 2) {
        const ns = parts[0];
        const key = parts[1];
        if (!context[ns]) context[ns] = {};
        context[ns][key] = val;
      }
    }

    try {
      useComputeStore.setState({ loading: true, error: null });
      const evalResult = await evaluate(adapter, context);
      setOutputValues(evalResult.outputs);
      useComputeStore.setState({ result: evalResult, error: null, loading: false });
    } catch (e: unknown) {
      useComputeStore.setState({ error: String(e), loading: false });
    }
  }, [charData, weaponData, inputValues, getAttr90]);

  const searchParams = {
    char_data: (charData ?? {}) as Record<string, unknown>,
    char_level: 90,
    weapon_level: 90,
    trust_level: 12,
    skill_name: "战技",
    skill_type: "战技",
    skill_multiplier: 1.0,
    damage_type: "物理",
    weapon_scope_label: "同类型",
    equipment_scope_label: "全部",
    all_weapons: allWeapons as Record<string, unknown>[],
    current_weapon: (weaponData ?? {}) as Record<string, unknown>,
    equipment_catalog: equipmentCatalog as Record<string, Record<string, unknown>[]>,
    enemy_defense: 100,
  };

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
              />
            </Paper>

            <AttributeDisplay characterData={charData} weaponData={weaponData} />
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

            {error && (
              <Paper sx={{ p: 2, mt: 2 }}>
                <Typography color="error">{error}</Typography>
              </Paper>
            )}
          </Grid>
        </Grid>
      )}

      {tab === 1 && (
        <Paper sx={{ p: 3 }}>
          <SearchPanel currentParams={searchParams as any} />
        </Paper>
      )}
    </Box>
  );
}
