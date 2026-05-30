import { Box, Paper, Typography, Table, TableBody, TableCell, TableRow, Chip, TableContainer } from "@mui/material";

interface AttributeDisplayProps {
  characterData: Record<string, unknown> | null;
  weaponData: Record<string, unknown> | null;
}

/** 从角色/武器的等级数组中取 Lv.90 的值 */
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
              </TableBody>
            </Table>
          </TableContainer>
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
        </Paper>
      )}
    </Box>
  );
}
