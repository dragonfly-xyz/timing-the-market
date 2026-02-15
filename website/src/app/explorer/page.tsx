import { tokens } from "@/data";
import TokenTable from "@/components/tables/TokenTable";

export default function ExplorerPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-primary text-3xl md:text-4xl font-bold tracking-[-1px]">
          Token Explorer
        </h1>
        <p className="text-dim mt-2">
          Browse, sort, and filter all {tokens.length} tokens. Click column
          headers to sort. Use the dropdowns to filter by market cycle or
          category.
        </p>
      </div>
      <TokenTable tokens={tokens} />
    </div>
  );
}
