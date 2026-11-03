"""SPICE models and numerical checks of the two composite TIAs (survey Sections 11.5 and 11.6).

Usage:  python spice_composite_checks.py <check> [--ngspice <library>] [--spice <spice folder>]
        <check> = ths_smoke | ths_referee | ths_zol | all

The vendor models are not part of this archive (spice/models/README.md gives the terms):
  OPA859   TI SBOMBQ2, as in Section 10 (spice_tia_checks.VENDOR_MODELS)
  THS3491  TI SBOMBP9, 'ths3491.lib' (TINA-TI 'All In One' model v1.0, 2/16/18, part THS3491RGT),
           placed at <spice>/models/THS3491/extracted/sbombp9/ths3491.lib
Both are translated into <spice>/runs/_models/ by spice_tia_checks.translate_model (T_ABS
noiseless resistors to noisy=0, CAP to C) before use.  Decks are written to
<spice>/runs/composite/<check>/<case>/ and run through ngspice loaded as a shared library
(ngspice_shared.py, PSpice compatibility on); results go to <spice>/results/composite_<check>.json.

Checks:
  ths_smoke    operating point (supply current, output offset) and the model's noise at G = 5:
               e_n from the output noise with the non-inverting input grounded, i_n+ from the
               excess with 1 kOhm (noiseless) in series with it, against the datasheet (p8).
  ths_referee  the datasheet's own test circuit (Fig 9-1: 50-ohm source, 49.9-ohm termination,
               49.9 ohm into 50 ohm) at the four gains of Table 9-2 / Fig 8-1; the normalized
               gain V(load)/V(source) for overlay_digitized.py (Fig 8-1), -3 dB and peaking.
  ths_zol      the model's open-loop transimpedance as Fig 8-22 defines it: non-inverting input
               grounded, AC current into the inverting input, output DC-fed back through 1 GH;
               Z_OL = -V(out)/I(inverting pin), no load and 100 ohm; and the current-feedback
               formula H = G/(1 + (R_F + G r_i)/Z_OL) with the model's own Z_OL against the model's
               closed loop (ths_referee), which tests the formula the analytical composite uses.

Every deck's ngspice log is scanned for the messages that mark convergence trouble (CONV_PATTERNS);
each hit is recorded with its deck in results/composite_convergence.json and printed.  What was
done about each is written down in CONVERGENCE_NOTES below and in the survey (Section 11.7, Table 11.13).
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np

import composite_tia as ct
from ngspice_shared import NgSpice
from spice_tia_checks import (VENDOR_MODELS, loop_metrics_from_T, prepared_model, read_wrdata, translate_model,
                              write_deck, zt_metrics)

HERE = Path(__file__).resolve().parent

THS3491 = dict(lib="THS3491/extracted/sbombp9/ths3491.lib",
               # pins INP INN OUT PD_not VCC VEE GND; PD_not high enables (threshold 1 V above GND)
               inst="{p} {n} {o} vcc2 vcc2 vee2 0 THS3491RGT",
               source="TI SBOMBP9, THS3491 TINA-TI 'All In One' model v1.0 (2/16/18), ths3491.lib, part THS3491RGT")
VS2 = 15.0                     # THS3491 supplies, +/-15 V (datasheet characterization)
C12_MODEL = 1.2e-12            # the model's capacitance at its internal inverting node (C_C12)
# Table 9-2 (RGT package) and Fig 8-1: gain, R_F, R_G
TABLE_9_2 = ((2, 976.0, 976.0), (5, 576.0, 143.0), (10, 499.0, 54.9), (20, 383.0, 20.0))

# ngspice messages that mark convergence aids or trouble, by kind
CONV_PATTERNS = {
    "gmin stepping (operating point found only with it)": re.compile(r"gmin stepping", re.I),
    "source stepping (operating point found only with it)": re.compile(r"source stepping", re.I),
    "failure": re.compile(r"singular|timestep too small|no convergence|iteration limit|trouble|doanalyses|"
                          r"\berror\b|aborted", re.I),
    "warning": re.compile(r"warning", re.I),
}
# what each kind of message meant in these decks and how it was resolved
CONVERGENCE_NOTES = {
    "gmin stepping (operating point found only with it)":
        "317 of the 406 decks, all of them with the OPA859 or the THS3491 macromodel: Newton iteration from the "
        "initial guess does not converge and ngspice falls back on its automatic dynamic gmin stepping, which "
        "completes ('Dynamic gmin stepping completed').  The bipolar composites, the stand-alone transistor decks and "
        "the THS3491's open-loop decks converge without it.  The operating points reached are the expected ones "
        "(THS3491 16.8 mA, OPA859 20.2 mA, outputs within millivolts of their targets, the designed drain and "
        "collector currents), so no action was needed.",
    "warning":
        "Only the LSBF862 decks: ngspice's 'Model issue' warning for the PSpice-only parameters of Linear Systems' "
        "card (NETLIST_NOTES, 'PSpice-only JFET parameters').",
}
# netlist problems met while setting the decks up, and their fixes
NETLIST_NOTES = {
    "subcircuit name collision":
        "With the OPA859 and THS3491 libraries in one deck, ngspice reported 'redefinition of .subckt femt, "
        "ignored' and 'of .subckt vnse', then 'Mismatch: 5 formal but 3 actual params' and 'Undefined parameter "
        "[glff]': both TI libraries define the noise subcircuits FEMT and VNSE, with different parameter lists, "
        "and ngspice keeps the first definition of a name for both models.  Fix: the translated copy of the "
        "THS3491 library has all its helper subcircuits renamed THS3491_<name> (namespace_subckts); the vendor "
        "file is not touched.  The THS3491-only decks give the same results with and without the renaming.",
    "PSpice-only JFET parameters":
        "Linear Systems' LSBF862 card is used as published.  ngspice warns 'unrecognized parameter (isr) - ignored' "
        "and the same for nr, zxti, alpha, vk and mj, among them PSpice's recombination current (ISR, NR) and impact "
        "ionization (ALPHA, VK), which ngspice's JFET model does not have.  It accepts M = 0.33 and MFG without a warning but does not use them: every result is the "
        "same to the last printed digit with and without them, so its junction capacitances keep the exponent "
        "0.5 (C_gd = 1.12 pF at the operating point instead of the 1.6 pF that M = 0.33 would give).",
    "noise plot after other analyses":
        "In a deck that runs op and three ac analyses before 'noise', 'setplot noise1' finds no such plot; the "
        "noise analysis therefore runs in a deck of its own (as in Section 10).",
}
# routine notes that are not convergence messages
_ROUTINE = re.compile(r"gnd in a subcircuit is not set to 0|Compatibility modes selected|Reducing trtol to 1", re.I)


def split_log(out):
    """ngspice's console text as lines (the shared library's callback delivers them unterminated,
    each prefixed 'stdout ' or 'stderr ')."""
    return [s.strip() for s in re.split(r"(?=std(?:out|err) )|\n", out) if s.strip()]


def namespace_subckts(text, keep, prefix):
    """Prefix every subcircuit name defined in a library except `keep`: in its .SUBCKT and .ENDS
    lines and in the subcircuit-name token of each X statement (the last token before PARAMS:, or
    the last token).  Node names that equal a subcircuit name (THS3491: VICM) are not touched.
    Continuation lines (+) of an X statement are joined to it."""
    names = {m.group(1).lower() for m in re.finditer(r"^\s*\.subckt\s+(\S+)", text, re.I | re.M)}
    names.discard(keep.lower())
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        low = s.lower()
        if low.startswith(".subckt") or low.startswith(".ends"):
            tok = s.split()
            if len(tok) > 1 and tok[1].lower() in names:
                tok[1] = prefix + tok[1]
            out.append(" ".join(tok))
            i += 1
            continue
        if low[:1] == "x":
            stmt = s
            while i + 1 < len(lines) and lines[i + 1].strip().startswith("+"):
                i += 1
                stmt += " " + lines[i].strip()[1:]
            tok = stmt.split()
            k = next((j for j, t in enumerate(tok) if t.lower() == "params:"), len(tok)) - 1
            if tok[k].lower() in names:
                tok[k] = prefix + tok[k]
            out.append(" ".join(tok))
            i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out) + "\n", sorted(names)


def prepared_ths(spice):
    """Translated copy of the THS3491 library (spice_tia_checks.translate_model), with its helper
    subcircuits renamed THS3491_<name>: the OPA859 library defines FEMT and VNSE too, with other
    parameters, and ngspice keeps only the first definition of a name (see NETLIST_NOTES)."""
    src = spice / "models" / THS3491["lib"]
    dst = spice / "runs" / "_models" / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    text, _ = namespace_subckts(translate_model(src.read_text(encoding="latin-1")), "THS3491RGT", "THS3491_")
    dst.write_text(text, encoding="latin-1")
    return dst


def ths(p, n, o, name="XU2"):
    return f"{name} " + THS3491["inst"].format(p=p, n=n, o=o) + "\n"


def header_ths(title, with_opa859=False):
    inc = ".include ../../../_models/ths3491.lib\n"
    sup = f"VCC2 vcc2 0 DC {VS2}\nVEE2 vee2 0 DC {-VS2}\n"
    if with_opa859:
        inc += f".include ../../../_models/{Path(VENDOR_MODELS['OPA859']['lib']).name}\n"
        vs = VENDOR_MODELS["OPA859"]["vs_tia"]
        sup += f"VCC vcc 0 DC {vs}\nVEE vee 0 DC {-vs}\n"
    return f"* {title}\n{inc}.temp 25\n{sup}"


def run_logged(ng, folder, text, conv):
    """Write and run a deck; keep its log (one message per line); record, by kind, every line
    that matches CONV_PATTERNS.  Returns the log lines and the kinds found."""
    deck = write_deck(folder, text)
    lines = split_log(ng.run_deck(deck))
    (folder / "ngspice.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    found = {}
    for ln in lines:
        if _ROUTINE.search(ln):
            continue
        for kind, pat in CONV_PATTERNS.items():
            if pat.search(ln):
                found.setdefault(kind, [])
                if ln not in found[kind]:
                    found[kind].append(ln)
                break
    if found:
        conv[folder.as_posix().split("/runs/", 1)[-1]] = found
    return lines, sorted(found)


# ---------------------------------------------------------------- checks
def check_ths_smoke(ng, spice, conv):
    res = {}
    base = spice / "runs" / "composite" / "ths_smoke"
    for rs in (0.001, 1000.0):
        folder = base / f"G5_Rs{rs:g}".replace(".", "p")
        text = header_ths(f"THS3491 G = 5, Rs = {rs} ohm (noiseless), noise and operating point") + ths("inp", "n2", "o2") + (
            f"Vs src 0 DC 0 AC 1\nRS src inp rnl {rs}\nRF2 o2 n2 576\nRG2 n2 0 143\nRL o2 0 100\n"
            ".model rnl r(noisy=0)\n"
            ".control\nset wr_singlescale\nset wr_vecnames\nop\nprint v(o2) v(n2) i(vcc2) i(vee2)\n"
            "noise v(o2) Vs dec 20 1k 1G\nsetplot noise1\nwrdata noise.txt onoise_spectrum\n.endc\n.end\n")
        lines, hits = run_logged(ng, folder, text, conv)
        d = read_wrdata(folder / "noise.txt")
        f, on = d[:, 0], d[:, 1]
        op = [ln[7:] for ln in lines if re.match(r"stdout (v\(o2\)|v\(n2\)|i\(vcc2\)|i\(vee2\))\s*=", ln)]
        res[f"Rs{rs:g}"] = dict(op=op, onoise_nV={f"{x/1e6:g}MHz": float(np.interp(np.log10(x), np.log10(f), on) * 1e9)
                                                  for x in (1e5, 1e6, 1e7, 1e8)}, flags=hits)
    # output noise of the G = 5 stage: (e_n G)^2 + (i_nn R_F)^2 + 4kT R_F + 4kT R_F^2/R_G, with i_np Rs
    on0 = np.array(list(res["Rs0.001"]["onoise_nV"].values())) * 1e-9
    on1 = np.array(list(res["Rs1000"]["onoise_nV"].values())) * 1e-9
    kt = ct.KT
    resist = 4 * kt * 576.0 + 4 * kt * 576.0 ** 2 / 143.0
    inn_term = (ct.THS["inn"] * 576.0) ** 2
    en_model = np.sqrt(np.maximum(on0 ** 2 - resist - inn_term, 0)) / 5.0
    inp_model = np.sqrt(np.maximum(on1 ** 2 - on0 ** 2, 0)) / 5.0 / 1000.0
    res["e_n_nV_if_inn_as_datasheet"] = list(en_model * 1e9)
    res["i_np_pA"] = list(inp_model * 1e12)
    res["datasheet"] = dict(e_n_nV=ct.THS["en"] * 1e9, i_np_pA=ct.THS["inp"] * 1e12, i_nn_pA=ct.THS["inn"] * 1e12)
    print(f"THS3491 op: {res['Rs0.001']['op']}")
    print(f"  output noise at 0.1/1/10/100 MHz, Rs = 0: {np.round(on0*1e9, 2)} nV/rtHz; Rs = 1 k: {np.round(on1*1e9, 2)}")
    print(f"  e_n (assuming i_nn = 20 pA/rtHz) {np.round(en_model*1e9, 2)} nV/rtHz; i_np {np.round(inp_model*1e12, 1)} pA/rtHz "
          f"| datasheet e_n 1.7 nV, i_n+ 15 pA, i_n- 20 pA")
    return res


def check_ths_referee(ng, spice, conv):
    res = {}
    base = spice / "runs" / "composite" / "ths_referee"
    for g, rf, rg in TABLE_9_2:
        folder = base / f"G{g}"
        text = header_ths(f"THS3491 Fig 9-1 test circuit, G = {g}, R_F = {rf}, R_G = {rg}") + ths("inp", "n2", "o2") + (
            f"Vs src 0 DC 0 AC 1\nRS src inp 50\nRT inp 0 49.9\nRF2 o2 n2 {rf}\nRG2 n2 0 {rg}\n"
            "RO o2 out 49.9\nRLD out 0 50\n"
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 200 1meg 10G\n"
            "wrdata cl.txt real(v(out)) imag(v(out)) real(v(o2)) imag(v(o2)) real(v(inp)) imag(v(inp))\n.endc\n.end\n")
        out, hits = run_logged(ng, folder, text, conv)
        d = read_wrdata(folder / "cl.txt")
        f = d[:, 0]
        vout = d[:, 1] + 1j * d[:, 2]
        H = (d[:, 3] + 1j * d[:, 4]) / (d[:, 5] + 1j * d[:, 6])       # pin-to-pin gain V(o2)/V(inp)
        np.save(folder / "cl.npy", np.vstack([f, vout.real, vout.imag, H.real, H.imag]))
        norm = 20 * np.log10(np.abs(vout) / np.abs(vout[0]))
        zm = zt_metrics(f, vout)
        zp = zt_metrics(f, H)
        res[f"G{g}"] = dict(rf=rf, rg=rg, f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"], f_peak_MHz=zm["f_peak_MHz"],
                            pin_gain_lf=float(abs(H[0])), pin_f3_MHz=zp["f3_MHz"], pin_peak_dB=zp["peak_dB"], flags=hits)
        print(f"THS3491 G={g} R_F={rf:g}: -3 dB {zm['f3_MHz']:.0f} MHz, peak {zm['peak_dB']:.2f} dB at "
              f"{zm['f_peak_MHz']:.0f} MHz (load); pin gain {abs(H[0]):.3f}, -3 dB {zp['f3_MHz']:.0f} MHz | flags {hits[:2]}")
        res[f"G{g}"]["curve"] = dict(f_MHz=list(f[::4] / 1e6), norm_dB=list(norm[::4]))
    return res


def check_ths_zol(ng, spice, conv):
    res = {}
    base = spice / "runs" / "composite" / "ths_zol"
    for lab, rl in (("noload", 1e9), ("RL100", 100.0)):
        folder = base / lab
        text = header_ths(f"THS3491 open-loop transimpedance, R_L = {rl:g} ohm") + ths("0", "nn", "o2") + (
            f"Iinj 0 nx DC 0 AC 1\nVsense nx nn DC 0\nLB o2 nx 1G\nRL o2 0 {rl:g}\n"
            ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 10 10G\n"
            "wrdata zol.txt real(v(o2)) imag(v(o2)) real(i(vsense)) imag(i(vsense)) real(v(nn)) imag(v(nn))\n"
            ".endc\n.end\n")
        out, hits = run_logged(ng, folder, text, conv)
        d = read_wrdata(folder / "zol.txt")
        f = d[:, 0]
        i_n = d[:, 3] + 1j * d[:, 4]
        Z = -(d[:, 1] + 1j * d[:, 2]) / i_n
        Zin = (d[:, 5] + 1j * d[:, 6]) / i_n                     # inverting-input impedance, INP grounded
        np.save(folder / "zol.npy", np.vstack([f, Z.real, Z.imag, Zin.real, Zin.imag]))
        pick = {}
        for x in (1e3, 1e5, 1e6, 1e7, 1e8, 3e8, 5e8, 7.7e8, 1e9, 2e9):
            k = int(np.argmin(np.abs(np.log10(f) - np.log10(x))))
            pick[f"{x/1e6:g}MHz"] = dict(dB=float(20 * np.log10(abs(Z[k]))), deg=float(np.degrees(np.angle(Z[k]))),
                                         zin_re=float(Zin[k].real), zin_im=float(Zin[k].imag))
        res[lab] = dict(points=pick, flags=hits,
                        curve=dict(f_Hz=list(f[::3]), dB=list(20 * np.log10(np.abs(Z[::3]))),
                                   deg=list(np.degrees(np.unwrap(np.angle(Z)))[::3])))
        print(f"THS3491 Z_OL ({lab}) | flags {hits[:2]}")
        for k, v in pick.items():
            fd = float(k[:-3]) * 1e6
            ds = ""
            if 1e5 <= fd <= 9.5e8:
                zd = ct.zol(np.array([fd]))[0]
                ds = f" | Fig 8-22 {20*np.log10(abs(zd)):6.1f} dB {np.degrees(np.angle(zd)):7.1f} deg"
            print(f"   {k:>9}: {v['dB']:6.1f} dBohm {v['deg']:7.1f} deg, Z_in {v['zin_re']:6.1f} {v['zin_im']:+6.1f}j ohm{ds}")
    # the current-feedback formula with the model's own Z_OL and inverting-input impedance,
    # against the model's closed loop (pin-to-pin gain, R_L = 100 ohm as in the test circuit).
    # The pin current I_pin also charges the model's internal inverting-node capacitance C12
    # (1.2 pF, node INPUTN_ICMR), so with the non-inverting input grounded
    #   I_pin = i_r (1 + s C12 Z_i),  Z_in = V_pin / I_pin = Z_i / (1 + s C12 Z_i),
    # where i_r is the error current the transimpedance stage senses (through R18 = 15 ohm and
    # L4) and Z_i that path's impedance; hence Z_i = Z_in / (1 - s C12 Z_in) and the internal
    # Z_OL = -V_out / i_r = Z_OL,pin (1 + s C12 Z_i).  In closed loop the node follows the input,
    # so C12 acts as a capacitance across R_G:  H = G(s) / (1 + (R_F + G(s) Z_i) / Z_OL) with
    # G(s) = 1 + R_F/R_G + s R_F C12 (survey Eq. (71)).
    zl = np.load(base / "RL100" / "zol.npy")
    fz, Zm, Zinm = zl[0], zl[1] + 1j * zl[2], zl[3] + 1j * zl[4]
    out = {}
    for g, rf, rg in TABLE_9_2:
        cl = np.load(spice / "runs" / "composite" / "ths_referee" / f"G{g}" / "cl.npy")
        f = cl[0]
        s = 2j * np.pi * f
        H = cl[3] + 1j * cl[4]
        Zf = np.interp(np.log10(f), np.log10(fz), Zm.real) + 1j * np.interp(np.log10(f), np.log10(fz), Zm.imag)
        zin = np.interp(np.log10(f), np.log10(fz), Zinm.real) + 1j * np.interp(np.log10(f), np.log10(fz), Zinm.imag)
        zi = zin / (1 - s * C12_MODEL * zin)
        z_int = Zf * (1 + s * C12_MODEL * zi)
        gs = 1 + rf / rg + s * rf * C12_MODEL
        Hf_ri = g / (1 + (rf + g * ct.R_I) / Zf)
        Hf_gen = gs / (1 + (rf + gs * zi) / z_int)
        m_sp, m_ri, m_gen = zt_metrics(f, H), zt_metrics(f, Hf_ri), zt_metrics(f, Hf_gen)
        dev = np.abs(Hf_gen / H)
        band = f <= 3e9
        out[f"G{g}"] = dict(spice=m_sp, formula_ri15=m_ri, formula_with_cn=m_gen,
                            max_dev_dB_to_3GHz=float(np.max(np.abs(20 * np.log10(dev[band])))),
                            max_dev_deg_to_3GHz=float(np.max(np.abs(np.degrees(np.angle(Hf_gen[band] / H[band]))))))
        print(f"   G={g}: SPICE closed loop -3 dB {m_sp['f3_MHz']:.0f} MHz pk {m_sp['peak_dB']:.2f} | G/(1+(R_F+G r_i)/Z_OL,pin) "
              f"{m_ri['f3_MHz']:.0f} MHz pk {m_ri['peak_dB']:.2f} | G(s) form with C12 and Z_i {m_gen['f3_MHz']:.0f} MHz "
              f"pk {m_gen['peak_dB']:.2f}; largest deviation to 3 GHz {out[f'G{g}']['max_dev_dB_to_3GHz']:.2f} dB, "
              f"{out[f'G{g}']['max_dev_deg_to_3GHz']:.1f} deg")
    res["formula_check"] = out
    # the internal Z_OL and Z_i on the extraction grid, for each load: no load for the overlay on
    # Fig 8-22, 100 ohm for the analytical composite (composite_tia.ths_internal)
    for lab in ("noload", "RL100"):
        zl = np.load(base / lab / "zol.npy")
        fz, Zm, Zinm = zl[0], zl[1] + 1j * zl[2], zl[3] + 1j * zl[4]
        s = 2j * np.pi * fz
        zi = Zinm / (1 - s * C12_MODEL * Zinm)
        z_int = Zm * (1 + s * C12_MODEL * zi)
        np.save(base / f"zol_internal_{lab}.npy", np.vstack([fz, z_int.real, z_int.imag, zi.real, zi.imag]))
    a = np.load(base / "zol_internal_noload.npy")
    fz, z_int = a[0], a[1] + 1j * a[2]
    for x in (1e8, 3e8, 5e8, 7.7e8):
        k = int(np.argmin(np.abs(np.log10(fz) - np.log10(x))))
        zd = ct.zol(np.array([x]))[0]
        print(f"   internal Z_OL (no load) {x/1e6:5.0f} MHz: {20*np.log10(abs(z_int[k])):5.1f} dBohm "
              f"{np.degrees(np.angle(z_int[k])):7.1f} deg | Fig 8-22 {20*np.log10(abs(zd)):5.1f} dB "
              f"{np.degrees(np.angle(zd)):7.1f} deg")
    return res


def export_overlay(spice):
    """SPICE curves for overlay_digitized.py --spice: the model's closed loop on Fig 8-1 and its
    open-loop transimpedance (at the pin and internal) on Fig 8-22."""
    base = spice / "runs" / "composite"
    cols = {2: (0, 0, 0), 5: (230, 0, 0), 10: (110, 110, 110), 20: (40, 100, 120)}
    fig81 = []
    for g, rf, rg in TABLE_9_2:
        cl = np.load(base / "ths_referee" / f"G{g}" / "cl.npy")
        v = np.abs(cl[1] + 1j * cl[2])
        fig81.append(dict(x=list(cl[0] / 1e6), y=list(20 * np.log10(v / v[0])), color=cols[g], style="dotted"))
    zl = np.load(base / "ths_zol" / "noload" / "zol.npy")
    Z = zl[1] + 1j * zl[2]
    zi_ = np.load(base / "ths_zol" / "zol_internal_noload.npy")
    Zi = zi_[1] + 1j * zi_[2]
    fig822 = [dict(x=list(zl[0]), y=list(20 * np.log10(np.abs(Z))), color=(0, 90, 255), style="dotted", axis="left"),
              dict(x=list(zl[0]), y=list(np.degrees(np.unwrap(np.angle(Z)))), color=(0, 170, 0), style="dotted",
                   axis="right"),
              dict(x=list(zi_[0]), y=list(20 * np.log10(np.abs(Zi))), color=(0, 90, 255), axis="left"),
              dict(x=list(zi_[0]), y=list(np.degrees(np.unwrap(np.angle(Zi)))), color=(0, 170, 0), axis="right")]
    out = {"THS3491_Fig8-1_model_check": fig81, "THS3491_Fig8-22_Zol_spice": fig822}
    path = spice / "results" / "composite_overlay_curves.json"
    path.write_text(json.dumps(out, default=float), encoding="utf-8")
    print("wrote", path.name)


# ---------------------------------------------------------------- the high-voltage composite
R_L2 = 100.0          # load at the high-voltage output, as in the THS3491 characterization (Fig 9-4)


def hv_text(title, g2, c_f, c_l, c_d, vinj=0, iinj=0, iph=0):
    """The composite: OPA859 (+/-2.5 V) inverting at the summing node inm, the THS3491 (+/-15 V,
    gain g2 with Table 9-2's R_F2 interpolated) driven from the OPA859 output, R_F || C_F from the
    high-voltage output o2 to inm, C_L from the OPA859 output to inm.  Middlebrook's injection sits
    between the OPA859 output pin (oa) and the node it drives (o1)."""
    rf2 = ct.rf2_for(g2)
    rg2 = rf2 / (g2 - 1)
    text = header_ths(title, with_opa859=True)
    text += "XU1 " + VENDOR_MODELS["OPA859"]["inst"].format(p="0", n="inm", o="oa") + "\n"
    text += f"Vinj o1 oa DC 0 AC {vinj}\nIinj 0 o1 DC 0 AC {iinj}\n"
    text += ths("o1", "n2", "o2")
    text += f"RF2 o2 n2 {rf2:.6g}\nRG2 n2 0 {rg2:.6g}\nRL o2 0 {R_L2:g}\n"
    text += f"RF o2 inm {ct.R_F:g}\nCF o2 inm {c_f:.6g}\nCX inm 0 {c_d + ct.C_PCB_NOM:.6g}\n"
    if c_l > 0:
        text += f"CL o1 inm {c_l:.6g}\n"
    text += f"Iph 0 inm DC 0 AC {iph}\n"
    return text


def hv_point(ng, folder, title, g2, c_f, c_l, c_d, conv, noise=True):
    """One design: loop gain (Middlebrook, both injections), transimpedance, and input-referred
    noise; every figure next to the analytical value (macromodel parameters, composite_tia)."""
    ctl = (".control\nset wr_singlescale\nset wr_vecnames\nop\nprint v(o2) v(oa) v(inm) i(vcc) i(vcc2)\n"
           "ac dec 100 100k 5G\nwrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(o1)) imag(v(o1))\n"
           "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 5G\n"
           "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n"
           "alter @iinj[acmag] = 0\nalter @iph[acmag] = 1\nac dec 100 100k 5G\n"
           "wrdata zt.txt real(v(o2)) imag(v(o2))\n.endc\n.end\n")
    lines, hits = run_logged(ng, folder, hv_text(title, g2, c_f, c_l, c_d, vinj=1) + ctl, conv)
    v, c, z = (read_wrdata(folder / n) for n in ("vinj.txt", "iinj.txt", "zt.txt"))
    f = v[:, 0]
    Tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
    iv = c[:, 1] + 1j * c[:, 2]
    Ti = iv / (1 - iv)
    T = (Tv * Ti - 1) / (Tv + Ti + 2)
    Z = z[:, 1] + 1j * z[:, 2]
    np.save(folder / "loop_zt.npy", np.vstack([f, T.real, T.imag, Z.real, Z.imag]))
    lm, zm = loop_metrics_from_T(f, T), zt_metrics(f, Z)
    out = dict(f_c_MHz=lm["f_c_MHz"], pm_deg=lm["pm_deg"], gm_dB=lm["gm_dB"], second_MHz=lm["second_crossing_MHz"],
               f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"], flags=hits,
               op=[ln[7:] for ln in lines if re.match(r"stdout (v\(o2\)|v\(oa\)|v\(inm\)|i\(vcc\)|i\(vcc2\))\s*=", ln)])
    if noise:
        # in a deck of its own: after the op and ac analyses 'setplot noise1' finds no such plot
        nf = folder / "noise"
        _, nhits = run_logged(ng, nf, hv_text(title + ", noise", g2, c_f, c_l, c_d) + (
            ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(o2) Iph dec 50 100k 1G\nsetplot noise1\n"
            "wrdata noise.txt inoise_spectrum\n.endc\n.end\n"), conv)
        out["flags"] = sorted(set(out["flags"]) | set(nhits))
        d = read_wrdata(nf / "noise.txt")
        fn, inn = d[:, 0], d[:, 1]
        out["noise_nA"] = float(np.sqrt(ct.band(fn, inn ** 2)) * 1e9)
        out["noise_100MHz_pA"] = float(np.interp(8.0, np.log10(fn), inn) * 1e12)
    return out


def analytical_point(cmp, c_f, c_l, c_d):
    T, Z, *_ = cmp.solve(c_f, c_l, c_d=c_d)
    m = ct.metrics(cmp.f, T, Z)
    nz = cmp.noise(c_f, c_l, c_d=c_d)
    m["noise_nA"] = float(np.sqrt(ct.band(cmp.f, nz["total"])) * 1e9)
    m["noise_100MHz_pA"] = float(np.sqrt(np.interp(8.0, np.log10(cmp.f), nz["total"])) * 1e12)
    return m


def _fmt(v, p=1):
    return "none" if v is None else f"{v:.{p}f}"


# designs compared at nominal capacitances over the design space: (G2, C_F, C_L)
HV_COMPARE = ([(5.0, cf, cl) for cl in (1.0e-12, 2.0e-12, 3.0e-12, 4.0e-12) for cf in (0.10e-12, 0.20e-12, 0.30e-12)]
              + [(3.0, 0.10e-12, 3.0e-12), (8.0, 0.10e-12, 3.0e-12), (5.0, 0.20e-12, 0.0), (2.0, 0.375e-12, 0.0)])


def check_hv_compare(ng, spice, conv):
    """SPICE against Eqs. (72)-(73) with the macromodels' parameters, nominal capacitances, over
    the design space (dual topology at G2 = 5, a few other gains, two plain designs)."""
    res = {}
    base = spice / "runs" / "composite" / "hv_compare"
    cmps = {}
    for g2, cf, cl in HV_COMPARE:
        cmp = cmps.setdefault(g2, ct.HVComposite("macromodels", g2))
        tag = f"G{g2:g}_F{cf*1e12:.3f}p_L{cl*1e12:.1f}p".replace(".", "p")
        sp = hv_point(ng, base / tag, f"HV composite G2 = {g2:g}, C_F = {cf*1e12:.3f} pF, C_L = {cl*1e12:.1f} pF",
                      g2, cf, cl, ct.C_D, conv)
        an = analytical_point(cmp, cf, cl, ct.C_D)
        res[tag] = dict(g2=g2, c_f_pF=cf * 1e12, c_l_pF=cl * 1e12, spice=sp, analytical=an)
        print(f"{tag:22s} SPICE f_c {_fmt(sp['f_c_MHz'], 0)} PM {_fmt(sp['pm_deg'])} GM {_fmt(sp['gm_dB'])} f3 "
              f"{_fmt(sp['f3_MHz'], 0)} pk {sp['peak_dB']:.2f} n {sp['noise_nA']:.1f} | analytical f_c "
              f"{_fmt(an['f_c_MHz'], 0)} PM {_fmt(an['pm_deg'])} GM {_fmt(an['gm_dB'])} f3 {_fmt(an['f3_MHz'], 0)} "
              f"pk {an['peak_dB']:.2f} n {an['noise_nA']:.1f} | {sp['flags']}")
    return res


# designs verified over every capacitance corner: the robust designs of the macromodel description
# (composite_tia.py, fine scan) and the best two of the datasheet description that the macromodel
# description finds not robust: (label, G2, C_F, C_L)
HV_VERIFY = [("macromodels, G2 = 4", 4.0, 0.125e-12, 2.25e-12), ("macromodels, G2 = 4.5", 4.5, 0.100e-12, 2.50e-12),
             ("macromodels, G2 = 5", 5.0, 0.100e-12, 3.00e-12), ("macromodels, G2 = 5.5", 5.5, 0.100e-12, 3.25e-12),
             ("datasheet, G2 = 6", 6.0, 0.150e-12, 3.00e-12), ("datasheet, G2 = 7", 7.0, 0.150e-12, 3.75e-12)]


def check_hv_verify(ng, spice, conv):
    """Each design of HV_VERIFY at its 27 capacitance corners (C_D +/- 0.2 pF, C_F +/- 0.1 pF,
    C_L +/- 0.1 pF; composite_tia.corners) in SPICE, against the analytical worst case."""
    res = {}
    base = spice / "runs" / "composite" / "hv_verify"
    for label, g2, cf, cl in HV_VERIFY:
        cmp = ct.HVComposite("macromodels", g2)
        an = ct.hv_design(cmp, cf, cl)
        rows = []
        for cd, cfc, clc in ct.corners(cf, cl):
            tag = f"G{g2:g}_F{cf*1e12:.3f}p_L{cl*1e12:.2f}p__D{cd*1e12:.1f}_F{cfc*1e12:.3f}_L{clc*1e12:.2f}".replace(".", "p")
            nominal = abs(cd - ct.C_D) < 1e-18 and abs(cfc - cf) < 1e-18 and abs(clc - cl) < 1e-18
            sp = hv_point(ng, base / tag, f"HV composite {label}, corner C_D {cd*1e12:.1f} pF, C_F {cfc*1e12:.3f} pF, "
                          f"C_L {clc*1e12:.2f} pF", g2, cfc, clc, cd, conv, noise=nominal)
            rows.append(dict(c_d_pF=cd * 1e12, c_f_pF=cfc * 1e12, c_l_pF=clc * 1e12, nominal=nominal, **sp))
        pm = [r["pm_deg"] for r in rows]
        gm = [r["gm_dB"] for r in rows if r["gm_dB"] is not None]
        f3 = [r["f3_MHz"] for r in rows if r["f3_MHz"] is not None]
        worst = dict(pm_deg=None if None in pm else min(pm), gm_dB=min(gm) if gm else None,
                     peak_dB=max(r["peak_dB"] for r in rows), f3_MHz=min(f3) if len(f3) == len(rows) else None,
                     second=any(r["second_MHz"] for r in rows))
        nom = next(r for r in rows if r["nominal"])
        ok = (worst["pm_deg"] is not None and worst["pm_deg"] >= ct.CRITERIA["pm"]
              and (worst["gm_dB"] is None or worst["gm_dB"] >= ct.CRITERIA["gm"]) and worst["peak_dB"] <= ct.CRITERIA["peak"]
              and worst["f3_MHz"] is not None and worst["f3_MHz"] >= ct.CRITERIA["f3"] and not worst["second"])
        res[label] = dict(g2=g2, c_f_pF=cf * 1e12, c_l_pF=cl * 1e12, spice_worst=worst, spice_nominal=nom, spice_robust=ok,
                          analytical_worst=an["worst"], analytical_nominal=an["nominal"], analytical_noise_nA=an["noise_nA"],
                          analytical_robust=ct.robust(an), corners=rows)
        aw = an["worst"]
        print(f"{label:24s} C_F {cf*1e12:.3f} C_L {cl*1e12:.2f} | SPICE worst PM {_fmt(worst['pm_deg'])} GM {_fmt(worst['gm_dB'])} "
              f"pk {worst['peak_dB']:.2f} f3 {_fmt(worst['f3_MHz'], 0)} robust {ok} | analytical worst PM {_fmt(aw['pm_deg'])} "
              f"GM {_fmt(aw['gm_dB'])} pk {aw['peak_dB']:.2f} f3 {_fmt(aw['f3_MHz'], 0)} robust {ct.robust(an)} | noise SPICE "
              f"{nom['noise_nA']:.1f} / analytical {an['noise_nA']:.1f} nA")
    return res


TONE_FRACTIONS = np.round(np.arange(0.5, 1.301, 0.1), 2)
HV_TONE = [("macromodels, G2 = 5.5", 5.5, 0.100e-12, 3.25e-12), ("macromodels, G2 = 5", 5.0, 0.100e-12, 3.00e-12)]


def check_hv_tone(ng, spice, conv):
    """Large-signal limits, as Section 10's 'tone': a sine photocurrent at 100 and 150 MHz whose
    output amplitude is swept from 0.5 to 1.3 times the analytical ceiling (composite_tia, the
    smallest of the THS3491's Fig 9-4 limit and slew rate and |H2| times the OPA859's limits); the
    high-voltage output and the OPA859 output are read over the last 32 of 48 periods (256 points
    per period, Hann window); harmonics 2-5 give THD.  The THS3491's Fig 9-4 limit is internal
    saturation, which its macromodel does not model; the run locates the macromodels' own limits."""
    res = {}
    base = spice / "runs" / "composite" / "hv_tone"
    for label, g2, cf, cl in HV_TONE:
        cmp = ct.HVComposite("macromodels", g2)
        res[label] = {}
        for f0 in (100e6, 150e6):
            claim, lim, zt = cmp.ceiling(f0, cf, cl)
            sweep = []
            for frac in TONE_FRACTIONS:
                ipk = frac * claim / zt
                tag = f"G{g2:g}_f{f0/1e6:g}M_a{frac:g}".replace(".", "p")
                period, n_per = 1 / f0, 256
                tstep, tstop = period / n_per, 48 * period
                text = hv_text(f"HV composite {label}, tone {f0/1e6:g} MHz at {frac:g} x the ceiling", g2, cf, cl, ct.C_D)
                text = text.replace("Iph 0 inm DC 0 AC 0", f"Iph 0 inm SIN(0 {ipk:.6e} {f0:g})")
                text += (f".control\nset wr_singlescale\nset wr_vecnames\ntran {tstep:.4e} {tstop:.4e} 0 {tstep:.4e}\n"
                         "linearize v(o2) v(oa)\nwrdata tone.txt v(o2) v(oa)\n.endc\n.end\n")
                lines, hits = run_logged(ng, base / tag, text, conv)
                d = read_wrdata(base / tag / "tone.txt")
                t = d[:, 0]
                sel = t >= tstop - 32 * period - tstep / 2
                row = dict(frac=float(frac), ipk_mA=ipk * 1e3, flags=hits)
                for col, name in ((1, "o2"), (2, "oa")):       # wr_singlescale: time, v(o2), v(oa)
                    vv = d[sel, col][:32 * n_per]
                    vv = vv - np.mean(vv)
                    spec = np.abs(np.fft.rfft(vv * np.hanning(len(vv))))
                    h = [spec[32 * k] for k in (1, 2, 3, 4, 5)]
                    row[name] = dict(v_pos=float(np.max(vv)), v_neg=float(-np.min(vv)),
                                     hd2_dBc=float(20 * np.log10(h[1] / h[0])), hd3_dBc=float(20 * np.log10(h[2] / h[0])),
                                     thd_dBc=float(10 * np.log10(sum(x ** 2 for x in h[1:]) / h[0] ** 2)))
                sweep.append(row)
            fr = np.array([r["frac"] for r in sweep])
            thd = np.array([r["o2"]["thd_dBc"] for r in sweep])
            x60, x40 = _crossing(fr, thd, -60.0), _crossing(fr, thd, -40.0)
            res[label][f"{f0/1e6:g}MHz"] = dict(claim_V=claim, limit=lim, zt_ohm=zt, frac_at_thd_m60=x60, frac_at_thd_m40=x40,
                                               sweep=sweep)
            r1 = next(r for r in sweep if abs(r["frac"] - 1.0) < 1e-9)
            print(f"{label} {f0/1e6:5.0f} MHz: ceiling {claim:.2f} V ({lim}); THD -60 dBc at "
                  f"{'-' if x60 is None else f'{x60*claim:.2f} V ({x60:.2f} x)'}, -40 dBc at "
                  f"{'-' if x40 is None else f'{x40*claim:.2f} V ({x40:.2f} x)'}; at 1.0 x: output +{r1['o2']['v_pos']:.2f}/"
                  f"-{r1['o2']['v_neg']:.2f} V THD {r1['o2']['thd_dBc']:.1f} dBc, OPA859 +{r1['oa']['v_pos']:.2f}/"
                  f"-{r1['oa']['v_neg']:.2f} V | flags {r1['flags']}")
    return res


def _crossing(x, y, level):
    """First x at which y rises through level (linear interpolation), or None."""
    i = np.where((y[:-1] < level) & (y[1:] >= level))[0]
    if not len(i):
        return None
    i = i[0]
    return float(x[i] + (level - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i]))


