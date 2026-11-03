# market_scan scripts

All paths are passed as arguments; run from any working directory.

| Script | Purpose | Typical call |
|---|---|---|
| `ti_product_pages.py` | Fetch `https://www.ti.com/product/<PART>` pages; extract status, orderables with 1ku prices and packages, parametric table | `python ti_product_pages.py <out.json> <html_dir> OPA855 OPA858 ...` |
| `summarize_ti_pages.py` | Print status, 1ku price range, packages and key parametrics from that JSON | `python summarize_ti_pages.py <ti_pages.json>` |
| `merge_ti_status.py` | Write TI status/price rows into `data/market_scan.json` | `python merge_ti_status.py <ti_pages.json> <market_scan.json> PART ...` |
| `merge_fragment.py` | Merge a JSON fragment (replace or upsert sections) into `data/market_scan.json` | `python merge_fragment.py <market_scan.json> <fragment.json>` |
| `render_market_scan_md.py` | Regenerate `data/market_scan.md` from `data/market_scan.json` | `python render_market_scan_md.py <market_scan.json> <market_scan.md>` |
| `pdf_first_page_info.py` | Print metadata and opening text of page 1 of PDFs (identification only) | `python pdf_first_page_info.py 300 <pdf> ...` |

Interpreter: Python 3.13 with NumPy; PyMuPDF is needed only for `pdf_first_page_info.py`.
