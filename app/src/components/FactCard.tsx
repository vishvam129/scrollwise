"use client";

import { useState } from "react";
import type { Fact } from "@/lib/facts";

const CATEGORY_COLORS: Record<string, string> = {
  Science: "from-emerald-500 to-teal-700",
  Space: "from-indigo-600 to-purple-800",
  History: "from-amber-600 to-orange-800",
  Tech: "from-sky-500 to-blue-800",
  AI: "from-fuchsia-500 to-pink-700",
  Psychology: "from-rose-500 to-red-700",
  Money: "from-lime-500 to-green-700",
  Health: "from-red-500 to-rose-700",
  Nature: "from-green-500 to-emerald-800",
  "Pop Culture": "from-pink-500 to-purple-700",
  Sports: "from-orange-500 to-red-700",
  Food: "from-yellow-500 to-orange-700",
  Geography: "from-cyan-500 to-blue-700",
  Language: "from-violet-500 to-indigo-700",
  "Human Body": "from-rose-600 to-purple-800",
  Misc: "from-slate-600 to-slate-800",
};

type Props = {
  fact: Fact;
  saved: boolean;
  onToggleSave: (id: string) => void;
};

export function FactCard({ fact, saved, onToggleSave }: Props) {
  const [copied, setCopied] = useState(false);
  const gradient =
    CATEGORY_COLORS[fact.category] ?? CATEGORY_COLORS.Misc;

  const copy = async () => {
    const body = fact.detail ? `${fact.title}\n\n${fact.detail}` : fact.title;
    await navigator.clipboard.writeText(body);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section
      className={`snap-start h-screen w-full flex items-center justify-center bg-gradient-to-br ${gradient} px-6`}
    >
      <div className="max-w-2xl w-full text-white">
        <div className="flex items-center justify-between mb-8">
          <span className="text-xs uppercase tracking-widest bg-white/15 backdrop-blur rounded-full px-3 py-1">
            {fact.category}
          </span>
          <span className="text-xs opacity-60">{fact.source}</span>
        </div>

        <h2 className="text-2xl sm:text-3xl md:text-4xl font-semibold leading-tight">
          {fact.title}
        </h2>
        {fact.detail && (
          <p className="mt-5 text-base sm:text-lg leading-relaxed text-white/85">
            {fact.detail}
          </p>
        )}

        <div className="mt-10 flex items-center gap-3">
          <button
            onClick={() => onToggleSave(fact.id)}
            className="px-4 py-2 rounded-full bg-white/15 backdrop-blur hover:bg-white/25 transition text-sm"
          >
            {saved ? "★ Saved" : "☆ Save"}
          </button>
          <button
            onClick={copy}
            className="px-4 py-2 rounded-full bg-white/15 backdrop-blur hover:bg-white/25 transition text-sm"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
          {fact.url && (
            <a
              href={fact.url}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 rounded-full bg-white/15 backdrop-blur hover:bg-white/25 transition text-sm"
            >
              Source ↗
            </a>
          )}
        </div>

        <div className="mt-16 text-center text-xs opacity-50">
          swipe up for next
        </div>
      </div>
    </section>
  );
}