# ---------------------------------------------------------------- the discrete-FET composite
# Q1 (common source, gate = summing node g) and Q2 (cascode, gate at V_B2) carry I_D through R_D
# from V_DD; the drain node d carries the compensation C_N to ground; an ideal level-shift source
# (V_LS, no noise) takes d to the OPA859 unity-gain buffer, whose output drives R_F || C_F back to
# g and a 200-ohm load.  The bias loop through R_F sets the gate at V_G; V_LS = V(d) - V_G.
# Cards (ngspice NJF, level 1).  LSBF862: Linear Systems' published card ("Updated LSBF862 SPICE
# Model", Rev 2, 2026-02-09; reference [S23] of the note), typed in unchanged and renamed from
# LSBF862_UPDATED.  It remains Linear Systems' model and is not covered by this repository's CC0
# dedication.  ngspice ignores the parameters its JFET does not have (NETLIST_NOTES).  CPH3910 and CE3512K2
# have no vendor SPICE model; their cards are built here from datasheet values at the operating
# point (square law with g_m = 2 I_D / V_ov, V_ov = V_GS - V_TO; BETA from I_D = BETA V_ov^2
# (1 + LAMBDA V_DS); LAMBDA from the output conductance; CGS and CGD the datasheet's C_iss - C_rss
# and C_rss, held constant by PB = 1000).
FET_CARDS = {
    "LSBF862": dict(
        model=".model LSBF862 NJF (VTO=-0.79 BETA=2.658E-2 VTOTC=-2.5m BETATCE=-0.5 LAMBDA=0.03 RD=7.5 RS=7.5 "
              "IS=1E-14 ISR=1E-13 N=1 NR=2 XTI=3 ZXTI=1 ALPHA=1E-4 VK=180 CGS=8P CGD=3.5P PB=0.5 M=0.33 MJ=0.33 "
              "FC=0.5 KF=8.75E-17 AF=1 GDSNOI=2 NLEV=3 MFG=Linear_Systems)",
        dropped="",
        source="Linear Systems, Updated LSBF862 SPICE Model, Rev 2 (2026-02-09), as published; ngspice ignores ISR, NR, "
               "ZXTI, ALPHA, VK and MJ ('unrecognized parameter - ignored') and accepts M and MFG without effect"),
    "CPH3910": dict(
        model=".model CPH3910 NJF (VTO=-1.5 BETA=1.2E-2 LAMBDA=0.0222 CGS=3.7P CGD=2.3P PB=1000 IS=1E-14)",
        dropped="",
        source="constructed from onsemi CPH3910/D Rev 2 (2022-02) p1: I_DSS 20-40 mA (30 mA taken), |y_fs| 40 mS typ "
               "and C_iss 6.0 / C_rss 2.3 pF at V_DS 5 V, V_GS 0; p2 Fig 2: about 0.6 mS output conductance at 30 mA. "
               "V_ov = 2 x 30 mA / 40 mS = 1.5 V, so VTO = -1.5 V; LAMBDA = 0.0222 gives 0.6 mS; BETA = 30 mA / "
               "(1.5 V^2 x (1 + 5 LAMBDA)).  Its cutoff (Fig 4: about -1.2 V) is not matched; only the operating point is"),
    "CE3512K2": dict(
        model=".model CE3512K2 NJF (VTO=-0.79 BETA=5.95E-2 LAMBDA=0.5 CGS=0.238P CGD=0.028P PB=1000 IS=1E-14)",
        dropped="",
        source="constructed from CEL CDS-0018-05 Issue B (2018-11) p3: G_m 69 mS typ at V_DS 2 V, I_D 10 mA; p4: "
               "I_D = 10 mA at V_GS about -0.5 V (I_D-V_GS curve) and about 2.5 mS output conductance (I_D-V_DS "
               "curves); V_ov = 2 x 10 mA / 69 mS = 0.29 V, VTO = -0.5 - 0.29 V; LAMBDA = 0.5 gives 2.5 mS at 10 mA; "
               "CGS = C11 - C_gd = 0.266 - 0.028 pF and CGD = 0.028 pF from the S-parameters at 2 V, 10 mA, 2 GHz "
               "(s2p file CE3512K2v02n_2-26G_2V_10mA).  The gate current is a separate diode of IS = 1 uA (the value "
               "of Table 11.4), whose shot noise ngspice includes"),
    # the bipolar front end: Infineon's own model (Gummel-Poon, SPICE 2G6 syntax, v2.0 June 2011, valid to
    # 10 GHz) with the SOT-343 package parasitics and the ESD-protection network; subcircuit pins C B E1 E2
    "BFP740ESD": dict(
        model=None, file="BFP740ESD/bfp740esd-spice-v2.mdl", dropped="",
        source="Infineon Technologies, BFP740ESD Gummel-Poon model v2.0 (June 2011), bfp740esd-spice-v2.mdl"),
}
FET_RL = ct.FET_RL        # buffer output load, as the OPA859 TIA decks of Section 10


