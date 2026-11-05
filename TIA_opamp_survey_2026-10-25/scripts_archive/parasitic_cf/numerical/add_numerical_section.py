"""Insert Section G.14 (field solutions) into Appendix G and make the edits that refer to it.

Usage:
    python add_numerical_section.py <note.md> <sha256 prefix of the note> [--dry-run <section.md>]

Why this script exists
----------------------
Every number of Section G.14 comes from the records that the numerical scripts write into
data/parasitic_cf/numerical/ (checks.json, closed_forms_2d.json, resistor_3d.json, opa846_3d.json,
field_regions.json).  This script reads them and fills the placeholders <<name>> of
numerical_section_template.md, so the note cannot disagree with the records.  It also makes the
edits elsewhere in the note that the new section implies: the old Section G.14 becomes G.15,
Table G.6 quotes the field solution where it gave only a direction or an estimate, Appendices C, D
and E mention the new results, references and files, Sections G.1, G.8 and G.11 point to the new
values, and Section G.13.5 and Appendix C say that the bench board's layout is not recorded and may
be a poor one, so its 0.3 pF is no benchmark.  Each edit replaces a text that must
occur exactly once, and the note's SHA-256 is checked first, so the edits apply only to the version
they were written for.  With --dry-run the filled section is written to a file for reading, the whole
edited note to the same name with the suffix .note.md, and the note itself is not touched; the hash
check and every edit run as in a real application, so a dry run that succeeds shows exactly what the
real one will write.

Derived quantities (each computed in values() below, with its formula next to it):
  * extrapolation with a fixed order: the two finest meshes and C(r) = C_inf + k r^p with p given
    give C_inf = C3 - (C2 - C3) / ((r2/r3)^p - 1);
  * enclosure extrapolation with q = 1: the two largest enclosures and C(R) = C_inf + k/R give
    C_inf = (R3 C3 - R2 C2) / (R3 - R2);
  * local orders of the extrusion check against its exact value: e_i = C_i/C_exact - 1 and
    p_local = ln(e_i / e_(i+1)) / ln(r_i / r_(i+1)).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
NOTE_DIR = HERE.parents[3]
DATA = NOTE_DIR / "data" / "parasitic_cf" / "numerical"
TEMPLATE = HERE.parent / "numerical_section_template.md"
sys.path.insert(0, str(HERE.parents[4] / "pcbcap"))
from pcbcap.constants import EPS0          # noqa: E402  fF/mm, derived in pcbcap/constants.py


def load(name: str) -> dict:
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def sci(v: float, digits: int = 1) -> str:
    """$a\\times10^{b}$ for a small number (the note's style for relative errors)."""
    if v == 0:
        return "0"
    e = int(math.floor(math.log10(abs(v))))
    a = v / 10 ** e
    if round(a, digits) >= 10:          # 9.96 printed with one digit would read 10.0
        a, e = a / 10, e + 1
    return rf"${a:.{digits}f}\times10^{{{e}}}$"


def f(v: float, d: int = 1) -> str:
    return f"{v:.{d}f}"


def fs(v: float, d: int = 2) -> str:
    """Signed, with a true minus sign as in the note."""
    s = f"{v:+.{d}f}"
    return s.replace("-", "−")


def sig(v: float, n: int = 6) -> str:
    """n significant digits, fixed-point (the closed forms span 1e-3 to 5)."""
    if v == 0:
        return "0"
    d = max(n - 1 - int(math.floor(math.log10(abs(v)))), 0)
    return f"{v:.{d}f}"


def fixed_order_limit(r: list[float], C: list[float], p: float) -> float:
    """C_inf from the two finest of three meshes with the order p fixed (module docstring)."""
    r2, r3 = r[1], r[2]
    C2, C3 = C[1], C[2]
    return C3 - (C2 - C3) / ((r2 / r3) ** p - 1.0)


LAYS846 = ("double_sided", "under_body", "around")     # the OPA846 layouts (a), (b), (c) of Figure 51


# ================================================================================================
def values() -> dict:
    """Every number the section prints, keyed by its placeholder name."""
    ck, cf, r3, r8 = load("checks.json"), load("closed_forms_2d.json"), load("resistor_3d.json"), load("opa846_3d.json")
    V: dict[str, str] = {}

    # --- Table G.9: the package's checks -------------------------------------------------------
    nice = {"strips_free_space": "Coplanar strips in free space (2-D)",
            "strips_on_interface": "Coplanar strips on an air–FR-4 interface (2-D)",
            "mirror_vs_full": "Half domain (Eq. (G.53)) against the full domain (Eq. (G.52))",
            "layered_plates_2d": "Plates with two dielectric layers (2-D)",
            "layered_plates_3d": "Plates with two dielectric layers (3-D)",
            "floating_slab": "Floating conductor between plates (2-D)",
            "film_linear_block": "Block with the film's linear potential (2-D)",
            "extrusion_3d_vs_2d": "3-D model uniform along $y$ against the 2-D model",
            "symmetry_declaration": "A false symmetry is rejected",
            "resistor_section_shares": "Shares of the materials add up to $C_{F,\\mathrm{par}}$"}
    what = {"strips_free_space": "edge singularities, open enclosure",
            "strips_on_interface": "dielectric interface through the conductors",
            "mirror_vs_full": "the even and odd drives on a half",
            "layered_plates_2d": "continuity of the normal displacement",
            "layered_plates_3d": "the three-dimensional mesh and assembly",
            "floating_slab": "one shared unknown, zero net charge",
            "film_linear_block": "the film's prescribed potential, Eq. (G.28)",
            "extrusion_3d_vs_2d": "convergence and Eq. (G.56) as used for every 3-D result",
            "symmetry_declaration": "the check that guards Eq. (G.53)",
            "resistor_section_shares": "the resistor builder, film and shares"}
    rows = []
    for k in nice:
        c = ck.get(k)
        if not c:
            continue
        if k == "symmetry_declaration":
            res, tol = "rejected", "—"
        else:
            res = sci(abs(c["rel_error"])) if abs(c["rel_error"]) > 1e-16 else "below $10^{-15}$"
            tol = sci(c["tolerance"], 0 if k != "extrusion_3d_vs_2d" else 1)
            if k == "extrusion_3d_vs_2d":
                tol += " (the reported error)"
        rows.append(f"| {nice[k]} | {what[k]} | {res} | {tol} |")
    V["table_checks"] = "\n".join(rows)
    ex = ck.get("extrusion_3d_vs_2d", {})
    exd = ex.get("data", {})
    V["extr_order"] = f(exd.get("order", float("nan")), 2)
    V["extr_diff"] = sci(abs(ex.get("rel_error", float("nan"))))
    V["extr_reported"] = sci(ex.get("tolerance", float("nan")))
    if exd:
        e = [v / exd["reference"] - 1.0 for v in exd["values"]]        # errors against the exact value
        rr = exd["refine"]
        ratios = [e[i] / e[i + 1] for i in range(2)]
        locs = [math.log(ratios[i]) / math.log(rr[i] / rr[i + 1]) for i in range(2)]
        V["extr_ratio1"], V["extr_ratio2"] = f(ratios[0], 2), f(ratios[1], 2)
        V["extr_local1"], V["extr_local2"] = f(locs[0], 2), f(locs[1], 2)

    # --- Table G.10: the closed forms ------------------------------------------------------------
    cf_rows = [("G25_pads_halfplane", "(G.25)", "Pads on the edge of a half-plane"),
               ("G27_cut_layer", "(G.27)", "Pads on a 1.6-mm layer with its far face cut"),
               ("G28_block_upper", "(G.28)", "Body with the slots filled (upper bound)"),
               ("G32_block_lower", "(G.32)", "Body with the film's potential released (lower bound)"),
               ("G33_air_no_film", "(G.33)", "Air above the part, conductors only (no film potential)"),
               ("G38_air_with_film", "(G.38)", "Air above the part with the film's potential"),
               ("G41_plane_0p10", "(G.41)", "Pads over a plane 0.10 mm below (mutual)"),
               ("G41_plane_0p20", "(G.41)", "Pads over a plane 0.20 mm below (mutual)"),
               ("G41_plane_0p36", "(G.41)", "Pads over a plane 0.36 mm below (mutual)"),
               ("G43_guard", "(G.43)", "Guard strip 0.2 mm wide in the gap (mutual)"),
               ("G45_pins_no_middle", "(G.45)", "Pins 1 and 3, pin 2 removed"),
               ("G46_pins_wall", "(G.46)", "Pins 1 and 3, pin 2 a floating wall")]
    rows, rels = [], {}
    for key, eq, desc in cf_rows:
        c = cf.get(key)
        if not c:
            continue
        rel = abs(c["rel_error"])
        rels[key] = rel
        rows.append(f"| Eq. {eq} | {desc} | {sig(c['closed'])} | {sig(c['numeric'])} | "
                    f"{sci(rel) if rel > 1e-12 else 'rounding (' + sci(rel) + ')'} |")
    V["table_closed"] = "\n".join(rows)
    main_rows = [k for k in rels if k in ("G25_pads_halfplane", "G27_cut_layer", "G32_block_lower", "G33_air_no_film",
                                          "G38_air_with_film", "G45_pins_no_middle", "G46_pins_wall")]
    V["cf_min"], V["cf_max"] = sci(min(rels[k] for k in main_rows)), sci(max(rels[k] for k in main_rows))
    g41 = [cf[k] for k in ("G41_plane_0p10", "G41_plane_0p20", "G41_plane_0p36") if k in cf]
    V["g41_max"] = sci(max(abs(c["rel_error"]) for c in g41))
    V["g41_abs"] = sci(max(abs(c["numeric"] - c["closed"]) for c in g41))
    V["g41_ground"] = sci(max(abs(c["to_ground"][0] / c["to_ground"][1] - 1) for c in g41), 0)
    fr = [c["numeric"] / c["to_ground"][0] for c in g41]                 # mutual / capacitance to ground
    V["g41_frac_min"], V["g41_frac_max"] = sci(min(fr)), f(max(fr), 2)
    g43c = cf.get("G43_guard", {})
    V["g43_ground"] = sci(abs(g43c["to_ground"][0] / g43c["to_ground"][1] - 1), 0)
    V["g43_rel"] = sci(abs(g43c["rel_error"]))

    # --- what the closed forms bracketed ---------------------------------------------------------
    g8 = cf.get("G8_block_with_film", {})
    lo, hi = g8.get("bracket", (float("nan"), float("nan")))
    V["g8_val"] = f(g8.get("numeric", float("nan")), 4)
    V["g8_lo"], V["g8_hi"] = f(lo, 4), f(hi, 4)
    V["g8_pos"] = f(100 * g8.get("position", float("nan")), 0)
    # fF per unit of C'/eps0 for an 0402 body: eps0 [fF/mm] x eps_al x W [mm], W = 0.5 mm (Table G.2)
    k_al = 9.7 * EPS0 * 0.5
    V["g8_fF"] = f(k_al * g8.get("numeric", float("nan")), 1)
    V["g8_lo_fF"], V["g8_hi_fF"] = f(k_al * lo, 1), f(k_al * hi, 1)
    V["g8_over"] = f(k_al * (0.5 * (lo + hi) - g8.get("numeric", float("nan"))), 1)
    thin = cf.get("pins_thin_middle", {})
    V["thin_val"] = f(thin.get("numeric", float("nan")), 4)
    V["thin_pos"] = f(100 * thin.get("position", float("nan")), 0)
    V["g45"] = f(cf.get("G45_pins_no_middle", {}).get("closed", float("nan")), 4)
    V["g46"] = f(cf.get("G46_pins_wall", {}).get("closed", float("nan")), 4)
    p4 = cf.get("pins_pin4_grounded", {}).get("table", {})
    drops = [100 * (1 - b / a) for a, b in p4.values()] if p4 else [float("nan")]
    V["pin4_min"], V["pin4_max"] = f(min(drops), 0), f(max(drops), 0)
    a14 = cf.get("A14_pads_under_body", {}).get("table", {})
    V["a14_30"], V["a14_10"] = f(a14.get("0.03", float("nan")), 1), f(a14.get("0.01", float("nan")), 1)
    # Table G.6's parallel-plate estimate of the same coupling was 0.3 fF (0402, 30-um stand-off)
    V["a14_ratio"] = f(a14.get("0.03", float("nan")) / 0.3, 1)

    # --- the four sizes ---------------------------------------------------------------------------
    rows, pos, below_c = [], [], []
    orders, errs, encp, qs, a0ord = [], [], [], [], []
    for s in ("0201", "0402", "0603", "0805"):
        d = r3.get(f"size_{s}")
        if not d:
            continue
        cv, en, an = d["convergence"]["C_F"], d["enclosure"], d["analytic"]
        best = d["C_F_best"]
        p = (best - an["lower_bound"]) / (an["upper_estimate"] - an["lower_bound"])
        pos.append(100 * p)
        below_c.append(100 * (1 - best / an["central"]))
        rows.append(f"| {s} | {f(cv['finest'], 2)} | {f(cv.get('extrapolated') or cv['finest'], 2)} | "
                    f"{f(cv.get('order') or float('nan'), 2)} | {f(d['discretisation_error'], 2)} | "
                    f"{fs(d['enclosure_correction'])} | {f(en.get('order_C_F') or float('nan'), 2)} | "
                    f"**{f(best, 1)}** | {f(an['lower_bound'], 1)}, {f(an['central'], 1)}, {f(an['upper_estimate'], 1)} | "
                    f"{100 * p:.0f} % |")
        V[f"best_{s}"] = f(best, 1)
        V[f"pos_{s}"] = f(100 * p, 0)
        V[f"enc_{s}"] = fs(d["enclosure_correction"], 1)
        V[f"shares_{s}"] = ", ".join(f"{k} {v:.1f}" for k, v in sorted(d["convergence"]["contributions"].items()))
        V[f"an_terms_{s}"] = (f"board {an['board'][0]:.1f}–{an['board'][1]:.1f}, body {an['block'][0]:.1f}–"
                              f"{an['block'][1]:.1f}, air {an['air'][0]:.1f}–{an['air'][1]:.1f}")
        orders.append(f(cv.get("order") or float("nan"), 2))
        errs.append(f(d["discretisation_error"], 2))
        encp.append(100 * d["enclosure_correction"] / best)
        qs.append(f(en.get("order_C_F") or float("nan"), 2))
        a0 = d["convergence"]["C_A0"]
        a0ord.append((s, a0.get("order")))
        lv = [x["refine"] for x in d["convergence"]["levels"]]
        Cs = [x["C_F"] for x in d["convergence"]["levels"]]
        if s in ("0603", "0805") and cv.get("extrapolated") is not None:
            V[f"p1_change_{s}"] = fs(fixed_order_limit(lv, Cs, 1.0) - cv["extrapolated"])
    V["table_sizes"] = "\n".join(rows)
    V["pos_min"], V["pos_max"] = f(min(pos), 0), f(max(pos), 0)
    V["below_min"], V["below_max"] = f(min(below_c), 0), f(max(below_c), 0)

    def and_list(xs):
        return ", ".join(xs[:-1]) + " and " + xs[-1]
    V["orders_all"], V["errs_all"], V["q_all"] = and_list(orders), and_list(errs), and_list(qs)
    V["enc_pct_all"] = and_list([f(x, 1) for x in encp])
    V["enc_pct_min"], V["enc_pct_max"] = f(min(encp), 1), f(max(encp), 1)   # as in the list just above
    ok = [f"{o:.2f}" for s, o in a0ord if o is not None]
    bad = [s for s, o in a0ord if o is None]
    V["a0_orders"] = (and_list(ok) if len(ok) > 1 else (ok[0] if ok else "none")) + \
        (f" where the values allowed an extrapolation, while for the {and_list(bad) if len(bad) > 1 else bad[0]} they did not converge monotonically enough to extrapolate" if bad else "")

    d0402 = r3.get("size_0402", {})
    if d0402:
        lv = d0402["convergence"]["levels"]
        cv = d0402["convergence"]["C_F"]
        V["n_elem_0402"] = f"{int(lv[-1]['elements']):,}".replace(",", " ")     # counts are stored as floats
        V["n_dofs_0402"] = f"{int(lv[-1]['dofs']):,}".replace(",", " ")
        V["conv_0402"] = ", ".join(f(x["C_F"], 2) for x in lv)
        V["order_0402"] = f(cv.get("order") or float("nan"), 2)
        V["err_0402"] = f(d0402["discretisation_error"], 2)
        bias4 = lv[0]["C_F"] - cv["extrapolated"]                      # coarsest (15-um edge) minus limit
        V["bias4_0402"] = f(bias4, 2)
        V["bias4_pct_0402"] = f(100 * bias4 / cv["extrapolated"], 2)
        V["det_noise"] = f(lv[1]["C_F"] - cv["extrapolated"], 2)       # middle mesh minus limit
        a0 = d0402["convergence"]["C_A0"]
        a0b = (lv[0]["C_A0"] - a0["extrapolated"]) / a0["extrapolated"] if a0.get("extrapolated") else float("nan")
        V["a0_bias4_0402"] = f(100 * a0b, 2)
        e = d0402["enclosure"]
        V["enc_vals_0402"] = ", ".join(f(x, 2) for x in e["C_F"])
        V["enc_order_0402"] = f(e.get("order_C_F") or float("nan"), 2)
        V["dA0dF_0402"] = f(e["dC_A0"] / e["dC_F"], 2).replace("-", "−")
        R, C = e["R"], e["C_F"]
        cinf_q1 = (R[2] * C[2] - R[1] * C[1]) / (R[2] - R[1])         # q = 1 from the two largest
        V["q1_change_0402"] = fs((cinf_q1 - C[0]) - e["dC_F"], 3)
        V["enc_mesh_err_0402"] = f(2 * abs(a0b) * e["dC_F"], 3)
        V["ratio_0805_0402"] = f(r3["size_0805"]["C_F_best"] / d0402["C_F_best"], 2) if "size_0805" in r3 else "?"
        shares = d0402["convergence"]["contributions"]
        V["board_1pct_0402"] = f(0.01 * shares.get("board", float("nan")), 2)

    # --- details, corners, orientation ----------------------------------------------------------------
    det = r3.get("details_0402", {}).get("table", {})
    # The record names the variants in plain ASCII (g_resistor_3d.py, details_0402); the note's labels
    # say what changed and from what.  An unknown name falls back to its ASCII form with um -> µm.
    nice_details = {
        "reference": "Reference model (Section G.14.4)",
        "termination metal 30 um": "Termination metal 30 µm thick (15 µm in the reference)",
        "side wraps": "Terminations wrapped onto the side faces",
        "stand-off 10 um": "Stand-off 10 µm (30 µm in the reference)",
        "stand-off 50 um": "Stand-off 50 µm",
        "solder fillet 1/3 of T": "Solder fillet a third of $T$ high",
        "copper 18 um": "Copper 18 µm thick (35 µm in the reference)",
        "copper 70 um": "Copper 70 µm thick",
        "solder mask 20 um, eps 4.0": "Solder mask 20 µm thick, relative permittivity 4.0",
    }
    rows = []
    for name, v in det.items():
        delta = "—" if name == "reference" else fs(v["delta"])
        label = nice_details.get(name, (name[0].upper() + name[1:]).replace(" um", " µm"))
        rows.append(f"| {label} | {f(v['C_F'], 2)} | {delta} |")
    if det:   # quoted in Table G.6, approximation 2
        V["det_cu70"] = f(det["copper 70 um"]["delta"], 1)
        V["det_term30"] = f(det["termination metal 30 um"]["delta"], 1)
    fd = r3.get("film_down_0402", {}).get("table", {})
    if fd:
        rows.append(f"| Mounted upside down (film towards the board) | {f(fd['down']['C_F'], 2)} | "
                    f"{fs(fd['down']['C_F'] - fd['up']['C_F'])} |")
        up, dn = fd["up"]["shares"], fd["down"]["shares"]
        V["film_down"] = fs(fd["down"]["C_F"] - fd["up"]["C_F"])
        V["fd_air"] = f(up["air"] - dn["air"], 2)
        V["fd_body"] = fs(dn["alumina"] - up["alumina"])
        V["fd_board"] = fs(dn["board"] - up["board"])
    ec = r3.get("eps_corners_0402", {}).get("table", {})
    if ec:
        ref = ec["nominal"]["C_F"]
        for nm, lab in (("low", "Permittivities at the low corner (FR-4 3.65, alumina 9.4)"),
                        ("high", "Permittivities at the high corner (FR-4 4.6, alumina 10.0)")):
            rows.append(f"| {lab} | {f(ec[nm]['C_F'], 2)} | {fs(ec[nm]['C_F'] - ref)} |")
        V["eps_low_pct"] = fs(100 * (ec["low"]["C_F"] / ref - 1), 1)
        V["eps_high_pct"] = fs(100 * (ec["high"]["C_F"] / ref - 1), 1)
    V["table_details"] = "\n".join(rows)
    deltas = [abs(v["delta"]) for k, v in det.items() if k != "reference"]
    V["det_max"] = f(max(deltas), 1) if deltas else "?"
    if det:
        V["fillet_delta"] = fs(det["solder fillet 1/3 of T"]["delta"])
        V["so10_delta"] = f(det["stand-off 10 um"]["delta"], 2)
        V["so50_delta"] = f(det["stand-off 50 um"]["delta"], 2)

    # --- substrates --------------------------------------------------------------------------------
    sub = {s: r3.get(f"substrates_{s}", {}).get("rows", []) for s in ("0402", "0805")}
    docs = {"air (board removed)": "—",
            "RT/duroid 5880": "2.20 at 1 MHz and $2.20\\pm0.02$ at 10 GHz [A41, p. 2]",
            "RO3003": "$3.00\\pm0.04$ at 10 GHz, design value 3.00; about 1 % higher at 1 GHz [A40, pp. 2–3]",
            "I-Tera MT40": "3.45 at 2–10 GHz [A44, p. 2]",
            "RO4350B (design)": "$3.48\\pm0.05$ at 10 GHz, design value 3.66; about 3.76 at 1 GHz for 20-mil laminate [A39, pp. 2–3]",
            "MEGTRON 6 (1 GHz)": "3.71 at 1 GHz (54 % resin); 3.25–4.07 with the resin content [A42, pp. 1–8]",
            "FR-4 nominal": "4.17–4.24 at 0.1–1 GHz (Isola 370HR; Table G.3)",
            "FR-4 high": "upper end of Table G.3"}
    rows = []
    if sub["0402"]:
        for k, x in enumerate(sub["0402"]):
            y = sub["0805"][k] if k < len(sub["0805"]) else None
            name = x["material"].replace(" (design)", "").replace(" (1 GHz)", "").replace(" (board removed)", "")
            name = {"air": "No board (air)"}.get(name, name)
            rows.append(f"| {name} | {docs.get(x['material'], '')} | {x['eps_pcb']:g} | {f(x['C_F'], 1)} "
                        f"({x['relative_to_FR4']:.2f}) | "
                        + (f"{f(y['C_F'], 1)} ({y['relative_to_FR4']:.2f})" if y else "—") + " |")
        by = {s: {x["material"]: x for x in sub[s]} for s in sub}
        rel = {m: x["relative_to_FR4"] for m, x in by["0402"].items()}
        rel8 = {m: x["relative_to_FR4"] for m, x in by["0805"].items()}
        V["sub_air"] = f"{100 * (1 - rel['air (board removed)']):.0f}–{100 * (1 - rel8['air (board removed)']):.0f}"
        V["sub_ptfe"] = f"{100 * (1 - rel['RT/duroid 5880']):.0f}–{100 * (1 - rel8['RT/duroid 5880']):.0f}"
        V["sub_4350"] = f"{100 * (1 - rel['RO4350B (design)']):.0f}"
        V["sub_0805_ptfe"] = f(by["0805"]["RT/duroid 5880"]["C_F"], 0)
        V["sub_0402_fr4"] = f(by["0402"]["FR-4 nominal"]["C_F"], 0)
        al = [x["shares"]["alumina"] for x in sub["0402"]]
        V["alumina_share_range_0402"] = f"{min(al):.2f}–{max(al):.2f}"
        for s in ("0402", "0805"):
            V[f"air_eps1_{s}"] = f(by[s]["air (board removed)"]["shares"]["air"], 2)
            V[f"air_eps46_{s}"] = f(by[s]["FR-4 high"]["shares"]["air"], 2)
        # the central value of Section G.12 relative to FR-4, against the field solution's ratio
        devs = {}
        for s in ("0402", "0805"):
            cref = by[s]["FR-4 nominal"]["analytic"]["central"]
            for m, x in by[s].items():
                devs[(s, m)] = 100 * ((x["analytic"]["central"] / cref) / x["relative_to_FR4"] - 1)
        V["dev_eps1_0402"] = fs(devs[("0402", "air (board removed)")], 1)
        V["dev_eps1_0805"] = fs(devs[("0805", "air (board removed)")], 1)
        V["dev_max_22"] = f(max(abs(v) for (s, m), v in devs.items() if by[s][m]["eps_pcb"] >= 2.2), 1)
        # finite-difference check of Eq. (G.54) around 4.2: between 3.71 and 4.6
        a, b = by["0402"]["MEGTRON 6 (1 GHz)"], by["0402"]["FR-4 high"]
        V["fd_lo"], V["fd_hi"] = f"{a['eps_pcb']:g}", f"{b['eps_pcb']:g}"
        V["fd_board_0402"] = f((b["C_F"] - a["C_F"]) / math.log(b["eps_pcb"] / a["eps_pcb"]), 1)
        V["board_share_mid_0402"] = f(by["0402"]["FR-4 nominal"]["shares"]["board"], 1)
        se = r3.get("substrates_enclosure_0402", {}).get("table", {})
        if se:
            V["enc_air"] = fs(se["air (board removed)"]["dC_F"], 2)
            V["enc_ptfe"] = fs(se["RT/duroid 5880"]["dC_F"], 2)
            V["enc_fr4"] = fs(se["FR-4 nominal"]["dC_F"], 2)
            fr4 = by["0402"]["FR-4 nominal"]["C_F"] + se["FR-4 nominal"]["dC_F"]
            V["ratio_free_air"] = f((by["0402"]["air (board removed)"]["C_F"] + se["air (board removed)"]["dC_F"]) / fr4, 3)
            V["ratio_free_ptfe"] = f((by["0402"]["RT/duroid 5880"]["C_F"] + se["RT/duroid 5880"]["dC_F"]) / fr4, 3)
            V["ratio8_air"] = f(rel["air (board removed)"], 3)
            V["ratio8_ptfe"] = f(rel["RT/duroid 5880"], 3)
    V["table_substrates"] = "\n".join(rows)

    # --- OPA855 network ------------------------------------------------------------------------------
    o = r3.get("opa855_layout", {}).get("table", {})
    if o:
        lv = o["levels"]
        a, b = o[f"refine_{lv[0]}"], o[f"refine_{lv[-1]}"]          # lv[-1] is the finer mesh
        V["o855_alone"], V["o855_net"] = f(b["alone"], 1), f(b["network"], 1)
        V["o855_added"] = f(b["added"], 1)
        V["o855_added_diff"] = f(abs(b["added"] - a["added"]), 3)
        V["o855_B0"] = f(b["network_B0"], 0)
        enc = o["enclosure"]
        V["o855_enc"] = fs(enc["dC_F"], 1)
        V["o855_enc_order"] = f(enc.get("order_C_F") or float("nan"), 2)
        V["o855_free"] = f(b["network"] + enc["dC_F"], 0)
        V["o855_plane"] = f(o["plane_cutout"]["network"], 1)
        V["o855_plane_B0"] = f(o["plane_cutout"]["B0"], 0)
    pe = r3.get("opa855_plane_edge", {}).get("table", {})
    if pe:
        V["plane_edge_change"] = fs(pe["0.02"]["C_F"] - pe["0.04"]["C_F"])

    # --- OPA846 ---------------------------------------------------------------------------------------
    names = {"double_sided": "(a) $R_F$ on the bottom side under the package, through vias",
             "under_body": "(b) $R_F$ above pin 1, trace under the body to pin 4",
             "around": "(c) $R_F$ below pin 4, trace around the package from pin 1"}
    rows, all846, raw = [], [], {}
    for lay in ("double_sided", "under_body", "around"):
        cells = []
        for s in ("0402", "0603"):
            t = r8.get(f"{lay}_{s}", {}).get("table", {}).get("refine_5.66")
            cells.append(f"{f(t['C_F'], 1)}" if t else "—")
            if t:
                V[f"o846_{lay}_{s}"] = f(t["C_F"], 0)
                V[f"o846A0_{lay}_{s}"] = f(t["C_A0"], 0)
                V[f"o846B0_{lay}_{s}"] = f(t["C_B0"], 0)
                all846.append(t["C_F"])
                raw[(lay, s)] = t
        t402 = r8.get(f"{lay}_0402", {}).get("table", {}).get("refine_5.66", {})
        a0, b0 = t402.get("C_A0"), t402.get("C_B0")
        parts_t = r8.get(f"{lay}_0402_parts", {}).get("table", {})
        nores = f(parts_t["no_resistor"]["C_F"], 1) if parts_t else "—"
        nopkg = f(parts_t["no_package"]["C_F"], 1) if parts_t else "—"
        nopl = f(parts_t["no_planes"]["C_F"], 1) if parts_t else "—"
        if parts_t:
            V[f"o846_nores_{lay}"] = f(parts_t["no_resistor"]["C_F"], 0)
            V[f"o846_nopkg_{lay}"] = f(parts_t["no_package"]["C_F"], 0)
            V[f"o846_nopl_{lay}"] = f(parts_t["no_planes"]["C_F"], 0)
            V[f"o846_noplB0_{lay}"] = f(parts_t["no_planes"]["C_B0"], 0)
            raw[(lay, "parts")] = parts_t
        rows.append(f"| {names[lay]} | {cells[0]} | {cells[1]} | {f(a0, 0) if a0 else '—'} | "
                    f"{f(b0, 0) if b0 else '—'} | {nores} | {nopkg} | {nopl} |")
    V["table_opa846"] = "\n".join(rows)
    if all846:
        V["o846_min"], V["o846_max"] = f(min(all846), 0), f(max(all846), 0)
        b0s = [t["C_B0"] for k, t in raw.items() if k[1] != "parts"]
        V["o846B0_min"], V["o846B0_max"] = f(min(b0s), 0), f(max(b0s), 0)
    # Section G.14.11 places the OPA855 network between the lower corner and the nominal value of
    # Table 1.1 (0.05 and 0.08 pF); read that off the record too.
    if o:
        free855 = o[f"refine_{o['levels'][-1]}"]["network"] + o["enclosure"]["dC_F"]
        if not 50.0 < free855 < 80.0:
            raise ValueError("Section G.14.11 places the OPA855 network between 0.05 and 0.08 pF; "
                             "the record disagrees")
    # The text of Section G.14.10 states orderings; each is read off the records here, not assumed.
    if len(raw) == 9:
        cf = {k: v["C_F"] for k, v in raw.items() if k[1] != "parts"}
        checks = {
            "with the 0402, (b) > (a) > (c)": cf[("under_body", "0402")] > cf[("double_sided", "0402")]
            > cf[("around", "0402")],
            "with the 0603, (a) and (c) above their 0402 values": cf[("double_sided", "0603")]
            > cf[("double_sided", "0402")] and cf[("around", "0603")] > cf[("around", "0402")],
            "with the 0603, (b) below its 0402 value": cf[("under_body", "0603")] < cf[("under_body", "0402")],
            "(c) has the lowest C_B0 and the highest C_A0 (0402)":
                raw[("around", "0402")]["C_B0"] == min(raw[(l, "0402")]["C_B0"] for l in LAYS846)
                and raw[("around", "0402")]["C_A0"] == max(raw[(l, "0402")]["C_A0"] for l in LAYS846),
            "without the package C_F falls, without the planes C_F rises and C_B0 falls": all(
                raw[(l, "parts")]["no_package"]["C_F"] < raw[(l, "parts")]["whole"]["C_F"]
                < raw[(l, "parts")]["no_planes"]["C_F"]
                and raw[(l, "parts")]["no_planes"]["C_B0"] < raw[(l, "parts")]["whole"]["C_B0"] for l in LAYS846),
            "the parts cases' whole layout equals the network case": all(
                abs(raw[(l, "parts")]["whole"]["C_F"] / cf[(l, "0402")] - 1) < 0.01 for l in LAYS846),
        }
        failed = [k for k, ok in checks.items() if not ok]
        if failed:
            raise ValueError(f"Section G.14.10 states what the OPA846 records do not show: {failed}")
    fine = r8.get("under_body_0402_fine", {}).get("table", {}).get("refine_4.0", {})
    base = r8.get("under_body_0402", {}).get("table", {}).get("refine_5.66", {})
    enc16 = r8.get("under_body_0402_enclosure16", {}).get("table", {}).get("refine_5.66", {})
    if fine and base:
        V["o846_fine_change"] = fs(100 * (fine["C_F"] / base["C_F"] - 1))
    if enc16 and base:
        V["o846_enc_change"] = fs(100 * (enc16["C_F"] / base["C_F"] - 1))

    # --- Where the coupling of the 0402 sits (field_regions.py, Figure 45) ----------------------------
    fr = load("field_regions.json")
    if fr:
        reg, sh, g = fr["regions"], fr["by_distance"], fr["geometry"]
        V["fr_total"] = f(fr["C_F"], 1)
        V["fr_phi_min"] = f(fr["odd_potential_outer_half_of_termination"][0], 2)
        V["fr_al_in"] = f(reg["alumina between the wraps"]["total"], 1)
        V["fr_al_in_pct"] = f(100 * reg["alumina between the wraps"]["total"] / fr["C_F"], 0)
        V["fr_al_cap"] = f(reg["alumina inside a termination"]["total"], 1)
        V["fr_bd_gap"] = f(reg["board under the gap"]["total"], 1)
        V["fr_bd_else"] = f(reg["board elsewhere"]["total"], 1)
        V["fr_air_under"] = f(reg["air under the body"]["total"], 1)
        V["fr_air_else"] = f(reg["air elsewhere"]["total"], 1)
        inner = [sh[k] for k in ("0.0-0.5", "0.5-1.0")]
        outer = [sh[k] for k in ("1.0-2.0", "2.0-4.0", "4.0-inf")]
        V["fr_in1"] = f(sum(x["total"] for x in inner), 1)
        V["fr_neg_in1"] = fs(sum(x["negative"] for x in inner), 2)
        V["fr_out1"] = fs(sum(x["total"] for x in outer), 1)
        V["fr_neg_board"] = fs(reg["board under the gap"]["negative"] + reg["board elsewhere"]["negative"], 1)
        V["fr_neg_air"] = fs(reg["air under the body"]["negative"] + reg["air elsewhere"]["negative"], 1)
        # Three statements of the text are read off the record here rather than assumed.
        if any(sh[k]["positive"] != 0.0 for k in ("2.0-4.0", "4.0-inf")):
            raise ValueError("the text says every element beyond 2 mm is negative; the record disagrees")
        if fr["section_window_density"][0] < 0.0:
            raise ValueError("the text says the density is positive in the window of Figure 45b")
        la = fr["largest_at"]
        if not (fr["largest_in"] == "board" and abs(abs(la[0]) - g["x_pad"]) < 0.02
                and abs(abs(la[1]) - g["y_pad"]) < 0.03 and -0.02 < la[2] < 0.0):
            raise ValueError("the text places the largest density at an inner corner of a pad, in the board")
    return V


# ================================================================================================
def render(text: str, V: dict) -> str:
    """Fill every <<name>>; text blocks may themselves contain placeholders, so repeat until none
    is left, and fail if a name has no value."""
    import re
    for _ in range(4):
        names = set(re.findall(r"<<([A-Za-z0-9_]+)>>", text))
        if not names:
            return text
        missing = sorted(n for n in names if n not in V)
        if missing:
            raise KeyError(f"no value for placeholders: {missing}")
        for n in names:
            text = text.replace(f"<<{n}>>", V[n])
    raise RuntimeError("placeholders nested too deeply")


def note_edits(V: dict) -> list[tuple[str, str]]:
    """(old, new) pairs; each old text must occur exactly once in the note."""
    E = []
    # Appendix G's introduction: say that Section G.14 solves the same layouts numerically.
    E.append(("Those numerical checks confirm the arithmetic; they are not part of any argument.",
              "Those numerical checks confirm the arithmetic; they are not part of any argument. Section G.14 then "
              "solves the same layouts numerically, by the finite-element method in two and three dimensions, to check "
              "the closed forms and to measure what they leave out (Figures 44–51)."))
    # G.1: the field solutions in brief.
    E.append(("Measured careful single-resistor layouts in 0603 and 0805, which include traces and pins, give "
              "0.10–0.14 pF (Section G.13.3).",
              "Measured careful single-resistor layouts in 0603 and 0805, which include traces and pins, give "
              "0.10–0.14 pF (Section G.13.3).\n\nThe three-dimensional field solutions of Section G.14 check this "
              "estimate. For the resistor and its pads with no ground nearby they give <<best_0201>>, <<best_0402>>, "
              "<<best_0603>> and <<best_0805>> fF from 0201 to 0805, inside the brackets of Table G.1 at "
              "<<pos_min>>–<<pos_max>> % of the way up (Table G.11). The traces, pins and package of the OPA855 "
              "layout add <<o855_added>> fF, so that the network of Figure 43 gives about <<o855_free>> fF without "
              "the package interior (Section G.14.9)."))
    # G.8: where the body term lies in its bracket.
    E.append(("The analysis proves the bracket and does not place the true value within it; the central value of "
              "Section G.12 takes its middle.",
              "The analysis proves the bracket and does not place the true value within it; the central value of "
              "Section G.12 takes its middle. The field solution of Section G.14.3 places it <<g8_pos>> % of the way "
              "up, about <<g8_over>> fF below the middle for an 0402."))
    # G.11: the pins' values within their bounds.
    E.append(("the floating-wall value is an upper bound there.",
              "the floating-wall value is an upper bound there. The field solutions of Section G.14.3 give the value "
              "between the bounds: with pin 2 as a thin floating strip it lies <<thin_pos>> % of the way from the "
              "lower bound to the upper one, and grounding pin 4 lowers each model by <<pin4_min>>–<<pin4_max>> %."))
    # Table G.6: quote the field solutions.
    E.append(("| 1 | Cross-sections treated as uniform over their widths; no field around the ends | Lowers $C_m$ by "
              "the end fringing | Not computed; Section G.13 compares the sum with measurements |",
              "| 1 | Cross-sections treated as uniform over their widths; no field around the ends | Lowers $C_m$ by "
              "the end fringing | Section G.14.6: the three-dimensional field solutions lie <<pos_min>>–<<pos_max>> % "
              "of the way up the bracket, inside it for every size |"))
    E.append(("| Copper 35 µm thick against gaps of 0.3–1 mm: below 1 fF |",
              "| Copper 35 µm thick against gaps of 0.3–1 mm: below 1 fF by the estimate; in three dimensions "
              "70-µm copper adds <<det_cu70>> fF and 30-µm terminations <<det_term30>> fF to an 0402 (Table G.12) |"))
    E.append(("| 6 | Field in the termination slots | Bracketed | Eqs. (G.28) and (G.32) |",
              "| 6 | Field in the termination slots | Bracketed | Eqs. (G.28) and (G.32); the field solution lies "
              "<<g8_pos>> % of the way up (Section G.14.3) |"))
    E.append(("Within the zero-thickness model the floating-wall value is an upper bound; 14.9–21.0 fF plus 2.1–4.3 fF |",
              "Within the zero-thickness model the floating-wall value is an upper bound; 14.9–21.0 fF plus 2.1–4.3 fF. "
              "Section G.14.3: a thin floating pin 2 at <<thin_pos>> % of the bracket; pin 4 grounded lowers it by "
              "<<pin4_min>>–<<pin4_max>> % |"))
    E.append(("| Lowers | A parallel-plate estimate of that coupling gives 0.3 fF for an 0402 at $t_s$ = 30 µm; the cut "
              "keeps the lower bound rigorous |",
              "| Lowers | The field solution of that coupling gives <<a14_30>> fF for an 0402 at $t_s$ = 30 µm and "
              "<<a14_10>> fF at 10 µm (Section G.14.3), against 0.3 fF from a parallel-plate estimate; the cut keeps "
              "the lower bound rigorous |"))
    # The old Section G.14 becomes G.15, and the new section goes before it.
    E.append(("### G.14 How the note uses the estimate", "<<NEW_SECTION>>\n\n### G.15 How the note uses the estimate"))
    E.append(("corners of $C_{F,\\mathrm{par}}$ (Section G.14) |", "corners of $C_{F,\\mathrm{par}}$ (Section G.15) |"))
    # Appendix C, item 7.
    E.append(("The bench board of Section 3.10 points to about 0.3 pF in another layout (Section G.13.5).",
              "Three-dimensional field solutions of this layout give about <<o855_free>> fF for the resistor, pads, "
              "traces, pins and package, without the package interior (Section G.14.9), and <<o846_min>>–<<o846_max>> fF "
              "for OPA846 layouts in SOT-23-5 (Section G.14.10). The bench board of Section 3.10 points to about "
              "0.3 pF in another layout, but that layout is not recorded and may be a poor one, so the value is no "
              "benchmark (Section G.13.5)."))
    # Section G.13.5: the bench board is no benchmark.
    E.append(("The bench board shows what a layout other than the one assumed here can carry.",
              "The bench board shows what a layout other than the one assumed here can carry. Its layout is not "
              "recorded and may be a poor one, so 0.3 pF is no benchmark for a careful layout; Section G.14.10 "
              "computes three layouts that follow the datasheet's advice."))
    # Appendix D: references.
    E.append(("\n\n### Books\n",
              "\n" + "\n".join([
                  "- **[A35]** C. Geuzaine and J.-F. Remacle, \"Gmsh: A 3-D finite element mesh generator with built-in "
                  "pre- and post-processing facilities\", *Int. J. Numer. Methods Eng.* 79(11), 1309–1331 (2009). "
                  "https://doi.org/10.1002/nme.2579",
                  "- **[A36]** T. Gustafsson and G. D. McBain, \"scikit-fem: A Python package for finite element assembly\", "
                  "*J. Open Source Softw.* 5(52), 2369 (2020). https://doi.org/10.21105/joss.02369",
                  "- **[A37]** N. Bell, L. N. Olson and J. Schroder, \"PyAMG: Algebraic Multigrid Solvers in Python\", "
                  "*J. Open Source Softw.* 7(72), 4142 (2022). https://doi.org/10.21105/joss.04142",
                  "- **[A38]** L. F. Richardson and J. A. Gaunt, \"The deferred approach to the limit\", *Phil. Trans. R. "
                  "Soc. A* 226, 299–361 (1927). https://doi.org/10.1098/rsta.1927.0008",
                  "- **[A39]** Rogers Corporation, *RO4000 Series High Frequency Circuit Materials*, data sheet PUB# 92-004, "
                  "revision 1592 080322. " + V.get("url_A39", ""),
                  "- **[A40]** Rogers Corporation, *RO3000 Series Circuit Materials*, data sheet PUB# 92-130, revision "
                  "1687 013024. " + V.get("url_A40", ""),
                  "- **[A41]** Rogers Corporation, *RT/duroid 5870/5880 High Frequency Laminates*, data sheet PUB# 92-101, "
                  "revision 1603 080822. " + V.get("url_A41", ""),
                  "- **[A42]** Panasonic, *MEGTRON 6 Data Sheet: Laminate R-5775, Prepreg R-5670*, No. 260630, June 2026. "
                  + V.get("url_A42", ""),
                  "- **[A43]** DuPont, *Pyralux AP All-Polyimide Double-Sided Copper-Clad Laminate*, data sheet EI-10124 "
                  "(2/25). " + V.get("url_A43", ""),
                  "- **[A44]** Isola, *I-Tera MT40 Very Low-Loss Laminate and Prepreg*, data sheet, revision F "
                  "(8 December 2025). " + V.get("url_A44", ""),
              ]) + "\n\n### Books\n"))
    # [B6] is appended after [B5] by add_b6(), which finds [B5] by its line start.
    # Appendix E: figures, data and scripts.
    E.append(("| `figures/` | Figures 1–43 as PNG (600 dpi) and PDF.", "| `figures/` | Figures 1–51 as PNG (600 dpi) and PDF."))
    E.append(("the application notes and articles [A1]–[A34], with the documents behind Appendix G in `appnotes/parasitic_cf/`",
              "the application notes and articles [A1]–[A34] and [A39]–[A44], with the documents behind Appendix G in "
              "`appnotes/parasitic_cf/`"))
    return E


def add_b6(text: str) -> str:
    """Append [B6] after the [B5] entry (the line that starts with '- **[B5]**')."""
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("- **[B5]**")]
    if len(idx) != 1:
        raise ValueError("expected one [B5] entry")
    b6 = ("- **[B6]** S. C. Brenner and L. R. Scott, *The Mathematical Theory of Finite Element Methods*, 3rd ed., "
          "Springer, 2008. Its Chapter 2 (variational formulation) and Chapter 3 (Lagrange elements) underlie "
          "Section G.14.1. https://doi.org/10.1007/978-0-387-75934-0")
    lines.insert(idx[0] + 1, b6)
    return "\n".join(lines)


