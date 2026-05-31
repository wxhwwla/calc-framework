import { useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "endfield_ui_prefs";

interface UIPreferences {
  enemyPanelExpanded: boolean;
  calcMode: string;
  darkMode: boolean;
  tabIndex: number;
}

const DEFAULTS: UIPreferences = {
  enemyPanelExpanded: false,
  calcMode: "zone_snapshot",
  darkMode: false,
  tabIndex: 0,
};

function loadPrefs(): UIPreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {}
  return DEFAULTS;
}

function savePrefs(prefs: UIPreferences) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {}
}

export function useUIPreferences() {
  const [prefs, setPrefs] = useState<UIPreferences>(loadPrefs);

  useEffect(() => {
    savePrefs(prefs);
  }, [prefs]);

  const updatePref = useCallback(<K extends keyof UIPreferences>(key: K, value: UIPreferences[K]) => {
    setPrefs((prev) => ({ ...prev, [key]: value }));
  }, []);

  return { prefs, updatePref };
}
