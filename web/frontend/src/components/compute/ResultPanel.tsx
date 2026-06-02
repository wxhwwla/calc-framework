import {
  Typography,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Paper,
  Skeleton,
  Box,
  Alert,
  TableContainer,
} from "@mui/material";
import { useComputeStore } from "../../store/computeStore";

export default function ResultPanel() {
  const result = useComputeStore((s) => s.result);
  const loading = useComputeStore((s) => s.loading);
  const error = useComputeStore((s) => s.error);

  if (loading) {
    return (
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          结算结果
        </Typography>
        <Skeleton variant="rectangular" height={120} sx={{ borderRadius: 1 }} />
        <Box sx={{ mt: 1 }}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="text" width={`${60 + i * 10}%`} />
          ))}
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!result) {
    return (
      <Paper sx={{ p: 2, mt: 2, textAlign: "center" }}>
        <Typography color="text.secondary">
          选择适配器并输入参数后点击「计算」
        </Typography>
      </Paper>
    );
  }

  const entries = Object.entries(result.outputs);

  return (
    <Paper sx={{ p: 2, mt: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        结算结果
      </Typography>
      <TableContainer sx={{ overflowX: 'auto' }}>
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
      </TableContainer>
    </Paper>
  );
}
