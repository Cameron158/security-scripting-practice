# Multi-Format Asset Inventory Merger

A practice exercise in AI-assisted scripting — combining asset data exported
from three different systems, in three different formats, into one
deduplicated, conflict-flagged inventory.

## The problem this mirrors

Real IT/security environments rarely have one source of truth for assets.
A device management (MDM) tool, an internal IT register, and a manual
spreadsheet often each hold a partial, inconsistently-formatted view of the
same physical devices. This script merges them using a normalized matching
key, while surfacing — rather than silently resolving — any conflicting
details between sources.

## Input files

| File | Format | Columns/Fields |
|---|---|---|
| `it_asset_register.csv` | CSV (internal IT tool) | `asset_tag, hostname, assigned_user, status, serial_number` |
| `mdm_export.json` | JSON (MDM/device management export) | `serialNumber, deviceName, owner, complianceStatus` |
| `manual_asset_tracker.xlsx` | Excel (manual spreadsheet) | `Serial No, Device Name, Assigned To, Status` |

## Matching logic

Assets are matched across files using their **serial number**, normalized as:

1. Convert to lowercase
2. Replace all punctuation with spaces
3. Collapse multiple spaces into a single space

Example: `KP-SN-1007` and `kp sn 1007` both normalize to `kp sn 1007` and are
correctly treated as the same asset.

The **original, non-normalized serial number** (as first seen in the source
files) is preserved for the final report, since normalized text isn't
meant to be human-readable.

## Conflict handling

If `assigned_user` or `status` differs across sources for the same asset,
the script does **not** silently pick one value. Instead:

- The merged inventory shows all conflicting values separated by `/`
- The asset is added to a separate **conflicts needing review** list, with
  each source's value shown explicitly, so a human can investigate and
  resolve it

This deliberately avoids hiding a real risk — e.g. an asset marked "Active"
in one system but "Decommissioned" in another is exactly the kind of gap a
security or asset review needs to catch, not paper over.

## Usage

\`\`\`bash
python3 asset_merger.py it_asset_register.csv mdm_export.json manual_asset_tracker.xlsx
\`\`\`

Outputs:
1. A merged inventory table — one row per unique asset, with a "Found In"
