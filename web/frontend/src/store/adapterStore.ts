import { create } from "zustand";
import type { AdapterInfo } from "../api/compute";
import { fetchAdapters } from "../api/compute";

interface AdapterStoreState {
  adapters: AdapterInfo[];
  loading: boolean;
  load: () => Promise<void>;
}

export const useAdapterStore = create<AdapterStoreState>((set) => ({
  adapters: [],
  loading: false,
  load: async () => {
    set({ loading: true });
    try {
      const adapters = await fetchAdapters();
      set({ adapters, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
