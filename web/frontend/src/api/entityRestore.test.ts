import { describe, expect, it, vi } from "vitest";
import { fixedLoadoutFromPayload, historyPresetPayload, loadEntitiesForRestore } from "./entityRestore";

vi.mock("./data", () => {
  return {
    fetchCharacter: vi.fn(async (name: string) => ({ 名称: name, atk: 100 })),
    fetchWeapon: vi.fn(async (name: string) => ({ 名称: name, base_atk: 50 })),
  };
});

describe("entity restoration", () => {
  it("loads entities matching restored names", async () => {
    const [character, weapon] = await loadEntitiesForRestore("新角色", "新武器");

    expect(character).toEqual({ 名称: "新角色", atk: 100 });
    expect(weapon).toEqual({ 名称: "新武器", base_atk: 50 });
  });

  it("restores history payload and fixed equipment from transport fields", () => {
    const payload = historyPresetPayload({
      char_name: "历史角色",
      weapon_name: "历史武器",
      loadout: {
        fixed_equipment_names: { chest: "护甲", gloves: null, accessory_a: "配件A", accessory_b: null },
      },
    });

    expect(payload.char_name).toBe("历史角色");
    expect(fixedLoadoutFromPayload(payload)).toEqual({
      chest: "护甲",
      gloves: null,
      accessory_a: "配件A",
      accessory_b: null,
    });
  });
});