def add_appendix_e_rows(text: str) -> str:
    """Add the numerical files to the data/parasitic_cf/ and scripts_archive/ rows of Table E.1."""
    rows = text.split("\n")
    i = [k for k, l in enumerate(rows) if l.startswith("| `data/parasitic_cf/` |")]
    j = [k for k, l in enumerate(rows) if l.startswith("| `scripts_archive/` |")]
    if len(i) != 1 or len(j) != 1:
        raise ValueError("Table E.1 rows not found exactly once")
    # The cells of Table E.1 separate their sentences by full stops and end without one.
    rows[i[0]] = rows[i[0]].rstrip(" |") + (". The field solutions of Section G.14 are in `data/parasitic_cf/numerical/` "
                                            "(`checks.json`, `closed_forms_2d.json`, `resistor_3d.json`, `opa846_3d.json` and "
                                            "`field_regions.json`, each with the log of its run), and the board permittivities "
                                            "of Table G.13 in `substrate_permittivity.md`, `.json` |")
    rows[j[0]] = rows[j[0]].rstrip(" |") + (". The field solutions of Section G.14 use the package `pcbcap` at the root of "
                                            "the repository; their scripts are in `scripts_archive/parasitic_cf/numerical/`, "
                                            "and `rerun_all.sh` there recomputes every record |")
    return "\n".join(rows)


