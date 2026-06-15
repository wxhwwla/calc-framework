import type { EvaluateResult } from "../api/compute";
import type { WebLoadoutPayload } from "../api/loadout";
import { getCalcBackend } from "../config/calcBackend";
import { getCalcContextMode } from "../config/calcContext";
import { buildLoadoutContext } from "./context";
import { evaluateGraphInWorker } from "./dag/evaluateInWorker";
import { loadEndfieldDag } from "./dag";

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

async function resolveContext(payload: WebLoadoutPayload): Promise<Record<string, unknown>> {
  if (getCalcContextMode() === "local") {
    return buildLoadoutContext(payload);
  }
  return fetchLoadoutContext(payload);
}

/** wasm：本地/远程 context + Worker DAG 求值；失败时返回 null 以回退 API。 */
export async function evaluateLoadoutWasm(payload: WebLoadoutPayload): Promise<EvaluateResult | null> {
  try {
    const [context, dag] = await Promise.all([resolveContext(payload), loadEndfieldDag()]);
    const result = await evaluateGraphInWorker(dag, context);
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
