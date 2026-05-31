import { useEffect, useMemo, useState, useCallback } from "react";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
} from "@mui/material";
import { fetchCharacters, fetchWeapons } from "../../api/data";
import type { CharacterSummary, WeaponSummary } from "../../api/data";

interface CharacterSelectorProps {
  onSelectCharacter: (name: string, fullData: Record<string, unknown>) => void;
  onSelectWeapon: (name: string, fullData: Record<string, unknown>) => void;
  selectedChar: string;
  selectedWeapon: string;
}

export default function CharacterSelector({
  onSelectCharacter,
  onSelectWeapon,
  selectedChar,
  selectedWeapon,
}: CharacterSelectorProps) {
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [weapons, setWeapons] = useState<WeaponSummary[]>([]);
  const [charDataCache, setCharDataCache] = useState<Record<string, Record<string, unknown>>>({});
  const [weaponDataCache, setWeaponDataCache] = useState<Record<string, Record<string, unknown>>>({});
  const [charWeaponType, setCharWeaponType] = useState("");

  // 角色级联筛选状态
  const [charTypeFilter, setCharTypeFilter] = useState("");
  const [charStarFilter, setCharStarFilter] = useState("");

  // 武器级联筛选状态
  const [weaponStarFilter, setWeaponStarFilter] = useState("");

  useEffect(() => {
    fetchCharacters().then(setCharacters).catch(() => {});
    fetchWeapons().then(setWeapons).catch(() => {});
  }, []);

  // ── 角色级联筛选 ──────────────────────────────────────────────

  /** 可用的角色类型列表（去重排序） */
  const charTypes = useMemo(
    () => [...new Set(characters.map((c) => c.类型))].sort(),
    [characters],
  );

  /** 根据类型过滤后的角色 → 提取可用星级 */
  const charStarsByType = useMemo(() => {
    const pool = charTypeFilter
      ? characters.filter((c) => c.类型 === charTypeFilter)
      : characters;
    return [...new Set(pool.map((c) => c.星级))].sort((a, b) => b - a);
  }, [characters, charTypeFilter]);

  /** 根据类型+星级过滤后的角色名列表 */
  const filteredChars = useMemo(() => {
    let pool = characters;
    if (charTypeFilter) pool = pool.filter((c) => c.类型 === charTypeFilter);
    if (charStarFilter) pool = pool.filter((c) => c.星级 === Number(charStarFilter));
    return pool;
  }, [characters, charTypeFilter, charStarFilter]);

  // ── 武器级联筛选 ──────────────────────────────────────────────

  /** 根据角色武器类型 + 星级过滤武器 */
  const filteredWeapons = useMemo(() => {
    let pool = weapons;
    if (charWeaponType) {
      const byType = weapons.filter((w) => w.类型 === charWeaponType);
      if (byType.length > 0) pool = byType;
    }
    if (weaponStarFilter) {
      pool = pool.filter((w) => w.星级 === Number(weaponStarFilter));
    }
    return pool;
  }, [weapons, charWeaponType, weaponStarFilter]);

  /** 当前武器候选集的可用星级 */
  const weaponStars = useMemo(() => {
    const pool = charWeaponType
      ? weapons.filter((w) => w.类型 === charWeaponType)
      : weapons;
    return [...new Set(pool.map((w) => w.星级))].sort((a, b) => b - a);
  }, [weapons, charWeaponType]);

  // ── 事件处理 ──────────────────────────────────────────────────

  const handleCharChange = useCallback(async (name: string) => {
    if (!name) return;
    let data: Record<string, unknown>;
    if (charDataCache[name]) {
      data = charDataCache[name];
    } else {
      try {
        const { fetchCharacter } = await import("../../api/data");
        data = await fetchCharacter(name);
        setCharDataCache((prev) => ({ ...prev, [name]: data }));
      } catch {
        return;
      }
    }
    const weaponType = (data["武器"] as string) || "";
    setCharWeaponType(weaponType);
    setWeaponStarFilter("");
    if (weaponType && selectedWeapon) {
      const matchWeapon = weapons.find((w) => w.名称 === selectedWeapon);
      if (matchWeapon && matchWeapon.类型 !== weaponType) {
        onSelectWeapon("", {});
      }
    }
    onSelectCharacter(name, data);
  }, [charDataCache, weapons, selectedWeapon, onSelectCharacter, onSelectWeapon]);

  const handleWeaponChange = useCallback(async (name: string) => {
    if (!name) return;
    if (weaponDataCache[name]) {
      onSelectWeapon(name, weaponDataCache[name]);
      return;
    }
    try {
      const { fetchWeapon } = await import("../../api/data");
      const data = await fetchWeapon(name);
      setWeaponDataCache((prev) => ({ ...prev, [name]: data }));
      onSelectWeapon(name, data);
    } catch {
      // ignore
    }
  }, [weaponDataCache, onSelectWeapon]);

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom color="text.secondary">
        角色 / 武器选择
      </Typography>

      {/* ── 角色区域 ── */}
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
        角色
      </Typography>

      <Box sx={{ display: "flex", gap: 1, mb: 1 }}>
        <FormControl size="small" sx={{ minWidth: 100, flex: 1 }}>
          <InputLabel>类型</InputLabel>
          <Select
            value={charTypeFilter}
            label="类型"
            onChange={(e) => { setCharTypeFilter(e.target.value); setCharStarFilter(""); }}
          >
            <MenuItem value="">全部</MenuItem>
            {charTypes.map((t) => (
              <MenuItem key={t} value={t}>{t}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 80, flex: 1 }}>
          <InputLabel>星级</InputLabel>
          <Select
            value={charStarFilter}
            label="星级"
            onChange={(e) => setCharStarFilter(e.target.value)}
          >
            <MenuItem value="">全部</MenuItem>
            {charStarsByType.map((s) => (
              <MenuItem key={s} value={String(s)}>{s}★</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
        <InputLabel>名称</InputLabel>
        <Select
          value={selectedChar}
          label="名称"
          onChange={(e) => handleCharChange(e.target.value)}
        >
          {filteredChars.map((c) => (
            <MenuItem key={c.名称} value={c.名称}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <span>{c.名称}</span>
                <Chip label={c.类型} size="small" variant="outlined" sx={{ height: 20 }} />
                <Chip label={`${c.星级}★`} size="small" color="primary" sx={{ height: 20 }} />
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* ── 武器区域 ── */}
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
        武器
      </Typography>

      <Box sx={{ display: "flex", gap: 1, mb: 1 }}>
        {charWeaponType && (
          <FormControl size="small" sx={{ minWidth: 80, flex: 1 }} disabled>
            <InputLabel>类型</InputLabel>
            <Select value={charWeaponType} label="类型">
              <MenuItem value={charWeaponType}>{charWeaponType}</MenuItem>
            </Select>
          </FormControl>
        )}

        <FormControl size="small" sx={{ minWidth: 80, flex: 1 }}>
          <InputLabel>星级</InputLabel>
          <Select
            value={weaponStarFilter}
            label="星级"
            onChange={(e) => setWeaponStarFilter(e.target.value)}
          >
            <MenuItem value="">全部</MenuItem>
            {weaponStars.map((s) => (
              <MenuItem key={s} value={String(s)}>{s}★</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <FormControl fullWidth size="small">
        <InputLabel>名称</InputLabel>
        <Select
          value={selectedWeapon}
          label="名称"
          onChange={(e) => handleWeaponChange(e.target.value)}
        >
          {filteredWeapons.map((w) => (
            <MenuItem key={w.名称} value={w.名称}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <span>{w.名称}</span>
                <Chip label={w.类型} size="small" variant="outlined" sx={{ height: 20 }} />
                <Chip label={`${w.星级}★`} size="small" color="primary" sx={{ height: 20 }} />
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
