import { useEffect, useState, useCallback } from "react";
import {
  Box, Typography, Paper, Grid, TextField, Button, CircularProgress,
  Alert, Card, CardContent, Slider, Divider, Chip, Select, MenuItem,
  FormControl, InputLabel, Checkbox, FormControlLabel,
  Table, TableBody, TableCell, TableRow,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useArknightsStore } from "../store/arknightsStore";
import {
  parseSkill, parseAutoAttack,
  type ParsedSkill, type ArknightsSkill,
} from "../api/skillParser";
import OperatorSelector from "../components/arknights/OperatorSelector";
import ArknightsAttributeDisplay from "../components/arknights/ArknightsAttributeDisplay";

const SKILL_NAMES = ["普攻", "技能1", "技能2", "技能3"];

export default function ArknightsComputePage() {
  const {
    operatorIndex, operatorLoading, selectedOperator, operatorDetail, detailLoading,
    computeParams, computeResult, computeLoading, error,
    loadOperators, selectOperator, setParam, runCompute,
  } = useArknightsStore();

  const [skillIndex, setSkillIndex] = useState(1);
  const [parsedSkill, setParsedSkill] = useState<ParsedSkill>(parseAutoAttack());
  const [hitCount, setHitCount] = useState(1);
  const [useConditional, setUseConditional] = useState(false);
  const [manualMult, setManualMult] = useState("");

  useEffect(() => { loadOperators(); }, [loadOperators]);

  useEffect(() => {
    if (!operatorDetail) {
      setParsedSkill(parseAutoAttack());
      return;
    }
    if (skillIndex === 0) {
      setParsedSkill(parseAutoAttack());
      return;
    }
    const skills: ArknightsSkill[] = (operatorDetail as any).技能 ?? [];
    const idx = skillIndex - 1;
    if (idx >= skills.length) {
      setParsedSkill(parseAutoAttack());
      return;
    }
    const ps = parseSkill(skills[idx], computeParams.skill_level);
    setParsedSkill(ps);
    setHitCount(ps.hitCount);
    setManualMult("");
    setUseConditional(false);
  }, [operatorDetail, skillIndex, computeParams.skill_level]);

  const effectiveMult = useConditional && parsedSkill.hasConditional
    ? parsedSkill.conditionalMult
    : (manualMult ? parseFloat(manualMult) || parsedSkill.effectiveMultiplier : parsedSkill.effectiveMultiplier);

  const handleCompute = useCallback(() => {
    useArknightsStore.setState({
      computeParams: {
        ...computeParams,
        skill_multiplier: effectiveMult,
        atk_percent_bonus: computeParams.atk_percent_bonus + parsedSkill.atkBuffHint * 100,
      },
    });
    runCompute();
  }, [computeParams, effectiveMult, parsedSkill.atkBuffHint, runCompute]);

  const totalDamageMult = effectiveMult * hitCount;

  return (
    <Box sx={{ p: 2, maxWidth: 1400, mx: "auto" }}>
      <Typography variant="h5" gutterBottom>明日方舟 伤害计算器</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => useArknightsStore.setState({ error: null })}>{error}</Alert>}

      <Grid container spacing={2}>
        {/* 左栏 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            {operatorLoading ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}><CircularProgress size={24} /></Box>
            ) : (
              <OperatorSelector
                operatorIndex={operatorIndex}
                selectedOperator={selectedOperator}
                onSelect={selectOperator}
                skillLevel={computeParams.skill_level}
                onSkillLevelChange={(v) => setParam("skill_level", v)}
                skillMultiplier={computeParams.skill_multiplier}
                onSkillMultiplierChange={(v) => {
                  setManualMult(String(v));
                  setParam("skill_multiplier", v);
                }}
              />
            )}
          </Paper>

          {operatorDetail && !detailLoading && (
            <Paper sx={{ p: 2, mt: 2 }}>
              <ArknightsAttributeDisplay operator={operatorDetail as any} />
            </Paper>
          )}
        </Grid>

        {/* 右栏 */}
        <Grid item xs={12} md={8}>
          {/* 技能选择 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>技能选择</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>技能</InputLabel>
                  <Select
                    value={skillIndex}
                    label="技能"
                    onChange={(e) => setSkillIndex(e.target.value as number)}
                  >
                    {SKILL_NAMES.map((n, i) => {
                      const skills: ArknightsSkill[] = (operatorDetail as any)?.技能 ?? [];
                      const disabled = i > 0 && (i - 1) >= skills.length;
                      return <MenuItem key={i} value={i} disabled={disabled}>{n}</MenuItem>;
                    })}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">
                  技能等级
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Slider
                    size="small" min={1} max={10} step={1}
                    value={computeParams.skill_level}
                    onChange={(_e, v) => setParam("skill_level", v as number)}
                    valueLabelDisplay="auto" sx={{ flex: 1 }}
                    valueLabelFormat={(v) => v <= 7 ? `Lv.${v}` : `专${v - 7}`}
                  />
                  <Typography variant="caption" sx={{ minWidth: 50 }}>
                    {computeParams.skill_level <= 7 ? `Lv.${computeParams.skill_level}` : `专${computeParams.skill_level - 7}`}
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            {parsedSkill.description && (
              <Box sx={{ mt: 1, p: 1, bgcolor: "#1A1A1A", borderRadius: 1 }}>
                <Typography variant="caption" color="primary" sx={{ fontWeight: "bold" }}>
                  {parsedSkill.name}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                  SP={parsedSkill.spCost}  初始={parsedSkill.initSp}  持续={parsedSkill.duration}秒
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {parsedSkill.description}
                </Typography>
                {parsedSkill.isHealing && (
                  <Chip label="⚕ 治疗技能" size="small" color="success" sx={{ mt: 0.5 }} />
                )}
              </Box>
            )}
          </Paper>

          {/* 技能参数 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>技能参数</Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">技能倍率</Typography>
                <TextField
                  size="small" fullWidth
                  value={manualMult || parsedSkill.effectiveMultiplier.toFixed(2)}
                  onChange={(e) => setManualMult(e.target.value)}
                  placeholder={String(parsedSkill.effectiveMultiplier.toFixed(2))}
                />
                <Typography variant="caption" color="text.secondary">
                  自动检测: {parsedSkill.effectiveMultiplier.toFixed(2)}x
                  {parsedSkill.atkBuffHint > 0 && ` (ATK+${(parsedSkill.atkBuffHint * 100).toFixed(0)}%)`}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">连发数</Typography>
                <TextField
                  size="small" fullWidth type="number"
                  value={hitCount}
                  onChange={(e) => setHitCount(Math.max(1, parseInt(e.target.value) || 1))}
                />
                <Typography variant="caption" color="text.secondary">
                  自动检测: {parsedSkill.hitCount}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                {parsedSkill.hasConditional && (
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={useConditional}
                        onChange={(e) => setUseConditional(e.target.checked)}
                        size="small"
                      />
                    }
                    label={`仅攻击到一人时（${parsedSkill.conditionalMult.toFixed(2)}x）`}
                  />
                )}
                <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                  总伤害倍率: {totalDamageMult.toFixed(3)}x
                </Typography>
              </Grid>
            </Grid>
          </Paper>

          {/* 敌人参数 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>敌人参数</Typography>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">防御力 (DEF)</Typography>
                <Slider size="small" min={0} max={3000} step={10}
                  value={computeParams.enemy_def}
                  onChange={(_e, v) => setParam("enemy_def", v as number)}
                  valueLabelDisplay="auto" />
                <TextField size="small" type="number" value={computeParams.enemy_def}
                  onChange={(e) => setParam("enemy_def", Number(e.target.value) || 0)} />
              </Box>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">法术抗性 (RES)</Typography>
                <Slider size="small" min={0} max={100} step={1}
                  value={computeParams.enemy_res}
                  onChange={(_e, v) => setParam("enemy_res", v as number)}
                  valueLabelDisplay="auto" />
                <TextField size="small" type="number" value={computeParams.enemy_res}
                  onChange={(e) => setParam("enemy_res", Number(e.target.value) || 0)} />
              </Box>
            </Box>
          </Paper>

          {/* 额外加成 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>额外加成</Typography>
            <Grid container spacing={2}>
              {[
                { label: "攻击力%加成", key: "atk_percent_bonus" as const, min: -100, max: 200, step: 5 },
                { label: "伤害倍率加成%", key: "dmg_bonus" as const, min: -100, max: 200, step: 5 },
                { label: "防御穿透%", key: "def_penetration" as const, min: 0, max: 100, step: 5 },
                { label: "法抗穿透%", key: "res_penetration" as const, min: 0, max: 100, step: 5 },
              ].map(({ label, key, min, max, step }) => (
                <Grid item xs={12} sm={6} key={key}>
                  <Typography variant="caption" color="text.secondary">{label}</Typography>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Slider size="small" min={min} max={max} step={step}
                      value={computeParams[key]}
                      onChange={(_e, v) => setParam(key, v as number)}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(v) => `${v > 0 ? "+" : ""}${v}${key.includes("pen") ? "%" : "%"}`}
                      sx={{ flex: 1 }} />
                    <Typography variant="caption" sx={{ minWidth: 40, textAlign: "right" }}>
                      {computeParams[key] > 0 ? "+" : ""}{computeParams[key]}%
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Paper>

          {/* 计算按钮 */}
          <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
            <Button variant="contained" size="large"
              startIcon={computeLoading ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
              onClick={handleCompute}
              disabled={!selectedOperator || computeLoading}
              sx={{ minWidth: 200 }}>
              {computeLoading ? "计算中..." : "开始计算"}
            </Button>
          </Box>

          {/* 结果 */}
          {computeResult && (
            <>
              {/* 卡片 */}
              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
                {[
                  { label: "最终攻击力", value: Math.round(computeResult.final_atk), color: "default" },
                  { label: "物理伤害", value: Math.round(computeResult.physical_damage), color: "warning.main" },
                  { label: "法术伤害", value: Math.round(computeResult.magical_damage), color: "primary.main" },
                  { label: "真实伤害", value: Math.round(computeResult.true_damage), color: "success.main" },
                ].map(({ label, value, color }) => (
                  <Card key={label} variant="outlined" sx={{ flex: 1, minWidth: 140 }}>
                    <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                      <Typography variant="caption" color="text.secondary">{label}</Typography>
                      <Typography variant="h5" sx={{ color }}>{value.toLocaleString()}</Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>

              {/* 乘区明细 */}
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  乘区明细 — {computeResult.operator_name}（{parsedSkill.name}）
                  {parsedSkill.isHealing && <Chip label="⚕ 治疗" size="small" color="success" sx={{ ml: 1 }} />}
                </Typography>
                <Divider sx={{ mb: 1 }} />
                <Table size="small" sx={{ maxWidth: 500 }}>
                  <TableBody>
                    {[
                      ["基础攻击力", String(Math.round((operatorDetail as any)?.基础属性?.攻击 ?? 0))],
                      ["信赖加成", `+${Math.round((operatorDetail as any)?.信赖加成?.攻击 ?? 0)}`],
                      ["最终攻击力", String(Math.round(computeResult.final_atk))],
                      ["技能倍率", `x${effectiveMult.toFixed(2)}`],
                      ["连发数", `x${hitCount}`],
                      ["总伤害倍率", `x${totalDamageMult.toFixed(2)}`],
                      ["敌军防御力", String(computeParams.enemy_def)],
                      ["敌军法抗", `${computeParams.enemy_res}%`],
                      ...(hitCount > 1 ? [
                        [hitCount > 1 ? `物理伤害(合)` : "物理伤害", String(Math.round(computeResult.physical_damage))],
                        [hitCount > 1 ? `法术伤害(合)` : "法术伤害", String(Math.round(computeResult.magical_damage))],
                        [hitCount > 1 ? `真实伤害(合)` : "真实伤害", String(Math.round(computeResult.true_damage))],
                      ] as [string, string][] : []),
                    ].map(([k, v]) => (
                      <TableRow key={k} sx={{ "&:last-child td": { borderBottom: 0 } }}>
                        <TableCell sx={{ pl: 0, py: 0.25 }}><Typography variant="body2" color="text.secondary">{k}</Typography></TableCell>
                        <TableCell sx={{ pr: 0, py: 0.25 }} align="right"><Typography variant="body2">{v}</Typography></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>

              {/* 异常/元素面板 */}
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>异常/元素伤害</Typography>
                <Divider sx={{ mb: 1 }} />
                <Table size="small" sx={{ maxWidth: 500 }}>
                  <TableBody>
                    {[
                      ["灼燃损伤", "1.0x", "0"],
                      ["凋亡损伤", "1.0x", "0"],
                    ].map(([type, mult, extra]) => (
                      <TableRow key={type}>
                        <TableCell sx={{ pl: 0, py: 0.25 }}><Typography variant="body2" color="text.secondary">{type}</Typography></TableCell>
                        <TableCell sx={{ py: 0.25 }}><Typography variant="body2">{mult}</Typography></TableCell>
                        <TableCell sx={{ pr: 0, py: 0.25 }} align="right"><Typography variant="body2">{extra}</Typography></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            </>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
