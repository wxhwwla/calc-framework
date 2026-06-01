import { useState } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  List, ListItemButton, ListItemText, Box, Typography,
} from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";

interface HelpEntry {
  id: string;
  title: string;
  content: React.ReactNode;
}

const HELP_ENTRIES: HelpEntry[] = [
  {
    id: "process",
    title: "① 制造计算器完整流程",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <p><b>从零制造游戏计算器的 7 步流程：</b></p>
          <ol>
            <li><b>数据准备</b> — BWIKI 爬虫 / 手动录入 / OCR 识别 → characters.json / weapons.json</li>
            <li><b>设计计算逻辑</b> — DAG 图编辑器 → xxx_full.dag.json</li>
            <li><b>声明属性 Schema</b> — attr_schema.json + meta.json</li>
            <li><b>设计 UI 布局</b> — 配置包设计器 → layout.json</li>
            <li><b>验证测试</b> — CalcPackViewer 加载适配包，核对数值</li>
            <li><b>打包分发</b> — 导出 .calcpack / PyInstaller 单 exe</li>
            <li><b>终端用户使用</b> — 桌面版 / Web 版 / 启动器</li>
          </ol>
          <p>详见 <code>docs/制造游戏计算器完整流程.md</code>。</p>
        </Typography>
      </Box>
    ),
  },
  {
    id: "endfield",
    title: "② 终末地计算器",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <p><b>计算页控件：</b></p>
          <ul>
            <li>角色选择器 — 按职业/类型搜索角色，四级联动选择</li>
            <li>武器选择器 — 按类型筛选，当前角色可用武器自动过滤</li>
            <li>等级滑块 — 角色/武器 1-90 级调节</li>
            <li>技能等级滑块 — 战技/连携技/终结技 1-10 级</li>
            <li>潜能选择器 — Chip 按钮组快速切换 0-5</li>
            <li>信赖滑块 — 0-200% 调节信赖值</li>
            <li>敌方防御滑块 — 0-2000 调节敌方防御力</li>
            <li>敌方抗性滑块 — 0-100% 调节属性抗性</li>
            <li>计算按钮 — 确认选择后触发 DAG 求值</li>
            <li>总伤面板 — 各技能段伤害和加权总伤</li>
            <li>乘区占比图 — ECharts 饼图/柱图</li>
          </ul>
          <p><b>高级页控件：</b></p>
          <ul>
            <li>全量搜索 — 遍历所有配装组合，按前 N 条结果排序</li>
            <li>固定配装 — 锁定 0-4 件装备，其余遍历</li>
            <li>暴击/异常微调 — 手动覆盖暴击率和异常命中</li>
            <li>手动 Buff — 临时添加增益效果</li>
            <li>多技能次数 — 设置每段技能触发次数</li>
            <li>方案对比 — 多组角色+武器组合对比</li>
            <li>截图识装 — 上传截图自动识别</li>
            <li>预设导入/导出 — JSON 格式配装配置</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
  {
    id: "arknights",
    title: "③ 明日方舟计算器",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <ul>
            <li>干员选择器 — 搜索并选择干员</li>
            <li>技能选择器 — 普攻/技能1/技能2/技能3</li>
            <li>技能信息卡片 — 显示名称、SP 消耗、初始 SP、持续时间、描述</li>
            <li>技能等级滑块 — 1-10 级，自动解析技能倍率</li>
            <li>倍率输入框 — 自动填充解析值，可手动覆盖</li>
            <li>连发数输入框 — 技能段数，自动从描述解析</li>
            <li>条件触发复选框 — 开启后使用条件倍率</li>
            <li>治疗标记 Chip — 由解析器自动判定</li>
            <li>敌方防御/抗性滑块 — 调节敌方属性</li>
            <li>攻击%+/伤害%+ 输入框 — 额外百分比加成</li>
            <li>物理/法术/真伤卡片 — 三类伤害独立显示</li>
            <li>乘区明细表 — 按板块显示中间计算值</li>
            <li>异常伤害面板 — 异常类型选择 + 倍率 + 结果</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
  {
    id: "dag-editor",
    title: "④ DAG 图编辑器",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <p><b>三栏布局：</b>节点面板（左） | 画布（中） | 属性面板（右）</p>
          <p><b>9 种节点类型：</b></p>
          <ul>
            <li><b>const</b> (青) — 固定数值输出，编辑 value 字段</li>
            <li><b>var</b> (蓝) — 从 DataContext 读取属性，编辑 path 字段</li>
            <li><b>user_input</b> (绿) — 运行时用户输入，可设置默认/最小/最大/步长</li>
            <li><b>unary</b> (灰) — 一元运算：neg/abs/floor/sqrt/ln/sin/cos 等</li>
            <li><b>binary</b> (红棕) — 二元运算：+/-/*/^/mod/min/max</li>
            <li><b>condition</b> (橙) — 条件选择，Port0=条件，Port1=真值，Port2=假值</li>
            <li><b>call</b> (紫) — 调用子图，双击可编辑子图内容</li>
            <li><b>output</b> (橙) — 标记计算结果为输出</li>
            <li><b>expr</b> (粉) — 表达式字符串求值</li>
          </ul>
          <p><b>工具栏按钮：</b>新建 / 打开 / 保存 / 导入包 / 删除 / 适配 / 重置 / 运算 / 清除</p>
          <p><b>画布操作：</b>左键拖拽节点、中键平移、滚轮缩放、从端口拖拽创建连线</p>
        </Typography>
      </Box>
    ),
  },
  {
    id: "designer",
    title: "⑤ 数据设计器",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <p><b>公式反推页签：</b></p>
          <ul>
            <li>公式类型选择器 — 线性/指数/分段/带阈值</li>
            <li>数据输入表格 — 输入等级和数值对应关系</li>
            <li>[反推] 按钮 — 自动拟合并显示参数</li>
            <li>结果显示区 — 公式类型 + 拟合参数 + 误差评估</li>
          </ul>
          <p><b>数据编辑/浏览页签：</b></p>
          <ul>
            <li>类型选择器 — 角色/武器/装备</li>
            <li>实体搜索 — 按名称搜索</li>
            <li>字段编辑器 — 树形 JSON 编辑</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
  {
    id: "pack-designer",
    title: "⑥ 配置包设计器",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <p><b>数据录入页签：</b>角色/武器/装备 三 Tab，字段表单编辑，[保存] 按钮</p>
          <p><b>布局编辑页签：</b>变量池拖拽到 Section 画布，[+Section] [-Section] 按钮</p>
          <p><b>主题与导出页签：</b></p>
          <ul>
            <li>字体选择器 — 字体族/字号/粗细</li>
            <li>颜色拾取器 — 主色/背景色/文字色/成功/警告/错误色</li>
            <li>间距设置 — 内边距/区块间距</li>
            <li>[预览主题] 按钮</li>
            <li>[导出 .calcpack] 按钮 — 打包为 ZIP 文件</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
  {
    id: "hub",
    title: "⑦ 配置包市场",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <ul>
            <li>搜索框 — 按名称/描述搜索适配包</li>
            <li>排序选择器 — 按下载量/评分/更新时间排序</li>
            <li>适配包卡片 — 名称 + 评分 + 下载量 + 版本 + 描述</li>
            <li>[安装] 按钮 — 下载并安装</li>
            <li>[上传] 按钮 — 发布自己的适配包</li>
            <li>分页导航 — 浏览更多</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
];

export default function GlobalHelpDialog() {
  const [open, setOpen] = useState(false);
  const [activeId, setActiveId] = useState(HELP_ENTRIES[0].id);

  const activeEntry = HELP_ENTRIES.find((e) => e.id === activeId) ?? HELP_ENTRIES[0];

  return (
    <>
      <Button
        color="inherit"
        startIcon={<HelpOutlineIcon />}
        onClick={() => setOpen(true)}
        sx={{ ml: 0.5, textTransform: "none" }}
        title="使用说明"
      >
        帮助
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          使用说明
          <Typography variant="caption" sx={{ ml: 2, color: "text.secondary" }}>
            详见 docs/制造游戏计算器完整流程.md
          </Typography>
        </DialogTitle>
        <DialogContent dividers sx={{ display: "flex", gap: 2, minHeight: 400 }}>
          <List sx={{ width: 220, flexShrink: 0 }}>
            {HELP_ENTRIES.map((entry) => (
              <ListItemButton
                key={entry.id}
                selected={activeId === entry.id}
                onClick={() => setActiveId(entry.id)}
              >
                <ListItemText
                  primary={entry.title}
                  primaryTypographyProps={{ variant: "body2" }}
                />
              </ListItemButton>
            ))}
          </List>
          <Box sx={{ flex: 1, overflow: "auto" }}>
            {activeEntry.content}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>关闭</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
