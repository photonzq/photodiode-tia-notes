"""One-off report edit of 27 Oct 2026: the coherent-receiver TIAs in Section 11.4 (MATA-006801
restated at one gain, GX39220 and RG8G32423 added, Eqs. (60)-(61)), the discrete-FET composite
front end as a new Section 11.5 (Eqs. (62)-(65), Tables 11.3-11.4), the verdict renumbered 11.6,
and the matching changes to Sections 0 and 0.7, Appendices 1-4.

Every edit is anchored on whole lines that must occur exactly once, so the script stops without
writing if the report has changed underneath it.  The numbers in the text come from
dr_comparison.py and fet_composite_bound.py.

Usage: python edit_report_coherent_fet.py <TIA_opamp_survey.md>
"""
import sys
from pathlib import Path


def _index(lines, prefix):
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(idx) == 1, (prefix[:70], len(idx))
    return idx[0]


def replace_line(t, prefix, new):
    lines = t.split("\n")
    lines[_index(lines, prefix)] = new
    return "\n".join(lines)


def append_after(t, prefix, extra):
    lines = t.split("\n")
    i = _index(lines, prefix)
    lines[i] = lines[i] + "\n" + extra
    return "\n".join(lines)


def replace_block(t, start, end, new):
    lines = t.split("\n")
    s, e = _index(lines, start), _index(lines, end)
    assert s < e, (start[:40], end[:40])
    return "\n".join(lines[:s] + new.split("\n") + lines[e:])


def replace_once(t, old, new):
    assert t.count(old) == 1, (old[:70], t.count(old))
    return t.replace(old, new)


# ------------------------------------------------------------------ front matter and Section 0.7
DATE_OLD = "Survey and engineering comparison, 25 October 2026, revised 26 October 2026."
DATE_NEW = "Survey and engineering comparison, 25 October 2026, revised 26 and 27 October 2026."
READ_OLD = ("Section 11 compares the dynamic range of the leading designs, from their macromodels, with that of "
            "single-chip TIAs, and takes one design apart to show what sets it.")
READ_NEW = ("Section 11 compares the dynamic range of the leading designs, from their macromodels, with that of "
            "single-chip TIAs, lidar and coherent-receiver parts, takes one design apart to show what sets it, "
            "and asks what a discrete-FET front end would add.")

S07_HEAD = r"### 0.7 Dynamic range: what sets it, single-chip TIAs and a FET front end (Section 11)"
S07_TIA = r"""- **No single-chip lidar TIA comes within 10 dB at 1 mA.** Their linear input ranges are 3–250 µA, against 0.77–1.14 mA for the op-amp designs; the best, LMH32401 at 2 kΩ, gives 57.2 dB at 1 mA against 67.6–70.7 dB (Section 11.4).
- **The coherent-receiver TIAs, made for a balanced pair with one photodiode on each input, are 8.8–32.1 dB behind at 1 mA at the gains where their noise is published.** Their output is held at a few hundred millivolts, so at those gains their linear input is only 38–500 µA peak (Eq. (60)). GX39220 at 500 Ω, the only one with a full public datasheet, gives 58.8 dB, and MATA-006801 at its 2 kΩ gives 52.5 dB. Their full 3 mAppd of linear input holds only at 167–233 Ω, where no noise is published; there a TIA would match OPA818 at 1 mA only if it added no more than 17.9 pA/√Hz within 150 MHz (Section 11.4, Eq. (61)).
- **A discrete-FET composite front end cannot gain more than that 0.8 dB over OPA855 at 0.1 mA.** Silicon JFETs with sub-nanovolt noise bring 6–20 pF to a node of 1.6 pF and at best tie with OPA855; GaAs pHEMTs reach the floor of $R_F$ only if their gate current, which no datasheet gives at the operating point, is below about 1 µA. A composite would pay off in the output stage instead, where each doubling of the ceiling gains 6 dB (Section 11.5)."""

# ------------------------------------------------------------------ Section 11 head, 11.1, Figure 15
S11_HEAD = r"## 11. Dynamic range compared: the leading designs in SPICE, what limits them, single-chip TIAs and a FET front end"
S11_INTRO_TIA = r"- Section 11.4 compares single-chip TIAs on the same definition, from their public datasheets: lidar TIAs and the coherent-receiver TIAs made for a balanced pair (Table 11.2, Figure 15(c)–(d))."
S11_INTRO_REST = r"""- Section 11.5 asks whether a discrete-FET composite front end would lower the floor enough to matter (Tables 11.3–11.4).
- Section 11.6 gives the verdict."""
S111_TIA = r"- **Single-chip TIAs** (Section 11.4): $I_{\max}$ is the datasheet's linear input range, as rms, and $S_{i,0}$ the datasheet's input-referred noise density, taken as white over 0–150 MHz. For the variable-gain coherent-receiver TIAs both are taken at the one gain setting at which the noise is published (Eq. (60))."
FIG15_C = r"- *(c) The single-chip TIAs of Table 11.2 that reach 150 MHz with a linear gain, against $I_1 + I_2$ for a 100-MHz tone, from their datasheets' linear input range and band noise. The coherent-receiver TIAs (MATA-006801, GX39220, RG8G32423) are drawn at the gain at which their noise is published (Eq. (60)); GX39220's curve ends at 8 mA, its limit of 4 mA of DC on each input. Dashed dark grey: the best of OPA855, OPA955, OPA818 and OPA858 in SPICE at each point; LMH6629 is left out (Section 11.2).*"
FIG15_LIST = r"- *Amplifiers: OPA855, OPA955, OPA818, LMH6629 (COMP HI) and OPA858; single-chip TIAs: LMH32401, LMH32404, LMH34400, MAX40660, MAX40662, MAX40658, LTC6561, HMC799, MATA-006801 (2 kΩ, product-page values), GX39220 (500 Ω) and RG8G32423 (6 kΩ, short-form datasheet).*"

