import { useCallback, useRef, useState } from "react";
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
} from "@mui/material";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import FileUploadIcon from "@mui/icons-material/FileUpload";
import { mergeEnemyParams, type EnemyParams } from "../../api/search";
import { exportDesktopPreset, type WebLoadoutPayload } from "../../api/loadout";

/** Web 旧版预设 */
interface WebPresetData {
  schema: string;
  char_name: string;
  weapon_name: string;
  char_level: number;
  weapon_level: number;
  enemy_params: Partial<EnemyParams> & Pick<EnemyParams, "enemy_defense">;
  multi_skill: {
    use_manual_multi_skill_counts: boolean;
    manual_counts: Record<string, number>;
    damage_component_mode: string;
  };
  fixed_loadout: Record<string, string | null> | null;
  note?: string;
  exported_at: string;
}

/** 桌面 / Web 共用导入类型（`endfield_loadout_preset_v2` 或 Web 旧版） */
export type PresetData = WebPresetData | Record<string, unknown>;

interface PresetDialogProps {
  open: boolean;
  onClose: () => void;
  loadoutPayload: WebLoadoutPayload | null;
  currentState: {
    charName: string;
    weaponName: string;
    charLevel: number;
    weaponLevel: number;
    enemyParams: EnemyParams;
    multiSkill: { useManualCounts: boolean; manualCounts: Record<string, number>; damageComponentMode: string };
    fixedLoadout: Record<string, string | null> | null;
  };
  onImport: (data: Record<string, unknown>) => void;
}

export default function PresetDialog({
  open,
  onClose,
  loadoutPayload,
  currentState,
  onImport,
}: PresetDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [exporting, setExporting] = useState(false);

  const handleExport = useCallback(async () => {
    if (loadoutPayload) {
      setExporting(true);
      try {
        const preset = await exportDesktopPreset(loadoutPayload);
        const blob = new Blob([JSON.stringify(preset, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `preset_${currentState.charName || "unknown"}_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (e) {
        alert(`导出失败: ${e}`);
      } finally {
        setExporting(false);
      }
      return;
    }

    const preset: WebPresetData = {
      schema: "endfield_web_preset_v2",
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
  }, [loadoutPayload, currentState]);

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
          const raw = JSON.parse(evt.target?.result as string) as Record<string, unknown>;
          const schema = String(raw.schema || "");
          if (!schema || !raw.char_name) {
            alert("无效的预设文件：缺少必要字段");
            return;
          }
          if (schema === "endfield_loadout_preset_v2") {
            onImport(raw);
          } else if (schema === "endfield_web_preset_v2") {
            const web = raw as unknown as WebPresetData;
            onImport({
              ...raw,
              enemy_params: mergeEnemyParams(web.enemy_params ?? {}),
            });
          } else {
            alert(`不支持的预设格式: ${schema}`);
            return;
          }
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
          导出为桌面同款 <code>endfield_loadout_preset_v2</code>，或导入桌面/Web 预设。
        </Typography>

        <Box sx={{ display: "flex", gap: 2, justifyContent: "center" }}>
          <Button
            variant="outlined"
            startIcon={exporting ? <CircularProgress size={16} /> : <FileDownloadIcon />}
            onClick={handleExport}
            disabled={exporting}
          >
            导出配装
          </Button>
          <Button variant="contained" startIcon={<FileUploadIcon />} onClick={handleImportClick}>
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
