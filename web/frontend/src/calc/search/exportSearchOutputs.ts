import type { LoadoutResult } from "../../api/search";

export interface SearchOutputRow {
  rank: number;
  weapon_name: string;
  final_damage: number;
  chest: string;
  gloves: string;
  accessory_a: string;
  accessory_b: string;
}

function toRow(result: LoadoutResult, rank: number): SearchOutputRow {
  return {
    rank,
    weapon_name: result.weapon_name,
    final_damage: result.final_damage,
    chest: result.chest,
    gloves: result.gloves,
    accessory_a: result.accessory_a,
    accessory_b: result.accessory_b,
  };
}

function escapeCsv(value: string | number): string {
  const text = String(value);
  if (text.includes(",") || text.includes('"') || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

/** 对齐桌面 `export_search_outputs` 三文件内容。 */
export function buildSearchOutputFiles(
  results: LoadoutResult[],
  topN: number,
  exportAll = true,
): { topJson: string; topCsv: string; allNdjson?: string } {
  const sorted = [...results].sort((a, b) => b.final_damage - a.final_damage);
  const top = sorted.slice(0, Math.max(1, topN));
  const topRows = top.map((row, idx) => toRow(row, idx + 1));
  const topJson = JSON.stringify(topRows, null, 2);
  const header = "rank,weapon_name,final_damage,chest,gloves,accessory_a,accessory_b";
  const csvLines = [
    header,
    ...topRows.map((row) =>
      [
        row.rank,
        escapeCsv(row.weapon_name),
        row.final_damage,
        escapeCsv(row.chest),
        escapeCsv(row.gloves),
        escapeCsv(row.accessory_a),
        escapeCsv(row.accessory_b),
      ].join(","),
    ),
  ];
  const topCsv = `${csvLines.join("\n")}\n`;
  if (!exportAll) {
    return { topJson, topCsv };
  }
  const allNdjson = sorted.map((row, idx) => JSON.stringify(toRow(row, idx + 1))).join("\n");
  return { topJson, topCsv, allNdjson: allNdjson ? `${allNdjson}\n` : "" };
}

function downloadText(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

/** 下载与桌面 `search_output/` 同名的三文件。 */
export function downloadSearchOutputBundle(results: LoadoutResult[], topN: number): void {
  const files = buildSearchOutputFiles(results, topN, true);
  downloadText("top_results.json", files.topJson, "application/json");
  downloadText("top_results.csv", files.topCsv, "text/csv");
  if (files.allNdjson) {
    downloadText("all_results.ndjson", files.allNdjson, "application/x-ndjson");
  }
}