# ------------------------------------------------------------------ Section 11.4
S114_INTRO = r"Section 3.5 listed the single-chip TIAs on the market, and Section 7.7 showed that none can carry 0.1–10 mA of DC through its input. With the balanced pair and its imbalance servoed to zero (Section 7.10), a TIA with one input carries no DC. Two kinds are compared here: the lidar TIAs of Section 3.5, and the TIAs of coherent optical receivers, which are made for a balanced photodiode pair with one photodiode on each of two inputs. Their dynamic range on the definition of Eq. (57) depends on two datasheet quantities, the linear input current and the input-referred noise:"
S114_NOISE = r"""- **Noise.** The datasheet's input-referred noise integrated over 0–150 MHz, at the photodiode capacitance nearest 1 pF. Where only a density is given, it is taken as white. The coherent-receiver TIAs give only one average over their whole 24–65-GHz band, whose upper part is dominated by the voltage noise acting on the input capacitance (Eq. (17)); their noise within 150 MHz is not published (Appendix 1, item 19).

**Variable gain.** The coherent-receiver TIAs have a gain control, manual or automatic, that holds their differential output at a few hundred millivolts for the ADC that follows. Their documents quote a largest linear input that holds only at a low gain beside a noise figure that is lowest at the highest gain, so both must be taken at one setting. At the setting where the noise is published,

$$
I_{\mathrm{pk}} = \min\!\left(\frac{V_{\mathrm{lin,pp}}}{2Z_T},\ \frac{I_{\mathrm{in,pp}}}{2}\right),
\tag{60}
$$

where $V_{\mathrm{lin,pp}}$ is the largest differential output, peak to peak, that the document shows as linear, $Z_T$ the differential transimpedance at that setting, and $I_{\mathrm{in,pp}}$ the largest differential input current, peak to peak, that the document allows. These parts define the differential input current as $I_{\mathrm{in}} = I_{\mathrm{INP}} - I_{\mathrm{INN}}$, the difference of the currents into their two inputs (GX39220, note 1 on p. 10). That is the pair's difference current, the current the op-amp TIA receives, so their input and noise figures compare directly with Table 11.1. For GX39220 at 500 Ω, Eq. (60) gives $I_{\mathrm{pk}} = \min(0.50\ \mathrm{V}/(2 \times 500\ \Omega),\ 3\ \mathrm{mA}/2) = \min(0.50,\ 1.5)$ mA = 0.50 mA."""
S114_CAPTION = r"""*Table 11.2. Single-chip TIAs on the definition of Eq. (57), from their public datasheets, with the imbalance servoed to zero: transimpedance setting and bandwidth at the photodiode capacitance nearest 1 pF; input-referred noise over 0–150 MHz (density in brackets); the largest bipolar peak input current $I_{\mathrm{pk}}$ shown as linear, and its basis; dynamic range for a 100-MHz tone. The coherent-receiver TIAs are taken at the gain at which their noise is published (Eq. (60)). "Curve": read from a plotted curve; "derived": computed here (`data/integrated_tias.json`). For comparison, the SPICE designs of Table 11.1 give 79.5–82.9 dB in the dark and 67.6–70.7 dB at 1 mA. Datasheet revisions: Table A2.2. Amplifiers (single-chip TIAs): LMH32401, HMC799, LMH32404, MAX40662, MAX40660, LTC6561, LMH34400, MAX40658, GX39220, MATA-006801, RG8G32423, OPA857, ADA4355 (one per row).*"""
S114_ROWS = r"""| GX39220 (Renesas) | 500 Ω of 50–3,250 Ω, one photodiode on each input; 65 GHz with a 40-fF photodiode (p9); obsolete | 343 nA rms (28, the average to 65 GHz at 500 Ω, p9, taken as white) | 0.50 mA: THD 1.5 % for outputs below 500 mVppd (p9), at 500 Ω (Eq. (60), derived) | 60.3 / 60.1 / 58.8 / – (54.0 at its 8-mA limit) |
| MATA-006801 (MACOM) | 2 kΩ, one photodiode on each input; 45 GHz | 196 nA rms (16, product page, taken as white) | 175 µA: its 700-mVppd output swing at 2 kΩ (product page; Eq. (60), derived) | 56.0 / 55.5 / 52.5 / 44.7 |
| RG8G32423 (Renesas) | 6 kΩ of 250–6,000 Ω, four channels; 24 GHz | 220 nA rms (< 18, short-form datasheet, taken as white) | 37.5 µA: THD below 3 % at 450 mVppd (short form p1; Eq. (60), derived; a looser criterion) | 41.6 / 41.2 / 38.6 / 31.2 |"""
S114_EXAMPLE = r"""
**Worked example, GX39220 at 500 Ω and $I_1 + I_2$ = 1 mA.** Eq. (60) gives $I_{\mathrm{pk}}$ = 0.50 mA, so $I_{\max}$ = 0.50 mA / $\sqrt2$ = 353.6 µA rms. Its 28 pA/√Hz, taken as white, gives 28 pA/√Hz × $\sqrt{150\ \mathrm{MHz}}$ = 342.9 nA rms, and with the shot noise $i_{n,B} = \sqrt{342.9^2 + 219.2^2}$ nA = 407.0 nA rms. Then $\mathrm{DR}_{150\,\mathrm{MHz}} = 20\log_{10}(353.6\ \mathrm{\mu A}/407.0\ \mathrm{nA})$ = 58.8 dB, 8.8 dB below OPA855 and 11.9 dB below OPA818."""
S114_DC = r"- **The DC limits of Section 7.7 no longer decide.** For a TIA with one input the pair's DC never reaches that input; only the residual imbalance does, which the servo of Section 7.10 holds near zero. The ambient-light cancellation of the TI parts and the OFFSET inputs of the Maxim parts would carry that residual, and the shot noise of $I_1 + I_2$ is the same as for the op amps. A coherent-receiver TIA instead carries each photodiode's DC, about half of $I_1 + I_2$, on its own input and removes it with its DC loops. GX39220 allows 4 mA on each input and ±0.5 mA between the two (p. 9), so $I_1 + I_2$ up to 8 mA."

