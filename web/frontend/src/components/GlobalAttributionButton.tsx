import { useState } from "react";
import { Button } from "@mui/material";
import SourceIcon from "@mui/icons-material/Source";
import DataSourceDialog from "./calculator/DataSourceDialog";

/** 顶栏「开源/许可」— 全站可打开数据来源对话框 */
export default function GlobalAttributionButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        color="inherit"
        size="small"
        startIcon={<SourceIcon />}
        onClick={() => setOpen(true)}
        sx={{ ml: 0.5, textTransform: "none" }}
        title="源代码与数据许可"
      >
        开源/许可
      </Button>
      <DataSourceDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}
