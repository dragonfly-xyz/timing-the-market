"use client";

import { useState, useCallback } from "react";
import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
import type { MarketCycle, Token } from "@/types";

const CYCLE_COLORS: Record<string, string> = {
  Bull: "#34d399",
  Bear: "#fb7185",
  Neutral: "#888888",
  Early: "#5014FA",
  Unknown: "#555555",
};

const CYCLE_BAND_COLORS: Record<string, string> = {
  Bull: "rgba(52, 211, 153, 0.07)",
  Bear: "rgba(251, 113, 133, 0.07)",
  Neutral: "rgba(136, 136, 136, 0.05)",
  Early: "rgba(80, 20, 250, 0.05)",
  Unknown: "rgba(85, 85, 85, 0.05)",
};

interface MarketCycleChartProps {
  btcHistory: [number, number][];
  cycles: MarketCycle[];
  tokens: Token[];
}

interface TokenDot {
  timestamp: number;
  price: number;
  name: string;
  symbol: string;
  cycleType: string;
}

interface HoveredToken {
  token: TokenDot;
  x: number;
  y: number;
}

function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString("en-US", {
    year: "2-digit",
    month: "short",
  });
}

function formatPrice(price: number): string {
  if (price >= 1000) return `$${(price / 1000).toFixed(0)}k`;
  return `$${price.toFixed(0)}`;
}

function findClosestBtcPrice(
  dateStr: string,
  btcHistory: [number, number][]
): number | null {
  const targetTime = new Date(dateStr).getTime();
  if (isNaN(targetTime) || btcHistory.length === 0) return null;
  let closestIdx = 0;
  let closestDiff = Math.abs(btcHistory[0][0] - targetTime);
  for (let i = 1; i < btcHistory.length; i++) {
    const diff = Math.abs(btcHistory[i][0] - targetTime);
    if (diff < closestDiff) {
      closestDiff = diff;
      closestIdx = i;
    }
  }
  return btcHistory[closestIdx][1];
}

