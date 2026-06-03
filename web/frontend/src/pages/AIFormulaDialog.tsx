import { useState } from 'react';
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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [apiKey, setApiKey] = useState(() => localStorage.getItem('ai_api_key') || '');
  const [apiBase, setApiBase] = useState(() => localStorage.getItem('ai_api_base') || 'https://api.openai.com/v1');
  const [model, setModel] = useState(() => localStorage.getItem('ai_model') || 'gpt-4o-mini');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ status: string; message?: string } | null>(null);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AIFormulaResponse | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  const validateApiKey = (key: string): string | null => {
    if (!key.trim()) return '请输入 API Key';
    if (!key.trim().startsWith('sk-')) return 'API Key 似乎不正确，应以 sk- 开头（如 sk-xxxx）';
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
        localStorage.setItem('ai_api_key', apiKey);
        localStorage.setItem('ai_api_base', apiBase);
        localStorage.setItem('ai_model', model);
      }
    } catch (e: any) {
      setTestResult({ status: 'error', message: e.message });
    } finally {
      setTesting(false);
    }
  };

  const handleParse = async () => {
    if (!description.trim()) {
      setError('请输入公式描述');
      return;
    }
    const keyErr = validateApiKey(apiKey);
    if (keyErr) { setError(keyErr); return; }

    setLoading(true);
    setError('');
    setTestResult(null);
    try {
      // 保存到 localStorage
      localStorage.setItem('ai_api_key', apiKey);
      localStorage.setItem('ai_api_base', apiBase);
      localStorage.setItem('ai_model', model);

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
      <DialogTitle>AI 公式解析</DialogTitle>
      <DialogContent>
        {/* API 配置 */}
        <Accordion defaultExpanded={!apiKey} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>API 配置</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="API Key"
                type="password"
                value={apiKey}
                onChange={e => { setApiKey(e.target.value); setTestResult(null); }}
                placeholder="sk-..."
                error={!!apiKey && !apiKey.startsWith('sk-') && apiKey.length > 5}
                helperText={apiKey && !apiKey.startsWith('sk-') && apiKey.length > 5 ? '应以 sk- 开头' : 'OpenAI 兼容 API 的密钥'}
              />
              <TextField
                fullWidth
                label="API 地址"
                value={apiBase}
                onChange={e => setApiBase(e.target.value)}
                placeholder="https://api.openai.com/v1"
              />
              <TextField
                fullWidth
                label="模型"
                value={model}
                onChange={e => setModel(e.target.value)}
                placeholder="gpt-4o-mini"
                helperText="支持 GPT、Claude、Ollama、DeepSeek 等 OpenAI 兼容接口"
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
                  {testing ? '测试中...' : '测试连接'}
                </Button>
                {testResult && (
                  <Chip
                    size="small"
                    label={testResult.status === 'ok' ? '连接成功' : (testResult.message || '连接失败')}
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
          label="描述你的伤害公式"
          multiline
          rows={4}
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder={'例如：\n最终伤害 = 攻击力 × 技能倍率 × (1 + 伤害加成) × (1 - 防御/(防御+100))\n如果暴击则 × (1 + 暴击伤害)\n角色属性：攻击力、防御力、暴击率、暴击伤害\n用户输入：技能倍率、是否暴击'}
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
        {loading && <Box sx={{ textAlign: 'center', py: 3 }}><CircularProgress /><Typography>AI 正在分析公式...</Typography></Box>}

        {result && (
          <Box>
            {result.validation_warnings && result.validation_warnings.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {result.validation_warnings.map((w, i) => <div key={i}>{w}</div>)}
              </Alert>
            )}

            <Typography variant="h6" gutterBottom>AI 解析结果</Typography>

            <Typography variant="subtitle2">识别的变量 ({result.variables.length})</Typography>
            <TableContainer component={Paper} sx={{ mb: 2, maxHeight: 150, overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>名称</TableCell><TableCell>类型</TableCell><TableCell>来源</TableCell><TableCell>默认值</TableCell>
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

            <Typography variant="subtitle2">公式步骤 ({result.formula_steps.length})</Typography>
            <TableContainer component={Paper} sx={{ mb: 2, maxHeight: 150, overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>步骤</TableCell><TableCell>操作</TableCell><TableCell>左值</TableCell><TableCell>右值</TableCell>
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

            <Typography variant="subtitle2">输出 ({result.outputs.length})</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              {result.outputs.map((o, i) => (
                <Chip key={i} label={o.label} color={o.is_primary ? 'primary' : 'default'} />
              ))}
            </Box>

            {/* 展开原始响应 */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Button size="small" onClick={() => setShowRaw(!showRaw)}>
                {showRaw ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                {showRaw ? '收起' : '展开'}原始返回
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
        <Button onClick={onClose} sx={{ py: isMobile ? 1.5 : undefined }}>取消</Button>
        {result ? (
          <Button variant="contained" onClick={handleApply} sx={{ py: isMobile ? 1.5 : undefined }}>应用此结果</Button>
        ) : (
          <Button variant="contained" onClick={handleParse} disabled={loading || !description.trim()} sx={{ py: isMobile ? 1.5 : undefined }}>
            {loading ? '解析中...' : '解析公式'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
