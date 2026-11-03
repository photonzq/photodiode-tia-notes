"""Merge a JSON fragment into the market-scan JSON.

Usage
-----
python merge_fragment.py <market_scan.json> <fragment.json>

Fragment keys:
* "replace": {section: value}  - the section is replaced wholesale
  (e.g. candidates, rejected, makers_checked, tias, appnotes, not_accessible,
  open_items, state, preamble).
* "upsert": {section: [rows]}  - rows replace existing rows with the same
  "part" (or "local_file"/"url" when there is no "part"); others are appended.
"""
import json
import sys


def key(row: dict):
    return row.get("part") or row.get("local_file") or row.get("url") or row.get("title")


def main() -> None:
    scan_path, frag_path = sys.argv[1], sys.argv[2]
    with open(scan_path, encoding="utf-8") as fh:
        scan = json.load(fh)
    with open(frag_path, encoding="utf-8") as fh:
        frag = json.load(fh)
    for section, value in frag.get("replace", {}).items():
        scan[section] = value
    for section, rows in frag.get("upsert", {}).items():
        current = scan.setdefault(section, [])
        index = {key(r): i for i, r in enumerate(current)}
        for row in rows:
            if key(row) in index:
                current[index[key(row)]] = row
            else:
                current.append(row)
    with open(scan_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(scan, fh, indent=1, ensure_ascii=False)
    print("merged:", ", ".join(list(frag.get("replace", {})) + list(frag.get("upsert", {}))))


if __name__ == "__main__":
    main()
