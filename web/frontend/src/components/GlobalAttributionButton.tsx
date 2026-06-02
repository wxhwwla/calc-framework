import { useState } from "react";
import { Button, IconButton, useMediaQuery, useTheme } from "@mui/material";
import SourceIcon from "@mui/icons-material/Source";
import DataSourceDialog from "./calculator/DataSourceDialog";

/** 顶栏「开源/许可」— 全站可打开数据来源对话框 */
export default function GlobalAttributionButton() {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <>
      {isMobile ? (
        <IconButton
          color="inherit"
          size="small"
          onClick={() => setOpen(true)}
          title="源代码与数据许可"
        >
          <SourceIcon />
        </IconButton>
      ) : (
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
      )}
      <DataSourceDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}
