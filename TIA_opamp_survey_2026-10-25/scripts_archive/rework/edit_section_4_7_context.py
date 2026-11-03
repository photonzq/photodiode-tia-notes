"""Section 4.7 of the balanced-photodiode note: plain heading and the context the section lacked
(why current noise matters at 2 kOhm, why FET inputs look attractive, why the answer is a range).
Writes only if the note still has the hash it had when it was read and every anchor matches once."""
import hashlib
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "TIA_opamp_survey.md"
raw = DOC.read_bytes()
assert hashlib.sha256(raw).hexdigest()[:12] == "7a36ecdbd299", "note changed since it was read"
s = raw.decode("utf-8")

old = """### 4.7 High-frequency current noise of FET-input amplifiers: a bounded range

**The problem.** Several FET-input candidates publish current-noise curves that rise in proportion to frequency above 1–10 MHz (Table A4.4).

The bipolar OPA955 also shows a rise, from 0.56 to 1.10 pA/√Hz at 100 MHz (an excess of 0.95 pA/√Hz in quadrature).

Two mechanisms produce an input current proportional to frequency:"""

new = """### 4.7 Current noise of FET-input amplifiers at high frequency

**Why it matters here.** The amplifier's input current noise $i_n$ adds directly to the noise of the photocurrent (Eq. (23)), and at $R_F$ = 2 kΩ it competes with the feedback resistor's own $\\sqrt{4k_BT/R_F}$ = 2.87 pA/√Hz. A bipolar input carries the shot noise of its base current, which is flat with frequency: 2.6 pA/√Hz for OPA855 (Table 3.1). A FET input carries only the shot noise of its gate leakage, which at DC is about a femtoampere per root hertz; 5 pA of leakage, for example, gives $\\sqrt{2qI}$ = 1.3 fA/√Hz. On paper, therefore, a FET input removes current noise from the budget, and only its voltage noise $e_n$ remains. At the frequencies of this receiver that is not certain. Several FET-input datasheets show current-noise curves that rise in proportion to frequency from 1–10 MHz up and reach picoamperes per root hertz near 100 MHz (Table A4.4), the same order as the resistor's noise. How much of that rise is real, and additional to what Eq. (23) already counts, decides how much of the FET parts' advantage survives at 100–200 MHz. The bipolar OPA955 also shows a rise, from 0.56 to 1.10 pA/√Hz at 100 MHz, an excess of 0.95 pA/√Hz in quadrature.

**Why the datasheets do not settle it.** Two mechanisms produce an input current proportional to frequency:"""

assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old2 = """None of these datasheets says which mechanism its curve represents. Adding the curve to Eq. (23) may therefore count the first mechanism twice, and leaving it out may miss the second. We report a range.

**The physics-based lower bound.**"""
new2 = """None of these datasheets says which mechanism its curve represents. Adding the curve to Eq. (23) may therefore count the first mechanism twice, and leaving it out may miss the second. We therefore do not pick one. We bound the current noise from below with a physical model of the input pair, take Eq. (23) as the central estimate, and bound it from above by adding the datasheet curve as an independent source. The tables of Chapter 6 give the central value with the upper bound in brackets; for the FET parts the two differ by 0.3–2.7 dB in band noise (Section 6.3).

**A lower bound from the physics of the input pair.**"""
assert s.count(old2) == 1, s.count(old2)
s = s.replace(old2, new2)

old3 = "**Three estimates are reported.**"
assert s.count(old3) == 1
s = s.replace(old3, "**The three estimates.**")

out = s.encode("utf-8")
DOC.write_bytes(out)
print("written", hashlib.sha256(out).hexdigest()[:12])
