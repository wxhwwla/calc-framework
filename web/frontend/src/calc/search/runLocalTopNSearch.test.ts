import { beforeEach, describe, expect, it, vi } from "vitest";
import type { LoadoutResult, SearchRequest } from "../../api/search";
import { runLocalTopNSearch } from "./runLocalTopNSearch";
import * as resumeDb from "./searchResumeDb";

const history: LoadoutResult[] = [
  {
    weapon_name: "历史武器",
    chest: "历史护甲",
    gloves: "历史护手",
    accessory_a: "历史配件A",
    accessory_b: "历史配件B",
    final_damage: 12345,
  },
];

vi.mock("../dag", () => ({ loadEndfieldDag: vi.fn(async () => ({})) }));
vi.mock("./searchResumeDb", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./searchResumeDb")>();
  return {
    ...actual,
    initSearchResumeDb: vi.fn(async () => {}),
    ensureSearchRun: vi.fn(async () => {}),
    countProcessed: vi.fn(() => 1),
    isComboProcessed: vi.fn(() => true),
    markProcessedBatch: vi.fn(),
    replaceTopScores: vi.fn(),
    markRunStatus: vi.fn(),
    flushSearchResumeDb: vi.fn(async () => {}),
    loadTopScores: vi.fn(() => history),
  };
});

function params(): SearchRequest {
  return {
    char_data: { 名称: "角色" },
    char_level: 90,
    weapon_level: 90,
    trust_level: 0,
    skill_name: "战技",
    skill_type: "战技",
    skill_multiplier: 1,
    damage_type: "物理",
    current_weapon: { 名称: "武器" },
    weapon_scope_label: "当前武器",
    equipment_scope_label: "全部装备",
    fixed_equipment_names: {},
    enemy_defense: 100,
    enemy_resistance: 0,
  } as SearchRequest;
}

const catalog = {
  chest: [{ 名称: "护甲" }],
  gloves: [{ 名称: "护手" }],
  accessories: [{ 名称: "配件A" }, { 名称: "配件B" }],
};

describe("runLocalTopNSearch resume", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("restores historical TopN when every combination was already processed", async () => {
    const result = await runLocalTopNSearch(params(), {
      weapons: [{ 名称: "武器" }],
      equipmentCatalog: catalog,
      topN: 10,
    });

    expect(result.top_results).toEqual(history);
    expect(result.searched_combinations).toBe(1);
  });

  it("persists scores when cancellation happens before the next batch", async () => {
    const controller = new AbortController();
    controller.abort();

    await runLocalTopNSearch(params(), {
      weapons: [{ 名称: "武器" }],
      equipmentCatalog: catalog,
      topN: 10,
      signal: controller.signal,
    });

    expect(resumeDb.replaceTopScores).toHaveBeenCalled();
  });
});