S114_COHERENT = r"""- **The coherent-receiver TIAs are 8.8–32.1 dB behind the op-amp designs at 1 mA, at the gains where their noise is published** (Figure 15(c)–(d)).
  - Their output is held at a few hundred millivolts, so their linear input falls as their gain rises: at the 0.5–6 kΩ where their noise is quoted, Eq. (60) allows 38–500 µA peak. Their full 3 mAppd of linear input needs 167 Ω (GX39220) to 233 Ω (MATA-006801), where no noise is published.
  - The dynamic range of 20 to more than 30 dB stated in their documents is the range of their gain control, which an automatic loop (1.1 MHz for GX39220, p. 10) uses to follow slow changes of the input level. It is not the ratio of the largest linear signal to the noise at one setting, which Eq. (57) measures.
  - GX39220 (Renesas, 2 × 96 Gbaud) is the only one with a full public datasheet. Its noise is 19, 22 and 28 pA/√Hz at 3.25 kΩ, 1 kΩ and 500 Ω, each the average up to 65 GHz, and its THD 1.5 % for outputs below 500 mVppd and 2 % up to 550 mVppd (p. 9). The 500-Ω setting gives the most, 58.8 dB at 1 mA and 1.6 dB above LMH32401; 1 kΩ gives 54.1 dB and 3.25 kΩ 44.6 dB. It is specified with a 30–50-fF photodiode on a 150–300-pH bond wire (p. 8), not with 1 pF. It is obsolete: Renesas's notice PLC250030 of 12 September 2025 set its last shipment for 12 September 2026 and names GX39221 as the replacement, whose full datasheet is not public.
  - MATA-006801 (MACOM, 2 × 64 Gbaud) lists 2 kΩ, 16 pA/√Hz and a 700-mVppd output swing, and calls differential inputs up to 3 mApp linear (product page). At 2 kΩ the swing allows 0.35 mApp, 175 µA peak, which gives 52.5 dB at 1 mA. At its manual-mode maximum of 1.5 kΩ, with the noise of 2 kΩ, it would give 55.0 dB. Pairing its 3 mApp with its 16 pA/√Hz, two figures that hold at different gains, would give 71.1 dB at 1 mA and 63.4 dB at 10 mA; that is an upper bound, reached only if its noise at 233 Ω were as low as at 2 kΩ.
  - RG8G32423 (Renesas, 4 × 32 Gbaud, active) gives 38.6 dB at 1 mA at 6 kΩ, from its short-form datasheet's noise below 18 pA/√Hz and THD below 3 % at 450 mVppd (p. 1).
- **The other coherent-receiver TIAs publish no figures that Eq. (60) can use.**
  - Renesas's short-form datasheets of GX39221, RG8G31220, RG8G31223, RG8G3122B and RG8G31420 (active) and of GX32222, GX32223, GX36220, GX36420 and RG8G3122A (obsolete) give only the gain range and the bandwidth, and GX32424's datasheet needs a login.
  - Marvell's (formerly Inphi's) product briefs of IN3250TA, IN3252TA, IN3254TA, IN6450TA, IN6452TA and IN6454TA give no gain, noise or linearity figure.
  - MaxLinear's MxL9105 and MxL9162 appear only in announcements from 2017.
  - Qorvo's TGA4861, TGA4864, TGA4868 and TGA4872 are discontinued. Their product pages give 20–24 pA/√Hz at 4.8–7.5 kΩ and THD below 1 % up to 350 mVpp single-ended, i.e. 700 mVppd, which on Eq. (60) gives 40.0–43.0 dB at 1 mA.
  - MACOM's other coherent TIAs (MATA-006406, MATA-006806, MATA-009803-06, MATA-012403 and MATA-012803) have product pages only, like MATA-006801.

**What the coherent class could reach depends on its noise at low gain, which no public document gives.** With 3 mAppd of linear input and no amplifier noise at all, the shot noise alone would allow 83.7, 73.7 and 63.7 dB at 0.1, 1 and 10 mA, above OPA818's 77.3, 70.7 and 61.2 dB. From Eqs. (56)–(57), the in-band noise density that a TIA may add and still match a design of dynamic range $\mathrm{DR}_{\mathrm{ref}}$ at the photocurrent $I_{\mathrm{DC}}$ is

$$
i_{n,\mathrm{allowed}} = \sqrt{\frac{1}{B}\left[\left(\frac{I_{\max}}{10^{\mathrm{DR}_{\mathrm{ref}}/20}}\right)^{2} - 2qI_{\mathrm{DC}}B\right]}.
\tag{61}
$$

With $I_{\max}$ = 1.5 mA / $\sqrt2$ = 1.061 mA rms and OPA818's 70.68 dB at 1 mA, the total noise may be 1.061 mA / 3418 = 310.3 nA rms. The shot noise takes 219.2 nA of it, which leaves $\sqrt{310.3^2 - 219.2^2}$ nA = 219.6 nA rms, so $i_{n,\mathrm{allowed}}$ = 219.6 nA / $\sqrt{150\ \mathrm{MHz}}$ = 17.9 pA/√Hz. Matching OPA855's 67.6 dB allows 31.2 pA/√Hz. GX39220's 28 pA/√Hz at 500 Ω is an average up to 65 GHz, and none of these parts states its noise at the 167–233-Ω setting (Appendix 1, item 19).

### 11.5 A discrete-FET composite front end

Section 11.3 showed that from about 0.15 mA up the ceiling, not the noise, sets the dynamic range. This section asks whether a discrete FET at the summing node could still lower the floor enough to matter below that. The front end considered is a common-source FET with a cascode at its drain, followed by an op amp, with $R_F$ from the op amp's output back to the FET's gate. Referred to the photocurrent, its input noise density is

$$
S_i(f) = \frac{4k_BT}{R_F} + 2qI_G + e_n^2\left[(2\pi f C_T)^2 + \frac{1}{R_F^2}\right],
\qquad
C_T = C_D + C_{\mathrm{PCB}} + C_F + C_{\mathrm{iss}} + C_{\mathrm{rss}},
\tag{62}
$$

where $k_B$ is Boltzmann's constant, $T$ = 298.15 K, $I_G$ the gate current, $e_n$ the FET's input voltage noise density, $C_{\mathrm{iss}}$ its input capacitance and $C_{\mathrm{rss}}$ its gate–drain capacitance. $C_{\mathrm{rss}}$ is counted once inside $C_{\mathrm{iss}}$ and once more as the Miller term of the cascoded drain, whose voltage gain is about −1. The op amp's own noise, divided by the FET's gain, is neglected. Integrated over 0–$B$,

$$
i_{n,B}^2 = B\left(\frac{4k_BT}{R_F} + 2qI_G + \frac{e_n^2}{R_F^2}\right) + \frac{e_n^2\,(2\pi C_T)^2\,B^3}{3}.
\tag{63}
$$

All numbers are for the baseline of this survey: $C_D$ = 1 pF, $C_{\mathrm{PCB}}$ = 0.35 pF, $C_F$ = 0.25 pF and $R_F$ = 2 kΩ, so the node without the FET is $C_x = C_D + C_{\mathrm{PCB}} + C_F$ = 1.60 pF. They come from `scripts_archive/fet_composite_bound.py`, with the device values of Table A2.3.

**Why the question arises.** In the survey's model at its SPICE design, OPA855's input noise at 100 MHz, 4.17 pA/√Hz, is $\sqrt{2.87^2 + 2.60^2 + 1.54^2}$ pA/√Hz. Of this, 2.87 pA/√Hz is the Johnson noise of $R_F$, 2.60 pA/√Hz the bipolar input current noise, and 1.54 pA/√Hz its $e_n$ of 0.99 nV/√Hz acting on 2.36 pF of node and feedback capacitance, together with the small $e_n/R_F$ term (Eq. (17)). At this node OPA855 thus loses more to its base current than to its voltage noise. A FET removes the current noise but adds its own capacitance, and Eq. (63) decides which effect wins. OPA955, with 0.56 pA/√Hz of current noise, and OPA818, with essentially none, have little to remove.

**The most any front end can gain.** A noiseless amplifier leaves only the Johnson noise of $R_F$, $\sqrt{4k_BTB/R_F}$ = 35.1 nA rms over 150 MHz. At the same ceiling, a front end with the dark band noise $i_{n,B}$ gains over a design with the dark band noise $i_{n,B,\mathrm{ref}}$, at the photocurrent $I_{\mathrm{DC}}$,

$$
\Delta\mathrm{DR} = 10\log_{10}\frac{i_{n,B,\mathrm{ref}}^2 + 2qI_{\mathrm{DC}}B}{i_{n,B}^2 + 2qI_{\mathrm{DC}}B}.
\tag{64}
$$

For OPA855 at 0.1 mA and a noiseless amplifier, $\Delta\mathrm{DR} = 10\log_{10}[(49.6^2 + 69.3^2)/(35.1^2 + 69.3^2)] = 10\log_{10}(7267/6039)$ = 0.80 dB. Table 11.3 gives the rest. In the receiver's range of 0.1–10 mA, no front end can gain more than 0.80 dB over OPA855 or 0.19 dB over OPA955.

*Table 11.3. The largest dynamic-range gain of any front end over the SPICE designs of Table 11.1 (Eq. (64)): a noiseless amplifier, which leaves the Johnson noise of $R_F$ (35.1 nA rms over 150 MHz), at the same ceiling. Amplifiers: OPA855, OPA955, OPA818 (one per row).*

| Against | Dark band noise (nA rms) | Gain at $I_1+I_2$ = 0 / 0.1 / 1 / 10 mA (dB) |
|---|---|---|
| OPA855 | 49.6 | 2.99 / 0.80 / 0.11 / 0.01 |
| OPA955 | 38.8 | 0.86 / 0.19 / 0.02 / 0.00 |
| OPA818 | 84.8 | 7.65 / 2.98 / 0.49 / 0.05 |

**What a FET would need.** Write the FET's transconductance as $g_m = 2\pi f_T C_{\mathrm{iss}}$, with $f_T$ its transit frequency, and its channel noise as $e_n^2 = 4k_BT\Gamma/g_m$, with $\Gamma$ = 2/3 for an ideal long-channel FET and about 1 for short channels. Neglecting $C_{\mathrm{rss}}$, the $e_n$ term of Eq. (63) is then proportional to $(C_x + C_{\mathrm{iss}})^2/C_{\mathrm{iss}}$, which is smallest at $C_{\mathrm{iss}} = C_x$. There $C_T = 2C_x$ and

$$
\frac{e_n^2\,(2\pi C_T)^2\,B^3}{3} = \frac{4k_BT\Gamma}{2\pi f_T C_x}\cdot\frac{(4\pi C_x)^2\,B^3}{3} = \frac{32\pi}{3}\,\frac{k_BT\,\Gamma\,C_x\,B^3}{f_T}.
\tag{65}
$$

A FET matches OPA855's band noise, with no gate current, if this term stays below $(49.59\ \mathrm{nA})^2 - (35.14\ \mathrm{nA})^2 = (34.99\ \mathrm{nA})^2$. For $\Gamma$ = 2/3 that needs $f_T \ge (32\pi/3) \times 4.116\times10^{-21}\ \mathrm{J} \times (2/3) \times 1.60\ \mathrm{pF} \times (150\ \mathrm{MHz})^3/(34.99\ \mathrm{nA})^2 = 4.966\times10^{-7}\ \mathrm{A^2\,Hz}/1.224\times10^{-15}\ \mathrm{A^2}$ = 0.41 GHz, and 0.61 GHz for $\Gamma$ = 1; either way $e_n$ must be at most 1.64 nV/√Hz at $C_{\mathrm{iss}}$ = 1.6 pF. Matching OPA955 leaves only 16.4 nA rms for the term and needs 1.84–2.76 GHz, with $e_n \le$ 0.77 nV/√Hz. A FET whose $C_{\mathrm{iss}}$ differs from $C_x$ needs $(C_x + C_{\mathrm{iss}})^2/(4C_xC_{\mathrm{iss}})$ times that $f_T$: 2.1 times for the 10 pF of BF862 and 1.5 times for the 6 pF of CPH3910.

*Table 11.4. Discrete FETs at their datasheet operating points as the input of a cascoded composite at 1 pF and 2 kΩ ($C_F$ = 0.25 pF, $C_x$ = 1.60 pF): transconductance, input and reverse capacitance, $f_T = g_m/(2\pi C_{\mathrm{iss}})$, voltage noise, the node capacitance $C_T$ of Eq. (62), the band noise over 0–150 MHz of Eq. (63) with a gate current of 1 µA or the datasheet's leakage limit if smaller, and with that limit, and the change of dynamic range against OPA855's SPICE design at the same ceiling (Eq. (64), positive is better). For the pHEMTs, $g_m$ is $\lvert Y_{21}\rvert$ and $C_{\mathrm{iss}}$ is $\mathrm{Im}(Y_{11})/\omega$ from their lowest-frequency published S-parameters, package and fixture included; $e_n$ marked "channel-thermal" is $\sqrt{4k_BT(2/3)/g_m}$, not a datasheet figure. Datasheets: Table A2.3. Amplifiers (discrete FETs): BF862, LSBF862, BF861C, CPH3910, 2SK3557, J310, LSK170, BF545C, ATF-34143, ATF-54143, ATF-55143, SAV-551+, SAV-541+, CE3512K2, CE3520K3 (one per row).*

| Device (type) | $g_m$ (mS) | $C_{\mathrm{iss}}$ / $C_{\mathrm{rss}}$ (pF) | $f_T$ (GHz) | $e_n$ (nV/√Hz) | $C_T$ (pF) | Band noise (nA rms) | Against OPA855 at 0 / 0.1 / 1 mA (dB) | Basis |
|---|---|---|---|---|---|---|---|---|
| BF862 (Si JFET) | 45 | 10 / 1.9 | 0.72 | 0.80 | 13.50 | 80.2 / 80.2 | −4.18 / −1.90 / −0.33 | $\lvert y_{fs}\rvert$, $C_{\mathrm{iss}}$ TYP at $I_{DSS}$; $e_n$ TYP at 100 kHz; $I_{GSS}$ 1 nA MAX (p4) |
| LSBF862 (Si JFET) | 42 | 11.5 / 3.5 | 0.58 | 0.80 | 16.60 | 95.3 / 95.3 | −5.68 / −2.82 / −0.54 | $Y_{fs}$ TYP; $e_n$ TYP at 10 kHz (p2) |
| BF861C (Si JFET) | 25 | 10 / 2.1 | 0.40 | 1.0 | 13.70 | 98.0 / 98.0 | −5.92 / −2.98 / −0.57 | $\lvert y_{fs}\rvert$ 20–30 mS, the middle (Table 7); $e_n$ about 1.0 at 1 MHz (Fig 14) |
| CPH3910 (Si JFET) | 40 | 6.0 / 2.3 | 1.06 | 0.52 | 9.90 | 49.4 / 49.4 | +0.03 / +0.01 / +0.00 | $\lvert y_{fs}\rvert$ TYP (p1); $e_n$ not stated, channel-thermal |
| 2SK3557 (Si JFET) | 35 | 10 / 2.9 | 0.56 | 0.56 | 14.50 | 64.6 / 64.6 | −2.30 / −0.92 / −0.15 | $\lvert y_{fs}\rvert$ TYP (p2); $e_n$ not stated above 1 kHz, channel-thermal |
| J310 (Si JFET) | 12 | 7.0 / 2.2 | 0.27 | 1.7 | 10.80 | 127.7 / 127.7 | −8.22 / −4.63 / −1.05 | Re($y_{fs}$) TYP at 100 MHz (onsemi p2); $e_n$ about 1.7 at 100 kHz and still falling (Fairchild Fig 11) |
| LSK170 (Si JFET) | 22 | 20 / 5 | 0.18 | 0.93 | 26.60 | 168.7 / 168.7 | −10.63 / −6.61 / −1.80 | $G_{fs}$ TYP (p2); $e_n$ flat from 100 Hz to 100 kHz (p6); $I_G$ 0.5 nA MAX |
| BF545C (Si JFET) | 6.5 | 3.0 / 0.9 | 0.34 | 1.3 | 5.50 | 59.7 / 59.7 | −1.62 / −0.62 / −0.09 | $\lvert y_{fs}\rvert$ MAX (Table 7); $e_n$ not stated, channel-thermal |
| ATF-34143 (GaAs pHEMT) | 152 | 1.23 / 0.17 | 19.67 | 0.36 | 3.00 | 36.6 / 52.3 | +2.64 / +0.73 / +0.10 | S-parameters at 3 V, 20 mA, 0.5 GHz (p7), derived; $e_n = \sqrt{4k_BT_0R_n}$, $R_n$ = 8 Ω at 0.5 GHz (p7); $I_{gss}$ 30 µA TYP at −4 V (p3) |
| ATF-54143 (GaAs pHEMT) | 319 | 2.61 / 0.18 | 19.45 | 0.18 | 4.39 | 36.2 / 104.3 | +2.73 / +0.75 / +0.10 | S-parameters at 3 V, 40 mA, 0.1 GHz (p6), derived; $R_n$ = 2 Ω at 0.5 GHz; $I_{gss}$ 200 µA MAX at −3 V |
| ATF-55143 (GaAs pHEMT) | 169 | 1.28 / 0.11 | 21.01 | 0.28 | 2.99 | 36.3 / 76.4 | +2.71 / +0.74 / +0.10 | S-parameters at 2 V, 20 mA, 0.1 GHz (p9), derived; $R_n$ = 5 Ω at 0.5 GHz; $I_{gss}$ 95 µA MAX at −2.7 V |
| SAV-551+ (GaAs pHEMT) | 208 | 2.02 / 0.20 | 16.39 | 0.24 | 3.82 | 36.4 / 76.4 | +2.69 / +0.74 / +0.10 | S2P file at 3 V, 15 mA, 0.1 GHz, derived; $R_n$ = 3.5 Ω at 0.5 GHz (p9); $I_{GSS}$ 95 µA MAX at −3 V |
| SAV-541+ (GaAs pHEMT) | 375 | 2.46 / 0.19 | 24.26 | 0.20 | 4.25 | 36.3 / 104.3 | +2.71 / +0.74 / +0.10 | S2P file, derived; $R_n$ = 2.5 Ω at 0.5 GHz; $I_{GSS}$ 200 µA MAX |
| CE3512K2 (GaAs pHEMT) | 72.9 | 0.27 / – | 43.62 | 0.39 | 1.87 | 36.2 / 41.8 | +2.73 / +0.75 / +0.10 | S-parameters at 2 V, 10 mA, 2 GHz, derived; no noise data below 2 GHz, channel-thermal; $I_{GSO}$ 0.4 µA TYP, 10 µA MAX at −3 V (p3) |
| CE3520K3 (GaAs pHEMT) | 60.0 | 0.35 / – | 27.13 | 0.43 | 1.95 | 36.3 / 41.9 | +2.70 / +0.74 / +0.10 | the same basis as CE3512K2; $I_{GSO}$ 0.4 µA TYP, 10 µA MAX at −3 V (p3) |

**Silicon JFETs do not work at 1 pF.** Their sub-nanovolt noise comes from large devices, and the 6–20 pF that comes with it swamps a node of 1.6 pF. BF862, the classic choice, comes out at 80.2 nA rms, close to OPA818's 84.8 nA and 4.2 dB worse than OPA855 in the dark. Only CPH3910 reaches parity, at 49.4 nA rms, and only if its noise sits at the channel-thermal value, which its datasheet does not state. NXP has discontinued BF862, and Linear Systems sells LSBF862 as its replacement. JFET composites pay off with photodiodes of tens of picofarads, not at 1 pF.

**GaAs pHEMTs could reach the floor of $R_F$, on four conditions.** Their 0.3–2.6 pF and $f_T$ of 16–44 GHz bring the band noise to 36.2–36.6 nA rms with 1 µA of gate current, within 0.4 dB of $R_F$ alone and 0.5–0.6 dB below OPA955 in the dark. Four things stand in the way:
- No datasheet gives the gate current at the operating point. The leakage limits they do give, 10–200 µA with the gate reverse-biased at −2.7 to −4 V, carry 1.8–8.0 pA/√Hz of shot noise; at those limits five of the seven would be worse than OPA855 (52.3–104.3 nA rms), and the two CEL parts, at 10 µA, still 1.5 dB better.
- Nothing is specified below 0.5 GHz, so their 1/f and trap noise across 1–150 MHz is unknown.
- Of the parts read, DigiKey lists SAV-551+ and CE3512K2 as active (27 October 2026); whether Broadcom still makes the ATF parts was not settled.
- A two-stage loop with a microwave transistor inside it needs its own stability design.

Even if all four go right, the gain over OPA855 in the receiver's range is at most 0.75 dB at 0.1 mA and 0.10 dB at 1 mA (Table 11.4), the bound of Table 11.3.

**Where a composite would pay off is the ceiling, not the noise.** From about 0.15 mA up the dynamic range follows the output amplitude dB for dB (Section 11.3, Figure 16). Raising $V_{\mathrm{pk}}$ at 100 MHz from OPA818's 2.23 V to 10 V would add $20\log_{10}(10/2.23)$ = 13.0 dB at every photocurrent; that needs a slew rate of at least $2\pi \times 100\ \mathrm{MHz} \times 10\ \mathrm{V}$ = 6.3 kV/µs and rails of about ±12 V. The composite worth building is therefore a low-noise input stage, OPA855 or OPA955 itself without a discrete FET, driving a fast high-voltage output stage inside the $R_F$ loop. That design is not studied here; its loop stability, its distortion at 20 Vpp and the converter that would follow it are open (Appendix 1, item 20). To use 70.7 dB in 150 MHz, an ADC whose full scale matches the TIA's largest tone needs a noise spectral density of $-70.7 - 10\log_{10}(150\ \mathrm{MHz})$ = −152.5 dBFS/Hz, and 85 dB would need −166.8 dBFS/Hz.
"""

