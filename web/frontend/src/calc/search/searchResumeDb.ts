/**
 * 浏览器搜索续跑存储（sql.js，schema 对齐桌面 SearchRunStore + scores）。
 * DB 二进制持久化至 IndexedDB，可导出 search_runs.db 供桌面查看。
 */

import { buildComboKey } from "./comboKey";
import type { LoadoutResult } from "../../api/search";

const IDB_NAME = "endfield-search-resume";
const IDB_STORE = "databases";
const IDB_KEY = "active";

const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS runs (
  signature TEXT PRIMARY KEY,
  total_combinations INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'running'
);
CREATE TABLE IF NOT EXISTS processed (
  signature TEXT NOT NULL,
  combo_key TEXT NOT NULL,
  PRIMARY KEY (signature, combo_key)
);
CREATE TABLE IF NOT EXISTS scores (
  signature TEXT NOT NULL,
  combo_key TEXT NOT NULL,
  weapon_name TEXT NOT NULL,
  final_damage REAL NOT NULL,
  chest TEXT NOT NULL,
  gloves TEXT NOT NULL,
  accessory_a TEXT NOT NULL,
  accessory_b TEXT NOT NULL,
  PRIMARY KEY (signature, combo_key)
);
`;

type SqlJsDatabase = {
  run: (sql: string, params?: unknown[]) => void;
  exec: (sql: string) => { columns: string[]; values: unknown[][] }[];
  export: () => Uint8Array;
};

type SqlJsStatic = {
  Database: new (data?: ArrayLike<number>) => SqlJsDatabase;
};

let sqlModule: SqlJsStatic | null = null;
let db: SqlJsDatabase | null = null;
let persistTimer: ReturnType<typeof setTimeout> | null = null;

async function loadSql(): Promise<SqlJsStatic> {
  if (sqlModule) return sqlModule;
  const initSqlJs = (await import("sql.js")).default;
  sqlModule = await initSqlJs({
    locateFile: (file: string) => `/sql-wasm/${file}`,
  });
  return sqlModule;
}

function openIdb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_NAME, 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(IDB_STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function readStoredDb(): Promise<Uint8Array | null> {
  const idb = await openIdb();
  return new Promise((resolve, reject) => {
    const tx = idb.transaction(IDB_STORE, "readonly");
    const req = tx.objectStore(IDB_STORE).get(IDB_KEY);
    req.onsuccess = () => {
      resolve((req.result as Uint8Array | undefined) ?? null);
    };
    req.onerror = () => reject(req.error);
  });
}

async function writeStoredDb(data: Uint8Array): Promise<void> {
  const idb = await openIdb();
  return new Promise((resolve, reject) => {
    const tx = idb.transaction(IDB_STORE, "readwrite");
    tx.objectStore(IDB_STORE).put(data, IDB_KEY);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

function schedulePersist(): void {
  if (persistTimer) clearTimeout(persistTimer);
  persistTimer = setTimeout(() => {
    persistTimer = null;
    if (!db) return;
    void writeStoredDb(db.export());
  }, 400);
}

export async function initSearchResumeDb(): Promise<void> {
  if (db) return;
  const SQL = await loadSql();
  const stored = await readStoredDb();
  db = stored ? new SQL.Database(stored) : new SQL.Database();
  db.run(SCHEMA_SQL);
}

function requireDb(): SqlJsDatabase {
  if (!db) throw new Error("search resume db not initialized");
  return db;
}

export async function ensureSearchRun(signature: string, totalCombinations: number): Promise<void> {
  await initSearchResumeDb();
  const conn = requireDb();
  conn.run(
    `INSERT INTO runs(signature, total_combinations, status) VALUES (?, ?, 'running')
     ON CONFLICT(signature) DO UPDATE SET total_combinations=excluded.total_combinations`,
    [signature, totalCombinations],
  );
  schedulePersist();
}

export function isComboProcessed(signature: string, comboKey: string): boolean {
  const conn = requireDb();
  const rows = conn.exec(
    `SELECT combo_key FROM processed WHERE signature='${signature.replace(/'/g, "''")}' AND combo_key='${comboKey.replace(/'/g, "''")}'`,
  );
  return rows.length > 0 && rows[0].values.length > 0;
}

export function markProcessedBatch(signature: string, comboKeys: string[]): void {
  if (!comboKeys.length) return;
  const conn = requireDb();
  for (const key of comboKeys) {
    conn.run(
      "INSERT OR IGNORE INTO processed(signature, combo_key) VALUES (?, ?)",
      [signature, key],
    );
  }
  schedulePersist();
}

export function replaceTopScores(signature: string, results: LoadoutResult[]): void {
  const conn = requireDb();
  conn.run("DELETE FROM scores WHERE signature=?", [signature]);
  results.forEach((row, index) => {
    const comboKey = buildComboKey(
      row.weapon_name,
      row.chest,
      row.gloves,
      row.accessory_a,
      row.accessory_b,
    );
    conn.run(
      `INSERT OR REPLACE INTO scores(signature, combo_key, weapon_name, final_damage, chest, gloves, accessory_a, accessory_b)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        signature,
        comboKey || `top-${index}`,
        row.weapon_name,
        row.final_damage,
        row.chest,
        row.gloves,
        row.accessory_a,
        row.accessory_b,
      ],
    );
  });
  schedulePersist();
}

export function markRunStatus(signature: string, status: string): void {
  const conn = requireDb();
  conn.run("UPDATE runs SET status=? WHERE signature=?", [status, signature]);
  schedulePersist();
}

export async function flushSearchResumeDb(): Promise<void> {
  if (!db) return;
  await writeStoredDb(db.export());
}

export async function exportSearchRunsDb(): Promise<Blob> {
  await flushSearchResumeDb();
  const conn = requireDb();
  const bytes = conn.export();
  return new Blob([bytes.slice().buffer]);
}

export function countProcessed(signature: string): number {
  const conn = requireDb();
  const rows = conn.exec(
    `SELECT COUNT(*) FROM processed WHERE signature='${signature.replace(/'/g, "''")}'`,
  );
  if (!rows.length || !rows[0].values.length) return 0;
  return Number(rows[0].values[0][0]) || 0;
}
