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
} from "recharts";
import type { Token } from "@/types";

const CYCLE_COLORS: Record<string, string> = {
  Bull: "#34d399",
  Bear: "#fb7185",
  Neutral: "#888888",
  Early: "#5014FA",
  Unknown: "#555555",
};

const CYCLE_ORDER = [
  "Pre-2013 Early",
  "2013 Bull",
  "2014-2015 Bear",
  "2015-2016 Recovery",
  "2016-2017 Bull",
  "2018-2019 Bear",
  "2019-2020 Recovery",
  "2020-2021 Bull",
  "2022 Bear",
  "2023 Recovery",
  "2023-2025 Bull",
];

interface LaunchDistributionProps {
  tokens: Token[];
}

export default function LaunchDistribution({
  tokens,
}: LaunchDistributionProps) {
  const cycleCounts: Record<string, { count: number; type: string }> = {};
  for (const token of tokens) {
    const cycleName = token.cycle_name || "Unknown";
    const cycleType = token.cycle_type || "Unknown";
    if (!cycleCounts[cycleName]) {
      cycleCounts[cycleName] = { count: 0, type: cycleType };
    }
    cycleCounts[cycleName].count++;
  }

  if (Object.keys(cycleCounts).length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-dim">No data available</p>
      </div>
    );
  }

  const sortedCycles = Object.keys(cycleCounts).sort((a, b) => {
    const idxA = CYCLE_ORDER.indexOf(a);
    const idxB = CYCLE_ORDER.indexOf(b);
    if (idxA !== -1 && idxB !== -1) return idxA - idxB;
    if (idxA === -1 && idxB !== -1) return 1;
    if (idxA !== -1 && idxB === -1) return -1;
    return a.localeCompare(b);
  });

  const chartData = sortedCycles.map((name) => ({
    name,
    count: cycleCounts[name].count,
    cycleType: cycleCounts[name].type,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={380}>
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 20, bottom: 60, left: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#222222" />
          <XAxis
            dataKey="name"
            stroke="#333333"
            tick={{ fill: "#888888", fontSize: 11 }}
            angle={-35}
            textAnchor="end"
            interval={0}
            height={80}
          />
          <YAxis
            stroke="#333333"
            tick={{ fill: "#888888", fontSize: 12 }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0a0a0a",
              border: "1px solid #222222",
              color: "#F2F2F2",
              boxShadow: "0 8px 32px rgba(0,0,0,0.7)",
            }}
            formatter={(value) => [value ?? 0, "Tokens"]}
          />
          <Bar dataKey="count" radius={[2, 2, 0, 0]} maxBarSize={50}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={CYCLE_COLORS[entry.cycleType] || CYCLE_COLORS.Unknown}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex flex-wrap gap-5 mt-4 justify-center">
        {["Bull", "Bear", "Neutral", "Early"].map((type) => (
          <div key={type} className="flex items-center gap-2">
            <span
              className="inline-block w-2.5 h-2.5"
              style={{ backgroundColor: CYCLE_COLORS[type] }}
            />
            <span className="text-dim font-mono text-xs uppercase">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
