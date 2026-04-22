// staffSummary.ts
// Utility to generate a 30-word TL;DR summary for staff dashboard

export function generateStaffSummary(reasoning: string): string {
  // Simple implementation: take the first 30 words from the reasoning
  const words = reasoning.split(/\s+/);
  return words.slice(0, 30).join(' ') + (words.length > 30 ? '...' : '');
}

// Example usage:
// const summary = generateStaffSummary("Long reasoning text here...");
