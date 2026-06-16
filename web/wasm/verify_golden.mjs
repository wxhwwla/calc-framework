import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { evaluateGraph } from "./dag_eval.mjs";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const goldenPath = join(dirname(fileURLToPath(import.meta.url)), "golden", "canonical_loadout.json");
const dagPath = join(
  repoRoot,
  "framework",
  "adapters",
  "endfield",
  "dag",
  "endfield_full.dag.json",
);

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

function assertClose(actual, expected, tol, label) {
  if (Math.abs(actual - expected) > tol) {
    throw new Error(`${label}: TS=${actual} PY=${expected}`);
  }
}

function main() {
  const golden = JSON.parse(readFileSync(goldenPath, "utf-8"));
  const dag = JSON.parse(readFileSync(dagPath, "utf-8"));

  const weapon = golden.payload.weapon_data;
  const growth = weapon["成长参数"];
  if (!growth?.["基础攻击力"]) {
    throw new Error("golden 武器无成长参数.基础攻击力");
  }
  const curve = calculateGrowthCurve(growth["基础攻击力"], weapon["最大等级"] ?? 90);
  const tsVal = valueAtLevel(curve, golden.payload.weapon_level);
  const pyVal = golden.context?.weapon?.["基础攻击"];
  if (pyVal != null) {
    assertClose(tsVal, Number(pyVal), 1e-3, "曲线偏差");
  }

  if (!golden.outputs || Object.keys(golden.outputs).length < 1) {
    throw new Error("outputs 为空");
  }

  const ctx = golden.context;
  if (!ctx) {
    throw new Error("golden 缺少 context");
  }

  const local = evaluateGraph(dag, ctx);
  let checked = 0;
  for (const [key, expected] of Object.entries(golden.outputs)) {
    if (!(key in local.outputs)) {
      throw new Error(`本地 outputs 缺少键 ${key}`);
    }
    assertClose(Number(local.outputs[key]), Number(expected), 1e-4, key);
    checked += 1;
  }

  console.log(`[SEV-OK] WASM golden 校验通过 (${checked} outputs, ${local.execution_order.length} nodes)`);
}

main();