S116 = r"""### 11.6 Verdict

- **For dynamic range at 0.1–10 mA, the discrete op-amp TIA of this survey remains the answer.** OPA818 (variant B) gives the most from about 70 µA up, for tones below about 145 MHz. OPA855, or OPA955 once released, gives the most in the dark and at the highest tones (Sections 11.2–11.3).
- **Every single-chip TIA with public figures is at least 8.8 dB behind at 1 mA.** The lidar TIAs have 3–250 µA of linear input, against the 0.77–1.14 mA of the op-amp designs. The coherent-receiver TIAs, at the gains where their noise is published, have 38–500 µA and are 8.8–32.1 dB behind (Section 11.4).
- **From about 0.15 mA up, the ceiling sets the dynamic range, not the noise.** Even a noiseless front end would gain at most 0.8 dB over OPA855 at 0.1 mA and 0.1 dB at 1 mA, while each doubling of the output amplitude gains 6 dB at every photocurrent (Section 11.3, Eq. (58); Table 11.3).
- **A discrete-FET front end does not pay at 1 pF.** Silicon JFETs at best tie with OPA855, and GaAs pHEMTs could come within 0.4 dB of $R_F$ alone only with a gate current below about 1 µA, which no datasheet gives (Section 11.5). A composite would pay off in a faster, higher-voltage output stage, which is not studied.
- **A coherent-receiver TIA could match OPA818 only at the low gain where its 3 mAppd of input stays linear, and only with no more than 17.9 pA/√Hz within 150 MHz there (Eq. (61)).** No public document gives that figure; a full datasheet or a measurement of GX39221 or MATA-006801 at that setting would settle it.

---
"""