def fet_cards_lib(spice):
    """The NJF cards in runs/_models/fet_cards.lib (the LSBF862 card is Linear Systems' model), and
    translated copies of the vendor model files (BFP740ESD) beside it."""
    lines = ["* NJF cards for the discrete-FET composite (spice_composite_checks.py FET_CARDS)"]
    for name, c in FET_CARDS.items():
        if c["model"] is None:
            src = spice / "models" / c["file"]
            (spice / "runs" / "_models" / src.name).write_text(translate_model(src.read_text(encoding="latin-1")),
                                                               encoding="latin-1")
            continue
        lines += [f"* {name}: {c['source']}"] + ([f"* parameters not in ngspice's JFET, left out: {c['dropped']}"]
                                                  if c["dropped"] else []) + [c["model"]]
    lines += ["* gate-leakage diode for the shot noise of the pHEMT's gate current (CE3512K2: 1 uA)",
              ".model DLEAK D (IS=1u N=1 CJO=0 RS=0)"]
    dst = spice / "runs" / "_models" / "fet_cards.lib"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dst


def dev_includes(design, up):
    """.include lines for a design's device model."""
    c = FET_CARDS[ct.FET_DESIGN[design]["model"]]
    inc = f".include {up}_models/fet_cards.lib\n"
    if c["model"] is None:
        inc += f".include {up}_models/{Path(c['file']).name}\n"
    return inc


