"""
Access Audit Script v2
-----------------------
Built from spec:

Input: user_access_export.csv
Columns: username, last login date (YYYYMMDD), admin status (Admin/User),
         mfa status (Enabled/Disabled)

Conditions:
  C1 = last login date >= 90 days ago
  C2 = admin status == Admin AND (C1 OR C3)
  C3 = mfa status == Disabled

Risk tiers (by count of TRUE conditions):
  Tier 1 = exactly one of C1/C3 true (C2 can't be true alone by definition)
  Tier 2 = exactly two conditions true
  Tier 3 = all three conditions true
"""

import csv
import sys
from datetime import datetime, date

STALE_DAYS = 90
TODAY = date(2026, 7, 22)  # fixed for reproducible practice runs


def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y%m%d").date()


def load_users(filepath: str):
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def evaluate(user, today: date):
    last_login = parse_date(user["last login date"])
    days_since = (today - last_login).days

    c1 = days_since >= STALE_DAYS
    c3 = user["mfa status"].strip().lower() == "disabled"
    c2 = (user["admin status"].strip().lower() == "admin") and (c1 or c3)

    conditions_true = sum([c1, c2, c3])

    if conditions_true == 3:
        tier = 1  # highest risk
    elif conditions_true == 2:
        tier = 2
    elif conditions_true == 1:
        tier = 3  # lowest
    else:
        tier = None  # no conditions met, not flagged

    return {
        "username": user["username"],
        "days_since_login": days_since,
        "c1_stale": c1,
        "c2_admin_risk": c2,
        "c3_mfa_disabled": c3,
        "conditions_true": conditions_true,
        "tier": tier,
    }


def run_audit(filepath: str, today: date):
    users = load_users(filepath)
    results = [evaluate(u, today) for u in users]
    flagged = [r for r in results if r["tier"] is not None]
    flagged.sort(key=lambda r: r["tier"])  # Tier 1 (highest risk) first
    return flagged


def print_report(flagged):
    if not flagged:
        print("No users flagged.")
        return

    tier_labels = {1: "TIER 1 - HIGHEST RISK", 2: "TIER 2 - MEDIUM RISK", 3: "TIER 3 - LOW RISK"}
    current_tier = None

    for r in flagged:
        if r["tier"] != current_tier:
            current_tier = r["tier"]
            print(f"\n=== {tier_labels[current_tier]} ===")
        flags = []
        if r["c1_stale"]:
            flags.append(f"C1 stale ({r['days_since_login']}d)")
        if r["c2_admin_risk"]:
            flags.append("C2 admin-risk")
        if r["c3_mfa_disabled"]:
            flags.append("C3 MFA disabled")
        print(f"  {r['username']}: {', '.join(flags)}")

    print(f"\nTotal flagged: {len(flagged)}")


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "user_access_export.csv"
    flagged = run_audit(filepath, TODAY)
    print_report(flagged)
