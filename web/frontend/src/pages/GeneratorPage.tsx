import { useState, useEffect } from 'react';
import {
  Box, Stepper, Step, StepLabel, Typography, Card, CardContent,
  Button, TextField, Chip, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Table, TableBody, TableCell, TableContainer, TableRow, Paper,
} from '@mui/material';
import { fetchTemplates, fetchTemplateDetail, generateAdapter, type TemplateInfo, type TemplateDetail } from '../api/generator';
import AIFormulaDialog from './AIFormulaDialog';
import type { AIFormulaResponse } from '../api/generator';

const STEPS = ['选择模板', '填写游戏信息', '预览与生成', '导出'];

export default function GeneratorPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [templates, setTemplates] = useState<Record<string, TemplateInfo>>({});
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templateDetail, setTemplateDetail] = useState<TemplateDetail | null>(null);
  const [gameName, setGameName] = useState('');
  const [, setGenerating] = useState(false);
  const [result, setResult] = useState<{ files: Record<string, string>; file_count: number } | null>(null);
  const [error, setError] = useState('');
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiResult, setAiResult] = useState<AIFormulaResponse | null>(null);
  const [openFileDialog, setOpenFileDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState('');

  useEffect(() => {
    fetchTemplates()
      .then(setTemplates)
      .catch(e => setError('加载模板失败: ' + e.message));
  }, []);

  const handleSelectTemplate = async (id: string) => {
    setSelectedTemplate(id);
    try {
      const detail = await fetchTemplateDetail(id);
      setTemplateDetail(detail);
    } catch (e: any) {
      setError('加载模板详情失败: ' + e.message);
    }
  };

  const handleGenerate = async () => {
    if (!selectedTemplate || !gameName) return;
    setGenerating(true);
    setError('');
    try {
      const res = await generateAdapter({
        template_id: selectedTemplate,
        game_name: gameName,
        variables: aiResult?.variables || [],
        formula_steps: aiResult?.formula_steps || [],
        outputs: aiResult?.outputs || [],
      });
      setResult(res);
      setActiveStep(3);
    } catch (e: any) {
      setError('生成失败: ' + e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadAll = () => {
    if (!result) return;
    // 把多个文件逐个下载
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

  return (
    <Box sx={{ p: 3, maxWidth: 1000, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>AI 计算器生成器</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        选择模板，填写游戏信息，AI 自动生成计算器适配包。
      </Typography>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {STEPS.map(label => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
      </Stepper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Step 0: 选择模板 */}
      {activeStep === 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>选择一个品类模板</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 2 }}>
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
                      DAG: {templateDetail.dag_preview.nodes} 节点, {templateDetail.dag_preview.outputs} 输出
                    </Typography>
                  )}
                </CardContent>
              </Card>
            ))}
          </Box>
          <Box sx={{ mt: 3 }}>
            <Button variant="contained" disabled={!selectedTemplate} onClick={() => setActiveStep(1)}>
              下一步
            </Button>
          </Box>
        </Box>
      )}

      {/* Step 1: 填写游戏信息 */}
      {activeStep === 1 && (
        <Box>
          <Typography variant="h6" gutterBottom>填写游戏信息</Typography>
          <TextField
            fullWidth
            label="游戏名称"
            value={gameName}
            onChange={e => setGameName(e.target.value)}
            sx={{ mb: 2, maxWidth: 400 }}
            helperText="输入你的游戏名称，将用于命名计算器"
          />
          {templateDetail && (
            <Alert severity="info" sx={{ mb: 2 }}>
              已选择模板: {templateDetail.meta?.name as string}。
              {templateDetail.dag_preview && ` DAG: ${templateDetail.dag_preview.nodes} 个节点, ${templateDetail.dag_preview.outputs} 个输出。`}
            </Alert>
          )}
          {templateDetail && (
            <Box sx={{ mb: 2 }}>
              <Button variant="outlined" onClick={() => setAiDialogOpen(true)}>
                AI 辅助解析公式
              </Button>
              {aiResult && (
                <Typography variant="caption" display="block" sx={{ mt: 1, color: 'success.main' }}>
                  ✅ AI 已解析: {aiResult.variables.length} 个变量, {aiResult.formula_steps.length} 个步骤, {aiResult.outputs.length} 个输出
                </Typography>
              )}
            </Box>
          )}
          <Box>
            <Button variant="outlined" onClick={() => setActiveStep(0)} sx={{ mr: 1 }}>上一步</Button>
            <Button variant="contained" disabled={!gameName} onClick={handleGenerate}>
              生成计算器
            </Button>
          </Box>
        </Box>
      )}

      {/* Step 2: 生成中 */}
      {activeStep === 2 && (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>正在生成计算器文件...</Typography>
        </Box>
      )}

      {/* Step 3: 导出 */}
      {activeStep === 3 && result && (
        <Box>
          <Alert severity="success" sx={{ mb: 2 }}>
            生成成功！共 {result.file_count} 个文件。
          </Alert>

          <TableContainer component={Paper} sx={{ mb: 2 }}>
            <Table>
              <TableBody>
                {Object.entries(result.files).map(([name, content]) => (
                  <TableRow key={name} hover sx={{ cursor: 'pointer' }}
                    onClick={() => { setSelectedFile(name); setOpenFileDialog(true); }}>
                    <TableCell>{name}</TableCell>
                    <TableCell align="right">{content.length} 字符</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Button variant="contained" onClick={handleDownloadAll}>
            下载全部文件
          </Button>
        </Box>
      )}

      {/* 文件内容预览对话框 */}
      <Dialog open={openFileDialog} onClose={() => setOpenFileDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedFile}</DialogTitle>
        <DialogContent>
          <pre style={{ fontSize: 12, overflow: 'auto', maxHeight: 500 }}>
            {selectedFile && result?.files[selectedFile]}
          </pre>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenFileDialog(false)}>关闭</Button>
        </DialogActions>
      </Dialog>

      {/* AI 公式解析对话框 */}
      <AIFormulaDialog
        open={aiDialogOpen}
        onClose={() => setAiDialogOpen(false)}
        templateId={selectedTemplate}
        onApply={(data) => {
          setAiResult(data);
        }}
      />
    </Box>
  );
}