def dev_line(design, name, c, b, e):
    """Instance line of a design's transistor: drain/collector c, gate/base b, source/emitter e."""
    d = ct.FET_DESIGN[design]
    if d["kind"] == "bjt":
        return f"X{name} {c} {b} {e} {e} {d['model']}\n"
    return f"J{name} {c} {b} {e} {d['model']}\n"


def fet_text(title, dev, c_n, c_f, c_d, vinj=0, iinj=0, iph=0, v_ls=None, extra="", depth=3):
    """The FET composite deck (see the comment above FET_CARDS).  Middlebrook's injection sits
    between the buffer's output pin (oa) and the feedback network (fb).  depth: folder levels from
    the deck up to runs/."""
    b = ct.FET_DESIGN[dev]
    v_ls = (b["v_d"] - b["v_g"]) if v_ls is None else v_ls
    vb2 = b["v_x"] + b["v_g"] - b["v_s"]           # same device and current: V_GS2 = V_GS1 (V_BE2 = V_BE1)
    up = "../" * depth
    src = "s1" if b["v_s"] != 0 else "0"
    text = (f"* {title}\n" + dev_includes(dev, up) +
            f".include {up}_models/{Path(VENDOR_MODELS['OPA859']['lib']).name}\n.temp 25\n"
            f"VDD vdd 0 DC {b['vdd']:g}\nVCC vcc 0 DC 2.5\nVEE vee 0 DC -2.5\nVB2 b2 0 DC {vb2:.6g}\n"
            + (f"VS1 s1 0 DC {b['v_s']:g}\n" if src != "0" else "")
            + dev_line(dev, "1", "x", "g", src) + dev_line(dev, "2", "d", "b2", "x") +
            f"RD vdd d {b['r_d']:g}\nCN d 0 {c_n:.6g}\n"
            f"VLS d bi DC {v_ls:.6g}\n"
            "XB " + VENDOR_MODELS["OPA859"]["inst"].format(p="bi", n="oa", o="oa") + "\n"
            f"Vinj fb oa DC 0 AC {vinj}\nIinj 0 fb DC 0 AC {iinj}\nRL oa 0 {FET_RL:g}\n"
            f"RF fb g {ct.R_F:g}\nCF fb g {c_f:.6g}\nCX g 0 {c_d + ct.C_PCB_NOM:.6g}\nIph 0 g DC 0 AC {iph}\n")
    if b["i_g"] > 0:
        text += "VNEG vneg 0 DC -5\nDG vneg g DLEAK\n"
    return text + extra


