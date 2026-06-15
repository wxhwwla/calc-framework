/// <reference lib="webworker" />
import { evaluateGraph } from "./evaluate";
import type { DAGGraphRaw } from "./types";

export interface WorkerEvalRequest {
  id: number;
  graph: DAGGraphRaw;
  context: Record<string, unknown>;
}

export interface WorkerEvalResponse {
  id: number;
  ok: boolean;
  result?: ReturnType<typeof evaluateGraph>;
  error?: string;
}

self.onmessage = (event: MessageEvent<WorkerEvalRequest>) => {
  const { id, graph, context } = event.data;
  try {
    const result = evaluateGraph(graph, context);
    const response: WorkerEvalResponse = { id, ok: true, result };
    self.postMessage(response);
  } catch (err) {
    const response: WorkerEvalResponse = { id, ok: false, error: String(err) };
    self.postMessage(response);
  }
};