# ------------------------------------------------------------------ Appendices
APP1_19_20 = r"""19. **Single-chip TIAs (Section 11.4).**
    - The coherent-receiver TIAs publish their noise only at their higher gains and only as an average over 24–65 GHz. Whether they can approach the op-amp designs depends on their noise within 150 MHz at the 167–233-Ω setting where their 3 mAppd stays linear (Eq. (61)): at most 17.9 pA/√Hz to match OPA818 at 1 mA, and 31.2 pA/√Hz to match OPA855. A full datasheet or a measurement of GX39221 or MATA-006801 at that setting would settle it.
    - MATA-006801's figures come from its product page, which lists a 2-kΩ gain beside a manual-mode range of 65 Ω to 1.5 kΩ and states no conditions for its 16 pA/√Hz. Its datasheet, available on request, would also give its low-frequency and DC behaviour.
    - GX39220 is specified with a 30–50-fF photodiode; its stability and noise with 1 pF are not specified, and it is obsolete.
    - The noise of RG8G32423 (below 18 pA/√Hz) and of the Qorvo parts is taken at their maximum gain, the usual condition, which their documents do not state.
    - Qorvo's datasheets of TGA4861, TGA4864, TGA4868 and TGA4872 were not read, because qorvo.com refuses scripted downloads; their product pages were used.
    - The linear input ranges of Table 11.2 follow each datasheet's own criterion, about 1–3 % of gain change (1-dB compression for HMC799, 3 % THD for RG8G32423), and several are read off curves.
    - Centring LMH32401's asymmetric window with a deliberate imbalance (±475 µA) is untested.
    - Three ADI copies are older than the current revisions (MAX40660/61 Rev 4 against Rev 6, MAX40658/59 Rev 2 against Rev 4, LTC6561 Rev 0 against Rev C).
20. **The discrete-FET front end (Section 11.5).**
    - No pHEMT datasheet gives the gate current at the operating point, or any noise below 0.5 GHz. The $e_n$ of CPH3910, 2SK3557, BF545C and the two CEL parts is the channel-thermal value, not a datasheet figure.
    - Whether Broadcom still makes the ATF parts was not settled.
    - No SPICE run of a composite was made; NXP's BF862 model file and Nexperia's PMBFJ310 datasheet were not obtained.
    - The high-voltage output stage that would raise the ceiling is not studied: its loop stability, its distortion at 20 Vpp, and which ADCs reach the −152.5 to −166.8 dBFS/Hz it would need.
"""

