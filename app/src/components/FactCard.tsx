"use client";

import { useState } from "react";
import type { Fact } from "@/lib/facts";
import { HeartIcon, ShareIcon, SourceIcon, CheckIcon } from "./Icons";

const DOT_CLASS: Record<string, string> = {
  Space: "dot-space",
  Science: "dot-science",
  History: "dot-history",
  Tech: "dot-tech",
  AI: "dot-ai",
  Psychology: "dot-psychology",
  Money: "dot-money",
  Health: "dot-health",
  Nature: "dot-nature",
  "Pop Culture": "dot-popculture",
  Sports: "dot-sports",
  Food: "dot-food",
  Geography: "dot-geography",
  Language: "dot-language",
  "Human Body": "dot-humanbody",
  "Mental Health": "dot-mental",
  "This Day in History": "dot-history2",
  Misc: "dot-misc",
};

// soft accent glow color per category (very subtle — just atmosphere)
const GLOW: Record<string, [string, string]> = {
  Space: ["#312e81", "#0b1e6f"],
  Science: ["#064e3b", "#022c25"],
  History: ["#78350f", "#3a1c0a"],
  Tech: ["#0c4a6e", "#062738"],
  AI: ["#86198f", "#3b0a4a"],
  Psychology: ["#9d174d", "#3a0a1f"],
  Money: ["#3f6212", "#1a2906"],
  Health: ["#7f1d1d", "#2d0808"],
  Nature: ["#166534", "#052013"],
  "Pop Culture": ["#9f1239", "#3a081a"],
  Sports: ["#7c2d12", "#2d1408"],
  Food: ["#713f12", "#2d1908"],
  Geography: ["#155e75", "#051a22"],
  Language: ["#5b21b6", "#1c0844"],
  "Human Body": ["#9d174d", "#2c0817"],
  "Mental Health": ["#115e59", "#052024"],
  "This Day in History": ["#854d0e", "#221404"],
  Misc: ["#1f2937", "#0a1018"],
};

type Props = {
  fact: Fact;
  saved: boolean;
  onToggleSave: (id: string) => void;
};

export function FactCard({ fact, saved, onToggleSave }: Props) {
  const [copied, setCopied] = useState(false);
  const [popping, setPopping] = useState(false);
  const dot = DOT_CLASS[fact.category] ?? DOT_CLASS.Misc;
  const [g1, g2] = GLOW[fact.category] ?? GLOW.Misc;

  const handleSave = () => {
    onToggleSave(fact.id);
    setPopping(true);
    setTimeout(() => setPopping(false), 500);
  };

  const handleShare = async () => {
    const body = fact.detail ? `${fact.title}\n\n${fact.detail}` : fact.title;
    try {
      if (navigator.share) {
        await navigator.share({ title: fact.title, text: body });
      } else {
        await navigator.clipboard.writeText(body);
        setCopied(true);
        setTimeout(() => setCopied(false), 1400);
      }
    } catch {}
  };

  // category as a handle, lowercase no-space
  const handle = "@" + fact.category.toLowerCase().replace(/\s+/g, "");

  return (
    <section
      className="relative snap-start h-[100dvh] w-full bg-black overflow-hidden glow-tl glow-br flex"
      style={{ ["--glow" as string]: g1, ["--glow2" as string]: g2 }}
    >
      {/* caption block — bottom-left, TikTok style */}
      <div className="absolute inset-x-0 bottom-0 z-10 pb-[max(env(safe-area-inset-bottom),1.5rem)]">
        {/* gradient mask under text for legibility */}
        <div
          aria-hidden
          className="absolute inset-x-0 bottom-0 h-[70%] -z-10 bg-gradient-to-t from-black via-black/70 to-transparent pointer-events-none"
        />

        <div className="px-5 sm:px-8 pr-[5.5rem] sm:pr-[6.5rem] caption-rise">
          {/* handle */}
          <div className="flex items-center gap-2 mb-3">
            <span className={`w-2 h-2 rounded-full ${dot}`} />
            <span className="font-mono text-[0.78rem] tracking-tight text-white/90 font-medium">
              {handle}
            </span>
          </div>

          {/* title */}
          <h1
            className="text-white font-bold text-shadow-deep text-[clamp(1.55rem,5.6vw,2.35rem)] leading-[1.12] tracking-tight"
            style={{ fontWeight: 800 }}
          >
            {fact.title}
          </h1>

          {/* detail */}
          {fact.detail ? (
            <p className="mt-3 text-white/85 text-[clamp(0.95rem,3.6vw,1.05rem)] leading-[1.5] font-normal max-w-[42rem]">
              {fact.detail}
            </p>
          ) : (
            <p className="mt-3 text-white/40 text-sm italic">
              No expanded note for this entry yet.
            </p>
          )}
        </div>
      </div>

      {/* right action rail */}
      <div className="absolute right-3 sm:right-4 bottom-[max(env(safe-area-inset-bottom),1.5rem)] z-20 flex flex-col items-center gap-5 pb-2">
        <RailButton onClick={handleSave} label={saved ? "Saved" : ""}>
          <span className={popping ? "heart-pop block" : "block"}>
            <HeartIcon
              filled={saved}
              className={`w-8 h-8 ${saved ? "text-[var(--accent-2)]" : "text-white"}`}
            />
          </span>
        </RailButton>

        <RailButton onClick={handleShare} label={copied ? "Copied" : ""}>
          {copied ? (
            <CheckIcon className="w-8 h-8 text-[var(--accent)]" />
          ) : (
            <ShareIcon className="w-8 h-8 text-white" />
          )}
        </RailButton>

        {fact.url && (
          <a
            href={fact.url}
            target="_blank"
            rel="noreferrer"
            aria-label="Source"
            className="flex flex-col items-center"
          >
            <SourceIcon className="w-7 h-7 text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.7)]" />
            <span className="text-[0.62rem] mt-1 text-white/75 font-medium tracking-wide">
              Source
            </span>
          </a>
        )}
      </div>
    </section>
  );
}

function RailButton({
  children,
  label,
  onClick,
}: {
  children: React.ReactNode;
  label?: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center"
    >
      <span className="drop-shadow-[0_2px_8px_rgba(0,0,0,0.7)]">{children}</span>
      {label && (
        <span className="text-[0.62rem] mt-1 text-white/85 font-medium tracking-wide">
          {label}
        </span>
      )}
    </button>
  );
}
