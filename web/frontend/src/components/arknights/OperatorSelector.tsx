import { useMemo, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Autocomplete,
  TextField,
  Box,
  Typography,
  Chip,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
} from "@mui/material";
import type { OperatorIndexEntry } from "../../api/arknights";

const STAR_OPTIONS = [6, 5, 4, 3, 2, 1] as const;
const ALL_STARS = new Set<number>(STAR_OPTIONS);

interface OperatorSelectorProps {
  operatorIndex: OperatorIndexEntry[];
  selectedOperator: string | null;
  onSelect: (name: string) => void;
  skillLevel: number;
  onSkillLevelChange: (level: number) => void;
  skillMultiplier: number;
  onSkillMultiplierChange: (mult: number) => void;
}

function starLabel(star: number): string {
  return `${"★".repeat(star)}${"☆".repeat(Math.max(0, 6 - star))}`;
}

export default function OperatorSelector({
  operatorIndex,
  selectedOperator,
  onSelect,
  skillLevel,
  onSkillLevelChange,
  skillMultiplier,
  onSkillMultiplierChange,
}: OperatorSelectorProps) {
  const { t } = useTranslation();
  const [starFilter, setStarFilter] = useState<Set<number>>(() => new Set(ALL_STARS));
  const [professionFilter, setProfessionFilter] = useState("");
  const [branchFilter, setBranchFilter] = useState("");

  const professions = useMemo(() => {
    const set = new Set<string>();
    for (const op of operatorIndex) {
      if (op.职业) set.add(op.职业);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, "zh"));
  }, [operatorIndex]);

  const branches = useMemo(() => {
    const set = new Set<string>();
    for (const op of operatorIndex) {
      if (professionFilter && op.职业 !== professionFilter) continue;
      if (op.分支) set.add(op.分支);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, "zh"));
  }, [operatorIndex, professionFilter]);

  const allStarsOn = starFilter.size === STAR_OPTIONS.length;

  const filteredIndex = useMemo(() => {
    return operatorIndex.filter((op) => {
      if (!allStarsOn && !starFilter.has(op.星级)) return false;
      if (professionFilter && op.职业 !== professionFilter) return false;
      if (branchFilter && op.分支 !== branchFilter) return false;
      return true;
    });
  }, [operatorIndex, starFilter, professionFilter, branchFilter, allStarsOn]);

  const filteredNames = useMemo(
    () => filteredIndex.map((op) => op.名称),
    [filteredIndex],
  );

  const indexByName = useMemo(() => {
    const m = new Map<string, OperatorIndexEntry>();
    for (const op of operatorIndex) m.set(op.名称, op);
    return m;
  }, [operatorIndex]);

  useEffect(() => {
    if (branchFilter && !branches.includes(branchFilter)) {
      setBranchFilter("");
    }
  }, [branches, branchFilter]);

  useEffect(() => {
    if (selectedOperator && !filteredNames.includes(selectedOperator)) {
      onSelect("");
    }
  }, [filteredNames, selectedOperator, onSelect]);

  const toggleStar = (star: number) => {
    setStarFilter((prev) => {
      const next = new Set(prev);
      if (next.has(star)) next.delete(star);
      else next.add(star);
      return next;
    });
  };

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom color="text.secondary">
        {t('operatorSelector.searchPlaceholder')}
      </Typography>

      <Stack spacing={1.5} sx={{ mb: 2 }}>
        <Box>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
            {t('common.type', '星级')}
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
            <Chip
              label={t('common.all')}
              size="small"
              variant={allStarsOn ? "filled" : "outlined"}
              color={allStarsOn ? "primary" : "default"}
              onClick={() => setStarFilter(new Set(ALL_STARS))}
              sx={{ height: 26 }}
            />
            {STAR_OPTIONS.map((star) => (
              <Chip
                key={star}
                label={starLabel(star)}
                size="small"
                variant={starFilter.has(star) ? "filled" : "outlined"}
                color={starFilter.has(star) ? "primary" : "default"}
                onClick={() => toggleStar(star)}
                sx={{ height: 26 }}
              />
            ))}
          </Box>
        </Box>

        <FormControl fullWidth size="small">
          <InputLabel>{t('arknights.profession')}</InputLabel>
          <Select
            value={professionFilter}
            label={t('arknights.profession')}
            onChange={(e) => {
              setProfessionFilter(e.target.value);
              setBranchFilter("");
            }}
          >
            <MenuItem value="">{t('common.all')}</MenuItem>
            {professions.map((p) => (
              <MenuItem key={p} value={p}>{p}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth size="small">
          <InputLabel>{t('arknights.branch')}</InputLabel>
          <Select
            value={branchFilter}
            label={t('arknights.branch')}
            onChange={(e) => setBranchFilter(e.target.value)}
            disabled={branches.length === 0}
          >
            <MenuItem value="">{t('common.all')}</MenuItem>
            {branches.map((b) => (
              <MenuItem key={b} value={b}>{b}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Typography variant="caption" color="text.secondary">
          {`${t('arknights.operator')} ${filteredIndex.length} / ${operatorIndex.length}`}
        </Typography>
      </Stack>

      <Typography variant="subtitle2" gutterBottom color="text.secondary">
        {t('arknights.pageTitle')}
      </Typography>
      <Autocomplete
        options={filteredNames}
        value={selectedOperator && filteredNames.includes(selectedOperator) ? selectedOperator : null}
        onChange={(_e, v) => { if (v) onSelect(v); }}
        noOptionsText={filteredIndex.length === 0 ? t('operatorSelector.searchPlaceholder') : t('common.noData')}
        renderOption={(props, name) => {
          const op = indexByName.get(name);
          const { key, ...rest } = props;
          return (
            <li key={key} {...rest}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "100%" }}>
                <Typography variant="body2" sx={{ flex: 1 }}>{name}</Typography>
                {op && (
                  <Box sx={{ display: "flex", gap: 0.5, flexShrink: 0 }}>
                    <Chip label={`${op.星级}★`} size="small" sx={{ height: 20, fontSize: 11 }} />
                    <Chip label={op.职业} size="small" variant="outlined" sx={{ height: 20, fontSize: 11 }} />
                    <Chip label={op.分支} size="small" variant="outlined" sx={{ height: 20, fontSize: 11 }} />
                  </Box>
                )}
              </Box>
            </li>
          );
        }}
        renderInput={(params) => (
          <TextField {...params} size="small" placeholder={t('operatorSelector.searchPlaceholder')} />
        )}
        sx={{ mb: 2 }}
      />

      {selectedOperator && (
        <>
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            {t('arknights.skillLevel')}（{t('arknights.skillLevel')} 1-7, 8-10 = {t('arknights.specializationLevel', { n: 1 })}-{t('arknights.specializationLevel', { n: 3 })}）
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
              {t('compute.level')} {skillLevel}
            </Typography>
            <Slider
              size="small"
              min={1}
              max={10}
              step={1}
              value={skillLevel}
              onChange={(_e, v) => onSkillLevelChange(v as number)}
              valueLabelDisplay="auto"
              marks={[
                { value: 1, label: "1" },
                { value: 7, label: "7" },
                { value: 8, label: t('arknights.specializationLevel', { n: 1 }) },
                { value: 10, label: t('arknights.specializationLevel', { n: 3 }) },
              ]}
              sx={{ flex: 1 }}
            />
          </Box>

          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 2 }}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((lv) => (
              <Chip
                key={lv}
                label={lv <= 7 ? `${t('compute.level')} ${lv}` : t('arknights.specializationLevel', { n: lv - 7 })}
                size="small"
                variant={skillLevel === lv ? "filled" : "outlined"}
                color={skillLevel === lv ? "primary" : "default"}
                onClick={() => onSkillLevelChange(lv)}
                sx={{ height: 24, cursor: "pointer" }}
              />
            ))}
          </Box>

          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            {t('operatorSelector.skillMultiplier')}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
              {skillMultiplier.toFixed(1)}x
            </Typography>
            <Slider
              size="small"
              min={0.1}
              max={5.0}
              step={0.1}
              value={skillMultiplier}
              onChange={(_e, v) => onSkillMultiplierChange(v as number)}
              valueLabelDisplay="auto"
              marks={[
                { value: 1.0, label: "1.0" },
                { value: 2.0, label: "2.0" },
                { value: 3.0, label: "3.0" },
              ]}
              sx={{ flex: 1 }}
            />
          </Box>
        </>
      )}
    </Box>
  );
}
