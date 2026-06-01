import { useCallback, useEffect, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { fetchProfileRows } from "../../api/dataProfiles";
import { getEntity, getProfile } from "../../constants/dataProfileConfig";

interface Props {
  profileId: string;
}

/** 多游戏数据浏览 */
export default function ProfileDataBrowser({ profileId }: Props) {
  const profile = getProfile(profileId);
  const [entityKey, setEntityKey] = useState(profile?.entities[0]?.key ?? "");
  const entity = getEntity(profileId, entityKey);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);

  const loadData = useCallback(async () => {
    if (!entityKey) return;
    try {
      setRows(await fetchProfileRows(profileId, entityKey));
    } catch {
      setRows([]);
    }
  }, [profileId, entityKey]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    setEntityKey(profile?.entities[0]?.key ?? "");
  }, [profileId, profile]);

  const columns = entity?.columns ?? [];

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, mb: 2, alignItems: "center" }}>
        {profile && profile.entities.length > 1 && (
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>实体类型</InputLabel>
            <Select
              value={entityKey}
              label="实体类型"
              onChange={(e: SelectChangeEvent) => setEntityKey(e.target.value)}
            >
              {profile.entities.map((e) => (
                <MenuItem key={e.key} value={e.key}>
                  {e.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
        <Button variant="outlined" size="small" onClick={loadData}>
          刷新
        </Button>
        <Typography variant="body2" color="text.secondary">
          共 {rows.length} 条
        </Typography>
      </Box>

      <TableContainer sx={{ maxHeight: 500 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col}>{col}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, idx) => (
              <TableRow key={idx}>
                {columns.map((col) => (
                  <TableCell key={col}>{String(row[col] ?? "--")}</TableCell>
                ))}
              </TableRow>
            ))}
            {rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length || 1} align="center">
                  <Typography color="text.secondary">暂无数据</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
