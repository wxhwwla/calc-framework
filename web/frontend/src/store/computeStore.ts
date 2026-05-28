import { create } from "zustand";
import type { AdapterInfo, AdapterAttr, EvaluateResult } from "../api/compute";
import { fetchAdapters, fetchSchema, evaluate } from "../api/compute";

interface ComputeState {
  adapters: AdapterInfo[];
  selectedAdapter: string | null;
  schema: AdapterAttr[];
  paramValues: Record<string, number | boolean>;
  result: EvaluateResult | null;
  error: string | null;
  loading: boolean;

  loadAdapters: () => Promise<void>;
  selectAdapter: (name: string) => Promise<void>;
  setParam: (name: string, value: number | boolean) => void;
  runCompute: () => Promise<void>;
}

export const useComputeStore = create<ComputeState>((set, get) => ({
  adapters: [],
  selectedAdapter: null,
  schema: [],
  paramValues: {},
  result: null,
  error: null,
  loading: false,

  loadAdapters: async () => {
    try {
      const adapters = await fetchAdapters();
      set({ adapters });
    } catch (e: unknown) {
      set({ error: String(e) });
    }
  },

  selectAdapter: async (name: string) => {
    set({ selectedAdapter: name, schema: [], paramValues: {}, result: null, error: null });
    try {
      const schema = await fetchSchema(name);
      const paramValues: Record<string, number | boolean> = {};
      for (const attr of schema) {
        if (attr.source === "character" || attr.source === "user_input"|| true) {
          const key = attr.name.includes(".") ? attr.name.split(".")[1] : attr.name;
          paramValues[key] = attr.default ?? (attr.type === "bool" ? false : 0);
        }
      }
      set({ schema, paramValues });
    } catch (e: unknown) {
      set({ error: String(e) });
    }
  },

  setParam: (name: string, value: number | boolean) => {
    set((s) => ({
      paramValues: { ...s.paramValues, [name]: value },
    }));
  },

  runCompute: async () => {
    const { selectedAdapter, paramValues, schema } = get();
    if (!selectedAdapter) return;

    set({ loading: true, error: null, result: null });

    const context: Record<string, Record<string, number | boolean>> = {};

    for (const attr of schema) {
      const key = attr.name.includes(".") ? attr.name.split(".")[1] : attr.name;
      const source = attr.name.includes(".") ? attr.name.split(".")[0] : "character";
      if (!context[source]) {
        context[source] = {};
      }
      context[source][key] = paramValues[key] ?? attr.default ?? 0;
    }

    try {
      const result = await evaluate(selectedAdapter, context);
      set({ result, loading: false });
    } catch (e: unknown) {
      set({ error: String(e), loading: false });
    }
  },
}));
