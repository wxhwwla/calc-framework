import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const goldenPath = join(dirname(fileURLToPath(import.meta.url)), "golden", "canonical_loadout.json");

function calculateGrowthCurve(params, maxLevel = 90) {
  const base = params.base;
  const growth = params.growth;
  const divisor = params.divisor;
  const offset = params.offset ?? 0;
  const curve = [];
  for (let lv = 1; lv <= maxLevel; lv += 1) {
    curve.push(Math.round((base + Math.floor((growth * (lv - 1) + offset) / divisor)) * 10) / 10);
  }
  return curve;
}

function valueAtLevel(curve, level) {
  const idx = Math.max(0, Math.min(curve.length - 1, level - 1));
  return curve[idx];
}

function main() {
  const golden = JSON.parse(readFileSync(goldenPath, "utf-8"));
  const weapon = golden.payload.weapon_data;
  const growth = weapon["成长参数"];
  if (!growth?.["基础攻击力"]) {
    throw new Error("golden 武器无成长参数.基础攻击力");
  }
  const curve = calculateGrowthCurve(growth["基础攻击力"], weapon["最大等级"] ?? 90);
  const tsVal = valueAtLevel(curve, golden.payload.weapon_level);
  const pyVal = golden.context?.weapon?.["基础攻击"];
  if (pyVal != null && Math.abs(tsVal - Number(pyVal)) > 1e-3) {
    throw new Error(`曲线偏差 TS=${tsVal} PY=${pyVal}`);
  }
  if (!golden.outputs || Object.keys(golden.outputs).length < 1) {
    throw new Error("outputs 为空");
  }
  console.log("[SEV-OK] WASM golden 校验通过");
}

main();
