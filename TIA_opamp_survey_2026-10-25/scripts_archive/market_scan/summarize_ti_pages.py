"""Summarise the output of ti_product_pages.py: status, 1ku price range over
orderables, packages, and selected parametric fields.

Usage
-----
python summarize_ti_pages.py <ti_pages.json> [param-substring ...]

Parametric fields whose name contains any of the given substrings
(case-insensitive) are printed; default: GBW, Vn, Acl, Slew, supply, Input type.
"""
import json
import sys


def main() -> None:
    with open(sys.argv[1], encoding="utf-8") as fh:
        pages = json.load(fh)
    keys = [k.lower() for k in (sys.argv[2:] or
            ["gbw", "vn at", "acl", "slew", "total supply", "input type", "architecture",
             "rating", "transimpedance", "bandwidth", "noise", "input current"])]
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for part, page in pages.items():
        ords = page["orderables"]
        prices = [o["price_1ku"] for o in ords if o["price_1ku"] is not None]
        pkgs = sorted({f"{o['package']}-{o['pins']}" for o in ords})
        stats = sorted({str(o["status"]) for o in ords})
        rng = f"{min(prices):.3f}-{max(prices):.3f}" if prices else "none"
        print(f"== {part}: http {page['http']}, page status {page['status']}, "
              f"orderable status {stats}, 1ku {rng}, packages {pkgs}")
        for o in ords:
            print(f"     {o['opn']:22s} {o['price_1ku']} {o['package']}-{o['pins']} "
                  f"{o['status']} {o['carrier']} x{o['pack_qty']}")
        sel = {k: v for k, v in page["params"].items() if any(s in k.lower() for s in keys)}
        if sel:
            print("     params:", "; ".join(f"{k} = {v}" for k, v in sel.items()))


if __name__ == "__main__":
    main()
