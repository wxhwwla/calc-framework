import { useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Slider,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Chip,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useArknightsStore } from "../store/arknightsStore";
import OperatorSelector from "../components/arknights/OperatorSelector";
import ArknightsAttributeDisplay from "../components/arknights/ArknightsAttributeDisplay";

export default function ArknightsComputePage() {
  const {
    operators,
    operatorLoading,
    selectedOperator,
    operatorDetail,
    detailLoading,
    computeParams,
    computeResult,
    computeLoading,
    error,
    loadOperators,
    selectOperator,
    setParam,
    runCompute,
  } = useArknightsStore();

  useEffect(() => {
    loadOperators();
  }, [loadOperators]);

  const handleSkillLevelChange = (level: number) => {
    setParam("skill_level", level);
  };

  const handleSkillMultiplierChange = (mult: number) => {
    setParam("skill_multiplier", mult);
  };

  return (
    <Box sx={{ p: 2, maxWidth: 1400, mx: "auto" }}>
      <Typography variant="h5" gutterBottom>
        明日方舟 伤害计算器
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 2 }}>
        基于全自动 DAG 计算图的物理/法术/真伤计算
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => useArknightsStore.setState({ error: null })}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            {operatorLoading ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                <CircularProgress size={24} />
              </Box>
            ) : (
              <OperatorSelector
                operators={operators}
                selectedOperator={selectedOperator}
                onSelect={selectOperator}
                skillLevel={computeParams.skill_level}
                onSkillLevelChange={handleSkillLevelChange}
                skillMultiplier={computeParams.skill_multiplier}
                onSkillMultiplierChange={handleSkillMultiplierChange}
              />
            )}
          </Paper>

          {operatorDetail && !detailLoading && (
            <Paper sx={{ p: 2, mt: 2 }}>
              <ArknightsAttributeDisplay operator={operatorDetail} />
            </Paper>
          )}
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              敌人参数
            </Typography>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  防御力 (DEF)
                </Typography>
                <Slider
                  size="small"
                  min={0}
                  max={3000}
                  step={10}
                  value={computeParams.enemy_def}
                  onChange={(_e, v) => setParam("enemy_def", v as number)}
                  valueLabelDisplay="auto"
                />
                <TextField
                  size="small"
                  type="number"
                  value={computeParams.enemy_def}
                  onChange={(e) => setParam("enemy_def", Number(e.target.value) || 0)}
                  sx={{ width: 120 }}
                />
              </Box>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  法术抗性 (RES)
                </Typography>
                <Slider
                  size="small"
                  min={0}
                  max={100}
                  step={1}
                  value={computeParams.enemy_res}
                  onChange={(_e, v) => setParam("enemy_res", v as number)}
                  valueLabelDisplay="auto"
                />
                <TextField
                  size="small"
                  type="number"
                  value={computeParams.enemy_res}
                  onChange={(e) => setParam("enemy_res", Number(e.target.value) || 0)}
                  sx={{ width: 120 }}
                />
              </Box>
            </Box>
          </Paper>

          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              额外加成
            </Typography>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  攻击力%加成
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Slider
                    size="small"
                    min={-100}
                    max={200}
                    step={5}
                    value={computeParams.atk_percent_bonus}
                    onChange={(_e, v) => setParam("atk_percent_bonus", v as number)}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(v) => `${v > 0 ? "+" : ""}${v}%`}
                    sx={{ flex: 1 }}
                  />
                  <Typography variant="caption" sx={{ minWidth: 40, textAlign: "right" }}>
                    {computeParams.atk_percent_bonus > 0 ? "+" : ""}
                    {computeParams.atk_percent_bonus}%
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  伤害倍率加成
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Slider
                    size="small"
                    min={-100}
                    max={200}
                    step={5}
                    value={computeParams.dmg_bonus}
                    onChange={(_e, v) => setParam("dmg_bonus", v as number)}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(v) => `${v > 0 ? "+" : ""}${v}%`}
                    sx={{ flex: 1 }}
                  />
                  <Typography variant="caption" sx={{ minWidth: 40, textAlign: "right" }}>
                    {computeParams.dmg_bonus > 0 ? "+" : ""}
                    {computeParams.dmg_bonus}%
                  </Typography>
                </Box>
              </Box>
            </Box>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 1 }}>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  防御穿透
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Slider
                    size="small"
                    min={0}
                    max={100}
                    step={5}
                    value={computeParams.def_penetration}
                    onChange={(_e, v) => setParam("def_penetration", v as number)}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(v) => `${v}%`}
                    sx={{ flex: 1 }}
                  />
                  <Typography variant="caption" sx={{ minWidth: 40, textAlign: "right" }}>
                    {computeParams.def_penetration}%
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ minWidth: 180, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  法抗穿透
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Slider
                    size="small"
                    min={0}
                    max={100}
                    step={5}
                    value={computeParams.res_penetration}
                    onChange={(_e, v) => setParam("res_penetration", v as number)}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(v) => `${v}%`}
                    sx={{ flex: 1 }}
                  />
                  <Typography variant="caption" sx={{ minWidth: 40, textAlign: "right" }}>
                    {computeParams.res_penetration}%
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Paper>

          <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={computeLoading ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
              onClick={runCompute}
              disabled={!selectedOperator || computeLoading}
              sx={{ minWidth: 200 }}
            >
              {computeLoading ? "计算中..." : "开始计算"}
            </Button>
          </Box>

          {computeResult && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                计算结果 — {computeResult.operator_name}
              </Typography>
              <Divider sx={{ mb: 1.5 }} />

              <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 2 }}>
                <Card variant="outlined" sx={{ flex: 1, minWidth: 160 }}>
                  <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                    <Typography variant="caption" color="text.secondary">
                      最终攻击力
                    </Typography>
                    <Typography variant="h5">
                      {Math.round(computeResult.final_atk).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
                <Card variant="outlined" sx={{ flex: 1, minWidth: 160 }}>
                  <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                    <Typography variant="caption" color="text.secondary">
                      物理伤害
                    </Typography>
                    <Typography variant="h5" color="warning.main">
                      {Math.round(computeResult.physical_damage).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
                <Card variant="outlined" sx={{ flex: 1, minWidth: 160 }}>
                  <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                    <Typography variant="caption" color="text.secondary">
                      法术伤害
                    </Typography>
                    <Typography variant="h5" color="primary.main">
                      {Math.round(computeResult.magical_damage).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
                <Card variant="outlined" sx={{ flex: 1, minWidth: 160 }}>
                  <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                    <Typography variant="caption" color="text.secondary">
                      真实伤害
                    </Typography>
                    <Typography variant="h5">
                      {Math.round(computeResult.true_damage).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>

              <Table size="small" sx={{ maxWidth: 400 }}>
                <TableBody>
                  <TableRow>
                    <TableCell sx={{ pl: 0 }}>
                      <Typography variant="body2" color="text.secondary">
                        技能倍率
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        x{computeParams.skill_multiplier.toFixed(1)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ pl: 0 }}>
                      <Typography variant="body2" color="text.secondary">
                        敌人防御力
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {computeParams.enemy_def}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ pl: 0 }}>
                      <Typography variant="body2" color="text.secondary">
                        敌人法抗
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {computeParams.enemy_res}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  {computeResult.true_damage > 0 && (
                    <TableRow>
                      <TableCell sx={{ pl: 0 }}>
                        <Typography variant="body2" color="text.secondary">
                          包含真实伤害
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Chip label="✓" size="small" color="success" />
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Paper>
          )}

          {detailLoading && (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress size={24} />
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
