import { NextResponse } from "next/server";
import { loadFacts, shuffle, type Fact } from "@/lib/facts";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");
  const limit = Number(searchParams.get("limit") ?? "50");

  let facts: Fact[] = await loadFacts();
  if (category && category !== "All") {
    facts = facts.filter((f) => f.category === category);
  }
  const out = shuffle(facts).slice(0, limit);
  const categories = Array.from(
    new Set((await loadFacts()).map((f) => f.category)),
  ).sort();
  return NextResponse.json({ facts: out, categories });
}
