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
import type { SummaryStats } from "@/types";

const CYCLE_COLORS: Record<string, string> = {
  Bull: "#34d399",
  Bear: "#fb7185",
  Neutral: "#888888",
  Early: "#5014FA",
  Unknown: "#555555",
};

const CYCLE_TYPE_ORDER = ["Bull", "Bear"];

export default function SurvivalRateChart({
  summary,
}: {
  summary: SummaryStats;
}) {
  const survivalData = summary.fraction_currently_top100_by_cycle_type;
  if (!survivalData || Object.keys(survivalData).length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-dim">No data available</p>
      </div>
    );
  }

  const orderedTypes = CYCLE_TYPE_ORDER.filter((ct) => survivalData[ct] != null);

  const chartData = orderedTypes.map((ct) => ({
      cycleType: ct,
      survivalRate: (survivalData[ct] as number) * 100,
    }));

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-dim">No data available</p>
      </div>
    );
  }

  const maxVal = Math.max(...chartData.map((d) => d.survivalRate));
  const yMax = Math.ceil(maxVal / 5) * 5 + 10;

  return (
    <div>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={chartData}
          margin={{ top: 30, right: 20, bottom: 20, left: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#222222" />
          <XAxis
            dataKey="cycleType"
            stroke="#333333"
            tick={{ fill: "#888888", fontSize: 13 }}
          />
          <YAxis
            domain={[0, yMax]}
            tickFormatter={(v: number) => `${v}%`}
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
            labelStyle={{ color: "#888888" }}
            itemStyle={{ color: "#F2F2F2" }}
            formatter={(value) => [
              `${Number(value ?? 0).toFixed(1)}%`,
              "Fraction in Top 100",
            ]}
          />
          <Bar dataKey="survivalRate" radius={[2, 2, 0, 0]} maxBarSize={80}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={
                  CYCLE_COLORS[entry.cycleType] || CYCLE_COLORS.Unknown
                }
              />
            ))}
            <LabelList
              dataKey="survivalRate"
              position="top"
              formatter={(v) => `${Number(v ?? 0).toFixed(1)}%`}
              style={{ fill: "#F2F2F2", fontSize: 13, fontWeight: 700, fontFamily: "'Non Natural Mono', monospace" }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex flex-wrap gap-5 mt-4 justify-center">
        {chartData.map(({ cycleType }) => (
          <div key={cycleType} className="flex items-center gap-2">
            <span
              className="inline-block w-2.5 h-2.5"
              style={{
                backgroundColor:
                  CYCLE_COLORS[cycleType] || CYCLE_COLORS.Unknown,
              }}
            />
            <span className="text-dim font-mono text-xs uppercase">{cycleType}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
