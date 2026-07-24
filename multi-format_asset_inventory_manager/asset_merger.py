"""
Multi-Format Asset Inventory Merger
--------------------------------------
Built from spec:

Inputs:
  - it_asset_register.csv  : asset_tag, hostname, assigned_user, status, serial_number
  - mdm_export.json        : serialNumber, deviceName, owner, complianceStatus
  - manual_asset_tracker.xlsx : Serial No, Device Name, Assigned To, Status

Matching key: serial number, normalized as:
  1. lowercase
  2. replace punctuation with spaces
  3. collapse multiple spaces into one

Conflict handling: if assigned_user or status differs across sources for the
same asset, flag it for human review rather than auto-resolving.

Output:
  1. Merged inventory - one row per unique asset, showing ORIGINAL
     (non-normalized) serial number as it appeared in its first-seen source.
  2. Separate conflicts list - assets where sources disagree on
     assigned user or status.
"""

import csv
import json
import re
import sys
import openpyxl


def normalize_serial(serial: str) -> str:
    s = serial.lower()
    s = re.sub(r"[^\w\s]", " ", s)   # punctuation -> space
    s = re.sub(r"\s+", " ", s)       # collapse multiple spaces
    return s.strip()


def load_csv(filepath: str):
    records = []
    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            records.append({
                "source": "CSV (IT Asset Register)",
                "serial_original": row["serial_number"],
                "device_name": row["hostname"],
                "assigned_user": row["assigned_user"],
                "status": row["status"],
            })
    return records


def load_json(filepath: str):
    records = []
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    for row in data:
        records.append({
            "source": "JSON (MDM Export)",
            "serial_original": row["serialNumber"],
            "device_name": row["deviceName"],
            "assigned_user": row["owner"],
            "status": row["complianceStatus"],
        })
    return records


def load_xlsx(filepath: str):
    records = []
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    for row in rows[1:]:
        row_dict = dict(zip(headers, row))
        records.append({
            "source": "Excel (Manual Tracker)",
            "serial_original": row_dict["Serial No"],
            "device_name": row_dict["Device Name"],
            "assigned_user": row_dict["Assigned To"],
            "status": row_dict["Status"],
        })
    return records


def merge_assets(all_records):
    assets = {}  # normalized_serial -> asset info
    order = []   # preserve first-seen order

    for rec in all_records:
        norm = normalize_serial(rec["serial_original"])
        if norm not in assets:
            assets[norm] = {
                "serial_display": rec["serial_original"],  # first-seen original format
                "entries": [],
            }
            order.append(norm)
        assets[norm]["entries"].append(rec)

    merged_rows = []
    conflicts = []

    for norm in order:
        asset = assets[norm]
        entries = asset["entries"]
        sources = [e["source"] for e in entries]

        device_names = {e["device_name"] for e in entries}
        assigned_users = {e["assigned_user"] for e in entries}
        statuses = {e["status"] for e in entries}

        merged_rows.append({
            "serial_number": asset["serial_display"],
            "device_name": next(iter(device_names)),
            "assigned_user": " / ".join(assigned_users) if len(assigned_users) > 1 else next(iter(assigned_users)),
            "status": " / ".join(statuses) if len(statuses) > 1 else next(iter(statuses)),
            "found_in": ", ".join(sources),
        })

        if len(assigned_users) > 1 or len(statuses) > 1:
            conflict_detail = {
                "serial_number": asset["serial_display"],
                "conflicting_fields": [],
            }
            if len(assigned_users) > 1:
                conflict_detail["conflicting_fields"].append({
                    "field": "assigned_user",
                    "values": [{"source": e["source"], "value": e["assigned_user"]} for e in entries]
                })
            if len(statuses) > 1:
                conflict_detail["conflicting_fields"].append({
                    "field": "status",
                    "values": [{"source": e["source"], "value": e["status"]} for e in entries]
                })
            conflicts.append(conflict_detail)

    return merged_rows, conflicts


def print_report(merged_rows, conflicts):
    print("=" * 100)
    print("MERGED ASSET INVENTORY")
    print("=" * 100)
    print(f"{'Serial':<14} {'Device':<16} {'Assigned To':<40} {'Status':<25} Found In")
    print("-" * 130)
    for r in merged_rows:
        print(f"{r['serial_number']:<14} {r['device_name']:<16} {r['assigned_user']:<40} {r['status']:<25} {r['found_in']}")

    print(f"\nTotal unique assets: {len(merged_rows)}")

    print("\n" + "=" * 100)
    print(f"CONFLICTS NEEDING REVIEW ({len(conflicts)})")
    print("=" * 100)
    if not conflicts:
        print("No conflicts found.")
    for c in conflicts:
        print(f"\nSerial: {c['serial_number']}")
        for field_conflict in c["conflicting_fields"]:
            print(f"  Field: {field_conflict['field']}")
            for v in field_conflict["values"]:
                print(f"    - {v['source']}: {v['value']}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "it_asset_register.csv"
    json_path = sys.argv[2] if len(sys.argv) > 2 else "mdm_export.json"
    xlsx_path = sys.argv[3] if len(sys.argv) > 3 else "manual_asset_tracker.xlsx"

    all_records = load_csv(csv_path) + load_json(json_path) + load_xlsx(xlsx_path)
    merged_rows, conflicts = merge_assets(all_records)
    print_report(merged_rows, conflicts)
