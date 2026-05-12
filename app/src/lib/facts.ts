import { readFile } from "fs/promises";
import path from "path";

export type Fact = {
  id: string;
  source: string;
  category: string;
  title: string;
  detail?: string;
  url?: string;
};

let cache: Fact[] | null = null;

export async function loadFacts(): Promise<Fact[]> {
  if (cache) return cache;
  const file = path.join(process.cwd(), "..", "data", "facts.json");
  const raw = await readFile(file, "utf8");
  cache = JSON.parse(raw) as Fact[];
  return cache;
}

export function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
