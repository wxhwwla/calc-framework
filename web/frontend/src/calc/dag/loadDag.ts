import type { DAGGraphRaw } from "./types";

let dagCache: DAGGraphRaw | null = null;

/** 加载终末地 DAG JSON（缓存单例）。 */
export async function loadEndfieldDag(): Promise<DAGGraphRaw> {
  if (dagCache) return dagCache;
  const r = await fetch("/api/layout/dag?adapter=endfield");
  if (!r.ok) {
    throw new Error(`加载 DAG 失败: ${r.status}`);
  }
  dagCache = (await r.json()) as DAGGraphRaw;
  return dagCache;
}

/** 测试用：注入 DAG 缓存。 */
export function setDagCacheForTest(dag: DAGGraphRaw | null): void {
  dagCache = dag;
}
