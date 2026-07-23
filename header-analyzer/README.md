# Email Header Authentication & Phishing Detection Analyzer

A practice exercise in AI-assisted scripting — building a deterministic
phishing-detection tool from raw email headers using structured prompting,
without hand-writing the parsing logic myself.

## What it does

Parses a raw email header file (RFC 5322 format), extracts authentication
results and sender details, and applies a priority-ordered verdict table to
classify the email as legitimate, suspicious, or a likely spoof/phishing
attempt.

## Extracted fields

| Field | Source | Method |
|---|---|---|
| Sender IP | `Received-SPF:` (primary) or last `Received:` line (fallback) | `client-ip=` regex, or last bracketed IP |
| SPF result | last `Authentication-Results:` block | `spf=(\w+)` |
| DKIM result | last `Authentication-Results:` block | `dkim=(\w+)` |
| DMARC result | last `Authentication-Results:` block | `dmarc=(\w+)`, defaults to `none` if absent |
| Display name / domain | `From:` header | Compares display name against protected brand keywords vs. actual sending domain |

Line-folded headers (continuation lines starting with space/tab) are
unfolded before parsing, and the **last** occurrence of repeated headers is
used, since that reflects the most authoritative inbound edge server.

## Verdict logic (priority order, first match wins)

1. **CRITICAL_SPOOF** — SPF, DKIM, and DMARC all fail → `REJECT`
2. **HIGH_RISK_SPOOF** — DMARC fails, SPF fails/softfails, DKIM doesn't pass → `REJECT`
3. **HIGH_RISK_SPOOF** — no DMARC policy, but SPF and DKIM both fail → `REJECT`
4. **TAMPERED_OR_FORGED** — DKIM and DMARC fail (SPF may still pass) → `REJECT`
5. **LEGITIMATE_FORWARD** — SPF fails but DMARC passes (common in forwarding) → `DELIVER` (warn)
6. **PHISHING_IMPERSONATION** — display name spoofs a trusted brand, domain doesn't match → `QUARANTINE`
7. **INCONCLUSIVE** — SPF softfail/neutral/none → `DELIVER` (warn)
8. **LEGITIMATE** — SPF, DKIM, DMARC all pass → `DELIVER`
9. **UNCERTAIN** — fallback, no clean match → `DELIVER` (warn), manual review

## Usage

```bash
python3 header_analyzer.py header.txt
```

Outputs a JSON report, e.g.:

```json
{
  "sender_ip": "209.85.210.53",
  "spf_result": "pass",
  "dkim_result": "fail",
  "dmarc_result": "fail",
  "display_name": "",
  "actual_domain": "",
  "display_name_mismatch": false,
  "verdict": "TAMPERED_OR_FORGED",
  "recommended_action": "REJECT",
  "reasoning": "DKIM failed (body/headers altered in transit) and DMARC did not pass."
}
```

## Sample files included

- `header.txt` — a real-world spoofed sender example (SPF passes, DKIM/DMARC fail)
- `header_impersonation_example.txt` — a brand-impersonation example ("Microsoft Security Team" sent from an unrelated domain)

## Why this exercise matters

The real skill practiced here is turning email authentication concepts
(SPF/DKIM/DMARC and what each one actually proves) into a precise,
deterministic decision table *before* writing any prompt or code — including
catching logic gaps (like an early draft treating "DKIM pass" as automatically
safe even when SPF failed) and resolving priority conflicts between rules
before they become bugs.
