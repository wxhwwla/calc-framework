import { getDagWorkerPool } from "./workerPool";
import type { DAGEvalResult, DAGGraphRaw } from "./types";

/** 在 Web Worker 池中求值 DAG，避免阻塞主线程。 */
export function evaluateGraphInWorker(
  graph: DAGGraphRaw,
  context: Record<string, unknown>,
): Promise<DAGEvalResult> {
  return getDagWorkerPool().evaluate(graph, context);
}