def check_fet_devices(ng, spice, conv):
    """For each device: the composite's operating point; each FET's two-port Y-parameters (common
    source) at its own operating point there; Q1's input-referred voltage noise (common source with
    a noiseless current-sensing load); and the buffer's gain and input admittance with its loads.
    Saved under runs/composite/fet_devices/<device>/ for composite_tia.FETComposite."""
    res = {}
    base = spice / "runs" / "composite" / "fet_devices"
    for dev, dz in ct.FET_DESIGN.items():
        folder = base / dev
        # 1. operating point of the composite (nominal capacitances; they do not change the DC)
        text = fet_text(f"FET composite {dev}: operating point", dev, 2e-12, 0.25e-12, ct.C_D, depth=4) + (
            ".control\nop\nprint v(g) v(x) v(d) v(b2) v(oa) i(vdd)\n.endc\n.end\n")
        lines, hits = run_logged(ng, folder / "op", text, conv)
        op = {}
        for ln in lines:
            m = re.match(r"stdout (\S+)\s*=\s*([-+0-9.eE]+)", ln)
            if m:
                op[m.group(1)] = float(m.group(2))
        vg, vx, vd, vb2, vs = op["v(g)"], op["v(x)"], op["v(d)"], op["v(b2)"], dz["v_s"]
        biases = {"J1": (vg - vs, vx - vs), "J2": (vb2 - vx, vd - vx)}           # (V_GS or V_BE, V_DS or V_CE)
        out = dict(op=op, flags=hits, v_gs={k: v[0] for k, v in biases.items()}, v_ds={k: v[1] for k, v in biases.items()})
        dc = {}
        # 2. two-port Y-parameters at each transistor's bias: gate/base driven (drain AC-shorted), then
        # drain/collector driven; the DC currents of that bias point are printed first
        for jn, (vgs, vds) in biases.items():
            text = (f"* {dev} {jn} two-port at V_GS {vgs:.4f} V, V_DS {vds:.4f} V\n" + dev_includes(dev, "../../../../") +
                    f".temp 25\nVG g 0 DC {vgs:.6g} AC 1\nVD d 0 DC {vds:.6g} AC 0\n" + dev_line(dev, "1", "d", "g", "0") +
                    ".control\nset wr_singlescale\nset wr_vecnames\nop\nprint i(vg) i(vd)\nac dec 100 100k 5G\n"
                    "wrdata yg.txt real(i(vg)) imag(i(vg)) real(i(vd)) imag(i(vd))\n"
                    "alter @vg[acmag] = 0\nalter @vd[acmag] = 1\nac dec 100 100k 5G\n"
                    "wrdata yd.txt real(i(vg)) imag(i(vg)) real(i(vd)) imag(i(vd))\n.endc\n.end\n")
            ylines, _ = run_logged(ng, folder / f"y_{jn}", text, conv)
            for ln in ylines:
                m = re.match(r"stdout i\((vg|vd)\)\s*=\s*([-+0-9.eE]+)", ln)
                if m:
                    dc[f"i_{'b' if m.group(1) == 'vg' else 'c'}{jn[-1]}"] = -float(m.group(2))
        (folder / "dc.json").write_text(json.dumps(dc, indent=1), encoding="utf-8")
        out["dc"] = dc
        for jn in biases:
            g_ = read_wrdata(folder / f"y_{jn}" / "yg.txt")
            d_ = read_wrdata(folder / f"y_{jn}" / "yd.txt")
            f = g_[:, 0]
            # source currents flow out of the + terminal: the current into the device is -i(source)
            y11, y21 = -(g_[:, 1] + 1j * g_[:, 2]), -(g_[:, 3] + 1j * g_[:, 4])
            y12, y22 = -(d_[:, 1] + 1j * d_[:, 2]), -(d_[:, 3] + 1j * d_[:, 4])
            np.save(folder / f"y_{jn}.npy", np.vstack([f, y11, y12, y21, y22]))
            k = int(np.argmin(np.abs(f - 1e6)))
            w = 2 * np.pi * f[k]
            out[f"y_{jn}_1MHz"] = dict(gm_mS=float(y21[k].real * 1e3), gds_mS=float(y22[k].real * 1e3),
                                       c11_pF=float(y11[k].imag / w * 1e12), cgd_pF=float(-y12[k].imag / w * 1e12))
        # 3. Q1's input-referred voltage noise: drain at V_DS through a noiseless current sense (H)
        vgs, vds = biases["J1"]
        text = (f"* {dev} input voltage noise at V_GS {vgs:.4f} V, V_DS {vds:.4f} V\n" + dev_includes(dev, "../../../../") +
                f".temp 25\nVG g 0 DC {vgs:.6g} AC 1\nVD dd 0 DC {vds:.6g}\nVS dd d DC 0\n" + dev_line(dev, "1", "d", "g", "0") +
                "HS out 0 VS 1\nRO out 0 1G\n.model rnl r(noisy=0)\n"
                ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(out) VG dec 20 100k 1G\nsetplot noise1\n"
                "wrdata en.txt inoise_spectrum\n.endc\n.end\n").replace("RO out 0 1G", "RO out 0 rnl 1G")
        run_logged(ng, folder / "en", text, conv)
        e = read_wrdata(folder / "en" / "en.txt")
        np.save(folder / "en.npy", np.vstack([e[:, 0], e[:, 1]]))
        out["e_n_nV"] = {f"{x/1e6:g}MHz": float(np.interp(np.log10(x), np.log10(e[:, 0]), e[:, 1]) * 1e9)
                         for x in (1e6, 1e7, 1e8)}
        # 4. the buffer: gain V(oa)/V(bi) and input admittance, loaded by R_L and R_F to the virtual ground
        text = (f"* OPA859 unity-gain buffer for the {dev} composite\n"
                f".include ../../../../_models/{Path(VENDOR_MODELS['OPA859']['lib']).name}\n.temp 25\n"
                f"VCC vcc 0 DC 2.5\nVEE vee 0 DC -2.5\nVS bi 0 DC {op['v(oa)']:.6g} AC 1\n"
                "XB " + VENDOR_MODELS["OPA859"]["inst"].format(p="bi", n="oa", o="oa") + "\n"
                f"RL oa 0 {FET_RL:g}\nRF oa 0 {ct.R_F:g}\n"
                ".control\nset wr_singlescale\nset wr_vecnames\nac dec 100 100k 5G\n"
                "wrdata buf.txt real(v(oa)) imag(v(oa)) real(i(vs)) imag(i(vs))\n.endc\n.end\n")
        run_logged(ng, folder / "buffer", text, conv)
        bf = read_wrdata(folder / "buffer" / "buf.txt")
        Bv = bf[:, 1] + 1j * bf[:, 2]
        Yin = -(bf[:, 3] + 1j * bf[:, 4])
        np.save(folder / "buffer.npy", np.vstack([bf[:, 0], Bv, Yin]))
        k = int(np.argmin(np.abs(bf[:, 0] - 1e8)))
        out["buffer_100MHz"] = dict(gain_dB=float(20 * np.log10(abs(Bv[k]))), deg=float(np.degrees(np.angle(Bv[k]))),
                                    c_in_pF=float(Yin[k].imag / (2 * np.pi * bf[k, 0]) * 1e12))
        res[dev] = out
        print(f"{dev}: op V_G {vg:.3f} V_x {vx:.3f} V_d {vd:.3f} V_out {op.get('v(oa)', float('nan')):.3f} V, I(VDD) "
              f"{-op.get('i(vdd)', float('nan'))*1e3:.2f} mA | DC {({k: f'{v*1e3:.4g} mA' for k, v in dc.items()})}, "
              f"Y at 1 MHz {out['y_J1_1MHz']} | J2 {out['y_J2_1MHz']} | e_n {out['e_n_nV']} | buffer {out['buffer_100MHz']} "
              f"| flags {sorted(set(hits))}")
    return res


