import { useState } from "react";
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  List, ListItemButton, ListItemText, Box, Typography, Divider,
} from "@mui/material";

interface HelpSection {
  id: string;
  title: string;
  content: React.ReactNode;
}

const HELP_SECTIONS: HelpSection[] = [
  {
    id: "overview",
    title: "概述",
    content: (
      <Box>
        <Typography variant="body2" paragraph>
          终末地伤害计算器 Web 版，用于计算角色在不同配装下的伤害数值。
          支持单技能伤害计算、乘区快照查看、全量搜索最佳配装等功能。
        </Typography>
        <Typography variant="body2" component="div">
          <strong>基本流程：</strong>
          <ol>
            <li>选择角色和武器</li>
            <li>设置等级、信赖、技能等级等参数</li>
            <li>调整敌方参数（防御、抗性、失衡）</li>
            <li>点击「计算」查看伤害结果</li>
            <li>前往高级页进行全量搜索或更详细配置</li>
          </ol>
        </Typography>
      </Box>
    ),
  },
  {
    id: "calc-page",
    title: "计算页",
    content: (
      <Box>
        <Typography variant="body2" paragraph>
          计算页是主操作界面，分为左栏参数区和右栏结果区。
        </Typography>
        <Typography variant="body2" component="div">
          <strong>左栏（参数设置）：</strong>
          <ul>
            <li>角色/武器选择器 — 按类型/星级/名称选择</li>
            <li>等级滑块 — 角色和武器分别 1-90 级调节</li>
            <li>技能等级 — 展开后可设置战技/连携技/终结技等级</li>
            <li>武器技能 — 展开后可设置武器普通/特殊技能等级</li>
            <li>角色属性面板 — 显示四维和基础攻击力，含信赖滑块</li>
            <li>敌方参数 — 防御力、属性抗性、失衡易伤系数</li>
            <li>计算模式选择 — 单段伤害 / 乘区快照</li>
            <li>搜索范围 — 武器候选范围和装备范围设置</li>
          </ul>
          <strong>右栏（结果展示）：</strong>
          <ul>
            <li>乘区表 — 15 个乘区的详细数据</li>
            <li>总伤面板 — 各技能段级伤害明细和加权总伤</li>
            <li>乘区占比图 — 各乘区对最终伤害的贡献比例</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
  {
    id: "advanced-page",
    title: "高级页",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <strong>左列（工具与控制）：</strong>
          <ul>
            <li>工具与分享 — 预设配置的导入/导出</li>
            <li>Buff微调 — 手动调整各乘区数值</li>
            <li>方案对比 — 多组角色+武器组合的伤害对比</li>
            <li>截图识装 — 上传截图自动识别角色/武器</li>
            <li>固定配装 — 锁定特定装备部位</li>
            <li>多技能次数 — 设置各技能段触发次数</li>
            <li>暴击与异常 — 暴击率/暴伤微调和异常状态矩阵</li>
          </ul>
          <strong>右列（搜索）：</strong>
          <ul>
            <li>搜索设置 — 结果条数、并行线程数</li>
            <li>全量搜索 — 遍历所有配装组合找出最优解</li>
            <li>支持搜索历史和计算历史回顾</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
  {
    id: "search",
    title: "搜索功能",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <strong>搜索模式：</strong>
          <ul>
            <li>单技能遍历 — 快速预览单技能各装备组合</li>
            <li>多技能遍历 — 按手动次数加权计算多技能总伤</li>
            <li>全量搜索前 N 条 — 遍历所有组合返回最优 N 组</li>
          </ul>
          <strong>参数设置：</strong>
          <ul>
            <li>武器候选范围 — 当前武器/同类型同星级/同类型全部</li>
            <li>装备范围 — 全部/仅套装/仅散件</li>
            <li>固定配装 — 锁定 0-4 个部位减少搜索空间</li>
          </ul>
          <strong>提示：</strong>
          <ul>
            <li>搜索组合数较多时请耐心等待</li>
            <li>可先使用「快速预览」缩小范围再全量搜索</li>
          </ul>
        </Typography>
      </Box>
    ),
  },
  {
    id: "faq",
    title: "常见问题",
    content: (
      <Box>
        <Typography variant="body2" component="div">
          <strong>Q: 修改参数后结果没有变化？</strong>
          <br />
          A: 请点击「计算」按钮重新计算，部分参数变更不会自动触发计算。
        </Typography>
        <Divider sx={{ my: 1 }} />
        <Typography variant="body2" component="div">
          <strong>Q: 全量搜索要等多久？</strong>
          <br />
          A: 取决于装备组合总数，通常 30 秒到数分钟不等。
          可通过缩小搜索范围、固定配装等方式减少等待时间。
        </Typography>
        <Divider sx={{ my: 1 }} />
        <Typography variant="body2" component="div">
          <strong>Q: 数据来源是什么？</strong>
          <br />
          A: 游戏数据来自 BWIKI 社区。如有数据错误请报告。
        </Typography>
        <Divider sx={{ my: 1 }} />
        <Typography variant="body2" component="div">
          <strong>Q: 计算结果和游戏内一致吗？</strong>
          <br />
          A: 计算器尽力还原游戏公式，但可能存在四舍五入或未覆盖的机制差异。
        </Typography>
      </Box>
    ),
  },
];

interface HelpDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function HelpDialog({ open, onClose }: HelpDialogProps) {
  const [activeId, setActiveId] = useState(HELP_SECTIONS[0].id);

  const activeSection = HELP_SECTIONS.find((s) => s.id === activeId) ?? HELP_SECTIONS[0];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>使用说明</DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: "flex", gap: 2, minHeight: 360, flexDirection: { xs: "column", sm: "row" } }}>
          <List dense sx={{ width: { xs: "100%", sm: 180 }, flexShrink: 0, borderRight: { xs: 0, sm: 1 }, borderColor: "divider", pt: 0 }}>
            {HELP_SECTIONS.map((section) => (
              <ListItemButton
                key={section.id}
                selected={activeId === section.id}
                onClick={() => setActiveId(section.id)}
                sx={{ borderRadius: 1, mb: 0.5 }}
              >
                <ListItemText
                  primary={section.title}
                  primaryTypographyProps={{ variant: "body2" }}
                />
              </ListItemButton>
            ))}
          </List>
          <Box sx={{ flex: 1, overflow: "auto", maxHeight: 400 }}>
            {activeSection.content}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}
