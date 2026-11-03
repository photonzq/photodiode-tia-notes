"""Fetch TI product pages and pull out lifecycle status, orderable part
numbers with their 1ku list prices and packages, and the parametric table.

Usage
-----
python ti_product_pages.py <out_json> <html_dir> PART [PART ...]

* Each page https://www.ti.com/product/<PART> is saved as <html_dir>/<PART>.html.
* The orderable data are the JSON objects embedded in the page that start
  with {"orderablePartNumber": ...}; "basePrice" is TI's price at the
  "baseQuantity" (1ku) break.
* The parametric table is read from the <ti-multicolumn-list-row> pairs.
* A one-second pause separates requests.
"""
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
ROW = re.compile(r"<ti-multicolumn-list-row[^>]*>\s*<ti-multicolumn-list-cell>\s*<span>(.*?)</span>"
                 r"\s*</ti-multicolumn-list-cell>\s*<ti-multicolumn-list-cell>\s*<span>(.*?)</span>",
                 re.S)


def fetch(url: str) -> tuple[int, str, str]:
    """Return (HTTP code, final URL, body text)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.geturl(), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, url, ""
    except Exception as err:  # network errors are recorded, not retried
        return -1, url, repr(err)


def orderables(html: str) -> list[dict]:
    """Decode every embedded {"orderablePartNumber": ...} object once."""
    dec = json.JSONDecoder()
    seen, out = set(), []
    for m in re.finditer(r'\{"orderablePartNumber"', html):
        try:
            obj, _ = dec.raw_decode(html, m.start())
        except ValueError:
            continue
        opn = obj.get("orderablePartNumber")
        if opn in seen:
            continue
        seen.add(opn)
        out.append({
            "opn": opn,
            "price_1ku": obj.get("basePrice"),
            "base_qty": obj.get("baseQuantity"),
            "package": obj.get("packaging"),
            "pins": obj.get("pins"),
            "status": obj.get("marketingStatusDescription"),
            "carrier": obj.get("packageCarrier"),
            "pack_qty": obj.get("packageQuantity"),
        })
    return out


def main() -> None:
    out_json, html_dir, parts = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3:]
    html_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for part in parts:
        code, final, html = fetch(f"https://www.ti.com/product/{part}")
        (html_dir / f"{part}.html").write_text(html, encoding="utf-8")
        status = re.search(r'"status"\s+content="([^"]+)"', html)
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        params = {}
        for name, value in ROW.findall(html):
            name = " ".join(re.sub(r"<[^>]+>", "", name).split())
            value = " ".join(re.sub(r"<[^>]+>", "", value).split())
            params.setdefault(name, value)
        result[part] = {
            "http": code, "final_url": final,
            "title": " ".join(title.group(1).split()) if title else None,
            "status": status.group(1) if status else None,
            "orderables": orderables(html), "params": params,
        }
        n = len(result[part]["orderables"])
        print(f"{part:12s} http={code} status={result[part]['status']} orderables={n}")
        time.sleep(1.0)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
