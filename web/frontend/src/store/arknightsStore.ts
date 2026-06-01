import { create } from "zustand";
import type {
  ComputeRequest, ComputeResponse, OperatorIndexEntry, OperatorSummary,
} from "../api/arknights";
import { fetchOperatorCatalog, fetchOperatorDetail, computeDamage } from "../api/arknights";

interface ArknightsState {
  operatorIndex: OperatorIndexEntry[];
  operators: string[];
  operatorLoading: boolean;
  selectedOperator: string | null;
  operatorDetail: OperatorSummary | null;
  detailLoading: boolean;

  computeParams: ComputeRequest;
  computeResult: ComputeResponse | null;
  computeLoading: boolean;
  error: string | null;

  loadOperators: () => Promise<void>;
  selectOperator: (name: string) => Promise<void>;
  setParam: <K extends keyof ComputeRequest>(key: K, value: ComputeRequest[K]) => void;
  runCompute: () => Promise<void>;
}

const defaultParams: ComputeRequest = {
  operator_name: "",
  skill_multiplier: 1.0,
  skill_level: 7,
  enemy_def: 200,
  enemy_res: 50,
  atk_percent_bonus: 0,
  dmg_bonus: 0,
  def_penetration: 0,
  res_penetration: 0,
};

export const useArknightsStore = create<ArknightsState>((set, get) => ({
  operatorIndex: [],
  operators: [],
  operatorLoading: false,
  selectedOperator: null,
  operatorDetail: null,
  detailLoading: false,

  computeParams: { ...defaultParams },
  computeResult: null,
  computeLoading: false,
  error: null,

  loadOperators: async () => {
    set({ operatorLoading: true });
    try {
      const catalog = await fetchOperatorCatalog();
      set({
        operatorIndex: catalog.index,
        operators: catalog.operators,
        operatorLoading: false,
      });
    } catch (e: unknown) {
      set({ error: String(e), operatorLoading: false });
    }
  },

  selectOperator: async (name: string) => {
    if (!name) {
      set({
        selectedOperator: null,
        operatorDetail: null,
        detailLoading: false,
        computeResult: null,
        computeParams: { ...get().computeParams, operator_name: "" },
      });
      return;
    }
    set({ selectedOperator: name, detailLoading: true, computeResult: null, error: null });
    try {
      const detail = await fetchOperatorDetail(name);
      const params = { ...get().computeParams, operator_name: name };
      set({ operatorDetail: detail, computeParams: params, detailLoading: false });
    } catch (e: unknown) {
      set({ error: String(e), detailLoading: false });
    }
  },

  setParam: <K extends keyof ComputeRequest>(key: K, value: ComputeRequest[K]) => {
    set((s) => ({
      computeParams: { ...s.computeParams, [key]: value },
    }));
  },

  runCompute: async () => {
    const { computeParams } = get();
    if (!computeParams.operator_name) return;

    set({ computeLoading: true, error: null, computeResult: null });
    try {
      const result = await computeDamage(computeParams);
      set({ computeResult: result, computeLoading: false });
    } catch (e: unknown) {
      set({ error: String(e), computeLoading: false });
    }
  },
}));
