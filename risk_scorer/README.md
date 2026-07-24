# Risk Register Auto-Scorer

A practice exercise in AI-assisted scripting — turning a manual risk-scoring
process into an automated script through structured prompting.

## What it does

Reads a risk register (CSV), calculates a numeric risk score for each risk,
and sorts them into four risk tiers, output highest-risk-first.

## Input format

**File:** `risk_register.csv`

| Column | Example |
|---|---|
| risk_id | R001 |
| risk_description | Unauthorized access to payroll database due to weak password policy |
| likelihood_rating | 4 (scale 1-5) |
| impact_rating | 5 (scale 1-5) |

## Scoring logic

**Risk Score = likelihood_rating × impact_rating** (range: 1-25)

| Score range | Tier |
|---|---|
| 1-6 | Low |
| 7-12 | Medium |
| 13-18 | Medium-High |
| 19-25 | High |

## Usage

```bash
python3 risk_scorer.py risk_register.csv
```

Outputs a table sorted from highest to lowest risk score.

## Real bug caught during testing

An early test run crashed with:
```
ValueError: invalid literal for int() with base 10: ' old records never purged'
```

Cause: one risk description contained an unquoted comma (`"...not enforced,
old records never purged"`), which split it across two CSV columns and
shifted every value after it. Fixed by quoting the field in the source CSV.
This is one of the most common real-world CSV bugs — any text field
containing a comma must be quoted, or every column after it shifts.

## Why this exercise matters

This script reuses the exact Low/Medium/Medium-High/High risk-rating scale
and multiplication-based scoring method from the Khaya Payroll POPIA/SOC 2
GRC portfolio project, making it a genuinely reusable tool rather than just
a standalone exercise.
