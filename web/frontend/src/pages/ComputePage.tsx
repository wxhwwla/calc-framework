import { Box, Button, Grid2 as Grid, Paper } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import AdapterSelector from "../components/compute/AdapterSelector";
import ParamForm from "../components/compute/ParamForm";
import ResultPanel from "../components/compute/ResultPanel";
import { useComputeStore } from "../store/computeStore";

export default function ComputePage() {
  const runCompute = useComputeStore((s) => s.runCompute);
  const selectedAdapter = useComputeStore((s) => s.selectedAdapter);

  return (
    <Grid container spacing={2}>
      <Grid size={4}>
        <Paper sx={{ p: 2 }}>
          <AdapterSelector />
          <ParamForm />
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<PlayArrowIcon />}
              onClick={runCompute}
              disabled={!selectedAdapter}
            >
              计算 (Compute)
            </Button>
          </Box>
        </Paper>
      </Grid>
      <Grid size={8}>
        <ResultPanel />
      </Grid>
    </Grid>
  );
}
