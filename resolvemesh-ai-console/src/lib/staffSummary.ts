// staffSummary.ts
// Utility to generate a 30-word TL;DR summary for staff dashboard

function countWords(s: string) {
  return s.trim().split(/\s+/).filter(Boolean).length;
}

function hardLimit30Words(s: string) {
  const words = s.trim().split(/\s+/).filter(Boolean);
  if (words.length <= 30) return words.join(" ");
  return `${words.slice(0, 30).join(" ")}...`;
}

/**
 * Preferred: ask backend Z.AI endpoint to produce staff TL;DR.
 * Fallback: hard truncate to 30 words.
 */
export async function generateStaffSummary(caseText: string, apiBase = "http://127.0.0.1:8000") {
  try {
    const res = await fetch(`${apiBase}/api/zai/staff-tldr`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ case_text: caseText }),
    });
    if (!res.ok) throw new Error("staff-tldr request failed");
    const data = (await res.json()) as { summary_tldr?: string };
    if (!data.summary_tldr) throw new Error("missing summary_tldr");
    const trimmed = data.summary_tldr.trim();
    return countWords(trimmed) <= 30 ? trimmed : hardLimit30Words(trimmed);
  } catch {
    return hardLimit30Words(caseText);
  }
}