A22_CAPTION = r"*Table A2.2. Single-chip TIA datasheets of Section 11.4, with the copy used; local copies are in `datasheets/integrated_tia/`, the coherent-receiver documents in `datasheets/integrated_tia/coherent/`. Status and 1ku price as listed on ti.com (26 October 2026), analog.com, renesas.com, qorvo.com and macom.com (27 October 2026). Amplifiers (single-chip TIAs): every part of Table 11.2 and of the text of Section 11.4 (one per row or group).*"
A22_ROWS_AND_A23 = r"""| GX39220 | Renesas (IDT) | R08DS0227EU0100 Rev 1.00 (28 November 2022) | Obsolete: last-time buy 12 March 2026, last shipment 12 September 2026 (notice PLC250030); replacement GX39221 |
| RG8G32423 | Renesas | short-form datasheet R08DO0023EU0100 Rev 1.00 (3 October 2023) | Active, USD 66.15 |
| GX39221, RG8G31220, RG8G31223, RG8G3122B, RG8G31420 | Renesas | short-form datasheets (GX39221: R08DO0013EU0100 Rev 1.00, 28 September 2023; the RG8G parts: 9 February 2026) | Active; USD 94.19, 157.50, 157.50, not listed, 315.00 |
| GX32222, GX32223, GX36220, GX36420, RG8G3122A | Renesas (IDT) | short-form datasheets (2017–2023) | Obsolete: last shipment 18 July 2024 (GX32222, GX32223; notice PLC230010) and 12 September 2026 (the others; PLC250030) |
| GX32424 | Renesas | datasheet behind a login, not read | Active |
| IN3250TA, IN3252TA, IN3254TA, IN6450TA, IN6452TA, IN6454TA | Marvell (Inphi) | product briefs, revised May 2021 | not stated |
| TGA4861, TGA4864, TGA4868, TGA4872 | Qorvo | product pages; the datasheets were not read | Discontinued (TGA4864: end of life 22 February 2016; TGA4872: last-time buy 28 April 2020) |
| MxL9105, MxL9162 | MaxLinear | announcements of 2017 only | not listed on maxlinear.com |

*Table A2.3. Discrete-FET datasheets of Section 11.5 (Table 11.4), with the copy used; local copies are in `datasheets/fet_front_end/`. The values were typed in with their page and table or figure in `scripts_archive/fet_front_end/fet_front_end_numbers.py` and `scripts_archive/fet_composite_bound.py`. Amplifiers (discrete FETs): every device of Table 11.4 (one per row or group).*

| Device | Maker | Document and revision used | Values read, and status where checked |
|---|---|---|---|
| BF862 | NXP | product specification (5 January 2000) | $\lvert y_{fs}\rvert$, $C_{\mathrm{iss}}$, $C_{\mathrm{rss}}$, $e_n$, $I_{GSS}$ (p4); discontinued by NXP (Linear Systems announcement, December 2025) |
| LSBF862 | Linear Systems | Doc 201195 Rev A2 (17 February 2026) | $Y_{fs}$, capacitances, $e_n$ (p2) |
| BF861C | NXP | Rev 5 (15 September 2011) | $\lvert y_{fs}\rvert$ (Table 7), $e_n$ (Fig 14) |
| CPH3910 | onsemi | Rev 2 (February 2022) | $\lvert y_{fs}\rvert$ and capacitances (p1) |
| 2SK3557 | onsemi | Rev 3 (September 2024) | $\lvert y_{fs}\rvert$ and capacitances (p2) |
| J310 | onsemi; Fairchild | J309/D Rev 1 (March 2006); MMBFJ309/MMBFJ310 | Re($y_{fs}$) at 100 MHz (p2); $e_n$ (Fig 11) |
| LSK170 | Linear Systems | Doc 201110 Rev A22 (19 November 2019) | $G_{fs}$ (p2), $e_n$ (p6) |
| BF545C | NXP | Rev 4 (15 September 2011) | $\lvert y_{fs}\rvert$ (Table 7), $C_{\mathrm{iss}}$ (Table 8) |
| ATF-34143, ATF-54143, ATF-55143 | Avago (Broadcom) | AV02-1283EN, AV02-0488EN, AV02-0923EN (2012), distributor copies | S-parameters, noise resistance, gate leakage |
| SAV-551+, SAV-541+ | Mini-Circuits | Rev F (ECO-010314), with their S2P files | S-parameters, noise resistance, gate leakage; SAV-551+ active (DigiKey, 27 October 2026) |
| CE3512K2, CE3520K3 | CEL | CDS-0018-05 Issue B (November 2018) and CDS-0019-04 Issue C (July 2019), with their S2P files | S-parameters, gate leakage (p3); CE3512K2 active (DigiKey, 27 October 2026) |"""

