import { useState, useEffect } from 'react';
import {
  Box, Stepper, Step, StepLabel, Typography, Card, CardContent,
  Button, TextField, Chip, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Table, TableBody, TableCell, TableContainer, TableRow, Paper,
  Accordion, AccordionSummary, AccordionDetails, IconButton,
  Select, MenuItem, Checkbox, useMediaQuery, useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { fetchTemplates, fetchTemplateDetail, generateAdapter, type TemplateInfo, type TemplateDetail } from '../api/generator';
import AIFormulaDialog from './AIFormulaDialog';
import type { AIFormulaResponse } from '../api/generator';

interface VarRow { name: string; type: string; source: string; default: number; description: string; }
interface StepRow { id: string; op: string; lhs: string; rhs: string; expr: string; label: string; cond: string; true_val: string; false_val: string; }
interface OutRow { name: string; node: string; label: string; is_primary: boolean; }

export default function GeneratorPage() {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const STEPS = [t('generator.steps.selectTemplate'), t('generator.steps.fillGameInfo'), t('generator.steps.previewGenerate'), t('generator.steps.exportStep')];

  const [activeStep, setActiveStep] = useState(0);
  const [templates, setTemplates] = useState<Record<string, TemplateInfo>>({});
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templateDetail, setTemplateDetail] = useState<TemplateDetail | null>(null);
  const [gameName, setGameName] = useState('');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<{ files: Record<string, string>; file_count: number } | null>(null);
  const [error, setError] = useState('');
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiResult, setAiResult] = useState<AIFormulaResponse | null>(null);
  const [openFileDialog, setOpenFileDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState('');
  const [showManualForm, setShowManualForm] = useState(false);

  // 可编辑的变量/步骤/输出
  const [editableVars, setEditableVars] = useState<VarRow[]>([]);
  const [editableSteps, setEditableSteps] = useState<StepRow[]>([]);
  const [editableOutputs, setEditableOutputs] = useState<OutRow[]>([]);

  useEffect(() => {
    fetchTemplates()
      .then(setTemplates)
      .catch(e => setError(t('generator.loadTemplatesFailed') + ': ' + e.message));
  }, [t]);

  const handleSelectTemplate = async (id: string) => {
    setSelectedTemplate(id);
    setAiResult(null);
    setEditableVars([]);
    setEditableSteps([]);
    setEditableOutputs([]);
    try {
      const detail = await fetchTemplateDetail(id);
      setTemplateDetail(detail);
    } catch (e: any) {
      setError(t('generator.loadTemplateDetailFailed') + ': ' + e.message);
    }
  };

  const handleGenerate = async () => {
    if (!selectedTemplate || !gameName) return;
    setGenerating(true);
    setError('');
    setActiveStep(2);
    try {
      // 使用可编辑数据（如果有 AI 结果则用 AI 的；如果有手动编辑的则用编辑过的）
      const vars = editableVars.length > 0 ? editableVars : (aiResult?.variables || []);
      const steps = editableSteps.length > 0 ? editableSteps : (aiResult?.formula_steps || []);
      const outs = editableOutputs.length > 0 ? editableOutputs : (aiResult?.outputs || []);

      const res = await generateAdapter({
        template_id: selectedTemplate,
        game_name: gameName,
        variables: vars,
        formula_steps: steps,
        outputs: outs,
      });
      setResult(res);
      setActiveStep(3);
    } catch (e: any) {
      setError(t('generator.generateFailed') + ': ' + e.message);
      setActiveStep(1);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadAll = () => {
    if (!result) return;
    for (const [name, content] of Object.entries(result.files)) {
      const blob = new Blob([content], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name.replace('/', '_');
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  /** 编辑变量 */
  const updateVar = (i: number, field: keyof VarRow, value: any) => {
    setEditableVars(prev => prev.map((r, idx) => idx === i ? { ...r, [field]: value } : r));
  };
  const removeVar = (i: number) => setEditableVars(prev => prev.filter((_, idx) => idx !== i));
  const addVar = () => setEditableVars(prev => [...prev, { name: '', type: 'number', source: 'input', default: 0, description: '' }]);

  /** 编辑步骤 */
  const updateStep = (i: number, field: keyof StepRow, value: any) => {
    setEditableSteps(prev => prev.map((r, idx) => idx === i ? { ...r, [field]: value } : r));
  };
  const removeStep = (i: number) => setEditableSteps(prev => prev.filter((_, idx) => idx !== i));
  const addStep = () => setEditableSteps(prev => [...prev, { id: '', op: 'multiply', lhs: '', rhs: '', expr: '', label: '', cond: '', true_val: '', false_val: '' }]);

  /** 编辑输出 */
  const updateOut = (i: number, field: keyof OutRow, value: any) => {
    setEditableOutputs(prev => prev.map((r, idx) => idx === i ? { ...r, [field]: value } : r));
  };
  const removeOut = (i: number) => setEditableOutputs(prev => prev.filter((_, idx) => idx !== i));
  const addOut = () => setEditableOutputs(prev => [...prev, { name: '', node: '', label: '', is_primary: false }]);

  /** AI 结果应用 */
  const handleAiApply = (data: AIFormulaResponse) => {
    setAiResult(data);
    setEditableVars(data.variables.map(v => ({
      name: v.name || '', type: v.type || 'number', source: v.source || 'input',
      default: v.default ?? 0, description: v.description || '',
    })));
    setEditableSteps(data.formula_steps.map(s => ({
      id: s.id || '', op: s.op || 'multiply', lhs: s.lhs || '', rhs: s.rhs || '',
      expr: s.expr || '', label: s.label || '', cond: s.cond || '',
      true_val: s.true_val || s.true_val || '', false_val: s.false_val || s.false_val || '',
    })));
    setEditableOutputs(data.outputs.map(o => ({
      name: o.name || '', node: o.node || '', label: o.label || '',
      is_primary: o.is_primary ?? false,
    })));
    setShowManualForm(true);
  };

  const hasEditData = editableVars.length > 0 || editableSteps.length > 0 || editableOutputs.length > 0;

  /** 渲染可编辑变量表 */
  const renderVarEditor = () => (
    <Box>
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 1, overflowX: 'auto' }}>
        <Table size="small">
          <TableBody>
            {editableVars.map((v, i) => (
              <TableRow key={i}>
                <TableCell sx={{ p: 0.5, minWidth: 100 }}>
                  <TextField size="small" variant="standard" value={v.name}
                    onChange={e => updateVar(i, 'name', e.target.value)} placeholder={t("generator.varPlaceholder")} />
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 80 }}>
                  <Select size="small" value={v.type} onChange={e => updateVar(i, 'type', e.target.value)}
                    variant="standard" sx={{ fontSize: 13 }}>
                    <MenuItem value="number">number</MenuItem>
                    <MenuItem value="boolean">boolean</MenuItem>
                  </Select>
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 80 }}>
                  <Select size="small" value={v.source} onChange={e => updateVar(i, 'source', e.target.value)}
                    variant="standard" sx={{ fontSize: 13 }}>
                    <MenuItem value="input">input</MenuItem>
                    <MenuItem value="constant">constant</MenuItem>
                    <MenuItem value="computed">computed</MenuItem>
                  </Select>
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 60 }}>
                  <TextField size="small" variant="standard" type="number" value={v.default}
                    onChange={e => updateVar(i, 'default', parseFloat(e.target.value) || 0)} />
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 120 }}>
                  <TextField size="small" variant="standard" value={v.description}
                    onChange={e => updateVar(i, 'description', e.target.value)} placeholder={t("generator.descPlaceholder")} />
                </TableCell>
                <TableCell sx={{ p: 0.5, width: 40 }}>
                  <IconButton size="small" onClick={() => removeVar(i)}><DeleteIcon fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Button size="small" startIcon={<AddIcon />} onClick={addVar}>{t("generator.addVar")}</Button>
    </Box>
  );

  /** 渲染可编辑步骤表 */
  const renderStepEditor = () => (
    <Box>
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 1, overflowX: 'auto' }}>
        <Table size="small">
          <TableBody>
            {editableSteps.map((s, i) => (
              <TableRow key={i}>
                <TableCell sx={{ p: 0.5, minWidth: 60 }}>
                  <TextField size="small" variant="standard" value={s.label}
                    onChange={e => updateStep(i, 'label', e.target.value)} placeholder={t("generator.stepLabel")} />
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 90 }}>
                  <Select size="small" value={s.op} onChange={e => updateStep(i, 'op', e.target.value)}
                    variant="standard" sx={{ fontSize: 13 }}>
                    <MenuItem value="add">+ (add)</MenuItem>
                    <MenuItem value="subtract">- (subtract)</MenuItem>
                    <MenuItem value="multiply">× (multiply)</MenuItem>
                    <MenuItem value="divide">÷ (divide)</MenuItem>
                    <MenuItem value="cond">if (cond)</MenuItem>
                    <MenuItem value="expr">{`${t("dag.nodeTypes.expr")} (expr)`}</MenuItem>
                  </Select>
                </TableCell>
                {s.op === 'cond' ? (
                  <>
                    <TableCell sx={{ p: 0.5, minWidth: 100 }}>
                      <TextField size="small" variant="standard" value={s.cond}
                        onChange={e => updateStep(i, 'cond', e.target.value)} placeholder={t("generator.stepOpCondition")} />
                    </TableCell>
                    <TableCell sx={{ p: 0.5, minWidth: 80 }}>
                      <TextField size="small" variant="standard" value={s.true_val}
                        onChange={e => updateStep(i, 'true_val', e.target.value)} placeholder={t("generator.stepOpTrue")} />
                    </TableCell>
                    <TableCell sx={{ p: 0.5, minWidth: 80 }}>
                      <TextField size="small" variant="standard" value={s.false_val}
                        onChange={e => updateStep(i, 'false_val', e.target.value)} placeholder={t("generator.stepOpFalse")} />
                    </TableCell>
                  </>
                ) : s.op === 'expr' ? (
                  <TableCell sx={{ p: 0.5, minWidth: 200 }}>
                    <TextField size="small" variant="standard" value={s.expr}
                      onChange={e => updateStep(i, 'expr', e.target.value)} placeholder={t("generator.stepOpExpr")} fullWidth />
                  </TableCell>
                ) : (
                  <>
                    <TableCell sx={{ p: 0.5, minWidth: 100 }}>
                      <TextField size="small" variant="standard" value={s.lhs}
                        onChange={e => updateStep(i, 'lhs', e.target.value)} placeholder={t("generator.stepOpLhs")} />
                    </TableCell>
                    <TableCell sx={{ p: 0.5, minWidth: 100 }}>
                      <TextField size="small" variant="standard" value={s.rhs}
                        onChange={e => updateStep(i, 'rhs', e.target.value)} placeholder={t("generator.stepOpRhs")} />
                    </TableCell>
                  </>
                )}
                <TableCell sx={{ p: 0.5, width: 40 }}>
                  <IconButton size="small" onClick={() => removeStep(i)}><DeleteIcon fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Button size="small" startIcon={<AddIcon />} onClick={addStep}>{t("generator.addStep")}</Button>
    </Box>
  );

  /** 渲染可编辑输出表 */
  const renderOutEditor = () => (
    <Box>
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 1, overflowX: 'auto' }}>
        <Table size="small">
          <TableBody>
            {editableOutputs.map((o, i) => (
              <TableRow key={i}>
                <TableCell sx={{ p: 0.5, minWidth: 100 }}>
                  <TextField size="small" variant="standard" value={o.name}
                    onChange={e => updateOut(i, 'name', e.target.value)} placeholder={t("generator.outPlaceholder")} />
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 80 }}>
                  <TextField size="small" variant="standard" value={o.node}
                    onChange={e => updateOut(i, 'node', e.target.value)} placeholder={t("generator.outNode")} />
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 100 }}>
                  <TextField size="small" variant="standard" value={o.label}
                    onChange={e => updateOut(i, 'label', e.target.value)} placeholder={t("generator.outDisplayName")} />
                </TableCell>
                <TableCell sx={{ p: 0.5, minWidth: 60 }}>
                  <Checkbox checked={o.is_primary}
                    onChange={e => updateOut(i, 'is_primary', e.target.checked)} size="small" />
                </TableCell>
                <TableCell sx={{ p: 0.5, width: 40 }}>
                  <IconButton size="small" onClick={() => removeOut(i)}><DeleteIcon fontSize="small" /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Button size="small" startIcon={<AddIcon />} onClick={addOut}>{t("generator.addOut")}</Button>
    </Box>
  );

  return (
    <Box sx={{ p: isMobile ? 2 : 3, maxWidth: 1000, mx: 'auto' }}>
      <Typography variant={isMobile ? 'h5' : 'h4'} gutterBottom>{t("generator.title")}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t("generator.description")}
      </Typography>

      <Stepper activeStep={activeStep} alternativeLabel={isMobile} sx={{ mb: 4 }}>
        {STEPS.map(label => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
      </Stepper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Step 0: 选择模板 */}
      {activeStep === 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>{t("generator.selectTemplateHeading")}</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))', gap: 2 }}>
            {Object.entries(templates).map(([id, info]) => (
              <Card
                key={id}
                sx={{
                  cursor: 'pointer',
                  border: selectedTemplate === id ? '2px solid' : '1px solid',
                  borderColor: selectedTemplate === id ? 'primary.main' : 'divider',
                }}
                onClick={() => handleSelectTemplate(id)}
              >
                <CardContent>
                  <Typography variant="h6">{info.name}</Typography>
                  <Typography variant="body2" color="text.secondary">{info.description}</Typography>
                  <Chip label={id} size="small" sx={{ mt: 1 }} />
                  {templateDetail?.dag_preview && selectedTemplate === id && (
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      DAG: {t("dag.editor.nodesCount", { n: templateDetail.dag_preview.nodes })}, {t("generator.outputs", { n: templateDetail.dag_preview.outputs })}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            ))}
          </Box>
          <Box sx={{ mt: 3 }}>
            <Button variant="contained" disabled={!selectedTemplate} onClick={() => setActiveStep(1)} sx={{ py: isMobile ? 1.5 : undefined }}>
              {t("generator.nextStep")}
            </Button>
          </Box>
        </Box>
      )}

      {/* Step 1: 填写游戏信息 */}
      {activeStep === 1 && (
        <Box>
          <Typography variant="h6" gutterBottom>{t("generator.fillGameInfoHeading")}</Typography>
          <TextField
            fullWidth
            label={t("generator.gameName")}
            value={gameName}
            onChange={e => setGameName(e.target.value)}
            sx={{ mb: 2, maxWidth: 400 }}
            helperText={t("generator.gameNameHelper")}
          />
          {templateDetail && (
            <Alert severity="info" sx={{ mb: 2 }}>
              {t("generator.selectedTemplate")}: {templateDetail.meta?.name as string}。
              {templateDetail.dag_preview && ` DAG: ${templateDetail.dag_preview.nodes} ${t("dag.editor.nodesCount", { n: templateDetail.dag_preview.nodes })}`}
            </Alert>
          )}

          {/* AI 按钮 */}
          <Box sx={{ mb: 2 }}>
            <Button variant="outlined" onClick={() => setAiDialogOpen(true)} sx={{ py: isMobile ? 1.5 : undefined }}>
              {t("generator.aiParseFormula")}
            </Button>
            {aiResult && (
              <Chip
                label={t("generator.aiParsedLabel", { vars: aiResult.variables.length, steps: aiResult.formula_steps.length })}
                color="success" size="small" sx={{ ml: 1 }}
                onDelete={() => { setAiResult(null); setEditableVars([]); setEditableSteps([]); setEditableOutputs([]); setShowManualForm(false); }}
              />
            )}
          </Box>

          {/* 可编辑数据表（AI 解析后或手动展开） */}
          {(hasEditData || showManualForm) && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>{t("generator.customData")}</Typography>
              <Accordion defaultExpanded={editableVars.length > 0}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="body2">{t("generator.variables", { n: editableVars.length })}</Typography>
                </AccordionSummary>
                <AccordionDetails>{renderVarEditor()}</AccordionDetails>
              </Accordion>
              <Accordion defaultExpanded={editableSteps.length > 0}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="body2">{t("generator.formulaSteps", { n: editableSteps.length })}</Typography>
                </AccordionSummary>
                <AccordionDetails>{renderStepEditor()}</AccordionDetails>
              </Accordion>
              <Accordion defaultExpanded={editableOutputs.length > 0}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="body2">{t("generator.outputs", { n: editableOutputs.length })}</Typography>
                </AccordionSummary>
                <AccordionDetails>{renderOutEditor()}</AccordionDetails>
              </Accordion>
            </Box>
          )}

          {/* 无 AI 时显示手动录入入口 */}
          {!hasEditData && !aiResult && (
            <Box sx={{ mb: 2 }}>
              <Button size="small" onClick={() => setShowManualForm(true)} disabled={showManualForm}>
                {t("generator.manualEntry")}
              </Button>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button variant="outlined" onClick={() => setActiveStep(0)} sx={{ py: isMobile ? 1.5 : undefined, flex: isMobile ? '1 1 auto' : undefined }}>{t("generator.prevStep")}</Button>
            <Button variant="contained" disabled={!gameName || generating} onClick={handleGenerate} sx={{ py: isMobile ? 1.5 : undefined, flex: isMobile ? '1 1 auto' : undefined }}>
              {generating ? t("generator.generating") : t("generator.generateCalc")}
            </Button>
          </Box>
        </Box>
      )}

      {/* Step 2: 生成中 */}
      {activeStep === 2 && (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>{t("generator.generatingInProgress")}</Typography>
        </Box>
      )}

      {/* Step 3: 导出 */}
      {activeStep === 3 && result && (
        <Box>
          <Alert severity="success" sx={{ mb: 2 }}>
            {t("generator.generateSuccess", { n: result.file_count })}
          </Alert>

          <TableContainer component={Paper} sx={{ mb: 2, overflowX: 'auto' }}>
            <Table>
              <TableBody>
                {Object.entries(result.files).map(([name, content]) => (
                  <TableRow key={name} hover sx={{ cursor: 'pointer' }}
                    onClick={() => { setSelectedFile(name); setOpenFileDialog(true); }}>
                    <TableCell>{name}</TableCell>
                    <TableCell align="right">{t("generator.chars", { n: content.length })}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Button variant="contained" onClick={handleDownloadAll} sx={{ py: isMobile ? 1.5 : undefined }}>
            {t("generator.downloadAll")}
          </Button>
        </Box>
      )}

      {/* 文件内容预览对话框 */}
      <Dialog open={openFileDialog} onClose={() => setOpenFileDialog(false)} maxWidth="md" fullWidth fullScreen={isMobile}>
        <DialogTitle>{selectedFile}</DialogTitle>
        <DialogContent>
          <pre style={{ fontSize: 12, overflow: 'auto', maxHeight: 500 }}>
            {selectedFile && result?.files[selectedFile]}
          </pre>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenFileDialog(false)}>{t("common.close")}</Button>
        </DialogActions>
      </Dialog>

      {/* AI 公式解析对话框 */}
      <AIFormulaDialog
        open={aiDialogOpen}
        onClose={() => setAiDialogOpen(false)}
        templateId={selectedTemplate}
        onApply={handleAiApply}
      />
    </Box>
  );
}
