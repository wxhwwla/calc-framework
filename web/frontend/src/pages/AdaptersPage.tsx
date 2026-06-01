import { useEffect, useState } from "react";
import {
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Collapse,
  IconButton,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { useAdapterStore } from "../store/adapterStore";
import { fetchSchema, type AdapterAttr } from "../api/compute";

function AdapterDetail({ name }: { name: string }) {
  const [open, setOpen] = useState(false);
  const [schema, setSchema] = useState<AdapterAttr[]>([]);

  useEffect(() => {
    if (open) {
      fetchSchema(name).then(setSchema).catch(() => setSchema([]));
    }
  }, [open, name]);

  return (
    <Box>
      <IconButton size="small" onClick={() => setOpen(!open)}>
        {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </IconButton>
      <Collapse in={open}>
        <Paper sx={{ p: 2, mt: 1, bgcolor: "grey.900" }}>
          <Typography variant="caption" display="block" gutterBottom>
            属性清单 ({schema.length} 项)
          </Typography>
          {schema.map((attr) => (
            <Typography key={attr.name} variant="caption" display="block">
              {attr.name} ({attr.type}, source={attr.source}){attr.description ? ` — ${attr.description}` : ""}
            </Typography>
          ))}
        </Paper>
      </Collapse>
    </Box>
  );
}

export default function AdaptersPage() {
  const adapters = useAdapterStore((s) => s.adapters);
  const load = useAdapterStore((s) => s.load);

  useEffect(() => {
    load();
  }, []);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        适配器管理
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox" />
              <TableCell>名称</TableCell>
              <TableCell>游戏</TableCell>
              <TableCell>版本</TableCell>
              <TableCell>说明</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {adapters.map((a) => (
              <TableRow key={a.name}>
                <TableCell padding="checkbox">
                  <AdapterDetail name={a.name} />
                </TableCell>
                <TableCell>
                  <Typography fontWeight="bold">{a.name}</Typography>
                </TableCell>
                <TableCell>
                  <Chip label={a.game} size="small" variant="outlined" />
                </TableCell>
                <TableCell>v{a.version}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {a.description}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
            {adapters.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography color="text.secondary">暂无适配器</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
