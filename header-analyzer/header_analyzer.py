"""
Email Header Authentication & Phishing Detection Analyzer
------------------------------------------------------------
Built from a full spec covering: line-folding, Authentication-Results
extraction (SPF/DKIM/DMARC), sender IP with primary/fallback logic,
display-name brand impersonation detection, and a deterministic
priority-ordered verdict table.

Usage:
    python3 header_analyzer.py header.txt
"""

import re
import sys
import json

LEGIT_BRAND_DOMAINS = {
    "microsoft": ["microsoft.com", "outlook.com", "office.com"],
    "paypal": ["paypal.com"],
    "apple": ["apple.com", "icloud.com"],
    "amazon": ["amazon.com"],
    "chase": ["chase.com"],
    "bank of america": ["bankofamerica.com"],
    "wells fargo": ["wellsfargo.com"],
    "google": ["google.com", "gmail.com"],
    "dropbox": ["dropbox.com"],
    "docusign": ["docusign.com", "docusign.net"],
    "fedex": ["fedex.com"],
    "ups": ["ups.com"],
}

PROTECTED_KEYWORDS = list(LEGIT_BRAND_DOMAINS.keys()) + [
    "ceo", "cfo", "it support", "security team", "helpdesk"
]


def unfold_headers(raw_text: str) -> str:
    """Join folded header lines (continuation lines start with space/tab)."""
    lines = raw_text.splitlines()
    joined = []
    for line in lines:
        if line.startswith((" ", "\t")) and joined:
            joined[-1] += " " + line.strip()
        else:
            joined.append(line)
    return "\n".join(joined)


def get_last_match_block(unfolded: str, header_name: str) -> str:
    """Return the content of the LAST occurrence of a header (case-insensitive)."""
    pattern = re.compile(rf"^{header_name}:(.*)$", re.IGNORECASE | re.MULTILINE)
    matches = pattern.findall(unfolded)
    return matches[-1].strip() if matches else ""


def extract_sender_ip(unfolded: str) -> str:
    # Primary: Received-SPF client-ip=
    spf_block = get_last_match_block(unfolded, "Received-SPF")
    if spf_block:
        m = re.search(r"client-ip=([\d.:a-fA-F]+)", spf_block)
        if m:
            return m.group(1)

    # Fallback: last bracketed IP on the bottom-most Received: line
    received_lines = re.findall(r"^Received:(.*)$", unfolded, re.IGNORECASE | re.MULTILINE)
    if received_lines:
        last_received = received_lines[-1]
        ip_matches = re.findall(r"\[([\d.:a-fA-F]+)\]", last_received)
        if ip_matches:
            return ip_matches[-1]

    return "not_found"


def extract_auth_results(unfolded: str):
    auth_block = get_last_match_block(unfolded, "Authentication-Results")

    def find(field, default="not_found"):
        m = re.search(rf"{field}=(\w+)", auth_block)
        return m.group(1).lower() if m else default

    spf = find("spf")
    dkim = find("dkim")
    dmarc = find("dmarc", default="none")  # spec: missing dmarc = "none"
    return spf, dkim, dmarc


def extract_display_name_and_domain(unfolded: str):
    from_block = get_last_match_block(unfolded, "From")
    display_name = ""
    domain = ""

    m = re.search(r'^\s*"?([^"<]*)"?\s*<([^>]+)>', from_block)
    if m:
        display_name = m.group(1).strip()
        email = m.group(2).strip()
    else:
        email = from_block.strip()

    if "@" in email:
        domain = email.split("@")[-1].strip().lower()

    return display_name, domain


def check_display_name_mismatch(display_name: str, domain: str) -> bool:
    name_lower = display_name.lower()
    for keyword in PROTECTED_KEYWORDS:
        if keyword in name_lower:
            legit_domains = LEGIT_BRAND_DOMAINS.get(keyword, [])
            if legit_domains and domain not in legit_domains:
                return True
            if not legit_domains:
                # generic keywords like "ceo"/"helpdesk" have no fixed domain list;
                # flag as mismatch since there's no "legitimate" domain to compare to
                return True
    return False


def determine_verdict(spf, dkim, dmarc, display_name_mismatch):
    if dmarc == "fail" and spf == "fail" and dkim == "fail":
        return ("CRITICAL_SPOOF", "REJECT",
                "All three authentication mechanisms (SPF, DKIM, DMARC) failed; sender is completely unverified.")

    if dmarc == "fail" and (spf == "fail" or spf == "softfail") and dkim != "pass":
        return ("HIGH_RISK_SPOOF", "REJECT",
                "DMARC failed due to SPF failure and DKIM did not pass alignment.")

    if spf == "fail" and dkim == "fail" and dmarc == "none":
        return ("HIGH_RISK_SPOOF", "REJECT",
                "No DMARC policy is set, but both SPF and DKIM explicitly failed.")

    if dkim == "fail" and dmarc == "fail":
        return ("TAMPERED_OR_FORGED", "REJECT",
                "DKIM failed (body/headers altered in transit) and DMARC did not pass.")

    if spf == "fail" and dmarc == "pass":
        return ("LEGITIMATE_FORWARD", "DELIVER",
                "SPF failed (common in forwarded email), but DKIM is passing and aligning with DMARC.")

    if display_name_mismatch:
        return ("PHISHING_IMPERSONATION", "QUARANTINE",
                "Display name impersonates a trusted brand, but the sending domain is not an authorized domain for that brand.")

    if spf in ("softfail", "neutral", "none"):
        return ("INCONCLUSIVE", "DELIVER (with warning)",
                "SPF gave no explicit authorization or a soft failure; treat with suspicion but do not block.")

    if spf == "pass" and dkim == "pass" and dmarc == "pass":
        return ("LEGITIMATE", "DELIVER",
                "All authentication checks (SPF, DKIM, DMARC) passed and aligned; email is authentic.")

    return ("UNCERTAIN", "DELIVER (with warning)",
            "No clear failure pattern matched, but results are not a clean pass; manual review advised.")


def analyze(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()

    unfolded = unfold_headers(raw_text)

    sender_ip = extract_sender_ip(unfolded)
    spf, dkim, dmarc = extract_auth_results(unfolded)
    display_name, domain = extract_display_name_and_domain(unfolded)
    mismatch = check_display_name_mismatch(display_name, domain)

    verdict, action, reasoning = determine_verdict(spf, dkim, dmarc, mismatch)

    return {
        "sender_ip": sender_ip,
        "spf_result": spf,
        "dkim_result": dkim,
        "dmarc_result": dmarc,
        "display_name": display_name,
        "actual_domain": domain,
        "display_name_mismatch": mismatch,
        "verdict": verdict,
        "recommended_action": action,
        "reasoning": reasoning,
    }


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "header.txt"
    result = analyze(filepath)
    print(json.dumps(result, indent=2))
