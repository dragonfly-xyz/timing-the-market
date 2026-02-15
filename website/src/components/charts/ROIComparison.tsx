"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from "recharts";
import type { Token } from "@/types";

const CYCLE_COLORS: Record<string, string> = {
  Bull: "#34d399",
  Bear: "#fb7185",
  Neutral: "#888888",
  Early: "#5014FA",
  Unknown: "#555555",
};

const CYCLE_TYPE_ORDER = ["Bull", "Bear"];

function formatROI(value: number): string {
  if (Math.abs(value) >= 10000) return `${(value / 1000).toFixed(0)}k%`;
  if (Math.abs(value) >= 100) return `${value.toFixed(0)}%`;
  return `${value.toFixed(1)}%`;
}

interface ROIComparisonProps {
  tokens: Token[];
  summaryMedians?: Record<string, number | null>;
}

export default function ROIComparison({ tokens, summaryMedians }: ROIComparisonProps) {
  // Group tokens by cycle type to get counts
  const roiByCycleType: Record<string, number[]> = {};
  for (const token of tokens) {
    const cycleType = token.cycle_type || "Unknown";
    if (token.annualized_roi == null) continue;
    if (!roiByCycleType[cycleType]) roiByCycleType[cycleType] = [];
    roiByCycleType[cycleType].push(token.annualized_roi);
  }

  const cycleTypes = CYCLE_TYPE_ORDER.filter(
    (ct) => roiByCycleType[ct] && roiByCycleType[ct].length > 0
  );

  if (cycleTypes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-dim">No data available</p>
      </div>
    );
  }

  const chartData = cycleTypes.map((ct) => {
    const values = roiByCycleType[ct];
    // Use summary medians if provided (ensures chart matches summary cards)
    const med = summaryMedians?.[ct] != null
      ? summaryMedians[ct]! * 100
      : (() => {
          const sorted = [...values].sort((a, b) => a - b);
          const mid = Math.floor(sorted.length / 2);
          return sorted.length % 2 === 0
            ? ((sorted[mid - 1] + sorted[mid]) / 2) * 100
            : sorted[mid] * 100;
        })();
    return {
      cycleType: ct,
      medianROI: med,
      count: values.length,
      label: `${ct} (n=${values.length})`,
    };
  });

  return (
    <div>
      <ResponsiveContainer width="100%" height={380}>
        <BarChart
          data={chartData}
          margin={{ top: 30, right: 30, bottom: 20, left: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#222222" />
          <XAxis
            dataKey="label"
            stroke="#333333"
            tick={{ fill: "#888888", fontSize: 13 }}
          />
          <YAxis
            domain={[Math.min(0, ...chartData.map((d) => d.medianROI)) - 5, Math.max(0, ...chartData.map((d) => d.medianROI)) + 5]}
            tickFormatter={formatROI}
            stroke="#333333"
            tick={{ fill: "#888888", fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0a0a0a",
              border: "1px solid #222222",
              color: "#F2F2F2",
              boxShadow: "0 8px 32px rgba(0,0,0,0.7)",
            }}
            formatter={(value) => [
              formatROI(Number(value ?? 0)),
              "Median ROI",
            ]}
          />
          <Bar dataKey="medianROI" radius={[2, 2, 0, 0]} maxBarSize={80}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={CYCLE_COLORS[entry.cycleType] || CYCLE_COLORS.Unknown}
              />
            ))}
            <LabelList
              dataKey="medianROI"
              position="top"
              formatter={(v) => formatROI(Number(v ?? 0))}
              style={{ fill: "#F2F2F2", fontSize: 13, fontWeight: 700, fontFamily: "'Non Natural Mono', monospace" }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex flex-wrap gap-5 mt-4 justify-center">
        {cycleTypes.map((type) => (
          <div key={type} className="flex items-center gap-2">
            <span
              className="inline-block w-2.5 h-2.5"
              style={{
                backgroundColor: CYCLE_COLORS[type] || CYCLE_COLORS.Unknown,
              }}
            />
            <span className="text-dim font-mono text-xs uppercase">
              {type} (n={roiByCycleType[type].length})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