def fet_point(ng, folder, title, dev, c_n, c_f, c_d, conv, noise=True):
    """One FET-composite design in SPICE: loop gain (Middlebrook at the buffer output), Z_T, noise."""
    ctl = (".control\nset wr_singlescale\nset wr_vecnames\nop\nprint v(g) v(d) v(oa) i(vdd)\n"
           "ac dec 100 100k 5G\nwrdata vinj.txt real(v(oa)) imag(v(oa)) real(v(fb)) imag(v(fb))\n"
           "alter @vinj[acmag] = 0\nalter @iinj[acmag] = 1\nac dec 100 100k 5G\n"
           "wrdata iinj.txt real(i(vinj)) imag(i(vinj))\n"
           "alter @iinj[acmag] = 0\nalter @iph[acmag] = 1\nac dec 100 100k 5G\n"
           "wrdata zt.txt real(v(oa)) imag(v(oa))\n.endc\n.end\n")
    lines, hits = run_logged(ng, folder, fet_text(title, dev, c_n, c_f, c_d, vinj=1) + ctl, conv)
    v, c, z = (read_wrdata(folder / n) for n in ("vinj.txt", "iinj.txt", "zt.txt"))
    f = v[:, 0]
    Tv = -(v[:, 1] + 1j * v[:, 2]) / (v[:, 3] + 1j * v[:, 4])
    iv = c[:, 1] + 1j * c[:, 2]
    Ti = iv / (1 - iv)
    T = (Tv * Ti - 1) / (Tv + Ti + 2)
    Z = z[:, 1] + 1j * z[:, 2]
    np.save(folder / "loop_zt.npy", np.vstack([f, T.real, T.imag, Z.real, Z.imag]))
    lm, zm = loop_metrics_from_T(f, T), zt_metrics(f, Z)
    out = dict(f_c_MHz=lm["f_c_MHz"], pm_deg=lm["pm_deg"], gm_dB=lm["gm_dB"], second_MHz=lm["second_crossing_MHz"],
               f3_MHz=zm["f3_MHz"], peak_dB=zm["peak_dB"], z_lf_ohm=zm["z_lf_ohm"], flags=hits,
               op=[ln[7:] for ln in lines if re.match(r"stdout (v\(g\)|v\(d\)|v\(oa\)|i\(vdd\))\s*=", ln)])
    if noise:
        nf = folder / "noise"
        _, nhits = run_logged(ng, nf, fet_text(title + ", noise", dev, c_n, c_f, c_d, depth=4) + (
            ".control\nset wr_singlescale\nset wr_vecnames\nnoise v(oa) Iph dec 50 100k 1G\nsetplot noise1\n"
            "wrdata noise.txt inoise_spectrum\n.endc\n.end\n"), conv)
        out["flags"] = sorted(set(out["flags"]) | set(nhits))
        d = read_wrdata(nf / "noise.txt")
        fn, inn = d[:, 0], d[:, 1]
        out["noise_nA"] = float(np.sqrt(ct.band(fn, inn ** 2)) * 1e9)
        out["noise_100MHz_pA"] = float(np.interp(8.0, np.log10(fn), inn) * 1e12)
    return out


