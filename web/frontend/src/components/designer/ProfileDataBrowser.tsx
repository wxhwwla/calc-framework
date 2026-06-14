import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Autocomplete,
  Box,
  Button,
  Chip,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import PlayCircleOutlineIcon from "@mui/icons-material/PlayCircleOutline";
import type { SelectChangeEvent } from "@mui/material/Select";
import { fetchProfileRows, validateData, type ValidateResult } from "../../api/dataProfiles";
import { getEntity, getProfile } from "../../constants/dataProfileConfig";
import DagVerifyDialog from "./DagVerifyDialog";

interface Props {
  profileId: string;
}

/** 在实体字段中可做为过滤条件的字段 key */
const FILTERABLE_KEYS: readonly string[] = ["类型", "星级", "部位", "所属套组"];

/** 多游戏数据浏览 */
export default function ProfileDataBrowser({ profileId }: Props) {
  const { t } = useTranslation();
  const profile = getProfile(profileId);
  const [entityKey, setEntityKey] = useState(profile?.entities[0]?.key ?? "");
  const entity = getEntity(profileId, entityKey);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);

  // 搜索、过滤、分页状态
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, string | null>>({});
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

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

  // profileId 变化时重置实体选择
  useEffect(() => {
    setEntityKey(profile?.entities[0]?.key ?? "");
  }, [profileId, profile]);

  // 切换实体时重置搜索、过滤、分页
  useEffect(() => {
    setSearch("");
    setFilters({});
    setPage(0);
  }, [entityKey]);

  // DAG 验证对话框
  const [verifyOpen, setVerifyOpen] = useState(false);
  const [verifyName, setVerifyName] = useState("");
  const openVerify = (name: string) => {
    setVerifyName(name);
    setVerifyOpen(true);
  };

  // 展开行详情
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  // 数据校验
  const [validating, setValidating] = useState(false);
  const [validateResult, setValidateResult] = useState<ValidateResult | null>(null);
  const handleValidate = async () => {
    setValidating(true);
    setValidateResult(null);
    try {
      setValidateResult(await validateData(profileId, entityKey));
    } catch {
      setValidateResult(null);
    } finally {
      setValidating(false);
    }
  };

  const columns = entity?.columns ?? [];
  const fields = entity?.fields ?? [];

  // 判断当前实体有哪些可过滤字段
  const filterableFields = useMemo(() => {
    return fields.filter((f) => FILTERABLE_KEYS.includes(f.key));
  }, [fields]);

  // 获取某个过滤字段的可选值列表
  const getFilterOptions = useCallback(
    (fieldKey: string): string[] => {
      const field = fields.find((f) => f.key === fieldKey);
      if (field?.options && field.options.length > 0) {
        return field.options;
      }
      if (fieldKey === "星级") {
        return ["1", "2", "3", "4", "5", "6"];
      }
      // 对于无预定义选项的文本字段（如"所属套组"），从数据中提取唯一值
      const values = new Set<string>();
      rows.forEach((row) => {
        const v = row[fieldKey];
        if (v != null && v !== "") {
          values.add(String(v));
        }
      });
      return Array.from(values).sort();
    },
    [fields, rows],
  );

  // 搜索 + 过滤后的数据
  const filteredRows = useMemo(() => {
    let result = rows;

    const searchTrimmed = search.trim();
    if (searchTrimmed) {
      const searchLower = searchTrimmed.toLowerCase();
      const nameCol = columns[0];
      if (nameCol) {
        result = result.filter((row) => {
          const val = String(row[nameCol] ?? "");
          return val.toLowerCase().includes(searchLower);
        });
      }
    }

    // 按列过滤
    for (const [key, value] of Object.entries(filters)) {
      if (value) {
        result = result.filter((row) => String(row[key] ?? "") === value);
      }
    }

    return result;
  }, [rows, search, filters, columns]);

  // 分页后的数据
  const paginatedRows = useMemo(() => {
    return filteredRows.slice(
      page * rowsPerPage,
      page * rowsPerPage + rowsPerPage,
    );
  }, [filteredRows, page, rowsPerPage]);

  const handleFilterChange = (key: string, value: string | null) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const showEntitySelector = profile && profile.entities.length > 1;

  return (
    <Box>
      {/* 工具栏：实体选择、搜索、过滤、刷新 */}
      <Stack
        direction="row"
        spacing={2}
        mb={2}
        alignItems="center"
        flexWrap="wrap"
      >
        {showEntitySelector && (
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>{t("designer.dataEditorTab.entityType")}</InputLabel>
            <Select
              value={entityKey}
              label={t("designer.dataEditorTab.entityType")}
              onChange={(e: SelectChangeEvent) => {
                setEntityKey(e.target.value);
              }}
            >
              {profile!.entities.map((e) => (
                <MenuItem key={e.key} value={e.key}>
                  {e.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        <TextField
          size="small"
          placeholder={t("common.search") + "..."}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          sx={{ minWidth: 200 }}
        />

        {filterableFields.map((field) => (
          <Autocomplete
            key={field.key}
            size="small"
            options={getFilterOptions(field.key)}
            value={filters[field.key] ?? null}
            onChange={(_e, v) => handleFilterChange(field.key, v)}
            renderInput={(params) => (
              <TextField {...params} label={field.label} placeholder={t("common.all")} />
            )}
            sx={{ minWidth: 140 }}
          />
        ))}

        <Button variant="outlined" size="small" onClick={loadData}>
          {t("designer.dataBrowserTab.refresh")}
        </Button>
        <Button
          variant="outlined"
          size="small"
          color="warning"
          onClick={handleValidate}
          disabled={validating}
        >
          {validating ? "…" : t("designer.dagVerify.validateData", "校验数据")}
        </Button>
        {validateResult && (
          <Typography variant="body2" color={validateResult.errors.length === 0 ? "success.main" : "error.main"}>
            {validateResult.valid}/{validateResult.total} 通过
            {validateResult.errors.length > 0 && ` (${validateResult.errors.length} 项有问题)`}
          </Typography>
        )}
        <Typography variant="body2" color="text.secondary">
          {t("designer.dataEditorTab.countLabel", { profile: profile?.label ?? "", entity: entity?.label ?? "", count: filteredRows.length })}
        </Typography>
      </Stack>

      {/* 校验错误详情 */}
      {validateResult && validateResult.errors.length > 0 && (
        <TableContainer sx={{ mb: 2, maxHeight: 200, overflowY: "auto" }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: 80 }}>#</TableCell>
                <TableCell>{t("common.name")}</TableCell>
                <TableCell>{t("common.error")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {validateResult.errors.map((e) => (
                <TableRow key={e.index}>
                  <TableCell>{e.index}</TableCell>
                  <TableCell>{e.name}</TableCell>
                  <TableCell>
                    {e.messages.map((m, mi) => (
                      <Typography key={mi} variant="body2" color="error.main">{m}</Typography>
                    ))}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* 数据表格 */}
      <TableContainer sx={{ maxHeight: 500, overflowX: "auto" }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col}>{col}</TableCell>
              ))}
              <TableCell align="center" sx={{ width: 60 }}>
                {t("designer.dagVerify.verify", "验证")}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedRows.map((row, idx) => {
              const globalIdx = page * rowsPerPage + idx;
              const isExpanded = expandedIdx === globalIdx;
              return [
                <TableRow
                  key={idx}
                  hover
                  onClick={() => setExpandedIdx(isExpanded ? null : globalIdx)}
                  sx={{ cursor: "pointer" }}
                >
                  {columns.map((col) => (
                    <TableCell key={col}>{String(row[col] ?? "--")}</TableCell>
                  ))}
                  <TableCell align="center" onClick={(e) => e.stopPropagation()}>
                    <Tooltip title={t("designer.dagVerify.verifyTip", "跑 DAG 验证数据")}>
                      <IconButton
                        size="small"
                        onClick={() => openVerify(String(row[columns[0]] ?? ""))}
                      >
                        <PlayCircleOutlineIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>,
                isExpanded && (
                  <TableRow key={`${idx}-detail`}>
                    <TableCell colSpan={columns.length + 1} sx={{ bgcolor: "grey.50", py: 0 }}>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, py: 1 }}>
                        {Object.entries(row).map(([key, val]) => {
                          const display = Array.isArray(val)
                            ? `[${val.length} 项] ${JSON.stringify(val).slice(0, 120)}${JSON.stringify(val).length > 120 ? "..." : ""}`
                            : typeof val === "object" && val !== null
                              ? JSON.stringify(val).slice(0, 120)
                              : String(val ?? "--");
                          return (
                            <Chip
                              key={key}
                              label={`${key}: ${display}`}
                              size="small"
                              variant="outlined"
                              sx={{ maxWidth: 400, fontSize: "0.7rem" }}
                              title={JSON.stringify(val, null, 2)}
                            />
                          );
                        })}
                      </Box>
                    </TableCell>
                  </TableRow>
                ),
              ];
            })}
            {paginatedRows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length + 1} align="center">
                  <Typography color="text.secondary">{t("common.noData")}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 分页 */}
      <TablePagination
        component="div"
        count={filteredRows.length}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[10, 25, 50, 100]}
      />

      {/* DAG 验证弹窗 */}
      <DagVerifyDialog
        open={verifyOpen}
        onClose={() => setVerifyOpen(false)}
        profileId={profileId}
        entityKey={entityKey}
        entityName={verifyName}
      />
    </Box>
  );
}
