import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Box, Paper, Typography, useTheme } from "@mui/material";
import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { PieChart, BarChart } from "echarts/charts";
import { TooltipComponent, GridComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([PieChart, BarChart, TooltipComponent, GridComponent, CanvasRenderer]);

interface DamageChartProps {
  outputValues: Record<string, number> | null;
  nodeValues: Record<string, number | string | null> | null;
  zoneShare?: Record<string, number>;
}

export default function DamageChart({ outputValues, zoneShare }: DamageChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const textColor = theme.palette.text.primary;
  const hasPieData = outputValues && Object.keys(outputValues).length > 1;

  const pieOption = useMemo(() => {
    if (!outputValues || Object.keys(outputValues).length <= 1) return null;

    const data = Object.entries(outputValues)
      .filter(([, v]) => v != null && v > 0)
      .map(([name, value]) => ({
        name,
        value: Number(value),
      }));

    if (data.length === 0) return null;

    return {
      tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
      series: [
        {
          type: "pie",
          radius: ["30%", "60%"],
          center: ["50%", "50%"],
          data,
          label: { formatter: "{b}\n{d}%", fontSize: 11, textBorderWidth: 0, color: textColor },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0, 0, 0, 0.5)" },
          },
        },
      ],
    };
  }, [outputValues]);

  const zoneOption = useMemo(() => {
    if (!zoneShare || Object.keys(zoneShare).length === 0) return null;
    const data = Object.entries(zoneShare)
      .filter(([, v]) => v != null && v > 0)
      .sort(([, a], [, b]) => b - a);
    if (data.length === 0) return null;
    return {
      tooltip: { trigger: "axis", formatter: "{b}: {c}%" },
      grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
      xAxis: { type: "category", data: data.map(([n]) => n), axisLabel: { fontSize: 9 } },
      yAxis: { type: "value", name: "%", max: 100 },
      series: [
        {
          type: "bar",
          data: data.map(([, v]) => Number(v).toFixed(1)),
          itemStyle: { borderRadius: [4, 4, 0, 0], color: "#4fc3f7" },
        },
      ],
    };
  }, [zoneShare]);

  const barOption = useMemo(() => {
    if (!outputValues || Object.keys(outputValues).length === 0) return null;

    const data = Object.entries(outputValues).filter(
      ([, v]) => v != null && v > 0,
    );
    if (data.length === 0) return null;

    return {
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
      xAxis: { type: "category", data: data.map(([n]) => n), axisLabel: { fontSize: 10 } },
      yAxis: { type: "value" },
      series: [
        {
          type: "bar",
          data: data.map(([, v]) => Number(v)),
          itemStyle: { borderRadius: [4, 4, 0, 0] },
        },
      ],
    };
  }, [outputValues]);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        {t("damageChart.title")}
      </Typography>

      {!hasPieData && (!outputValues || Object.keys(outputValues).length === 0) && (
        <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
          {t("damageChart.noData")}
        </Typography>
      )}

      {hasPieData && pieOption && (
        <Box sx={{ height: 280 }}>
          <ReactEChartsCore
            echarts={echarts}
            option={pieOption}
            style={{ height: "100%" }}
            notMerge
            lazyUpdate
          />
        </Box>
      )}

      {zoneOption && (
        <Box sx={{ height: 220, mt: hasPieData || barOption ? 2 : 0 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: "block" }}>
            {t("damageChart.zoneContribution")}
          </Typography>
          <ReactEChartsCore
            echarts={echarts}
            option={zoneOption}
            style={{ height: "90%" }}
            notMerge
            lazyUpdate
          />
        </Box>
      )}

      {barOption && (
        <Box sx={{ height: 220, mt: hasPieData || zoneOption ? 2 : 0 }}>
          <ReactEChartsCore
            echarts={echarts}
            option={barOption}
            style={{ height: "100%" }}
            notMerge
            lazyUpdate
          />
        </Box>
      )}
    </Paper>
  );
}