A3_DATASHEETS = r"| `datasheets/` | datasheets of every part in Section 3; `market_scan_candidates/` holds the market-scan extras, `integrated_tia/` the single-chip TIAs of Section 11.4 with the coherent-receiver documents in `integrated_tia/coherent/` (Table A2.2), and `fet_front_end/` the discrete FETs of Section 11.5 (Table A2.3) |"

A4_COHERENT = r"""- GX39220: pad 9 (In2N) is described as the input of channel 1 (p5), and pad 36 (VPDS1, a PD1 bias supply) as the PD2 bias supply (p6); the pad drawing gives the die size and the pad and channel pitches in mm where µm is meant (p3).
- MATA-006801 (product page): the specification table lists a 2-kΩ differential transimpedance, the description a manual-mode range of 65 Ω to 1.5 kΩ.
- RG8G3122B and RG8G31420: both short-form datasheets carry the document number R15DO0008EU0100 Rev 1.00 (9 February 2026)."""


def main():
    path = Path(sys.argv[1])
    with open(path, encoding="utf-8", newline="") as fh:
        t = fh.read()
    assert "\r\n" not in t
    t = replace_line(t, DATE_OLD, DATE_NEW)
    t = replace_once(t, READ_OLD, READ_NEW)
    t = replace_line(t, "### 0.7 Dynamic range: what sets it, and single-chip TIAs (Section 11)", S07_HEAD)
    t = replace_line(t, "- **No single-chip lidar TIA comes within 10 dB at 1 mA.** Their linear input ranges are 3–250 µA, "
                        "against 0.77–1.14 mA for the op-amp designs;", S07_TIA)
    t = replace_line(t, "## 11. Dynamic range compared: the leading designs in SPICE, what limits them, and single-chip TIAs",
                     S11_HEAD)
    t = replace_line(t, "- Section 11.4 compares single-chip TIAs on the same definition, from their datasheets", S11_INTRO_TIA)
    t = replace_line(t, "- Section 11.5 gives the verdict.", S11_INTRO_REST)
    t = replace_line(t, "- **Single-chip TIAs** (Section 11.4): $I_{\\max}$ is the datasheet's linear input range, as rms,",
                     S111_TIA)
    t = replace_line(t, "- *(c) The single-chip TIAs of Table 11.2 that reach 150 MHz with a linear gain,", FIG15_C)
    t = replace_line(t, "- *Amplifiers: OPA855, OPA955, OPA818, LMH6629 (COMP HI) and OPA858; single-chip TIAs: LMH32401,",
                     FIG15_LIST)
    t = replace_line(t, "Section 3.5 listed the single-chip TIAs on the market, and Section 7.7 showed that none can carry",
                     S114_INTRO)
    t = replace_line(t, "- **Noise.** The datasheet's input-referred noise integrated over 0–150 MHz, at the photodiode "
                        "capacitance nearest 1 pF.", S114_NOISE)
    t = replace_line(t, "*Table 11.2. Single-chip TIAs on the definition of Eq. (57), from their datasheets,", S114_CAPTION)
    t = replace_line(t, "| MATA-006801 (MACOM) | 2 kΩ, differential input for a balanced pair; 45 GHz |", S114_ROWS)
    t = append_after(t, "**Worked example, LMH32401 at $I_1 + I_2$ = 1 mA.**", S114_EXAMPLE)
    t = replace_line(t, "- **The DC limits of Section 7.7 no longer decide.**", S114_DC)
    t = replace_block(t, "- **The one integrated part within reach is a coherent-receiver TIA, on its product-page figures.**",
                      "### 11.5 Verdict", S114_COHERENT)
    t = replace_block(t, "### 11.5 Verdict", "## Appendix 1. Open questions and unknowns", S116)
    t = replace_block(t, "19. **Single-chip TIAs (Section 11.4).**", "## Appendix 2. References", APP1_19_20)
    t = replace_line(t, "*Table A2.2. Single-chip TIA datasheets of Section 11.4, with the copy used;", A22_CAPTION)
    t = append_after(t, "| MATA-006801 | MACOM | product page only; datasheet on request | not shown |",
                     A22_ROWS_AND_A23)
    t = replace_line(t, "| `datasheets/` | datasheets of every part in Section 3;", A3_DATASHEETS)
    t = append_after(t, "- MAX40662: the output noise density on toc18a at 10 MHz", A4_COHERENT)
    for h in ("### 11.4 ", "### 11.5 A discrete-FET", "### 11.6 Verdict", "\\tag{60}", "\\tag{65}"):
        assert t.count(h) == 1, h
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)
    print("edited;", len(t.splitlines()), "lines")


if __name__ == "__main__":
    main()
