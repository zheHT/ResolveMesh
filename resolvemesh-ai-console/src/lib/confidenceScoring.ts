# confidenceScoring.ts
# Logic for generating a confidence score and citing evidence for investigation summaries

from typing import List, Dict

def calculate_confidence_score(evidence: List[Dict], reasoning: str) -> int:
    """
    Calculate a confidence score (0-100) based on evidence strength and reasoning quality.
    - More evidence and clear reasoning increases score.
    - Placeholder logic: customize as needed.
    """
    base_score = 50
    if not evidence:
        return 10  # Very low confidence if no evidence
    score = base_score + min(len(evidence) * 10, 30)
    if 'hash' in reasoning.lower():
        score += 10
    if 'timestamp' in reasoning.lower():
        score += 5
    return min(score, 100)

# Example usage:
# evidence = [{"transaction_id": "tx123", "hash": "abc", "details": "..."}]
# reasoning = "Transaction hash abc matches dispute."
# score = calculate_confidence_score(evidence, reasoning)
