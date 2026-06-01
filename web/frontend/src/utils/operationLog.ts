interface LogEntry {
  timestamp: string;
  action: string;
  detail: string;
}

const STORAGE_KEY = "calc-framework-operation-log";

function loadLogs(): LogEntry[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persistLogs(entries: LogEntry[]): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // 存储满或隐私模式时静默降级
  }
}

let logs: LogEntry[] = loadLogs();

export function logOperation(action: string, detail: string = "") {
  logs.push({
    timestamp: new Date().toISOString(),
    action,
    detail,
  });
  persistLogs(logs);
}

export function getOperationLogs(): LogEntry[] {
  return [...logs];
}

export function exportLogsAsJson(): void {
  const data = JSON.stringify(logs, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `operation-log-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function clearLogs(): void {
  logs = [];
  persistLogs(logs);
}
