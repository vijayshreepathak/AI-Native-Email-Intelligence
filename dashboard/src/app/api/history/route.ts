import { NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_BASE}/evaluations`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) {
      return NextResponse.json({ evaluations: [] });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ evaluations: [] });
  }
}
