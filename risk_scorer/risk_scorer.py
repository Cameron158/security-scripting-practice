"""
Risk Register Auto-Scorer
---------------------------
Built from spec:

Input: risk_register.csv
Columns: risk_id, risk_description, likelihood_rating, impact_rating

Score = likelihood_rating x impact_rating  (range 1-25)

Tiers:
  Low          = 1-6
  Medium       = 7-12
  Medium-High  = 13-18
  High         = 19-25

Output: risks sorted highest risk -> lowest risk.
"""

import csv
import sys


def get_tier(score: int) -> str:
    if 1 <= score <= 6:
        return "Low"
    elif 7 <= score <= 12:
        return "Medium"
    elif 13 <= score <= 18:
        return "Medium-High"
    elif 19 <= score <= 25:
        return "High"
    return "Unknown"


def load_and_score(filepath: str):
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        risks = list(reader)

    for r in risks:
        likelihood = int(r["likelihood_rating"])
        impact = int(r["impact_rating"])
        score = likelihood * impact
        r["risk_score"] = score
        r["risk_tier"] = get_tier(score)

    # Sort highest risk first
    risks.sort(key=lambda r: r["risk_score"], reverse=True)
    return risks


def print_report(risks):
    print(f"{'ID':<6} {'Score':<6} {'Tier':<12} Description")
    print("-" * 90)
    for r in risks:
        print(f"{r['risk_id']:<6} {r['risk_score']:<6} {r['risk_tier']:<12} {r['risk_description']}")


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "risk_register.csv"
    risks = load_and_score(filepath)
    print_report(risks)
