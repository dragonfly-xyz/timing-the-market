"use client";

import { useState, useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  createColumnHelper,
  flexRender,
  type SortingState,
} from "@tanstack/react-table";
import type { Token } from "@/types";

const CYCLE_COLORS: Record<string, string> = {
  Bull: "text-bull",
  Bear: "text-bear",
  Neutral: "text-dim",
  Early: "text-dfly-blue",
  Unknown: "text-faint",
};

function fmtPct(n: number | null | undefined): string {
  if (n == null) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

const col = createColumnHelper<Token>();

export default function TokenTable({ tokens }: { tokens: Token[] }) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "market_cap_rank", desc: false },
  ]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [cycleFilter, setCycleFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");

  const columns = useMemo(
    () => [
      col.accessor("market_cap_rank", {
        header: "#",
        cell: (info) => (
          <span className="font-mono text-dim">
            {info.getValue() ?? "—"}
          </span>
        ),
        size: 50,
        sortingFn: (a, b) => {
          const aVal = a.original.market_cap_rank;
          const bVal = b.original.market_cap_rank;
          if (aVal == null && bVal == null) return 0;
          if (aVal == null) return 1;
          if (bVal == null) return -1;
          return aVal - bVal;
        },
      }),
      col.accessor("name", {
        header: "Name",
        cell: (info) => (
          <div className="flex items-center gap-2">
            {info.row.original.image && (
              <img
                src={info.row.original.image}
                alt=""
                className="h-5 w-5 rounded-full"
              />
            )}
            <span className="font-medium">{info.getValue()}</span>
            <span className="text-xs text-faint font-mono uppercase">
              {info.row.original.symbol}
            </span>
          </div>
        ),
        size: 200,
      }),
      col.accessor("binance_delisted", {
        header: "Status",
        cell: (info) => {
          const delisted = info.getValue();
          if (delisted) {
            return (
              <span className="text-bear text-xs font-mono uppercase px-1.5 py-0.5 bg-bear/10">
                Delisted
              </span>
            );
          }
          return (
            <span className="text-bull text-xs font-mono uppercase px-1.5 py-0.5 bg-bull/10">
              Active
            </span>
          );
        },
        size: 80,
      }),
      col.accessor("cycle_type", {
        header: "Cycle",
        cell: (info) => {
          const v = info.getValue() ?? "Unknown";
          return (
            <span className={CYCLE_COLORS[v] ?? "text-faint"}>
              {info.row.original.cycle_name ?? v}
            </span>
          );
        },
        size: 160,
      }),
      col.accessor("category", {
        header: "Category",
        cell: (info) => (
          <span className="text-dim">{info.getValue() ?? "—"}</span>
        ),
        size: 110,
      }),
      col.accessor("roi_since_launch", {
        header: "ROI",
        cell: (info) => {
          const v = info.getValue();
          if (v == null) return <span className="text-faint">—</span>;
          return (
            <span
              className={`font-mono ${v >= 0 ? "text-bull" : "text-bear"}`}
            >
              {fmtPct(v)}
            </span>
          );
        },
        size: 100,
      }),
      col.accessor("annualized_roi", {
        header: "Ann. ROI",
        cell: (info) => {
          const v = info.getValue();
          if (v == null) return <span className="text-faint">—</span>;
          return (
            <span
              className={`font-mono ${v >= 0 ? "text-bull" : "text-bear"}`}
            >
              {fmtPct(v)}
            </span>
          );
        },
        size: 100,
      }),
      col.accessor("roi_vs_btc", {
        header: "vs BTC",
        cell: (info) => {
          const v = info.getValue();
          if (v == null) return <span className="text-faint">—</span>;
          return (
            <span
              className={`font-mono ${v >= 0 ? "text-bull" : "text-bear"}`}
            >
              {fmtPct(v)}
            </span>
          );
        },
        size: 100,
      }),
      col.accessor("drawdown_from_ath", {
        header: "Drawdown",
        cell: (info) => {
          const v = info.getValue();
          if (v == null) return <span className="text-faint">—</span>;
          return <span className="font-mono text-bear">-{fmtPct(v)}</span>;
        },
        size: 100,
      }),
      col.accessor("launch_date", {
        header: "Launch",
        cell: (info) => (
          <span className="font-mono text-dim text-xs">
            {info.getValue() ?? "—"}
          </span>
        ),
        size: 110,
      }),
    ],
    []
  );

  const cycleTypes = useMemo(
    () => ["All", ...new Set(tokens.map((t) => t.cycle_type ?? "Unknown"))],
    [tokens]
  );
  const categories = useMemo(
    () => ["All", ...new Set(tokens.map((t) => t.category ?? "Other"))],
    [tokens]
  );

  const filtered = useMemo(() => {
    let data = tokens;
    if (cycleFilter !== "All") {
      data = data.filter((t) => (t.cycle_type ?? "Unknown") === cycleFilter);
    }
    if (categoryFilter !== "All") {
      data = data.filter((t) => (t.category ?? "Other") === categoryFilter);
    }
    return data;
  }, [tokens, cycleFilter, categoryFilter]);

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 50 } },
  });

  if (tokens.length === 0) {
    return (
      <p className="text-faint py-8 text-center">
        No token data available. Run the data pipeline first.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <input
          type="text"
          placeholder="Search tokens..."
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="bg-surface border border-edge px-4 py-2 text-sm text-dfly-grey placeholder:text-faint focus:outline-none focus:border-accent font-mono"
        />
        <select
          value={cycleFilter}
          onChange={(e) => setCycleFilter(e.target.value)}
          className="bg-surface border border-edge px-3 py-2 text-sm text-dfly-grey font-mono"
        >
          {cycleTypes.map((ct) => (
            <option key={ct} value={ct}>
              {ct === "All" ? "All Cycles" : ct}
            </option>
          ))}
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="bg-surface border border-edge px-3 py-2 text-sm text-dfly-grey font-mono"
        >
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat === "All" ? "All Categories" : cat}
            </option>
          ))}
        </select>
        <span className="text-xs text-faint font-mono uppercase">
          {table.getFilteredRowModel().rows.length} tokens
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-surface border border-edge">
        <table className="min-w-[900px] w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b border-edge">
                {hg.headers.map((h) => (
                  <th
                    key={h.id}
                    onClick={h.column.getToggleSortingHandler()}
                    className="cursor-pointer px-3 py-3 text-left font-mono text-xs uppercase text-faint hover:text-accent select-none transition-colors"
                    style={{ width: h.getSize() }}
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(
                        h.column.columnDef.header,
                        h.getContext()
                      )}
                      {{ asc: " \u2191", desc: " \u2193" }[
                        h.column.getIsSorted() as string
                      ] ?? ""}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-edge/30 hover:bg-raised transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-3 py-2.5 whitespace-nowrap"
                  >
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext()
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-dim">
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="bg-surface border border-edge px-4 py-1.5 disabled:opacity-30 hover:border-accent transition-colors font-mono text-xs uppercase"
          >
            Previous
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="bg-surface border border-edge px-4 py-1.5 disabled:opacity-30 hover:border-accent transition-colors font-mono text-xs uppercase"
          >
            Next
          </button>
        </div>
        <span className="font-mono text-xs">
          Page {table.getState().pagination.pageIndex + 1} of{" "}
          {table.getPageCount()}
        </span>
      </div>
    </div>
  );
}
