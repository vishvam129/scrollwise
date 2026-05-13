"use client";

import { useCallback, useEffect, useState } from "react";
import { FactCard } from "./FactCard";
import { MenuIcon } from "./Icons";
import type { Fact } from "@/lib/facts";

const SAVED_KEY = "scrollwise:saved";

export function Feed() {
  const [facts, setFacts] = useState<Fact[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState<string>("All");
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(SAVED_KEY);
      if (raw) setSaved(new Set(JSON.parse(raw)));
    } catch {}
  }, []);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/facts?category=${encodeURIComponent(category)}&limit=80`)
      .then((r) => r.json())
      .then((data) => {
        setFacts(data.facts);
        setCategories(["All", ...data.categories]);
      })
      .finally(() => setLoading(false));
  }, [category]);

  const toggleSave = useCallback((id: string) => {
    setSaved((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      localStorage.setItem(SAVED_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  return (
    <>
      {/* floating menu — minimal, glassy */}
      <button
        onClick={() => setSheetOpen(true)}
        aria-label="Open categories"
        className="fixed top-[max(env(safe-area-inset-top),1rem)] right-4 z-30 flex items-center gap-2 px-3 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-white"
      >
        <MenuIcon className="w-4 h-4" />
        <span className="text-[0.74rem] font-semibold tracking-wide">
          {category === "All" ? "All" : category}
        </span>
      </button>

      <main className="feed h-[100dvh] w-screen overflow-y-scroll snap-y snap-mandatory bg-black">
        {loading && (
          <div className="h-[100dvh] flex items-center justify-center">
            <div className="flex items-center gap-2 text-white/70 text-sm font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
              loading feed
            </div>
          </div>
        )}
        {!loading && facts.length === 0 && (
          <div className="h-[100dvh] flex items-center justify-center text-white/55 px-8 text-center">
            No facts in this category yet.
          </div>
        )}
        {facts.map((f) => (
          <FactCard
            key={f.id}
            fact={f}
            saved={saved.has(f.id)}
            onToggleSave={toggleSave}
          />
        ))}
      </main>

      {sheetOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setSheetOpen(false)}
        >
          <div
            className="absolute left-0 right-0 bottom-0 bg-[#0c0c0d] border-t border-white/8 rounded-t-3xl px-5 pt-3 pb-[max(env(safe-area-inset-bottom),1.5rem)] max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mx-auto w-10 h-1 rounded-full bg-white/18 mb-5" />
            <div className="text-white/45 text-[0.7rem] tracking-[0.22em] uppercase font-bold mb-3">
              Categories
            </div>
            <div className="flex flex-col">
              {categories.map((c) => {
                const active = c === category;
                return (
                  <button
                    key={c}
                    onClick={() => {
                      setCategory(c);
                      setSheetOpen(false);
                    }}
                    className={`flex items-center justify-between py-3.5 border-b border-white/5 text-left ${
                      active ? "text-[var(--accent)]" : "text-white"
                    }`}
                  >
                    <span className="text-[1.02rem] font-semibold">{c}</span>
                    {active && (
                      <span className="w-2 h-2 rounded-full bg-[var(--accent)]" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
