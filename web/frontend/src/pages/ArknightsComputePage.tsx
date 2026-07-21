import { useEffect, useState, useCallback, useMemo } from "react";
import {
  Box, Typography, Paper, Grid, TextField, Button, CircularProgress,
  Alert, Card, CardContent, Slider, Divider, Chip, Select, MenuItem,
  FormControl, InputLabel, Checkbox, FormControlLabel,
  Table, TableBody, TableCell, TableRow, TableContainer,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useTranslation } from "react-i18next";
import { useArknightsStore } from "../store/arknightsStore";
import {
  parseSkill, parseAutoAttack,
  type ParsedSkill, type ArknightsSkill,
} from "../api/skillParser";
import OperatorSelector from "../components/arknights/OperatorSelector";
import ArknightsAttributeDisplay from "../components/arknights/ArknightsAttributeDisplay";

export default function ArknightsComputePage() {
  const { t } = useTranslation();
  const skillNames = useMemo(() => [t("arknights.normalAtk"), t("arknights.skill1"), t("arknights.skill2"), t("arknights.skill3")], [t]);
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
    const skills: ArknightsSkill[] = operatorDetail.技能 ?? [];
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
      <Typography variant="h5" gutterBottom>{t("arknights.pageTitle")}</Typography>

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
              <ArknightsAttributeDisplay operator={operatorDetail} />
            </Paper>
          )}
        </Grid>

        {/* 右栏 */}
        <Grid item xs={12} md={8}>
          {/* 技能选择 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>{t("arknights.skillSelect")}</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>{t("arknights.skill")}</InputLabel>
                  <Select
                    value={skillIndex}
                    label={t("arknights.skill")}
                    onChange={(e) => setSkillIndex(e.target.value as number)}
                  >
                    {skillNames.map((n, i) => {
                      const skills: ArknightsSkill[] = operatorDetail?.技能 ?? [];
                      const disabled = i > 0 && (i - 1) >= skills.length;
                      return <MenuItem key={i} value={i} disabled={disabled}>{n}</MenuItem>;
                    })}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="caption" color="text.secondary">
                  {t("arknights.skillLevel")}
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
                  SP={parsedSkill.spCost}  {t("arknights.initSp")}={parsedSkill.initSp}  {t("arknights.durationSec")}={parsedSkill.duration}{t("arknights.seconds")}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {parsedSkill.description}
                </Typography>
                {parsedSkill.isHealing && (
                  <Chip label={t("arknights.healSkill")} size="small" color="success" sx={{ mt: 0.5 }} />
                )}
              </Box>
            )}
          </Paper>

          {/* 技能参数 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>{t("arknights.skillParams")}</Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">{t("arknights.skillMultiplier")}</Typography>
                <TextField
                  size="small" fullWidth
                  value={manualMult || parsedSkill.effectiveMultiplier.toFixed(2)}
                  onChange={(e) => setManualMult(e.target.value)}
                  placeholder={String(parsedSkill.effectiveMultiplier.toFixed(2))}
                />
                <Typography variant="caption" color="text.secondary">
                  {t("arknights.autoDetect")}: {parsedSkill.effectiveMultiplier.toFixed(2)}x
                  {parsedSkill.atkBuffHint > 0 && ` (ATK+${(parsedSkill.atkBuffHint * 100).toFixed(0)}%)`}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">{t("arknights.hitCount")}</Typography>
                <TextField
                  size="small" fullWidth type="number"
                  value={hitCount}
                  onChange={(e) => setHitCount(Math.max(1, parseInt(e.target.value) || 1))}
                />
                <Typography variant="caption" color="text.secondary">
                  {t("arknights.autoDetect")}: {parsedSkill.hitCount}
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
                    label={`${t("arknights.conditionalSingleTarget")}（${parsedSkill.conditionalMult.toFixed(2)}x）`}
                  />
                )}
                <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                  {t("arknights.totalDamageMultiplier")}: {totalDamageMult.toFixed(3)}x
                </Typography>
              </Grid>
            </Grid>
          </Paper>

          {/* 敌人参数 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>{t("arknights.enemyParams")}</Typography>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">{t("arknights.enemyDefense")}</Typography>
                <Slider size="small" min={0} max={3000} step={10}
                  value={computeParams.enemy_def}
                  onChange={(_e, v) => setParam("enemy_def", v as number)}
                  valueLabelDisplay="auto" />
                <TextField size="small" type="number" value={computeParams.enemy_def}
                  onChange={(e) => setParam("enemy_def", Number(e.target.value) || 0)} />
              </Box>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">{t("arknights.magicResistance")}</Typography>
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
            <Typography variant="subtitle1" gutterBottom>{t("arknights.extraBonus")}</Typography>
            <Grid container spacing={2}>
              {[
                { i18nKey: "arknights.atkPercentBonus" as const, key: "atk_percent_bonus" as const, min: -100, max: 200, step: 5 },
                { i18nKey: "arknights.dmgBonusPercent" as const, key: "dmg_bonus" as const, min: -100, max: 200, step: 5 },
                { i18nKey: "arknights.defPenetration" as const, key: "def_penetration" as const, min: 0, max: 100, step: 5 },
                { i18nKey: "arknights.resPenetration" as const, key: "res_penetration" as const, min: 0, max: 100, step: 5 },
              ].map(({ i18nKey, key, min, max, step }) => (
                <Grid item xs={12} sm={6} key={key}>
                  <Typography variant="caption" color="text.secondary">{t(i18nKey)}</Typography>
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
              {computeLoading ? t("arknights.calculating") : t("arknights.startCalc")}
            </Button>
          </Box>

          {/* 结果 */}
          {computeResult && (
            <>
              {/* 卡片 */}
              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
                {[
                  { i18nKey: "arknights.finalAttack" as const, value: Math.round(computeResult.final_atk), color: "default" },
                  { i18nKey: "arknights.physDmg" as const, value: Math.round(computeResult.physical_damage), color: "warning.main" },
                  { i18nKey: "arknights.magicDmg" as const, value: Math.round(computeResult.magical_damage), color: "primary.main" },
                  { i18nKey: "arknights.trueDmg" as const, value: Math.round(computeResult.true_damage), color: "success.main" },
                ].map(({ i18nKey, value, color }) => (
                  <Card key={i18nKey} variant="outlined" sx={{ flex: 1, minWidth: 140 }}>
                    <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                      <Typography variant="caption" color="text.secondary">{t(i18nKey)}</Typography>
                      <Typography variant="h5" sx={{ color }}>{value.toLocaleString()}</Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>

              {/* 乘区明细 */}
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  {t("arknights.zoneDetail")} — {computeResult.operator_name}（{parsedSkill.name}）
                  {parsedSkill.isHealing && <Chip label={t("arknights.healChip")} size="small" color="success" sx={{ ml: 1 }} />}
                </Typography>
                <Divider sx={{ mb: 1 }} />
                <TableContainer sx={{ overflowX: 'auto' }}>
                  <Table size="small" sx={{ maxWidth: 500 }}>
                    <TableBody>
                      {[
                        [t("arknights.baseAttack"), String(Math.round(operatorDetail?.基础属性?.攻击 ?? 0))],
                        [t("arknights.trustBonus"), `+${Math.round(operatorDetail?.信赖加成?.攻击 ?? 0)}`],
                        [t("arknights.finalAttack"), String(Math.round(computeResult.final_atk))],
                        [t("arknights.skillMultiplier"), `x${effectiveMult.toFixed(2)}`],
                        [t("arknights.hitCount"), `x${hitCount}`],
                        [t("arknights.totalDmgMultiplier"), `x${totalDamageMult.toFixed(2)}`],
                        [t("arknights.enemyDefense"), String(computeParams.enemy_def)],
                        [t("arknights.enemyRes"), `${computeParams.enemy_res}%`],
                        ...(hitCount > 1 ? [
                          [t("arknights.physDmg"), String(Math.round(computeResult.physical_damage))],
                          [t("arknights.magicDmg"), String(Math.round(computeResult.magical_damage))],
                          [t("arknights.trueDmg"), String(Math.round(computeResult.true_damage))],
                        ] as [string, string][] : []),
                      ].map(([k, v]) => (
                        <TableRow key={k} sx={{ "&:last-child td": { borderBottom: 0 } }}>
                          <TableCell sx={{ pl: 0, py: 0.25 }}><Typography variant="body2" color="text.secondary">{k}</Typography></TableCell>
                          <TableCell sx={{ pr: 0, py: 0.25 }} align="right"><Typography variant="body2">{v}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>

              {/* 异常/元素面板 */}
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>{t("arknights.abnormalElement")}</Typography>
                <Divider sx={{ mb: 1 }} />
                <TableContainer sx={{ overflowX: 'auto' }}>
                  <Table size="small" sx={{ maxWidth: 500 }}>
                    <TableBody>
                      {[
                        [t("arknights.burnDamage"), "1.0x", "0"],
                        [t("arknights.decayDamage"), "1.0x", "0"],
                      ].map(([type, mult, extra]) => (
                        <TableRow key={type}>
                          <TableCell sx={{ pl: 0, py: 0.25 }}><Typography variant="body2" color="text.secondary">{type}</Typography></TableCell>
                          <TableCell sx={{ py: 0.25 }}><Typography variant="body2">{mult}</Typography></TableCell>
                          <TableCell sx={{ pr: 0, py: 0.25 }} align="right"><Typography variant="body2">{extra}</Typography></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