export default function MarketCycleChart({
  btcHistory,
  cycles,
  tokens,
}: MarketCycleChartProps) {
  const [hovered, setHovered] = useState<HoveredToken | null>(null);

  const handleDotEnter = useCallback(
    (token: TokenDot, cx: number, cy: number) => {
      setHovered({ token, x: cx, y: cy });
    },
    []
  );

  const handleDotLeave = useCallback(() => {
    setHovered(null);
  }, []);

  if (!btcHistory || btcHistory.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-dim">No data available</p>
      </div>
    );
  }

  const maxPoints = 500;
  const step = Math.max(1, Math.floor(btcHistory.length / maxPoints));
  const priceData = btcHistory
    .filter((_, i) => i % step === 0 || i === btcHistory.length - 1)
    .map(([timestamp, price]) => ({ timestamp, price }));

  const tokenDots: TokenDot[] = tokens
    .filter((t) => t.launch_date)
    .map((t) => {
      const timestamp = new Date(t.launch_date!).getTime();
      const btcPrice = findClosestBtcPrice(t.launch_date!, btcHistory);
      if (btcPrice === null) return null;
      return {
        timestamp,
        price: btcPrice,
        name: t.name,
        symbol: t.symbol,
        cycleType: t.cycle_type || "Unknown",
      };
    })
    .filter(Boolean) as TokenDot[];

  const minTime = priceData[0]?.timestamp ?? 0;
  const maxTime = priceData[priceData.length - 1]?.timestamp ?? 0;

  const cycleBands = cycles
    .map((c) => {
      const start = c.start ? new Date(c.start).getTime() : minTime;
      const end = c.end ? new Date(c.end).getTime() : maxTime;
      return {
        start: Math.max(start, minTime),
        end: Math.min(end, maxTime),
        type: c.type,
        name: c.name,
      };
    })
    .filter((c) => c.start < maxTime && c.end > minTime);

  return (
    <div style={{ position: "relative" }}>
      <ResponsiveContainer width="100%" height={420}>
        <ComposedChart
          data={priceData}
          margin={{ top: 10, right: 20, bottom: 20, left: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#222222" />

          {cycleBands.map((band) => (
            <ReferenceArea
              key={band.name}
              x1={band.start}
              x2={band.end}
              fill={CYCLE_BAND_COLORS[band.type] || CYCLE_BAND_COLORS.Unknown}
              fillOpacity={1}
              ifOverflow="hidden"
            />
          ))}

          <XAxis
            dataKey="timestamp"
            type="number"
            domain={[minTime, maxTime]}
            tickFormatter={formatDate}
            stroke="#333333"
            tick={{ fill: "#888888", fontSize: 12 }}
            tickCount={8}
          />
          <YAxis
            dataKey="price"
            scale="log"
            domain={["auto", "auto"]}
            tickFormatter={formatPrice}
            stroke="#333333"
            tick={{ fill: "#888888", fontSize: 12 }}
            width={60}
          />

          <Tooltip
            content={({ active, payload, label }) => {
              if (hovered || !active || !payload?.length) return null;
              const ts = Number(label);
              const price = payload.find(
                (p) => p.dataKey === "price" && p.name === "BTC Price"
              )?.value;
              if (!price) return null;
              return (
                <div
                  style={{
                    backgroundColor: "#0a0a0a",
                    border: "1px solid #222222",
                    padding: "10px 14px",
                    boxShadow: "0 8px 32px rgba(0,0,0,0.7)",
                    whiteSpace: "nowrap",
                  }}
                >
                  <div style={{ fontSize: "11px", color: "#888888", marginBottom: "2px", fontFamily: "'Non Natural Mono', monospace", textTransform: "uppercase" }}>
                    {new Date(ts).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </div>
                  <div
                    style={{
                      fontWeight: 700,
                      color: "#F2F2F2",
                      fontFamily: "'Non Natural Mono', monospace",
                      fontSize: "14px",
                    }}
                  >
                    BTC ${Number(price).toLocaleString()}
                  </div>
                </div>
              );
            }}
          />

          <Line
            type="monotone"
            dataKey="price"
            stroke="#FA4C14"
            strokeWidth={2}
            dot={false}
            name="BTC Price"
          />

          <Scatter
            data={tokenDots}
            dataKey="price"
            name="Token Launches"
            isAnimationActive={false}
            shape={(props) => {
              const { cx, cy } = props;
              const payload = (
                props as unknown as { payload: TokenDot }
              ).payload;
              const color =
                CYCLE_COLORS[payload?.cycleType] || CYCLE_COLORS.Unknown;
              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={6}
                  fill={color}
                  stroke="#000000"
                  strokeWidth={1.5}
                  opacity={0.9}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={() => handleDotEnter(payload, cx ?? 0, cy ?? 0)}
                  onMouseLeave={handleDotLeave}
                />
              );
            }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Custom token tooltip */}
      {hovered && (
        <div
          style={{
            position: "absolute",
            left: hovered.x + 12,
            top: hovered.y - 20,
            backgroundColor: "#0a0a0a",
            border: "1px solid #222222",
            color: "#F2F2F2",
            fontSize: "13px",
            lineHeight: "1.6",
            padding: "10px 14px",
            boxShadow: "0 8px 32px rgba(0,0,0,0.7)",
            pointerEvents: "none",
            zIndex: 50,
            whiteSpace: "nowrap",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              marginBottom: "4px",
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                backgroundColor:
                  CYCLE_COLORS[hovered.token.cycleType] || CYCLE_COLORS.Unknown,
                display: "inline-block",
                flexShrink: 0,
              }}
            />
            <span style={{ fontWeight: 700 }}>{hovered.token.name}</span>
            <span
              style={{
                opacity: 0.5,
                fontSize: "11px",
                textTransform: "uppercase",
                fontFamily: "'Non Natural Mono', monospace",
              }}
            >
              {hovered.token.symbol}
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#888888", fontFamily: "'Non Natural Mono', monospace" }}>
            <div>
              {new Date(hovered.token.timestamp).toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </div>
            <div>
              BTC at launch: $
              {Number(hovered.token.price).toLocaleString()}
            </div>
            <div
              style={{
                color:
                  CYCLE_COLORS[hovered.token.cycleType] ||
                  CYCLE_COLORS.Unknown,
              }}
            >
              {hovered.token.cycleType} cycle
            </div>
          </div>
        </div>
      )}

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
        <div className="flex items-center gap-2">
          <span
            className="inline-block w-4 h-0.5"
            style={{ backgroundColor: "#FA4C14" }}
          />
          <span className="text-dim font-mono text-xs uppercase">BTC Price</span>
        </div>
      </div>
    </div>
  );
}
