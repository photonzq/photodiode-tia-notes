"""Render the market-scan JSON (candidates, status/price, integrated TIAs,
application notes) into a Markdown report.

Usage
-----
python render_market_scan_md.py <market_scan.json> <market_scan.md>

The JSON is the single source of truth; the Markdown file is regenerated
from it every time, so edit the JSON and re-run.
"""
import json
import sys


def cell(value) -> str:
    """Format one table cell: lists joined, pipes and newlines escaped."""
    if value is None:
        return "not checked"
    if value == "":
        return ""
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(v) for v in value)
    return str(value).replace("|", "/").replace("\n", " ")


def table(rows, columns) -> list[str]:
    """Return Markdown table lines for the given rows and (key, header) columns."""
    lines = ["| " + " | ".join(h for _, h in columns) + " |",
             "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(cell(row.get(k)) for k, _ in columns) + " |")
    return lines


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        data = json.load(fh)

    out: list[str] = [f"# {data['title']}", ""]
    out += [f"Date seen for all prices and status labels: {data['date_seen']}. "
            f"State of this file: {data['state']}.", ""]
    for para in data.get("preamble", []):
        out += [para, ""]

    out += ["## A. Additional voltage-feedback op-amp candidates", ""]
    out += table(data["candidates"], [
        ("part", "Part"), ("maker", "Maker"), ("input_type", "Input"),
        ("gbw_MHz", "GBW (MHz)"), ("min_gain", "Min. stable gain (V/V)"),
        ("en", "e_n (nV/rtHz)"), ("in", "i_n (pA/rtHz)"), ("cin_pF", "C_in (pF)"),
        ("supply", "Supply"), ("swing", "Output swing"), ("slew", "Slew (V/us)"),
        ("packages", "Packages"), ("status", "Lifecycle"), ("price_1ku", "1ku price (USD)"),
        ("verdict", "Verdict"), ("datasheet_url", "Datasheet"), ("sources", "Sources")])
    out += ["", "### A2. Parts checked and rejected", ""]
    out += table(data["rejected"], [("part", "Part"), ("maker", "Maker"),
                                     ("reason", "Reason"), ("source", "Source")])
    if data.get("makers_checked"):
        out += ["", "### A3. Manufacturers checked", ""]
        out += table(data["makers_checked"], [("maker", "Maker"), ("checked", "What was checked"),
                                              ("result", "Result")])

    out += ["", "## B. Lifecycle status and 1ku price", ""]
    out += table(data["status_price"], [
        ("part", "Part"), ("maker", "Maker"), ("status", "Status"),
        ("price_1ku_usd", "1ku price (USD)"), ("price_basis", "Price basis"),
        ("packages", "Packages"), ("source", "Source"), ("notes", "Notes")])

    out += ["", "## C. Integrated TIAs and photodiode front ends", ""]
    out += table(data["tias"], [
        ("part", "Part"), ("maker", "Maker"), ("function", "Function"),
        ("transimpedance", "Transimpedance"), ("bandwidth", "Bandwidth"),
        ("noise", "Input-referred noise"), ("max_input", "Max. input current"),
        ("dc_cancel", "DC / ambient cancellation"), ("status", "Lifecycle"),
        ("price_1ku", "1ku price (USD)"), ("sources", "Sources")])

    out += ["", "## D. Application notes and references", "",
            "The documents themselves are not part of the public repository; the URL column gives each source.", ""]
    out += table(data["appnotes"], [
        ("target", "Topic"), ("title", "Title"), ("authors", "Author(s)"),
        ("publisher", "Publisher, doc. no."), ("year", "Year"), ("url", "URL"),
        ("local_file", "File name"), ("note", "Relevance")])

    if data.get("not_accessible"):
        out += ["", "## Sources not read directly", ""]
        out += table(data["not_accessible"], [("url", "URL"), ("reason", "Reason")])
    if data.get("open_items"):
        out += ["", "## Open items", ""]
        out += [f"- {item}" for item in data["open_items"]]
    out.append("")

    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print(f"wrote {dst}: {len(data['candidates'])} candidates, "
          f"{len(data['status_price'])} status rows, {len(data['tias'])} TIAs, "
          f"{len(data['appnotes'])} app notes")


if __name__ == "__main__":
    main()