def fet_analytical_point(cmp, c_n, c_f, c_d):
    T, Z, _ = cmp.solve(c_n, c_f, c_d=c_d)
    m = ct.metrics(cmp.f, T, Z)
    nz = cmp.noise(c_n, c_f, c_d=c_d)
    m["noise_nA"] = float(np.sqrt(ct.band(cmp.f, nz["total"])) * 1e9)
    m["noise_100MHz_pA"] = float(np.sqrt(np.interp(8.0, np.log10(cmp.f), nz["total"])) * 1e12)
    m["z_lf_ohm"] = float(abs(Z[0]))
    return m


FET_COMPARE = ([(dev, cn, cf) for dev in ("CE3512K2", "CPH3910", "LSBF862")
                for cn in (0.0, 3e-12, 10e-12) for cf in (0.2e-12, 0.5e-12)]
               + [(dev, cn, cf) for dev, cns in (("BFP740ESD_1mA", (2e-12, 4e-12, 10e-12)),
                                                 ("BFP740ESD_3mA", (4e-12, 8e-12, 20e-12)),
                                                 ("BFP740ESD_10mA", (10e-12, 20e-12, 60e-12)))
                  for cn in cns for cf in (0.3e-12, 0.6e-12)])


def check_fet_compare(ng, spice, conv):
    """SPICE against Eqs. (67)-(68) at nominal capacitances over the design space of each device."""
    res = {}
    base = spice / "runs" / "composite" / "fet_compare"
    cmps = {}
    for dev, cn, cf in FET_COMPARE:
        cmp = cmps.setdefault(dev, ct.FETComposite(dev))
        tag = f"{dev}_N{cn*1e12:.1f}p_F{cf*1e12:.2f}p".replace(".", "p")
        sp = fet_point(ng, base / tag, f"FET composite {dev}, C_N = {cn*1e12:.1f} pF, C_F = {cf*1e12:.2f} pF",
                       dev, cn, cf, ct.C_D, conv)
        an = fet_analytical_point(cmp, cn, cf, ct.C_D)
        res[tag] = dict(dev=dev, c_n_pF=cn * 1e12, c_f_pF=cf * 1e12, spice=sp, analytical=an)
        print(f"{tag:24s} SPICE f_c {_fmt(sp['f_c_MHz'], 0)} PM {_fmt(sp['pm_deg'])} GM {_fmt(sp['gm_dB'])} f3 "
              f"{_fmt(sp['f3_MHz'], 0)} pk {sp['peak_dB']:.2f} Z0 {sp['z_lf_ohm']:.0f} n {sp['noise_nA']:.1f} | analytical f_c "
              f"{_fmt(an['f_c_MHz'], 0)} PM {_fmt(an['pm_deg'])} GM {_fmt(an['gm_dB'])} f3 {_fmt(an['f3_MHz'], 0)} pk "
              f"{an['peak_dB']:.2f} Z0 {an['z_lf_ohm']:.0f} n {an['noise_nA']:.1f} | {sp['flags']}")
    return res


