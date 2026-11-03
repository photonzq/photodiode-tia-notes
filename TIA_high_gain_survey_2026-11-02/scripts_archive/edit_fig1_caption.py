from pathlib import Path

p = Path(__file__).resolve().parents[1] / "parts" / "01_problem.md"
s = p.read_text(encoding="utf-8")
old = ("the board's $C_{PCB}$, the amplifier's input capacitances $C_{CM} + C_{DIFF}$, and the feedback capacitance "
       "$C_F$, the resistor's own $C_{par}$ plus any capacitor $C_{add}$ placed on purpose. The noise sources are "
       "purple: $i_R$, the Johnson noise of $R_F$; $i_{PD}$, the photodiode's thermal noise $4k_BT/R_{sh}$ together "
       "with the shot noise $2q\\,(I_{ph} + I_D)$; the amplifier's current noise $i_n$; and its voltage noise $e_n$, "
       "in series with the grounded non-inverting input. All but $e_n$ are currents at the summing node and are "
       "referred to the input unchanged (Section 2.1).")
new = ("the board's $C_{PCB}$, the amplifier's common-mode input capacitance $C_{CM}$ from its inverting input to "
       "ground, its differential input capacitance $C_{DIFF}$ between its two inputs, and the feedback capacitance "
       "$C_F$, the resistor's own $C_{par}$ plus any capacitor $C_{add}$ placed on purpose. $C_{DIFF}$ ends on the "
       "non-inverting input, which is grounded, so it connects the summing node to ground just as $C_{CM}$ does; "
       "that is why the two add in $C_T$. The noise sources are purple: $i_R$, the Johnson noise of $R_F$; "
       "$i_{PD}$, the photodiode's thermal noise $4k_BT/R_{sh}$ together with the shot noise "
       "$2q\\,(I_{ph} + I_D)$; the amplifier's current noise $i_n$; and its voltage noise $e_n$, drawn between the "
       "grounded non-inverting pin and the amplifier. Through the loop the summing node follows $e_n$, so $e_n$ "
       "drives a current through every capacitance at the node, $C_{DIFF}$ included (Eq. (9)). All but $e_n$ are "
       "currents at the summing node and are referred to the input unchanged (Section 2.1).")
assert s.count(old) == 1
p.write_text(s.replace(old, new), encoding="utf-8", newline="\n")
print("ok")
