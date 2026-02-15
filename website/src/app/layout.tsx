import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Timing the Token Market",
  description:
    "Does it matter when you launch your token? Analysis of every token announced on the Binance blog.",
};

function Nav() {
  const links = [
    { href: "/", label: "Overview" },
    { href: "/analysis", label: "Analysis" },
    { href: "/methodology", label: "Methodology" },
    { href: "/explorer", label: "Explorer" },
  ];
  return (
    <nav className="border-b border-edge bg-black">
      <div className="mx-auto max-w-6xl px-6 py-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <Link href="/" className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/images/Dragonfly_Logo-Light.svg"
            alt="Dragonfly"
            className="h-5 w-auto"
          />
          <span className="text-dfly-grey font-primary text-lg font-bold tracking-tight">
            TIMING
            <span className="text-dim mx-1 text-sm font-normal uppercase tracking-[0.15em]">the</span>
            <span className="text-accent">TOKEN MARKET</span>
          </span>
        </Link>
        <div className="flex gap-6 md:gap-8">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="font-mono text-xs uppercase tracking-[0.1em] text-dim hover:text-accent transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-black text-dfly-grey font-primary antialiased">
        <Nav />
        <main className="mx-auto max-w-6xl px-6 py-12">{children}</main>
        <footer className="border-t border-dotted border-edge py-8 text-center font-mono text-xs text-faint">
          Data from CoinGecko and Binance. For educational purposes only — not
          financial advice.
        </footer>
      </body>
    </html>
  );
}
