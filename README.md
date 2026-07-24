# Security Scripting Practice

A collection of hands-on exercises in AI-assisted scripting for cybersecurity
and GRC work — using structured prompting to turn plain-English security and
compliance tasks into working Python scripts, without needing to hand-write
or fully learn a programming language.

## Why this repo exists

A recurring theme in cybersecurity and GRC work is dealing with raw data in
inconsistent formats — CSV exports, log files, email headers — from
different systems, and needing to quickly build custom tools to parse,
score, and report on that data. This repo demonstrates that skill: not
memorized programming, but the ability to precisely specify a problem well
enough that an AI coding assistant can solve it correctly, plus the ability
to read the resulting output (and errors) critically enough to catch bugs
and logic gaps.

Each exercise follows the same disciplined process:

1. Define the goal in plain English
2. Pin down the exact input format, column/field names, and value formats
3. Write each rule as a complete, unambiguous sentence
4. Resolve edge cases and logical conflicts *before* writing the prompt
5. Write one complete, self-contained prompt combining data spec + logic
6. Run it, verify the output against hand-worked examples, and iterate

## Exercises

| Folder | Description |
|---|---|
| [`access-audit/`](./access-audit) | Flags stale user accounts, admin + low-activity risk, and missing MFA from a user access export, sorted into risk tiers |
| [`header-analyzer/`](./header-analyzer) | Parses raw email headers to extract sender IP and SPF/DKIM/DMARC results, detects brand-impersonation display names, and applies a deterministic phishing verdict table |
| [`risk-scorer/`](./risk-scorer) | Automates risk register scoring (likelihood × impact) and sorts findings into Low/Medium/Medium-High/High tiers |
| [`multi-format_asset_inventory_manager/`](./multi-format_asset_inventory_manager) | Merges asset exports from a CSV (IT register), JSON (MDM tool), and Excel (manual tracker) into one deduplicated inventory, normalizing serial numbers as the matching key and flagging cross-source conflicts (assigned user, status) for human review |

More exercises will be added as this practice continues (planned: compliance evidence checklist generator, breach notification timer, data retention checker, vendor risk questionnaire scorer,
network scan diff tool, and a chat export keyword flagger).

## Skills demonstrated

- Translating ambiguous, real-world requests into precise technical specifications
- Identifying and resolving logical edge cases and conflicting rules before implementation
- Reading and debugging real errors (e.g. CSV parsing issues, date format mismatches)
- Structuring prompts with explicit input formats, field names, and deterministic logic
- Applying the output to real GRC/security workflows (e.g. reused directly in the
  [Khaya Payroll POPIA & SOC 2 readiness project](https://github.com/YOUR-USERNAME/khaya-payroll))

## How to run any exercise

Each folder is self-contained with its own script, sample data, and README.
General pattern:

```bash
python3 <script_name>.py <sample_input_file>
```

See each folder's own README for exact usage and logic details.

---

*This is a self-directed learning portfolio. Scripts use mock/fictional data
throughout and are not connected to any real company's systems.*
