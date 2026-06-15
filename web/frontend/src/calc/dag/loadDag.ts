import type { DAGGraphRaw } from "./types";

const STATIC_DAG_URL = "/endfield-dag.json";

let dagCache: DAGGraphRaw | null = null;

/** 加载终末地 DAG JSON（静态资源优先，回退 API）。 */
export async function loadEndfieldDag(): Promise<DAGGraphRaw> {
  if (dagCache) return dagCache;
  const urls = [STATIC_DAG_URL, "/api/layout/dag?adapter=endfield"];
  let lastError: Error | null = null;
  for (const url of urls) {
    try {
      const r = await fetch(url);
      if (!r.ok) {
        lastError = new Error(`加载 DAG 失败: ${url} ${r.status}`);
        continue;
      }
      dagCache = (await r.json()) as DAGGraphRaw;
      return dagCache;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
    }
  }
  throw lastError ?? new Error("无法加载 DAG");
}

/** 测试用：注入 DAG 缓存。 */
export function setDagCacheForTest(dag: DAGGraphRaw | null): void {
  dagCache = dag;
}
