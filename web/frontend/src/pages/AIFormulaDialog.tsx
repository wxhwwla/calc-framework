import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Button, Alert, CircularProgress, Chip,
  Box, Typography, Accordion, AccordionSummary, AccordionDetails,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Collapse, useMediaQuery, useTheme,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { aiParseFormula, aiTestConnection, type AIFormulaResponse } from '../api/generator';

interface Props {
  open: boolean;
  onClose: () => void;
  templateId: string;
  onApply: (data: AIFormulaResponse) => void;
}

export default function AIFormulaDialog({ open, onClose, templateId, onApply }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [apiKey, setApiKey] = useState('');
  const [apiBase, setApiBase] = useState(() => sessionStorage.getItem('ai_api_base') || 'https://api.openai.com/v1');
  const [model, setModel] = useState(() => sessionStorage.getItem('ai_model') || 'gpt-4o-mini');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ status: string; message?: string } | null>(null);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AIFormulaResponse | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  const validateApiKey = (key: string): string | null => {
    if (!key.trim()) return t('generator.aiDialog.enterApiKey');
    if (!key.trim().startsWith('sk-')) return t('generator.aiDialog.apiKeyInvalid');
    return null;
  };

  const handleTestConnection = async () => {
    const keyErr = validateApiKey(apiKey);
    if (keyErr) { setTestResult({ status: 'error', message: keyErr }); return; }

    setTesting(true);
    setTestResult(null);
    setError('');
    try {
      const res = await aiTestConnection({
        api_key: apiKey,
        api_base: apiBase,
        model,
      });
      setTestResult(res);
      if (res.status === 'ok') {
        // 仅持久化非敏感配置
        sessionStorage.setItem('ai_api_base', apiBase);
        sessionStorage.setItem('ai_model', model);
      }
    } catch (e: any) {
      setTestResult({ status: 'error', message: e.message });
    } finally {
      setTesting(false);
    }
  };

  const handleParse = async () => {
    if (!description.trim()) {
      setError(t('generator.aiDialog.enterFormulaDesc'));
      return;
    }
    const keyErr = validateApiKey(apiKey);
    if (keyErr) { setError(keyErr); return; }

    setLoading(true);
    setError('');
    setTestResult(null);
    try {
      // 仅持久化非敏感配置（API Key 保持在内存中，刷新后需重新输入）
      sessionStorage.setItem('ai_api_base', apiBase);
      sessionStorage.setItem('ai_model', model);

      const res = await aiParseFormula({
        api_key: apiKey,
        api_base: apiBase,
        model,
        formula_description: description,
        template_id: templateId,
      });
      setResult(res);

      // 如果 AI 返回了警告，展开原始响应方便排查
      if (res.validation_warnings?.length) {
        setShowRaw(true);
      }
    } catch (e: any) {
      setError(e.message);
      // 尝试解析后端返回的 detail 字段
      try {
        const parsed = JSON.parse(e.message);
        if (parsed.detail) setError(parsed.detail);
      } catch { /* 已经是纯文本错误 */ }
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => {
    if (result) {
      onApply(result);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth fullScreen={isMobile}>
      <DialogTitle>{t('generator.aiDialog.title')}</DialogTitle>
      <DialogContent>
        {/* API 配置 */}
        <Accordion defaultExpanded={!apiKey} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>{t('generator.aiDialog.apiConfig')}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label={t('generator.aiDialog.apiKey')}
                type="password"
                value={apiKey}
                onChange={e => { setApiKey(e.target.value); setTestResult(null); }}
                placeholder="sk-..."
                error={!!apiKey && !apiKey.startsWith('sk-') && apiKey.length > 5}
                helperText={apiKey && !apiKey.startsWith('sk-') && apiKey.length > 5 ? t('generator.aiDialog.shouldStartWithSk') : t('generator.aiDialog.apiKeyHelp')}
              />
              <TextField
                fullWidth
                label={t('generator.aiDialog.apiBase')}
                value={apiBase}
                onChange={e => setApiBase(e.target.value)}
                placeholder="https://api.openai.com/v1"
              />
              <TextField
                fullWidth
                label={t('generator.aiDialog.model')}
                value={model}
                onChange={e => setModel(e.target.value)}
                placeholder="gpt-4o-mini"
                helperText={t('generator.aiDialog.modelHint')}
              />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Button
                  size={isMobile ? 'medium' : 'small'}
                  variant="outlined"
                  onClick={handleTestConnection}
                  disabled={testing || !apiKey.trim()}
                  sx={{ py: isMobile ? 1.5 : undefined }}
                >
                  {testing ? <CircularProgress size={16} sx={{ mr: 0.5 }} /> : null}
                  {testing ? t('generator.aiDialog.testing') : t('generator.aiDialog.testConnection')}
                </Button>
                {testResult && (
                  <Chip
                    size="small"
                    label={testResult.status === 'ok' ? t('generator.aiDialog.connected') : (testResult.message || t('generator.aiDialog.connectionFailed'))}
                    color={testResult.status === 'ok' ? 'success' : 'error'}
                    variant="outlined"
                  />
                )}
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* 公式输入 */}
        <TextField
          fullWidth
          label={t('generator.aiDialog.formulaDescription')}
          multiline
          rows={4}
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder={t('generator.aiDialog.formulaPlaceholder')}
          sx={{ mb: 2 }}
        />

        {/* 示例按钮 */}
        <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {['攻击力×倍率-防御', 'ATK×倍率×(1-护甲/(护甲+100))', '基础伤害×暴击分支'].map(ex => (
            <Chip key={ex} label={ex} size="small" variant="outlined"
              onClick={() => setDescription(prev => prev ? prev + '\n' + ex : ex)} />
          ))}
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

        {/* 解析结果 */}
        {loading && <Box sx={{ textAlign: 'center', py: 3 }}><CircularProgress /><Typography>{t('generator.aiDialog.analyzing')}</Typography></Box>}

        {result && (
          <Box>
            {result.validation_warnings && result.validation_warnings.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {result.validation_warnings.map((w, i) => <div key={i}>{w}</div>)}
              </Alert>
            )}

            <Typography variant="h6" gutterBottom>{t('generator.aiDialog.aiResult')}</Typography>

            <Typography variant="subtitle2">{t('generator.aiDialog.identifiedVars', { n: result.variables.length })}</Typography>
            <TableContainer component={Paper} sx={{ mb: 2, maxHeight: 150, overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('common.name')}</TableCell><TableCell>{t('common.type')}</TableCell><TableCell>{t('generator.varPlaceholder', '来源')}</TableCell><TableCell>{t('dag.nodeEdit.defaultVal')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.variables.map((v, i) => (
                    <TableRow key={i}>
                      <TableCell>{v.name}</TableCell>
                      <TableCell>{v.type}</TableCell>
                      <TableCell>{v.source}</TableCell>
                      <TableCell>{v.default}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="subtitle2">{t('generator.aiDialog.formulaStepResults', { n: result.formula_steps.length })}</Typography>
            <TableContainer component={Paper} sx={{ mb: 2, maxHeight: 150, overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('generator.stepLabel')}</TableCell><TableCell>{t('dag.nodeEdit.operator')}</TableCell><TableCell>{t('generator.stepOpLhs')}</TableCell><TableCell>{t('generator.stepOpRhs')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.formula_steps.map((s, i) => (
                    <TableRow key={i}>
                      <TableCell>{s.label}</TableCell>
                      <TableCell><Chip label={s.op} size="small" /></TableCell>
                      <TableCell>{s.lhs || s.cond || '-'}</TableCell>
                      <TableCell>{s.rhs || s.true_val || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="subtitle2">{t('generator.aiDialog.outputResults', { n: result.outputs.length })}</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              {result.outputs.map((o, i) => (
                <Chip key={i} label={o.label} color={o.is_primary ? 'primary' : 'default'} />
              ))}
            </Box>

            {/* 展开原始响应 */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Button size="small" onClick={() => setShowRaw(!showRaw)}>
                {showRaw ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                {showRaw ? t('generator.aiDialog.hideRaw') : t('generator.aiDialog.showRaw')}
              </Button>
            </Box>
            <Collapse in={showRaw}>
              <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50', maxHeight: 200, overflow: 'auto' }}>
                <pre style={{ fontSize: 11, margin: 0, whiteSpace: 'pre-wrap' }}>
                  {result.raw_response}
                </pre>
              </Paper>
            </Collapse>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ py: isMobile ? 1.5 : undefined }}>{t('common.cancel')}</Button>
        {result ? (
          <Button variant="contained" onClick={handleApply} sx={{ py: isMobile ? 1.5 : undefined }}>{t('generator.aiDialog.applyResult')}</Button>
        ) : (
          <Button variant="contained" onClick={handleParse} disabled={loading || !description.trim()} sx={{ py: isMobile ? 1.5 : undefined }}>
            {loading ? t('generator.aiDialog.parsing') : t('generator.aiDialog.parseFormula')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
