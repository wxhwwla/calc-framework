import { create } from "zustand";
import { listAdapters, type AdapterInfo } from "../api/adapters";

interface PackDesignerState {
  adapters: AdapterInfo[];
  adapterId: string;
  adaptersLoaded: boolean;
  layoutDraft: Record<string, unknown> | null;
  loadAdapters: () => Promise<void>;
  setAdapterId: (id: string) => void;
  setLayoutDraft: (layout: Record<string, unknown> | null) => void;
}

export const usePackDesignerStore = create<PackDesignerState>((set, get) => ({
  adapters: [],
  adapterId: "endfield",
  adaptersLoaded: false,
  layoutDraft: null,
  loadAdapters: async () => {
    if (get().adaptersLoaded) return;
    try {
      const list = await listAdapters();
      set({
        adapters: list,
        adaptersLoaded: true,
        adapterId: list.some((a) => a.id === "endfield")
          ? "endfield"
          : list[0]?.id ?? "endfield",
      });
    } catch {
      set({ adaptersLoaded: true });
    }
  },
  setAdapterId: (id) => set({ adapterId: id, layoutDraft: null }),
  setLayoutDraft: (layout) => set({ layoutDraft: layout }),
}));
