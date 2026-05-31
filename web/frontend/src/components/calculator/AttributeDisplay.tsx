import { Box, Paper, Typography, Table, TableBody, TableCell, TableRow, Chip, TableContainer, Divider } from "@mui/material";

interface AttributeDisplayProps {
  characterData: Record<string, unknown> | null;
  weaponData: Record<string, unknown> | null;
}

const SKILL_INFO: { label: string; rateField: string; dmgTypeField: string }[] = [
  { label: "战技", rateField: "战技倍率", dmgTypeField: "战技段伤害类型" },
  { label: "连携技", rateField: "连携技倍率", dmgTypeField: "连携技段伤害类型" },
  { label: "终结技", rateField: "终结技倍率", dmgTypeField: "终结技段伤害类型" },
];

function getAttrAtLevel90(data: Record<string, unknown> | null, attrName: string): number | string {
  if (!data) return "--";
  const arr = data[attrName];
  if (Array.isArray(arr)) {
    const idx = Math.min(89, arr.length - 1);
    const val = arr[idx];
    return typeof val === "number" ? val : String(val);
  }
  const val = data[attrName];
  return val !== undefined ? String(val) : "--";
}

function renderSkillDamageTypes(charData: Record<string, unknown>) {
  const rows: { skill: string; segments: string[] }[] = [];

  for (const info of SKILL_INFO) {
    const dmgTypes = charData[info.dmgTypeField];
    if (!Array.isArray(dmgTypes) || dmgTypes.length === 0) continue;

    const segments: string[] = dmgTypes.map((t: unknown, i: number) => {
      const label = typeof t === "string" ? t : "物理";
      return `第${i + 1}段 · ${label}`;
    });
    rows.push({ skill: info.label, segments });
  }

  if (rows.length === 0) return null;

  return (
    <Box>
      <Divider sx={{ my: 1 }} />
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
        技能伤害类型
      </Typography>
      {rows.map((row) => (
        <Typography key={row.skill} variant="body2" sx={{ fontSize: "0.75rem", lineHeight: 1.6 }}>
          {row.skill}: {row.segments.join(" | ")}
        </Typography>
      ))}
    </Box>
  );
}

function formatCurveRange(curve: unknown): string {
  if (!Array.isArray(curve) || curve.length === 0) return "";
  const nums = curve.filter((v): v is number => typeof v === "number");
  if (nums.length === 0) return "";
  return `${nums[0]} ~ ${nums[nums.length - 1]}`;
}

function renderWeaponSkills(weaponData: Record<string, unknown>) {
  const normalSkills = weaponData["normal_skills"];
  const specialSkills = weaponData["special_skills"];

  const sections: { title: string; skills: unknown[] }[] = [];
  if (Array.isArray(normalSkills) && normalSkills.length > 0) {
    sections.push({ title: "普通技能", skills: normalSkills });
  }
  if (Array.isArray(specialSkills) && specialSkills.length > 0) {
    sections.push({ title: "特殊能力", skills: specialSkills });
  }

  if (sections.length === 0) return null;

  return (
    <Box>
      <Divider sx={{ my: 1 }} />
      {sections.map((section) => (
        <Box key={section.title} sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
            {section.title}
          </Typography>
          {section.skills.map((skill: unknown, i: number) => {
            const s = skill as Record<string, unknown>;
            const effect = String(s["effect"] || "");
            const name = String(s["name"] || "");
            const curve = formatCurveRange(s["curve"]);
            const displayName = name || effect;
            return (
              <Typography
                key={i}
                variant="body2"
                sx={{ fontSize: "0.75rem", lineHeight: 1.6 }}
              >
                {displayName}
                {curve ? ` (Lv.1-9: ${curve})` : ""}
                {s["max_stack"] != null && Number(s["max_stack"]) > 1
                  ? ` · 最多${s["max_stack"]}层`
                  : ""}
              </Typography>
            );
          })}
        </Box>
      ))}
    </Box>
  );
}

export default function AttributeDisplay({ characterData, weaponData }: AttributeDisplayProps) {
  if (!characterData && !weaponData) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography color="text.secondary" variant="body2" textAlign="center">
          请先选择角色和武器
        </Typography>
      </Paper>
    );
  }

  return (
    <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
      {characterData && (
        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            角色属性
            <Chip
              label={String(characterData["类型"] || "")}
              size="small"
              variant="outlined"
              sx={{ ml: 1, height: 20 }}
            />
            <Chip
              label={`${String(characterData["星级"] || "")}★`}
              size="small"
              color="primary"
              sx={{ ml: 0.5, height: 20 }}
            />
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>名称</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {String(characterData["名称"] || "")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>主能力</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {String(characterData["主能力"] || "")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>副能力</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {String(characterData["副能力"] || "")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>力量 (Lv.90)</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel90(characterData, "力量")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>敏捷 (Lv.90)</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel90(characterData, "敏捷")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>智识 (Lv.90)</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel90(characterData, "智识")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>意志 (Lv.90)</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel90(characterData, "意志")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>基础攻击 (Lv.90)</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel90(characterData, "基础攻击力")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>信赖 (0-4级)</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    0 (暂未支持编辑)
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
          {renderSkillDamageTypes(characterData)}
        </Paper>
      )}

      {weaponData && (
        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            武器属性
            <Chip
              label={`${String(weaponData["星级"] || "")}★`}
              size="small"
              color="primary"
              sx={{ ml: 1, height: 20 }}
            />
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>名称</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {String(weaponData["名称"] || "")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>类型</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {String(weaponData["类型"] || "")}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>基础攻击 (Lv.90)</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel90(weaponData, "基础攻击力")}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
          {renderWeaponSkills(weaponData)}
        </Paper>
      )}
    </Box>
  );
}
