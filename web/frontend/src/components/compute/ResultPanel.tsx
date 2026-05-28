import {
  Typography,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Paper,
} from "@mui/material";
import { useComputeStore } from "../../store/computeStore";

export default function ResultPanel() {
  const result = useComputeStore((s) => s.result);
  const loading = useComputeStore((s) => s.loading);
  const error = useComputeStore((s) => s.error);

  if (loading) {
    return (
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography>计算中...</Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2, mt: 2, bgcolor: "error.main" }}>
        <Typography color="error.contrastText">{error}</Typography>
      </Paper>
    );
  }

  if (!result) return null;

  const entries = Object.entries(result.outputs);

  return (
    <Paper sx={{ p: 2, mt: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        结算结果
      </Typography>
      <Table size="small">
        <TableBody>
          {entries.map(([key, value]) => (
            <TableRow key={key}>
              <TableCell sx={{ border: "none", pl: 0 }}>{key}</TableCell>
              <TableCell sx={{ border: "none", textAlign: "right", fontWeight: "bold" }}>
                {typeof value === "number" ? value.toFixed(4) : String(value)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
}
