"use client";

import { useCallback, useEffect, useState } from "react";
import { FactCard } from "./FactCard";
import type { Fact } from "@/lib/facts";

const SAVED_KEY = "scrollwise:saved";

export function Feed() {
  const [facts, setFacts] = useState<Fact[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState<string>("All");
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

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
    <main className="h-screen w-screen overflow-y-scroll snap-y snap-mandatory bg-black">
      <header className="fixed top-0 left-0 right-0 z-10 px-4 py-3 flex gap-2 overflow-x-auto bg-gradient-to-b from-black/60 to-transparent backdrop-blur">
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={`shrink-0 text-xs px-3 py-1.5 rounded-full transition ${
              category === c
                ? "bg-white text-black"
                : "bg-white/15 text-white hover:bg-white/25"
            }`}
          >
            {c}
          </button>
        ))}
      </header>

      {loading && (
        <div className="h-screen flex items-center justify-center text-white/60">
          Loading…
        </div>
      )}

      {!loading && facts.length === 0 && (
        <div className="h-screen flex items-center justify-center text-white/60 px-6 text-center">
          No facts in this category yet. Try another, or run the scrapers in
          <code className="ml-1 px-1.5 bg-white/10 rounded">generator/</code>.
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
  );
}
