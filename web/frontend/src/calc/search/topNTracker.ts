import type { LoadoutResult } from "../../api/search";

/** 内存 TopN 追踪（对齐 TopNTracker 语义）。 */
export class TopNTracker {
  private readonly topN: number;
  private items: LoadoutResult[] = [];

  constructor(topN: number) {
    this.topN = Math.max(1, topN);
  }

  consider(row: LoadoutResult): void {
    this.items.push(row);
    this.items.sort((a, b) => b.final_damage - a.final_damage);
    if (this.items.length > this.topN) {
      this.items.length = this.topN;
    }
  }

  snapshot(): LoadoutResult[] {
    return [...this.items];
  }
}
