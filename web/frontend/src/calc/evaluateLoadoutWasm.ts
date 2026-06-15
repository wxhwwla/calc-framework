import type { EvaluateResult } from "../api/compute";
import type { WebLoadoutPayload } from "../api/loadout";
import { getCalcBackend } from "../config/calcBackend";
import { evaluateGraph, loadEndfieldDag } from "./dag";

async function fetchLoadoutContext(payload: WebLoadoutPayload): Promise<Record<string, unknown>> {
  const r = await fetch("/api/compute/loadout-context", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    throw new Error(await r.text());
  }
  const data = (await r.json()) as { context: Record<string, unknown> };
  return data.context;
}

/** 4.2：服务端构建 context + 浏览器本地 DAG 求值；失败时返回 null 以回退 API。 */
export async function evaluateLoadoutWasm(payload: WebLoadoutPayload): Promise<EvaluateResult | null> {
  try {
    const [context, dag] = await Promise.all([fetchLoadoutContext(payload), loadEndfieldDag()]);
    const result = evaluateGraph(dag, context);
    return {
      outputs: result.outputs,
      node_values: result.node_values,
      execution_order: result.execution_order,
    };
  } catch {
    return null;
  }
}

export async function evaluateLoadoutWithBackend(
  payload: WebLoadoutPayload,
  apiCall: () => Promise<EvaluateResult>,
): Promise<EvaluateResult> {
  if (getCalcBackend() === "wasm") {
    const local = await evaluateLoadoutWasm(payload);
    if (local) return local;
  }
  return apiCall();
}
