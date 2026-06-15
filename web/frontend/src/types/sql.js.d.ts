declare module "sql.js" {
  export interface SqlJsStatic {
    Database: new (data?: ArrayLike<number>) => {
      run: (sql: string, params?: unknown[]) => void;
      exec: (sql: string) => { columns: string[]; values: unknown[][] }[];
      export: () => Uint8Array;
    };
  }

  export default function initSqlJs(config?: {
    locateFile?: (file: string) => string;
  }): Promise<SqlJsStatic>;
}
