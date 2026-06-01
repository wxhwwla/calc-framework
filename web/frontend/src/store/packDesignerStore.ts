import { create } from "zustand";
import { listAdapters, type AdapterInfo } from "../api/adapters";

interface PackDesignerState {
  adapters: AdapterInfo[];
  adapterId: string;
  adaptersLoaded: boolean;
  loadAdapters: () => Promise<void>;
  setAdapterId: (id: string) => void;
}

export const usePackDesignerStore = create<PackDesignerState>((set, get) => ({
  adapters: [],
  adapterId: "endfield",
  adaptersLoaded: false,
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
  setAdapterId: (id) => set({ adapterId: id }),
}));
