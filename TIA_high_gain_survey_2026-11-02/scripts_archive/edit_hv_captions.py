"""Move the explanatory lines that were drawn inside the old schematics into the captions
of hv_output_stage.md, and explain the stage's remaining parts in Figure 3's caption.
Refuses to write unless the document still has the hash it had when it was read."""
import hashlib
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "hv_output_stage" / "hv_output_stage.md"
EXPECT = "2a88bf34c7dd"

raw = DOC.read_bytes()
h = hashlib.sha256(raw).hexdigest()[:12]
assert h == EXPECT, f"document changed: {h}"
s = raw.decode("utf-8")
assert "\r\n" not in s

EDITS = [
    ("*Figure 2. The front end. The photodiode's cathode is at the summing node, so the output is positive for "
     "photocurrent. $C_F$ is drawn separately but is the feedback resistor's own capacitance.*",
     "*Figure 2. The front end. The photodiode's cathode is at the summing node, so the output is positive for "
     "photocurrent. $C_F$ is drawn separately, in grey like every parasitic element in these schematics, but is "
     "the feedback resistor's own capacitance. The guard ring around the summing node is tied to the + input, "
     "and the divider of 980 kΩ over 20 kΩ divides the output by 50 for a ±2 V converter.*"),
    ("*Figure 3. The ±100 V stage at transistor level, with the values used in every simulation of this study.*",
     "*Figure 3. The ±100 V stage at transistor level, with the values used in every simulation of this study. "
     "The NPN transistors are Rohm 2SCR346P and the PNP transistors 2SAR340P, both rated 400 V; QD1–QD4 are "
     "2SCR346P with the base tied to the collector. The 1 kΩ in series with Q2's base isolates the LMC662's "
     "output from the stage's input capacitance. The 1-kΩ emitter resistors of the pair degenerate it, which "
     "widens its linear input range, and those of the mirror make its two halves match; Section 3.3 explains "
     "why they are not larger. The 200 kΩ from 0 V feeds QD3 and QD4 with about 0.5 mA, so Q6's base sits two "
     "diode drops above −100 V and its emitter one drop above; 650 Ω turns that drop of about 0.6 V into Q6's "
     "0.9 mA. The 47-Ω emitter resistors of Q7 and Q8 stabilize the followers' quiescent current against the "
     "spread and the temperature dependence of their base–emitter voltages. 140 kΩ and 10 kΩ set the gain, "
     "1 + 140/10 = 15.*"),
    ("*Figure 10. The grounded guard of an inverting TIA. The guard ring is tied to the + input. A coax carries "
     "the photocurrent; its shield is both the guard and the return, grounded at the amplifier only.*",
     "*Figure 10. The grounded guard of an inverting TIA. The guard ring is tied to the + input, so it sits at "
     "0 V and the only leakage across its gap is $V_{OS}/R_{gap}$ (Eq. (11)). A coax carries the photocurrent; "
     "its shield is both the guard and the return, grounded at the amplifier only, so no loop current flows "
     "in it.*"),
    ("*Figure 12. A driven guard for a TIA whose + input sits at a bias. U2 copies the filtered bias onto the "
     "guard ring and the inner shield of a triax through $R_{iso}$; the outer shield is the return.*",
     "*Figure 12. A driven guard for a TIA whose + input sits at a bias. $R_f$ and $C_f$ filter the bias "
     "(1.6 Hz), and U2 copies the filtered bias onto the guard ring and the inner shield of a triax through "
     "$R_{iso}$; the outer shield is the return. The voltage across the ring's gap is $V_{OS,U1} + V_{OS,U2}$, "
     "and because the inner shield follows a step of $V_{bias}$, the cable capacitance is not charged through "
     "the photodiode.*"),
    ("*Figure 13. A shield bootstrapped from the summing node: the cable capacitance drops out of the loop, at "
     "the cost of the buffer's noise, input current and input capacitance.*",
     "*Figure 13. A shield bootstrapped from the summing node. The cable capacitance $C_{cable}$ drops out of "
     "the loop and of the $e_n\\omega C_T$ term, at a cost: U2's own voltage noise now acts across $C_{cable}$, "
     "and its input current and input capacitance add at the summing node.*"),
]
for old, new in EDITS:
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
DOC.write_bytes(s.encode("utf-8"))
print("written", hashlib.sha256(s.encode("utf-8")).hexdigest()[:12])
