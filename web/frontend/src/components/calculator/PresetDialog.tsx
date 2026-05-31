import { useCallback, useRef } from "react";
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import FileUploadIcon from "@mui/icons-material/FileUpload";

interface PresetData {
  schema: string;
  char_name: string;
  weapon_name: string;
  char_level: number;
  weapon_level: number;
  enemy_params: {
    enemy_defense: number;
    enemy_resistance: number;
    ignore_resistance: number;
    imbalance_vulnerability_coeff: number;
    is_unbalanced: boolean;
  };
  multi_skill: {
    use_manual_multi_skill_counts: boolean;
    manual_counts: Record<string, number>;
    damage_component_mode: string;
  };
  fixed_loadout: Record<string, string | null> | null;
  note?: string;
  exported_at: string;
}

interface PresetDialogProps {
  open: boolean;
  onClose: () => void;
  currentState: {
    charName: string;
    weaponName: string;
    charLevel: number;
    weaponLevel: number;
    enemyParams: { enemy_defense: number; enemy_resistance: number; ignore_resistance: number; imbalance_vulnerability_coeff: number; is_unbalanced: boolean };
    multiSkill: { useManualCounts: boolean; manualCounts: Record<string, number>; damageComponentMode: string };
    fixedLoadout: Record<string, string | null> | null;
  };
  onImport: (data: PresetData) => void;
}

export type { PresetData };

export default function PresetDialog({ open, onClose, currentState, onImport }: PresetDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = useCallback(() => {
    const preset: PresetData = {
      schema: "endfield_web_preset_v1",
      char_name: currentState.charName,
      weapon_name: currentState.weaponName,
      char_level: currentState.charLevel,
      weapon_level: currentState.weaponLevel,
      enemy_params: currentState.enemyParams,
      multi_skill: {
        use_manual_multi_skill_counts: currentState.multiSkill.useManualCounts,
        manual_counts: currentState.multiSkill.manualCounts,
        damage_component_mode: currentState.multiSkill.damageComponentMode,
      },
      fixed_loadout: currentState.fixedLoadout,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(preset, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `preset_${currentState.charName || "unknown"}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [currentState]);

  const handleImportClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (evt) => {
        try {
          const data = JSON.parse(evt.target?.result as string) as PresetData;
          if (!data.schema || !data.char_name) {
            alert("无效的预设文件：缺少必要字段");
            return;
          }
          onImport(data);
          onClose();
        } catch {
          alert("无效的预设文件：JSON 解析失败");
        }
      };
      reader.readAsText(file);
      e.target.value = "";
    },
    [onImport, onClose],
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>配装预设</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          导出当前配装配置为 JSON 文件，或导入已有预设快速恢复配置。
        </Typography>

        <Box sx={{ display: "flex", gap: 2, justifyContent: "center" }}>
          <Button
            variant="outlined"
            startIcon={<FileDownloadIcon />}
            onClick={handleExport}
          >
            导出配装
          </Button>
          <Button
            variant="contained"
            startIcon={<FileUploadIcon />}
            onClick={handleImportClick}
          >
            导入配装
          </Button>
        </Box>

        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
}
