import { Box, Paper, Typography, Table, TableBody, TableCell, TableRow, Chip, TableContainer, Divider, Slider } from "@mui/material";

interface AttributeDisplayProps {
  characterData: Record<string, unknown> | null;
  weaponData: Record<string, unknown> | null;
  charLevel: number;
  weaponLevel: number;
  trustLevel: number;
  onTrustLevelChange: (level: number) => void;
  skillLevels: Record<string, number>;
}

const SKILL_INFO: { label: string; rateField: string; dmgTypeField: string }[] = [
  { label: "战技", rateField: "战技倍率", dmgTypeField: "战技段伤害类型" },
  { label: "连携技", rateField: "连携技倍率", dmgTypeField: "连携技段伤害类型" },
  { label: "终结技", rateField: "终结技倍率", dmgTypeField: "终结技段伤害类型" },
];

function getAttrAtLevel(data: Record<string, unknown> | null, attrName: string, level: number): number | string {
  if (!data) return "--";
  const arr = data[attrName];
  if (Array.isArray(arr)) {
    const idx = Math.min(level - 1, arr.length - 1);
    const val = arr[idx];
    return typeof val === "number" ? val : String(val);
  }
  const val = data[attrName];
  return val !== undefined ? String(val) : "--";
}

function getSkillRateAtLevel(charData: Record<string, unknown>, rateField: string, skillLevel: number, segmentIndex: number = 0): string | null {
  const arr = charData[rateField];
  if (!Array.isArray(arr) || arr.length === 0) return null;
  const segIdx = Math.min(segmentIndex, arr.length - 1);
  const segment = arr[segIdx];
  if (!Array.isArray(segment) || segment.length === 0) return null;
  const lvlIdx = Math.min(skillLevel - 1, segment.length - 1);
  const val = segment[lvlIdx];
  if (val == null) return null;
  const num = Number(val);
  return Number.isInteger(num) ? `${num}%` : `${num.toFixed(1)}%`;
}

function renderSkillRateDetails(charData: Record<string, unknown>, skillLevels: Record<string, number>) {
  const rows: { skill: string; segments: string[] }[] = [];

  for (const info of SKILL_INFO) {
    const rateField = info.rateField;
    const segments = charData[rateField];
    if (!Array.isArray(segments) || segments.length === 0) continue;

    const key = info.label === "战技" ? "skill_1_level" : info.label === "连携技" ? "skill_2_level" : "skill_3_level";
    const skillLevel = (skillLevels[key] as number) || 8;

    const detailLines: string[] = [];
    for (let i = 0; i < segments.length; i++) {
      const dmgTypes = charData[info.dmgTypeField];
      const dmgType = Array.isArray(dmgTypes) && i < dmgTypes.length ? String(dmgTypes[i] || "物理") : "物理";
      const rate = getSkillRateAtLevel(charData, rateField, skillLevel, i);
      detailLines.push(`第${i + 1}段: ${rate || "--"} · ${dmgType}`);
    }
    rows.push({ skill: `${info.label} Lv.${skillLevel}`, segments: detailLines });
  }

  if (rows.length === 0) return null;

  return (
    <Box>
      <Divider sx={{ my: 1 }} />
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
        技能倍率明细
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

export default function AttributeDisplay({ characterData, weaponData, charLevel, weaponLevel, trustLevel, onTrustLevelChange, skillLevels }: AttributeDisplayProps) {
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
                  <TableCell sx={{ border: "none", pl: 0 }}>{`力量 (Lv.${charLevel})`}</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel(characterData, "力量", charLevel)}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>{`敏捷 (Lv.${charLevel})`}</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel(characterData, "敏捷", charLevel)}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>{`智识 (Lv.${charLevel})`}</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel(characterData, "智识", charLevel)}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>{`意志 (Lv.${charLevel})`}</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel(characterData, "意志", charLevel)}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>{`基础攻击 (Lv.${charLevel})`}</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel(characterData, "基础攻击力", charLevel)}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ border: "none", pl: 0 }}>信赖</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {trustLevel}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
              信赖等级
            </Typography>
            <Slider
              size="small"
              min={0}
              max={4}
              step={1}
              value={trustLevel}
              onChange={(_e, v) => onTrustLevelChange(v as number)}
              marks={[
                { value: 0, label: "0" },
                { value: 2, label: "2" },
                { value: 4, label: "4" },
              ]}
              valueLabelDisplay="auto"
            />
          </Box>

          {renderSkillRateDetails(characterData, skillLevels)}
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
                  <TableCell sx={{ border: "none", pl: 0 }}>{`基础攻击 (Lv.${weaponLevel})`}</TableCell>
                  <TableCell sx={{ border: "none", fontWeight: "bold" }}>
                    {getAttrAtLevel(weaponData, "基础攻击力", weaponLevel)}
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