def substrate_urls() -> dict:
    """Links of [A39]-[A44] from the collection data/parasitic_cf/substrate_permittivity.json."""
    p = NOTE_DIR / "data" / "parasitic_cf" / "substrate_permittivity.json"
    recs = json.loads(p.read_text(encoding="utf-8"))
    keys = {"RO4350B": "url_A39", "RO3003": "url_A40", "RT/duroid 5880": "url_A41", "MEGTRON 6": "url_A42",
            "Pyralux AP": "url_A43", "I-Tera MT40": "url_A44"}
    out = {}
    for r in recs:
        for k, v in keys.items():
            if r.get("material", "").startswith(k) and v not in out and r.get("url"):
                out[v] = r["url"]
    return out


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    note, prefix = Path(args[0]), args[1]
    dry = args[3] if len(args) > 3 and args[2] == "--dry-run" else None
    V = values()
    V.update(substrate_urls())
    section = render(TEMPLATE.read_text(encoding="utf-8").rstrip("\n"), V)
    raw = note.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(prefix):
        print(f"the note's SHA-256 is {sha[:12]}, not {prefix}: refusing to edit a version these edits were not written for")
        return 1
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    text = text.replace("\r\n", "\n")
    V["NEW_SECTION"] = section
    for old, new in note_edits(V):
        n = text.count(old)
        if n != 1:
            raise ValueError(f"expected exactly one occurrence, found {n}: {old[:80]!r}")
        text = text.replace(old, render(new, V))
    text = add_b6(text)
    text = add_appendix_e_rows(text)
    out = text.replace("\n", newline).encode("utf-8")
    if dry:
        # The section alone, and the whole edited note beside it, so that every edit can be read and
        # diffed before the note itself is touched.
        Path(dry).write_text(section + "\n", encoding="utf-8", newline="\n")
        whole = Path(dry).with_suffix(".note.md")
        whole.write_bytes(out)
        print(f"section written to {dry} ({len(section.splitlines())} lines) and the edited note to "
              f"{whole.name}; the note is untouched")
        return 0
    note.write_bytes(out)
    print(f"note edited; new SHA-256 {hashlib.sha256(note.read_bytes()).hexdigest()[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
