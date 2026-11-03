"""Quick numerical checks of the first-order URC results quoted in the explanation."""
import sys
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hg_model as m

R, CG, CEE = 1e9, 0.3e-12, 0.05e-12
w_lo = np.array([2 * np.pi * 0.01])          # far below every corner

# first-order coefficient of y_f for several conductor profiles, from a fine ladder
profiles = {
    "grounded (a=0)": lambda x: 0.0,
    "output (a=1)": lambda x: 1.0,
    "one third (a=1/3)": lambda x: 1.0 / 3.0,
    "graded (a=x)": lambda x: x,
    "four strips": lambda x: (min(int(x * 4), 3) + 0.5) / 4.0,
}
for name, prof in profiles.items():
    y11, yf = m.ladder_y(w_lo, R, CG, CEE, 400, prof)
    k_f = (yf.imag[0] - w_lo[0] * CEE) / (w_lo[0] * CG)
    k_11 = (y11.imag[0] - w_lo[0] * CEE) / (w_lo[0] * CG)
    print(f"{name:20s}  dyf/(jwCg) = {k_f:+.5f}   dy11/(jwCg) = {k_11:+.5f}   shunt at input/Cg = {k_11 - k_f:+.5f}")
print("expected: -1/6 = -0.16667, +1/3 = 0.33333, 0, 0, 1/192 = 0.00521")

# the line's noise, Re{y11} R, against frequency for 1 GOhm and 0.3 pF
f = np.array([500.0, 1e3, 2e3, 3e3, 3.69e3, 4e3, 4.6e3, 8e3])
y11, _ = m.urc_y(2 * np.pi * f, R, CG, 0.0)
for fi, v in zip(f, (y11.real * R)):
    print(f"f = {fi:7.0f} Hz   wRCg = {2*np.pi*fi*R*CG:5.2f}   Re(y11) R = {v:.3f}   series 1+x^2/45 = {1 + (2*np.pi*fi*R*CG)**2/45:.3f}")

# band average of Re{y11} R from 0 to 3.69 kHz and 4.01 kHz
for fb in (3.69e3, 4.01e3):
    ff = np.linspace(1.0, fb, 4000)
    y, _ = m.urc_y(2 * np.pi * ff, R, CG, 0.0)
    avg = np.mean(y.real * R)
    print(f"band 0-{fb:.0f} Hz: mean Re(y11) R = {avg:.3f}  ({10*np.log10(avg):.2f} dB)")

# second-order term at alpha = 1/3, against the exact value at 4 kHz
wk = np.array([2 * np.pi * 4e3])
y11e, y21e = m.urc_y(wk, R, CG, 0.0)
yf13 = (y11e + 2 * (-y21e)) / 3
x = wk[0] * R * CG
print(f"alpha=1/3 at 4 kHz: exact yf R = {complex(yf13[0] * R):.4f};  series 1 - x^2/180 + j x^3/1512 = {1 - x**2/180:.4f} + j{x**3/1512:.4f}")
