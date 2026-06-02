import { useCallback, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Collapse,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import DeleteIcon from "@mui/icons-material/Delete";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DownloadIcon from "@mui/icons-material/Download";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import {
  submitContributeData,
  validateContributeData,
} from "../../api/contribute";

const CLASS_OPTIONS = ["近卫", "术师", "重装", "辅助", "先锋", "突击"];
const ATTRIBUTE_OPTIONS = ["物理", "能量", "电磁", "热熔", "异裂"];
const SKILL_LABEL_OPTIONS = ["主动", "被动"];
const SKILL_TYPE_OPTIONS = ["物理", "能量", "电磁", "热熔", "异裂", "治疗", "增益", "减益"];

interface SegmentForm {
  倍率: string;
  伤害类型: string;
}

interface SkillForm {
  名称: string;
  标签: "主动" | "被动";
  百分比: boolean;
  技能类型: string;
  段: SegmentForm[];
}

interface EntityForm {
  名称: string;
  星级: number;
  类型: string;
  属性: string;
  技能: SkillForm[];
}

function emptySkill(): SkillForm {
  return { 名称: "", 标签: "主动", 百分比: true, 技能类型: "", 段: [] };
}

function emptySegment(): SegmentForm {
  return { 倍率: "", 伤害类型: "" };
}

function buildEntityJson(form: EntityForm): Record<string, unknown> {
  const skills = form.技能
    .filter((s) => s.名称.trim())
    .map((s) => ({
      名称: s.名称.trim(),
      标签: s.标签,
      百分比: s.百分比,
      ...(s.技能类型.trim() ? { 技能类型: s.技能类型.trim() } : {}),
      段: s.段
        .filter((seg) => seg.倍率.trim())
        .map((seg) => ({
          倍率: seg.倍率
            .split(",")
            .map((v) => v.trim())
            .filter((v) => v !== "")
            .map(Number),
          ...(seg.伤害类型.trim() ? { 伤害类型: seg.伤害类型.trim() } : {}),
        })),
    }));
  return {
    名称: form.名称.trim(),
    星级: form.星级,
    类型: form.类型,
    属性: form.属性,
    技能: skills,
  };
}

function validateForm(form: EntityForm): string[] {
  const errors: string[] = [];
  if (!form.名称.trim()) errors.push("名称不能为空");
  if (form.星级 < 3 || form.星级 > 6) errors.push("星级必须在 3~6 之间");
  if (!form.类型) errors.push("请选择职业");
  if (!form.属性) errors.push("请选择属性");
  const validSkills = form.技能.filter((s) => s.名称.trim());
  if (validSkills.length === 0) errors.push("至少录入一个技能");
  for (const s of validSkills) {
    const validSegments = s.段.filter((seg) => seg.倍率.trim());
    if (validSegments.length === 0) errors.push(`技能"${s.名称}"至少有一个倍率段`);
    for (const seg of validSegments) {
      const nums = seg.倍率.split(",").map((v) => v.trim()).filter(Boolean);
      if (nums.some((n) => isNaN(Number(n)) || !Number.isInteger(Number(n)))) {
        errors.push(`技能"${s.名称}"的倍率包含非整数`);
      }
    }
  }
  return errors;
}

export default function SimpleDataForm() {
  const [form, setForm] = useState<EntityForm>({
    名称: "",
    星级: 3,
    类型: "",
    属性: "",
    技能: [],
  });
  const [expandedSkills, setExpandedSkills] = useState<number[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [submitResult, setSubmitResult] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const toggleSkill = (idx: number) => {
    setExpandedSkills((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  const updateField = useCallback(
    (key: keyof EntityForm, value: unknown) => {
      setForm((prev) => ({ ...prev, [key]: value }));
      setErrors([]);
      setSubmitResult(null);
    },
    []
  );

  const updateSkill = useCallback(
    (idx: number, key: keyof SkillForm, value: unknown) => {
      setForm((prev) => {
        const skills = [...prev.技能];
        skills[idx] = { ...skills[idx], [key]: value };
        return { ...prev, 技能: skills };
      });
      setErrors([]);
      setSubmitResult(null);
    },
    []
  );

  const addSkill = useCallback(() => {
    setForm((prev) => ({
      ...prev,
      技能: [...prev.技能, emptySkill()],
    }));
  }, []);

  const removeSkill = useCallback((idx: number) => {
    setForm((prev) => ({
      ...prev,
      技能: prev.技能.filter((_, i) => i !== idx),
    }));
    setExpandedSkills((prev) =>
      prev.filter((i) => i !== idx).map((i) => (i > idx ? i - 1 : i))
    );
  }, []);

  const addSegment = useCallback((skillIdx: number) => {
    setForm((prev) => {
      const skills = [...prev.技能];
      skills[skillIdx] = {
        ...skills[skillIdx],
        段: [...skills[skillIdx].段, emptySegment()],
      };
      return { ...prev, 技能: skills };
    });
  }, []);

  const updateSegment = useCallback(
    (skillIdx: number, segIdx: number, key: keyof SegmentForm, value: string) => {
      setForm((prev) => {
        const skills = [...prev.技能];
        const segments = [...skills[skillIdx].段];
        segments[segIdx] = { ...segments[segIdx], [key]: value };
        skills[skillIdx] = { ...skills[skillIdx], 段: segments };
        return { ...prev, 技能: skills };
      });
    },
    []
  );

  const removeSegment = useCallback((skillIdx: number, segIdx: number) => {
    setForm((prev) => {
      const skills = [...prev.技能];
      skills[skillIdx] = {
        ...skills[skillIdx],
        段: skills[skillIdx].段.filter((_, i) => i !== segIdx),
      };
      return { ...prev, 技能: skills };
    });
  }, []);

  const jsonOutput = buildEntityJson(form);
  const validationErrors = validateForm(form);

  const handleValidate = async () => {
    setSubmitResult(null);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    try {
      const result = await validateContributeData(jsonOutput);
      if (result.valid) {
        setErrors([]);
        setSubmitResult("校验通过！数据格式正确。");
      } else {
        setErrors(result.errors);
      }
    } catch {
      setErrors(["校验请求失败，请检查网络连接"]);
    }
  };

  const handleSubmit = async () => {
    setSubmitResult(null);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    setSubmitting(true);
    try {
      const result = await submitContributeData(jsonOutput);
      setErrors([]);
      setSubmitResult(`提交成功！已保存为 ${result.filename}。感谢您的贡献！`);
    } catch (e: unknown) {
      setErrors([e instanceof Error ? e.message : "提交失败"]);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(jsonOutput, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${form.名称.trim() || "contribute"}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(jsonOutput, null, 2));
    setSubmitResult("JSON 已复制到剪贴板");
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        简易录入
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        按步骤填写角色信息，系统会自动生成标准格式的 JSON 数据。
      </Typography>

      {/* 基本信息 */}
      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          基本信息
        </Typography>
        <Stack spacing={2}>
          <TextField
            fullWidth
            size="small"
            label="名称"
            placeholder="如：陈千语"
            value={form.名称}
            onChange={(e) => updateField("名称", e.target.value)}
          />
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>星级</InputLabel>
              <Select
                value={String(form.星级)}
                label="星级"
                onChange={(e: SelectChangeEvent) =>
                  updateField("星级", Number(e.target.value))
                }
              >
                {[3, 4, 5, 6].map((v) => (
                  <MenuItem key={v} value={v}>
                    {"★".repeat(v)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>职业</InputLabel>
              <Select
                value={form.类型}
                label="职业"
                onChange={(e: SelectChangeEvent) =>
                  updateField("类型", e.target.value)
                }
              >
                {CLASS_OPTIONS.map((v) => (
                  <MenuItem key={v} value={v}>
                    {v}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>属性</InputLabel>
              <Select
                value={form.属性}
                label="属性"
                onChange={(e: SelectChangeEvent) =>
                  updateField("属性", e.target.value)
                }
              >
                {ATTRIBUTE_OPTIONS.map((v) => (
                  <MenuItem key={v} value={v}>
                    {v}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </Stack>
      </Paper>

      {/* 技能录入 */}
      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <Typography variant="subtitle1" fontWeight={600} sx={{ flexGrow: 1 }}>
            技能录入
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<AddCircleIcon />}
            onClick={addSkill}
          >
            添加技能
          </Button>
        </Box>

        {form.技能.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: "center" }}>
            暂无技能，点击"添加技能"开始录入
          </Typography>
        )}

        <Stack spacing={2}>
          {form.技能.map((skill, si) => {
            const isExpanded = expandedSkills.includes(si);
            return (
              <Card key={si} variant="outlined">
                <CardContent sx={{ pb: 1, "&:last-child": { pb: 1 } }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <IconButton size="small" onClick={() => toggleSkill(si)}>
                      {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                    <TextField
                      size="small"
                      placeholder="技能名称"
                      value={skill.名称}
                      onChange={(e) => updateSkill(si, "名称", e.target.value)}
                      sx={{ flexGrow: 1 }}
                    />
                    <Chip
                      label={skill.标签 === "主动" ? "主动" : "被动"}
                      color={skill.标签 === "主动" ? "primary" : "default"}
                      size="small"
                    />
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => removeSkill(si)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>

                  <Collapse in={isExpanded}>
                    <Box sx={{ mt: 2, pl: 4 }}>
                      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                          <InputLabel>标签</InputLabel>
                          <Select
                            value={skill.标签}
                            label="标签"
                            onChange={(e: SelectChangeEvent) =>
                              updateSkill(si, "标签", e.target.value as "主动" | "被动")
                            }
                          >
                            {SKILL_LABEL_OPTIONS.map((v) => (
                              <MenuItem key={v} value={v}>
                                {v}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={skill.百分比}
                              onChange={(e) =>
                                updateSkill(si, "百分比", e.target.checked)
                              }
                            />
                          }
                          label="百分比"
                        />
                        <FormControl size="small" sx={{ minWidth: 130 }}>
                          <InputLabel>技能类型</InputLabel>
                          <Select
                            value={skill.技能类型}
                            label="技能类型"
                            onChange={(e: SelectChangeEvent) =>
                              updateSkill(si, "技能类型", e.target.value)
                            }
                          >
                            <MenuItem value="">（无）</MenuItem>
                            {SKILL_TYPE_OPTIONS.map((v) => (
                              <MenuItem key={v} value={v}>
                                {v}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Stack>

                      <Typography variant="body2" fontWeight={500} sx={{ mb: 1 }}>
                        倍率段
                      </Typography>

                      {skill.段.map((seg, segIdx) => (
                        <Stack
                          key={segIdx}
                          direction="row"
                          spacing={1}
                          alignItems="center"
                          sx={{ mb: 1 }}
                        >
                          <TextField
                            size="small"
                            placeholder="如：169,186,203"
                            value={seg.倍率}
                            onChange={(e) =>
                              updateSegment(si, segIdx, "倍率", e.target.value)
                            }
                            sx={{ flexGrow: 1 }}
                          />
                          <FormControl size="small" sx={{ minWidth: 110 }}>
                            <Select
                              value={seg.伤害类型}
                              displayEmpty
                              onChange={(e: SelectChangeEvent) =>
                                updateSegment(si, segIdx, "伤害类型", e.target.value)
                              }
                            >
                              <MenuItem value="">（默认类型）</MenuItem>
                              {SKILL_TYPE_OPTIONS.map((v) => (
                                <MenuItem key={v} value={v}>
                                  {v}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => removeSegment(si, segIdx)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Stack>
                      ))}

                      <Button
                        size="small"
                        startIcon={<AddCircleIcon />}
                        onClick={() => addSegment(si)}
                        sx={{ mt: 1 }}
                      >
                        添加段
                      </Button>
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      </Paper>

      {/* 校验错误 */}
      {errors.length > 0 && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErrors([])}>
          {errors.map((e, i) => (
            <div key={i}>{e}</div>
          ))}
        </Alert>
      )}

      {submitResult && (
        <Alert
          severity={errors.length === 0 ? "success" : "warning"}
          sx={{ mb: 2 }}
          onClose={() => setSubmitResult(null)}
        >
          {submitResult}
        </Alert>
      )}

      {/* 操作按钮 */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }} flexWrap="wrap">
        <Button
          variant="outlined"
          startIcon={<ContentCopyIcon />}
          onClick={handleCopyJson}
        >
          复制 JSON
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
        >
          下载 JSON
        </Button>
        <Button
          variant="outlined"
          onClick={handleValidate}
        >
          校验数据
        </Button>
        <Button
          variant="contained"
          startIcon={<CloudUploadIcon />}
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? "提交中..." : "提交数据"}
        </Button>
      </Stack>

      {/* 预览面板 */}
      <Typography variant="subtitle2" gutterBottom>
        JSON 预览
      </Typography>
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          maxHeight: 400,
          overflow: "auto",
          bgcolor: "grey.50",
          fontFamily: "monospace",
          fontSize: 13,
          whiteSpace: "pre-wrap",
        }}
      >
        {JSON.stringify(jsonOutput, null, 2)}
      </Paper>
    </Box>
  );
}
