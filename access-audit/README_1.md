# User Access Audit Script

A practice exercise in AI-assisted scripting — using structured prompting to
turn a plain-English access review process into a working Python script,
without needing to hand-write the code myself.

## What it does

Reads a user access export (CSV) and flags accounts against three risk
conditions, then sorts flagged users into risk tiers.

**Input format:** `user_access_export.csv`

| Column | Example value |
|---|---|
| username | jsmith |
| last login date | 20260718 (YYYYMMDD) |
| admin status | Admin / User |
| mfa status | Enabled / Disabled |

## Conditions

- **C1 (Stale):** last login is 90+ days ago
- **C2 (Admin risk):** admin status is Admin, AND (C1 is true OR C3 is true)
- **C3 (MFA risk):** MFA status is Disabled

## Risk tiers

Users are flagged and sorted by how many conditions they meet:

- **Tier 1 (highest risk):** all 3 conditions true
- **Tier 2 (medium risk):** any 2 conditions true
- **Tier 3 (lowest risk):** exactly 1 condition true (C1 or C3 alone)

Note: C2 can never be true on its own — it always requires C1 or C3 to also
be true — so a user can never land in Tier 3 from C2 alone.

## Usage

```bash
python3 access_audit_v2.py user_access_export.csv
```

## Why this exercise matters

The real skill being practiced here isn't the Python — it's the process of
turning a vague idea ("find risky users") into a precise, unambiguous
specification an AI assistant can act on correctly the first time:

1. Define the goal in plain English
2. Pin down the exact input format, column names, and value formats
3. Write each rule as a complete, testable sentence
4. Resolve edge cases and logical overlaps *before* writing the prompt
5. Write one complete prompt combining data spec + logic
6. Run it, verify the output against hand-worked examples, and iterate

This mirrors real access-review work for compliance frameworks like SOC 2
and POPIA, where the ability to quickly script custom checks against messy,
inconsistently-formatted exports is a genuinely valuable skill.
