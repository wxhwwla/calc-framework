import type { DAGEvalResult, DAGGraphRaw } from "./types";

interface PendingJob {
  resolve: (result: DAGEvalResult) => void;
  reject: (error: Error) => void;
}

interface QueuedTask {
  id: number;
  graph: DAGGraphRaw;
  context: Record<string, unknown>;
}

interface WorkerMessage {
  id: number;
  ok: boolean;
  result?: DAGEvalResult;
  error?: string;
}

function defaultPoolSize(): number {
  if (typeof navigator === "undefined") {
    return 2;
  }
  const cores = navigator.hardwareConcurrency || 2;
  return Math.max(1, Math.min(4, cores - 1));
}

/** 可复用 Web Worker 池，用于单配装与批量 TopN 并行求值。 */
export class DagWorkerPool {
  private readonly size: number;
  private workers: Worker[] = [];
  private idleWorkers: Worker[] = [];
  private queue: QueuedTask[] = [];
  private pending = new Map<number, PendingJob>();
  private seq = 0;

  constructor(size = defaultPoolSize()) {
    this.size = size;
  }

  private ensureWorkers(): void {
    while (this.workers.length < this.size) {
      const worker = new Worker(new URL("./dagWorker.ts", import.meta.url), { type: "module" });
      worker.onmessage = (event: MessageEvent<WorkerMessage>) => {
        this.onWorkerMessage(worker, event.data);
      };
      this.workers.push(worker);
      this.idleWorkers.push(worker);
    }
  }

  private onWorkerMessage(worker: Worker, data: WorkerMessage): void {
    const job = this.pending.get(data.id);
    if (!job) {
      return;
    }
    this.pending.delete(data.id);
    this.idleWorkers.push(worker);
    this.pump();
    if (data.ok && data.result) {
      job.resolve(data.result);
    } else {
      job.reject(new Error(data.error ?? "Worker 求值失败"));
    }
  }

  private pump(): void {
    while (this.queue.length > 0 && this.idleWorkers.length > 0) {
      const task = this.queue.shift();
      if (!task) {
        break;
      }
      const worker = this.idleWorkers.pop();
      if (!worker) {
        break;
      }
      worker.postMessage({ id: task.id, graph: task.graph, context: task.context });
    }
  }

  /** 单配装 DAG 求值。 */
  evaluate(graph: DAGGraphRaw, context: Record<string, unknown>): Promise<DAGEvalResult> {
    this.ensureWorkers();
    const id = ++this.seq;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.queue.push({ id, graph, context });
      this.pump();
    });
  }

  /** 同一 DAG、多 context 并行求值（阶段 5 TopN 搜索前置）。 */
  evaluateBatch(graph: DAGGraphRaw, contexts: Record<string, unknown>[]): Promise<DAGEvalResult[]> {
    if (contexts.length === 0) {
      return Promise.resolve([]);
    }
    return Promise.all(contexts.map((context) => this.evaluate(graph, context)));
  }

  /** 释放全部 Worker（测试或页面卸载时）。 */
  terminate(): void {
    for (const worker of this.workers) {
      worker.terminate();
    }
    this.workers = [];
    this.idleWorkers = [];
    this.queue = [];
    for (const job of this.pending.values()) {
      job.reject(new Error("Worker 池已终止"));
    }
    this.pending.clear();
  }
}

let sharedPool: DagWorkerPool | null = null;

export function getDagWorkerPool(): DagWorkerPool {
  if (!sharedPool) {
    sharedPool = new DagWorkerPool();
  }
  return sharedPool;
}

export function evaluateBatchInWorkerPool(
  graph: DAGGraphRaw,
  contexts: Record<string, unknown>[],
): Promise<DAGEvalResult[]> {
  return getDagWorkerPool().evaluateBatch(graph, contexts);
}

export function resetDagWorkerPoolForTest(): void {
  sharedPool?.terminate();
  sharedPool = null;
}