# the designs verified over the capacitance corners (C_D +/- 0.2 pF, C_F +/- 0.1 pF): the pHEMT's
# and each bipolar bias current's robust design of largest dynamic range at 0.1 mA, and each JFET's
# widest-band design that keeps PM >= 45 deg, GM >= 3 dB and peaking <= 1 dB (composite_tia.py):
# (design, C_N, C_F)
FET_VERIFY = [("CE3512K2", 8.0e-12, 0.55e-12), ("LSBF862", 0.0, 0.10e-12), ("CPH3910", 2.0e-12, 0.10e-12),
              ("BFP740ESD_1mA", 4.0e-12, 0.60e-12), ("BFP740ESD_3mA", 8.0e-12, 0.55e-12),
              ("BFP740ESD_10mA", 20.0e-12, 0.50e-12)]


def check_fet_verify(ng, spice, conv):
    res = {}
    base = spice / "runs" / "composite" / "fet_verify"
    for dev, cn, cf in FET_VERIFY:
        cmp = ct.FETComposite(dev)
        an = ct.fet_design(cmp, cn, cf)
        rows = []
        for cd, cfc, _ in ct.corners(cf, 0.0):
            tag = f"{dev}_N{cn*1e12:.1f}p_F{cf*1e12:.2f}p__D{cd*1e12:.1f}_F{cfc*1e12:.3f}".replace(".", "p")
            nominal = abs(cd - ct.C_D) < 1e-18 and abs(cfc - cf) < 1e-18
            sp = fet_point(ng, base / tag, f"FET composite {dev}, corner C_D {cd*1e12:.1f} pF, C_F {cfc*1e12:.3f} pF",
                           dev, cn, cfc, cd, conv, noise=nominal)
            rows.append(dict(c_d_pF=cd * 1e12, c_f_pF=cfc * 1e12, nominal=nominal, **sp))
        pm = [r["pm_deg"] for r in rows]
        gm = [r["gm_dB"] for r in rows if r["gm_dB"] is not None]
        f3 = [r["f3_MHz"] for r in rows if r["f3_MHz"] is not None]
        worst = dict(pm_deg=None if None in pm else min(pm), gm_dB=min(gm) if gm else None,
                     peak_dB=max(r["peak_dB"] for r in rows), f3_MHz=min(f3) if len(f3) == len(rows) else None,
                     second=any(r["second_MHz"] for r in rows))
        nom = next(r for r in rows if r["nominal"])
        aw = an["worst"]
        res[dev] = dict(c_n_pF=cn * 1e12, c_f_pF=cf * 1e12, spice_worst=worst, spice_nominal=nom,
                        analytical_worst=aw, analytical_nominal=an["nominal"], analytical_noise_nA=an["noise_nA"],
                        analytical_noise_parts_nA=an["noise_parts_nA"], corners=rows)
        print(f"{dev:9s} C_N {cn*1e12:.1f} C_F {cf*1e12:.2f} | SPICE worst PM {_fmt(worst['pm_deg'])} GM {_fmt(worst['gm_dB'])} pk "
              f"{worst['peak_dB']:.2f} f3 {_fmt(worst['f3_MHz'], 0)} | analytical worst PM {_fmt(aw['pm_deg'])} GM "
              f"{_fmt(aw['gm_dB'])} pk {aw['peak_dB']:.2f} f3 {_fmt(aw['f3_MHz'], 0)} | nominal f3 SPICE {_fmt(nom['f3_MHz'], 0)} "
              f"| noise SPICE {nom['noise_nA']:.1f} / analytical {an['noise_nA']:.1f} nA")
    return res


CHECKS = dict(ths_smoke=check_ths_smoke, ths_referee=check_ths_referee, ths_zol=check_ths_zol,
              hv_compare=check_hv_compare, hv_verify=check_hv_verify, hv_tone=check_hv_tone,
              fet_devices=check_fet_devices, fet_compare=check_fet_compare, fet_verify=check_fet_verify)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("check", choices=list(CHECKS) + ["all", "notes"],
                    help="a check, all of them, or 'notes': rewrite only the notes of composite_convergence.json")
    ap.add_argument("--ngspice", default=None, help="path of the ngspice shared library")
    ap.add_argument("--spice", default=str(HERE.parent / "spice"), help="spice folder (models/, runs/, results/)")
    a = ap.parse_args()
    spice = Path(a.spice)
    if a.check == "notes":                      # no simulation: keep the recorded decks, refresh the notes
        conv_path = spice / "results" / "composite_convergence.json"
        decks = json.loads(conv_path.read_text(encoding="utf-8"))["decks"]
        conv_path.write_text(json.dumps(dict(notes=CONVERGENCE_NOTES, netlist_notes=NETLIST_NOTES, decks=decks),
                                        indent=1), encoding="utf-8")
        print(f"notes rewritten; {len(decks)} decks kept")
        return
    ng = NgSpice(a.ngspice)
    prepared_ths(spice)
    prepared_model("OPA859", spice)
    fet_cards_lib(spice)
    conv_path = spice / "results" / "composite_convergence.json"
    conv = json.loads(conv_path.read_text(encoding="utf-8")).get("decks", {}) if conv_path.exists() else {}
    names = list(CHECKS) if a.check == "all" else [a.check]
    for name in names:
        print(f"\n===== {name}")
        found = {}
        out = CHECKS[name](ng, spice, found)
        conv.update(found)
        (spice / "results").mkdir(parents=True, exist_ok=True)
        (spice / "results" / f"composite_{name}.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
        if name == "ths_zol":
            export_overlay(spice)
        kinds = sorted({k for v in found.values() for k in v})
        for kind in kinds:
            decks = [d for d, v in found.items() if kind in v]
            print(f"  [{kind}] in {len(decks)} deck(s), e.g. {decks[0]}: {found[decks[0]][kind][:2]}")
            if kind not in CONVERGENCE_NOTES:
                print("    -> not yet explained in CONVERGENCE_NOTES")
    conv_path.write_text(json.dumps(dict(notes=CONVERGENCE_NOTES, netlist_notes=NETLIST_NOTES, decks=conv), indent=1),
                         encoding="utf-8")


if __name__ == "__main__":
    main()
