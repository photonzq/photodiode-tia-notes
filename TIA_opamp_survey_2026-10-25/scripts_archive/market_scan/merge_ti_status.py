"""Merge TI lifecycle/price rows (from ti_product_pages.py output) into the
market-scan JSON, replacing any earlier TI rows for the same parts.

Usage
-----
python merge_ti_status.py <ti_pages.json> <market_scan.json> PART [PART ...]

For each part: page-level status, 1ku price range over orderables (active
ones first), package list, and a note naming orderables that are not ACTIVE.
"""
import json
import sys


def row(part: str, page: dict, date_seen: str) -> dict:
    url = f"https://www.ti.com/product/{part}"
    if page["http"] != 200:
        return {"part": part, "maker": "Texas Instruments",
                "status": f"no TI product page (HTTP {page['http']}); not offered",
                "price_1ku_usd": "n/a", "price_basis": "n/a", "packages": "n/a",
                "source": url, "date_seen": date_seen, "notes": ""}
    ords = page["orderables"]
    active = [o for o in ords if o["status"] == "ACTIVE" and o["price_1ku"] is not None]
    pool = active or [o for o in ords if o["price_1ku"] is not None]
    if pool:
        lo = min(pool, key=lambda o: o["price_1ku"])
        hi = max(pool, key=lambda o: o["price_1ku"])
        price = (f"{lo['price_1ku']:.2f} ({lo['opn']})" if lo is hi or lo["price_1ku"] == hi["price_1ku"]
                 else f"{lo['price_1ku']:.2f} ({lo['opn']}) to {hi['price_1ku']:.2f} ({hi['opn']})")
    else:
        price = "none listed"
    pkgs = sorted({f"{o['package']}-{o['pins']}".replace("DIESALE (Y)-0", "bare die (Y)") for o in ords})
    odd = [f"{o['opn']} {o['status']}" for o in ords if o["status"] != "ACTIVE"]
    notes = ("non-active orderables: " + ", ".join(odd)) if odd else ""
    if page["status"] == "PREVIEW":
        notes = ("product page status PREVIEW (pre-production); only orderable is the X-prefixed "
                 "pre-production part. " + notes).strip()
    return {"part": part, "maker": "Texas Instruments", "status": page["status"],
            "price_1ku_usd": price, "price_basis": "TI list price at 1ku break, per orderable",
            "packages": "; ".join(pkgs), "source": url + " (orderable data embedded in page)",
            "date_seen": date_seen, "notes": notes}


def main() -> None:
    ti_json, scan_json, parts = sys.argv[1], sys.argv[2], sys.argv[3:]
    with open(ti_json, encoding="utf-8") as fh:
        pages = json.load(fh)
    with open(scan_json, encoding="utf-8") as fh:
        scan = json.load(fh)
    new_rows = [row(p, pages[p], scan["date_seen"]) for p in parts]
    keep = [r for r in scan["status_price"] if r["part"] not in set(parts)]
    scan["status_price"] = new_rows + keep
    with open(scan_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(scan, fh, indent=1, ensure_ascii=False)
    print(f"merged {len(new_rows)} TI rows; {len(keep)} other rows kept")


if __name__ == "__main__":
    main()
