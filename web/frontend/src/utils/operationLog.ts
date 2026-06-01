interface LogEntry {
  timestamp: string;
  action: string;
  detail: string;
}

let logs: LogEntry[] = [];

export function logOperation(action: string, detail: string = "") {
  logs.push({
    timestamp: new Date().toISOString(),
    action,
    detail,
  });
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
}
