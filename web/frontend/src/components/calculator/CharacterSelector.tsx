import { useEffect, useState } from "react";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
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

  useEffect(() => {
    fetchCharacters().then(setCharacters).catch(() => {});
    fetchWeapons().then(setWeapons).catch(() => {});
  }, []);

  const handleCharChange = async (e: SelectChangeEvent) => {
    const name = e.target.value;
    if (charDataCache[name]) {
      onSelectCharacter(name, charDataCache[name]);
      return;
    }
    try {
      const { fetchCharacter } = await import("../../api/data");
      const data = await fetchCharacter(name);
      setCharDataCache((prev) => ({ ...prev, [name]: data }));
      onSelectCharacter(name, data);
    } catch {
      // ignore
    }
  };

  const handleWeaponChange = async (e: SelectChangeEvent) => {
    const name = e.target.value;
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
  };

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom color="text.secondary">
        角色 / 武器选择
      </Typography>

      <FormControl fullWidth size="small" sx={{ mb: 1.5 }}>
        <InputLabel>角色</InputLabel>
        <Select value={selectedChar} label="角色" onChange={handleCharChange}>
          {characters.map((c) => (
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

      <FormControl fullWidth size="small">
        <InputLabel>武器</InputLabel>
        <Select value={selectedWeapon} label="武器" onChange={handleWeaponChange}>
          {weapons.map((w) => (
            <MenuItem key={w.名称} value={w.名称}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <span>{w.名称}</span>
                <Chip label={`${w.星级}★`} size="small" color="primary" sx={{ height: 20 }} />
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
