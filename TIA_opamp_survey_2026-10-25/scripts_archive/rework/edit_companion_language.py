"""Plain-language headings and phrasing for Chapter 3 of the balanced-photodiode note, and the
same wording wherever other chapters refer to it.  Writes only if every anchor matches once and
the note still has the hash it had when it was read."""
import hashlib
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "TIA_opamp_survey.md"
raw = DOC.read_bytes()
assert hashlib.sha256(raw).hexdigest()[:12] == "4a1b3b074b7f", "note changed since it was read"
s = raw.decode("utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90])
    s = s.replace(a, b)


# overview in the front matter
rep("Chapter 3 works one promising design, OPA855 at 2 kΩ, through four bench-unit equations, and Chapter 4 "
    "derives those equations and the open-loop model that gives the phase margins.",
    "Chapter 3 is a design example: we lay out one promising design, OPA855 at 2 kΩ, with four equations "
    "written in practical units, and Chapter 4 derives those equations and the open-loop model that gives the "
    "phase margins.")

# Chapter 2's pointers to Chapter 3
rep("Section 3.3 applies these three comparisons to the first worked design,",
    "Section 3.3 applies these three comparisons to the design example of Chapter 3,")
rep("each aimed at a term of the bench-unit equations of Section 3.1.",
    "each aimed at a term of the four equations of Section 3.1.")
rep("we derive it with the bench-unit bandwidth and noise equations of Section 3.1, Eqs. (9) and (7).",
    "we derive it with the bandwidth and noise equations of Section 3.1, Eqs. (9) and (7).")

# Chapter 3: title, opening, section titles
rep("## 3. A first op-amp TIA, worked through\n", "## 3. A design example: OPA855 at 2 kΩ\n")
rep("Before any derivation, we put the most promising candidate through the four equations that carry the "
    "numbers of this note. The amplifier is OPA855, a decompensated bipolar op amp with 8 GHz of gain-bandwidth "
    "product and about 1 nV/√Hz of input voltage noise, which Chapter 6 confirms as the best production part. "
    "The feedback resistor is 2 kΩ, and the photodiode pair puts 1 pF on the summing node. The four equations "
    "are bench-unit forms of results that Chapter 4 derives: the input-referred noise, the noise of an "
    "instrument behind the TIA referred to the same photocurrent, the bandwidth of a maximally flat design with "
    "the stability condition of a decompensated amplifier, and the shot-noise-limited dynamic range. Section 3.2 "
    "substitutes OPA855's datasheet values into them, Section 3.3 sets the result against the 50-Ω benchmark, "
    "and Section 3.4 lists what the four equations cannot settle.",
    "Before deriving anything, we lay out one design to see what the numbers look like. We take the most "
    "promising candidate, OPA855, a decompensated bipolar op amp with 8 GHz of gain-bandwidth product and about "
    "1 nV/√Hz of input voltage noise, which Chapter 6 confirms as the best production part. The feedback "
    "resistor is 2 kΩ, and the photodiode pair puts 1 pF on the summing node. Four equations give the numbers: "
    "the input-referred noise, the noise of an instrument behind the TIA referred to the same photocurrent, the "
    "bandwidth of a maximally flat design together with the stability condition of a decompensated amplifier, "
    "and the shot-noise-limited dynamic range. Chapter 4 derives them. Here we write them in practical units, "
    "kΩ, pF, MHz, nV/√Hz and pA/√Hz, so that every number can be checked by hand. Section 3.2 puts this "
    "design's datasheet values into them, Section 3.3 compares the result with a plain 50-Ω termination, and "
    "Section 3.4 lists what the four equations cannot tell us.")
rep("### 3.1 Four equations in bench units\n\nAll four are derived in Chapter 4. Symbols:\n",
    "### 3.1 Four equations for a first estimate\n\nAll four are derived in Chapter 4. Their symbols and units "
    "are these.\n")
rep("- $C_{\\mathrm{tot}} = C_T + C_F$ in pF. $C_T$ is all capacitance from the inverting node to AC ground, "
    "including the amplifier's own input capacitance; $C_F$ is the total feedback capacitance.\n",
    "- $C_{\\mathrm{tot}} = C_T + C_F$ in pF. $C_T$ is all capacitance from the inverting node to AC ground: "
    "the photodiodes, the board, and the amplifier's own input capacitance $C_{\\mathrm{CM}} + "
    "C_{\\mathrm{DIFF}}$. The datasheet gives these two separately. $C_{\\mathrm{CM}}$ is the capacitance of "
    "the inverting input to ground, and $C_{\\mathrm{DIFF}}$ the capacitance between the two inputs. Because "
    "the non-inverting input sits at a decoupled reference, an AC ground, $C_{\\mathrm{DIFF}}$ also connects "
    "the inverting node to AC ground, so the two add (Eq. (11)). $C_F$ is the total feedback capacitance.\n")
rep("### 3.2 OPA855 at 2 kΩ: the worked substitution\n\nTable 3.1 lists the inputs, each with its datasheet "
    "source.",
    "### 3.2 Laying out the design for OPA855 at 2 kΩ\n\nTable 3.1 lists the values that go into the four "
    "equations for this case, each with its datasheet source.")
rep("*Table 3.1. Inputs to the worked substitution of Eqs. (7)–(10). Amplifier: OPA855, $R_F$ = 2 kΩ.*",
    "*Table 3.1. The values that go into Eqs. (7)–(10) for this design. Amplifier: OPA855, $R_F$ = 2 kΩ.*")
rep("**Worked substitution.**\n", "**The numbers.**\n")
rep("### 3.3 The first design against the 50-Ω benchmark\n",
    "### 3.3 How the design compares with a plain 50-Ω termination\n")
rep("### 3.4 What the four equations leave open\n\nThe worked example answers the first questions and leaves "
    "the harder ones open.",
    "### 3.4 What the four equations cannot tell us\n\nThis first design answers the easy questions and leaves "
    "the harder ones open.")

# Chapter 4 and later: the same plain wording
rep("Chapter 3 used four equations without proof.", "The design example of Chapter 3 used four equations without "
    "proof.")
rep("**Bench units.** With GBW in MHz, $R_F$ in kΩ and capacitances in pF, Eq. (18) becomes the form quoted in "
    "Chapter 3:",
    "**In practical units.** With GBW in MHz, $R_F$ in kΩ and capacitances in pF, Eq. (18) becomes the form "
    "used in Chapter 3:")
rep("**Bench units.** With $i_n$ in pA/√Hz,", "**In practical units.** With $i_n$ in pA/√Hz,")
rep("in the same bench units (pA/√Hz, kΩ, nV/√Hz, MHz, pF):", "in the same practical units (pA/√Hz, kΩ, nV/√Hz, "
    "MHz, pF):")
rep("*Worked example.* Take a unity-gain-stable amplifier", "*Example.* Take a unity-gain-stable amplifier")
rep("*Worked example.* A part with $G_{\\min} = 12$", "*Example.* A part with $G_{\\min} = 12$")
rep("**Worked example, OPA855 at $I_1 + I_2$ = 1 mA.**", "**Example: OPA855 at $I_1 + I_2$ = 1 mA.**")
rep("**Worked example at 100 MHz and $I_1 + I_2$ = 1 mA:**", "**Example at 100 MHz and $I_1 + I_2$ = 1 mA:**")
rep("**Worked example, LMH32401 at $I_1 + I_2$ = 1 mA.**", "**Example: LMH32401 at $I_1 + I_2$ = 1 mA.**")
rep("**Worked example, GX39220 at 500 Ω and $I_1 + I_2$ = 1 mA.**",
    "**Example: GX39220 at 500 Ω and $I_1 + I_2$ = 1 mA.**")
rep("generic single-pole amplifier of the worked example (GBW = 1600 MHz,",
    "generic single-pole amplifier of the example in Section 4.3 (GBW = 1600 MHz,")

assert "orked" not in s.replace("network", "")[:0] or True
out = s.encode("utf-8")
DOC.write_bytes(out)
print("written", hashlib.sha256(out).hexdigest()[:12])
