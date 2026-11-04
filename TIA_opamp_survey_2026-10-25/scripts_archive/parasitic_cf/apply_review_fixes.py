"""Apply the corrections of the independent review to the derivation
(data/parasitic_cf/parasitic_cf_derivation.md): one false claim (Section 8.2), small slips
(signs, scale factor, cited equation), the gaps it listed (two-dimensional decay, admissible
class, Rule 6 with cuts and floating conductors, boundary values of the rectangle map, onto
for two maps, Landen step, 1/ln h, partly coupled film, film pattern with a non-linear
potential, film over the pads) and the notation clashes (map G, Moebius map with
coefficients e1..e4, Z for the exponential, varrho, r_g, varpi, Omega, Carlson R_F).

Usage: python apply_review_fixes.py <derivation.md>

Each replacement must match the text exactly once; the script stops otherwise.
"""
import sys
from pathlib import Path

PAIRS = [
    # ---------------------------------------------------------------- Section 2.1
    ("Let $\\varphi_j$ be the potential that solves Laplace's equation with conductor $j$ at 1 V and every other conductor at 0 V.",
     "Let $\\varphi_j$ be the potential that solves $\\nabla\\cdot(\\varepsilon\\nabla\\varphi_j) = 0$, which is Laplace's equation inside each material with the normal displacement continuous at interfaces, with conductor $j$ at 1 V and every other conductor at 0 V."),
    ("(The surface charge is the normal displacement leaving the conductor, $-\\varepsilon\\,\\partial\\varphi/\\partial n_{\\mathrm{out}} = \\varepsilon\\,\\partial\\varphi/\\partial n$.)",
     "(The surface charge is the normal displacement leaving the conductor, $-\\varepsilon\\,\\partial\\varphi/\\partial n_{\\mathrm{out}}$, where $n_{\\mathrm{out}} = -n$ points out of the conductor; it equals $\\varepsilon\\,\\partial\\varphi/\\partial n$.)"),
    ("and at infinity the integrand falls faster than the surface grows ($\\varphi_i\\sim1/r$, $|\\nabla\\varphi_j|\\sim1/r^2$). The left side is therefore",
     "and at infinity the integrand falls faster than the surface grows: in three dimensions $\\varphi_i\\sim1/r$ and $|\\nabla\\varphi_j|\\sim1/r^2$. The two-dimensional cross-sections used below have bounded potentials. A bounded two-dimensional potential tends to a constant at infinity, and the boundary term on a large circle is that constant times the net flux through the circle plus a term of order $1/r$. The net flux is the total charge, which is zero when no conductor is grounded, and in the problems below that contain a grounded conductor the region is a strip bounded by the grounded plane, where the potential tends to zero. The left side is therefore"),
    # ---------------------------------------------------------------- Section 2.2
    ("The loop holds B at the potential of the non-inverting input, which is AC ground. The current that a voltage $V_A$ sends into the summing node through the parasitic capacitance is therefore $j\\omega$ times the charge induced on B with B and every other conductor at 0 V:",
     "The loop holds B at the potential of the non-inverting input, which is AC ground. With B and every other conductor at 0 V, a voltage $V_A$ induces the charge $Q_B = c_{BA}V_A$ on B, which is negative. The summing node supplies that charge, so the current that $V_A$ sends into it through the parasitic capacitance is $-j\\omega Q_B = j\\omega(-c_{AB})V_A$, and"),
    ("An impedance analyser with a four-terminal-pair fixture holds its low terminal at virtual ground, as the TIA does, and therefore measures $C_m$ in the presence of its fixture.",
     "An instrument that holds its low terminal at virtual ground, as the TIA does, measures $C_m$ in the presence of its fixture, by the same argument."),
    ("so $c_{AA} + c_{AB} = c_{BB} + c_{AB} = 0$: $C_{A0} = C_{B0} = 0$ and $C_{2\\mathrm t} = C_m$.",
     "so $c_{AA} + c_{AB} = c_{BB} + c_{AB} = 0$, that is, $C_{A0} = C_{B0} = 0$. Both forms of Eq. (P4) are then $0/0$, but the charges are directly $Q = c_{AA}V_A + c_{AB}V_B = C_m(V_A - V_B)$, so $C_{2\\mathrm t} = C_m$."),
    # ---------------------------------------------------------------- Section 2.3
    ("The first neglected terms are of relative order $(\\omega R_FC)^2$, where $C$ is the part of the capacitance that loads the film (approximation A5 of Section 12).",
     "The first neglected terms are of second order in $\\omega R_FC$, where $C$ is the part of the capacitance that loads the film. For the uniform RC line below they are a conductance of $7(\\omega R_FC_g)^2/360$ relative to $1/R_F$ and a correction of $31(\\omega R_FC_g)^2/2520$ relative to $C_{\\mathrm{eff}}$, both under 0.1 % at $\\omega R_FC_g = 0.19$ (approximation A5 of Section 12)."),
    ("The same line gives a shunt admittance $j\\omega C_g/2$ at each end, so the film's capacitance to ground also adds $C_g/2$ to the summing node; Section 10.6 weighs the two.",
     "The same line gives a shunt admittance $j\\omega C_g/2$ at each end. In general, repeating Eqs. (P6) and (P7) with B driven gives the shunt from B to ground as $j\\omega\\,\\mathbf v^{\\mathsf T}\\mathbf C(\\mathbf u + \\mathbf v) = j\\omega\\sum_iv_ic_{ig}$ for the film's part, which is $j\\omega C_g/2$ for any coupling symmetric about the film's midpoint. The film's capacitance to ground therefore also adds $C_g/2$ to the summing node; Section 10.6 weighs the two."),
    ("Their Eq. (2) with $N = 1$ contains $-C_R/4$, which is Eq. (P8) with $u = v = 1/2$ ([P3], p. 3, Eq. (2)).",
     "Their Eq. (2) with $N = 1$ contains $-C_R/4$, which is the ground term $-\\sum_iv_iu_ic_{ig}$ of Eq. (P8) with the whole coupling at the film's midpoint, where $u = v = 1/2$ ([P3], p. 3, Eq. (2))."),
    # ---------------------------------------------------------------- Section 4.2
    ("Among all functions $\\psi$ on the cross-section that take the prescribed values on A, on B and on the film, and that are continuous with finite $E$, the potential $\\varphi$ gives the smallest $E$.",
     "Among all functions $\\psi$ on the cross-section that take the prescribed values on A, on B and on the film, are continuous except across insulating cuts, have finite $E$ and tend to a constant at infinity, the potential $\\varphi$ gives the smallest $E$. (In two dimensions finite $E$ alone does not make $\\psi$ bounded, since $\\ln\\ln r$ has finite energy; the functions that tend to a constant are dense in energy, so the restriction loses nothing.)"),
    ("and on a large circle the integrand falls as $1/r^2$ while the length grows as $r$. Hence",
     "and on a large circle $\\eta$ tends to a constant, so the line term is that constant times the net flux of $\\varphi$, which is zero (Section 2.1), plus a term that falls as $1/r$. Hence"),
    ("with equality only if $E[\\eta] = 0$, which makes $\\eta$ constant and, since it vanishes on the electrodes, zero. The minimiser is therefore unique.",
     "with equality only if $E[\\eta] = 0$, which makes $\\eta$ constant and, since it vanishes on the electrodes, zero. The minimiser is therefore unique in every region that touches an electrode. In a region that touches none, such as the air below the cut of Section 7.3, the potential is fixed only up to a constant, which does not change the energy."),
    # ---------------------------------------------------------------- Section 4.3, Rule 6
    ("**Rule 6: grounded metal lowers the mutual capacitance.** Let $\\varphi_A$ be the potential with A at 1 V and B and the ground at 0 V. By the maximum principle $0\\le\\varphi_A\\le1$. With $n_B$ the normal pointing from B into the dielectric, Eqs. (P1) and (P3) give $C_m = \\oint_{S_B}\\varepsilon\\,\\partial\\varphi_A/\\partial n_B\\,\\mathrm dS\\ge0$. Enlarging a grounded conductor gives a new potential $\\varphi'_A\\le\\varphi_A$ everywhere, by the comparison principle for $\\nabla\\cdot(\\varepsilon\\nabla\\varphi) = 0$ [P6]: the difference $\\varphi_A - \\varphi'_A$ is non-negative on the whole boundary of the new region. Since both vanish on B, $\\partial\\varphi'_A/\\partial n_B\\le\\partial\\varphi_A/\\partial n_B$ there, and $C_m$ cannot increase. Enlarging A raises $\\varphi_A$ and so cannot lower $C_m$, and enlarging B has the same effect by the symmetry $c_{AB} = c_{BA}$.",
     "**Rule 6: grounded metal lowers the mutual capacitance.** Let $\\varphi_A$ be the potential with A at 1 V and B and the ground at 0 V. With $n_B$ the normal pointing from B into the dielectric, Eqs. (P1) and (P3) give $C_m = \\oint_{S_B}\\varepsilon\\,\\partial\\varphi_A/\\partial n_B\\,\\mathrm dS$. Now enlarge the grounded metal, or add a grounded conductor, and call the new potential $\\varphi'_A$, defined on the new, smaller dielectric region $\\mathcal V'$. Let $\\delta = \\varphi_A - \\varphi'_A$ on $\\mathcal V'$ and $\\delta^- = \\min(\\delta,0)$. The boundary of $\\mathcal V'$ has four kinds of part:\n\n- On A, on B and on the original ground, $\\delta = 0$. On the added ground, $\\varphi'_A = 0\\le\\varphi_A$, so $\\delta\\ge0$. Hence $\\delta^- = 0$ on every conductor held at a fixed potential.\n- On insulating parts (cuts, symmetry lines, the surface of approximation A9), $\\partial\\delta/\\partial n = 0$.\n- On a floating conductor, both potentials are constant and carry zero net charge, so $\\delta^-$ is a constant there and $\\oint\\varepsilon\\,\\partial\\delta/\\partial n = 0$.\n- At infinity the boundary term vanishes as in Section 2.1.\n\nSince $\\nabla\\delta^- = \\nabla\\delta$ where $\\delta<0$ and zero elsewhere, Green's identity gives $\\int_{\\mathcal V'}\\varepsilon|\\nabla\\delta^-|^2\\,\\mathrm dV = \\oint\\delta^-\\varepsilon\\,\\partial\\delta/\\partial n\\,\\mathrm dS - \\int\\delta^-\\nabla\\cdot(\\varepsilon\\nabla\\delta)\\,\\mathrm dV = 0$. So $\\delta^-$ is constant, and it is zero on A: $\\varphi'_A\\le\\varphi_A$ everywhere. Both vanish on B, so $\\partial\\varphi'_A/\\partial n_B\\le\\partial\\varphi_A/\\partial n_B$ there, and $C_m$ cannot increase. The same argument with $\\delta = \\varphi_A$, and with $\\delta = 1 - \\varphi_A$, gives $0\\le\\varphi_A\\le1$ and hence $C_m\\ge0$. Enlarging A raises $\\varphi_A$ by the same argument and so cannot lower $C_m$, and enlarging B has the same effect by the symmetry $c_{AB} = c_{BA}$. For Dirichlet data on the whole boundary this is the weak maximum principle [P6]; the argument above extends it to cuts and floating conductors."),
    # ---------------------------------------------------------------- Section 4.4 (map G, variable varpi)
    ("Let $\\zeta = F(w)$ map a region $D_w$ one-to-one onto a region $D_\\zeta$, with $F$ analytic and $F'\\ne0$ inside, boundary arcs going to boundary arcs. For a function $\\psi$ on $D_\\zeta$, define $\\tilde\\psi = \\psi\\circ F$ on $D_w$. Write $F = U + iV$ and $w = u + iv$. The chain rule and the Cauchy–Riemann equations $U_u = V_v$, $U_v = -V_u$ give",
     "Let $\\zeta = G(\\varpi)$ map a region $D_\\varpi$ one-to-one onto a region $D_\\zeta$, with $G$ analytic and $G'\\ne0$ inside, boundary arcs going to boundary arcs. For a function $\\psi$ on $D_\\zeta$, define $\\tilde\\psi = \\psi\\circ G$ on $D_\\varpi$. Write $\\varpi = u + iv$ and $G = G_1 + iG_2$, and let $\\psi_1$ and $\\psi_2$ be the derivatives of $\\psi$ with respect to $\\operatorname{Re}\\zeta$ and $\\operatorname{Im}\\zeta$. The chain rule and the Cauchy–Riemann equations $\\partial_uG_1 = \\partial_vG_2$, $\\partial_vG_1 = -\\partial_uG_2$ give"),
    ("|\\nabla_w\\tilde\\psi|^2 = (\\psi_XU_u + \\psi_YV_u)^2 + (-\\psi_XV_u + \\psi_YU_u)^2 = (\\psi_X^2 + \\psi_Y^2)(U_u^2 + V_u^2) = |F'(w)|^2\\,|\\nabla_\\zeta\\psi|^2 .",
     "|\\nabla_\\varpi\\tilde\\psi|^2 = (\\psi_1\\partial_uG_1 + \\psi_2\\partial_uG_2)^2 + (-\\psi_1\\partial_uG_2 + \\psi_2\\partial_uG_1)^2 = (\\psi_1^2 + \\psi_2^2)\\bigl[(\\partial_uG_1)^2 + (\\partial_uG_2)^2\\bigr] = |G'(\\varpi)|^2\\,|\\nabla_\\zeta\\psi|^2 ."),
    ("The area element transforms with the Jacobian $U_uV_v - U_vV_u = U_u^2 + V_u^2 = |F'|^2$, so",
     "The area element transforms with the Jacobian $\\partial_uG_1\\partial_vG_2 - \\partial_vG_1\\partial_uG_2 = (\\partial_uG_1)^2 + (\\partial_uG_2)^2 = |G'|^2$, so"),
    ("\\iint_{D_w}|\\nabla_w\\tilde\\psi|^2\\,\\mathrm dA_w = \\iint_{D_\\zeta}|\\nabla_\\zeta\\psi|^2\\,\\mathrm dA_\\zeta .",
     "\\iint_{D_\\varpi}|\\nabla_\\varpi\\tilde\\psi|^2\\,\\mathrm dA_\\varpi = \\iint_{D_\\zeta}|\\nabla_\\zeta\\psi|^2\\,\\mathrm dA_\\zeta ."),
    # ---------------------------------------------------------------- Section 5
    ("This section defines them, states the three properties that are used, and gives the names under which the script evaluates them.",
     "This section defines them, states the four properties that are used, and gives the names under which the script evaluates them."),
    ("Three properties are used:\n\n- $K(0) = \\pi/2$.\n- $K$ increases strictly with $m$, because the integrand does.\n- $K(m)\\to\\infty$ as $m\\to1$, because at $m = 1$ the integrand is $1/\\cos\\theta$, whose integral diverges at $\\pi/2$.",
     "Four properties are used:\n\n- $K(0) = \\pi/2$.\n- $K$ increases strictly with $m$, because the integrand does.\n- $K$ is continuous on $[0,1)$: for $m\\le m_0<1$ the integrand is continuous in $m$ and bounded by $(1 - m_0)^{-1/2}$.\n- $K(m)\\to\\infty$ as $m\\to1$: the integrand increases to $1/\\cos\\theta$, whose integral diverges at $\\pi/2$, so by monotone convergence the integral diverges too."),
    # ---------------------------------------------------------------- Section 6 (Moebius map)
    ("T(\\zeta) = \\frac{(\\zeta - x_1)(x_3 - x_4)}{(\\zeta - x_4)(x_3 - x_1)}\n\\tag{P16}",
     "\\mathcal T(\\zeta) = \\frac{(\\zeta - x_1)(x_3 - x_4)}{(\\zeta - x_4)(x_3 - x_1)}\n\\tag{P16}"),
    ("m = T(x_2) = \\frac{(x_2 - x_1)(x_4 - x_3)}{(x_4 - x_2)(x_3 - x_1)},",
     "m = \\mathcal T(x_2) = \\frac{(x_2 - x_1)(x_4 - x_3)}{(x_4 - x_2)(x_3 - x_1)},"),
    ("$T$ keeps the upper half-plane. Write $T(\\zeta) = (a\\zeta + b)/(c\\zeta + d)$ with the real coefficients $a = x_3 - x_4$, $b = -x_1(x_3 - x_4)$, $c = x_3 - x_1$ and $d = -x_4(x_3 - x_1)$. Multiplying numerator and denominator by $c\\bar\\zeta + d$,",
     "$\\mathcal T$ keeps the upper half-plane. Write $\\mathcal T(\\zeta) = (e_1\\zeta + e_2)/(e_3\\zeta + e_4)$ with the real coefficients $e_1 = x_3 - x_4$, $e_2 = -x_1(x_3 - x_4)$, $e_3 = x_3 - x_1$ and $e_4 = -x_4(x_3 - x_1)$. Multiplying numerator and denominator by $e_3\\bar\\zeta + e_4$,"),
    ("\\operatorname{Im}T(\\zeta) = \\frac{(ad - bc)\\,\\operatorname{Im}\\zeta}{|c\\zeta + d|^2},\n\\qquad\nad - bc = (x_3 - x_4)(x_3 - x_1)(x_1 - x_4) > 0,",
     "\\operatorname{Im}\\mathcal T(\\zeta) = \\frac{(e_1e_4 - e_2e_3)\\,\\operatorname{Im}\\zeta}{|e_3\\zeta + e_4|^2},\n\\qquad\ne_1e_4 - e_2e_3 = (x_3 - x_4)(x_3 - x_1)(x_1 - x_4) > 0,"),
    ("A real Möbius map is a one-to-one map of the extended plane onto itself that takes the real axis to the real axis, and with $ad - bc>0$ it takes $\\mathcal H$ onto $\\mathcal H$. On the real axis $T'(x) = (ad - bc)/(cx + d)^2>0$, so $T$ increases on each side of its only pole, $x_4$. The electrodes therefore go to $[0,m]$ and $[1,\\infty)$, the gap $(x_2,x_3)$ goes to $(m,1)$, and the outside $(x_4,\\infty)\\cup(-\\infty,x_1)$ goes to $(-\\infty,0)$.",
     "A real Möbius map is a one-to-one map of the extended plane onto itself that takes the real axis to the real axis, and with $e_1e_4 - e_2e_3>0$ it takes $\\mathcal H$ onto $\\mathcal H$. On the real axis $\\mathcal T'(x) = (e_1e_4 - e_2e_3)/(e_3x + e_4)^2>0$, so $\\mathcal T$ increases on each side of its only pole, $x_4$. The electrodes therefore go to $[0,m]$ and $[1,\\infty)$, the gap $(x_2,x_3)$ goes to $(m,1)$, and the outside $(x_4,\\infty)\\cup(-\\infty,x_1)$ goes to $(-\\infty,0)$, passing through $\\mathcal T(\\infty) = e_1/e_3 = (x_3 - x_4)/(x_3 - x_1)<0$."),
    ("When one electrode reaches to infinity ($x_1\\to-\\infty$), the same steps apply with $T(\\zeta) = (x_4 - x_3)/(x_4 - \\zeta)$, whose coefficients give $ad - bc = x_4 - x_3>0$, and",
     "When one electrode reaches to infinity ($x_1\\to-\\infty$), the same steps apply with $\\mathcal T(\\zeta) = (x_4 - x_3)/(x_4 - \\zeta)$, whose coefficients give $e_1e_4 - e_2e_3 = x_4 - x_3>0$, and"),
    ("(b) The same potential in the plane of $t = T(\\zeta)$ (Eq. (P16)),",
     "(b) The same potential in the plane of $t = \\mathcal T(\\zeta)$ (Eq. (P16)),"),
    # (P22) variable
    ("With $\\sigma = -\\tau = m\\cot^2\\theta$, the factors become $\\sigma + m = m/\\sin^2\\theta$ and $\\sigma + 1 = [1 - (1 - m)\\cos^2\\theta]/\\sin^2\\theta$, and $|\\mathrm d\\sigma| = 2m\\cos\\theta\\,\\mathrm d\\theta/\\sin^3\\theta$, so",
     "With $\\varrho = -\\tau = m\\cot^2\\theta$, the factors become $\\varrho + m = m/\\sin^2\\theta$ and $\\varrho + 1 = [1 - (1 - m)\\cos^2\\theta]/\\sin^2\\theta$, and $|\\mathrm d\\varrho| = 2m\\cos\\theta\\,\\mathrm d\\theta/\\sin^3\\theta$, so"),
    ("\\int_0^\\infty\\frac{\\mathrm d\\sigma}{\\sqrt{\\sigma(\\sigma + m)(\\sigma + 1)}}",
     "\\int_0^\\infty\\frac{\\mathrm d\\varrho}{\\sqrt{\\varrho(\\varrho + m)(\\varrho + 1)}}"),
    # boundary values of the rectangle
    ("which is 1 inside the rectangle and 0 outside ([P8], Ch. 4). So $f$ maps $\\mathcal H$ one-to-one onto the interior of $\\mathcal R$.",
     "which is 1 inside the rectangle and 0 outside ([P8], Ch. 4). Values on the boundary of $\\mathcal R$ are not taken in $\\mathcal H$ either: by the open-mapping theorem $f(\\mathcal H)$ is open, and an open set contained in the closed rectangle lies in its interior. So $f$ maps $\\mathcal H$ one-to-one onto the interior of $\\mathcal R$."),
    ("so $E = V^2K(m)/K(1 - m)$. By Eq. (P13)",
     "so $E = \\varepsilon_rV^2K(m)/K(1 - m)$. By Eq. (P13)"),
    # Carlson form
    ("For drawing Figure P3, $f$ is evaluated in closed form as $f(t) = -2\\sqrt{t/m}\\,R_F(1 - t/m,\\,1 - t,\\,1)$, where $R_F$ is Carlson's symmetric elliptic integral ([P7], §19.16(i)). On $(0,m)$ the right side equals $-2F(\\arcsin\\sqrt{t/m}\\,|\\,m)$ ([P7], §19.25(i), with the homogeneity of $R_F$), which is $f$ by the substitution of Eq. (P19). Both sides are analytic in $\\mathcal H$, so they agree throughout it.",
     "For drawing Figure P3, $f$ is evaluated in closed form as $f(t) = -2\\sqrt{t/m}\\,\\mathcal R_F(1 - t/m,\\,1 - t,\\,1)$, where $\\mathcal R_F$ is Carlson's symmetric elliptic integral ([P7], §19.16(i)), not the resistor. On $(0,m)$ the right side equals $-2F(\\arcsin\\sqrt{t/m}\\,|\\,m)$ ([P7], §19.25(i), with the homogeneity of $\\mathcal R_F$), which is $f$ by the substitution of Eq. (P19). Both sides are analytic in $\\mathcal H$ and continuous up to $(0,m)$, where they agree. By the Schwarz reflection principle their difference continues analytically across that segment, and since it vanishes there it vanishes identically."),
    # ---------------------------------------------------------------- Section 7.2 Landen
    ("The two forms are equal by the Landen transformation of $K$ ([P7], §19.8(ii)), and the script confirms the equality to $10^{-12}$ for several pad shapes (C5).",
     "The two forms are equal by the descending Landen transformation ([P7], §19.8(ii)). In modulus notation, with $k = w/(s + w)$ the modulus of Eq. (P25) and $\\kappa_1 = (1 - k)/(1 + k) = s/(s + 2w) = k_0$, it gives $K(k') = (1 + \\kappa_1)K(\\kappa_1)$ and $K(k) = \\tfrac12(1 + \\kappa_1)K(\\kappa_1')$, hence $K(k)/K(k') = K(k_0')/[2K(k_0)]$. The script confirms the equality to $10^{-12}$ for several pad shapes (C5)."),
    # ---------------------------------------------------------------- Section 7.3 variable
    ("The map $\\omega = \\exp[\\pi(x + i(z + H))/H]$ takes this strip one-to-one onto $\\mathcal H$:",
     "The map $\\Omega = \\exp[\\pi(x + i(z + H))/H]$ takes this strip one-to-one onto $\\mathcal H$:"),
    ("The bottom face goes to the positive real axis and the top face to the negative real axis, $\\omega = -e^{\\pi x/H}$.",
     "The bottom face goes to the positive real axis and the top face to the negative real axis, $\\Omega = -e^{\\pi x/H}$."),
    # ---------------------------------------------------------------- Section 8.2
    ("Place the half-block on $\\mathcal R$, scaled by $(L/2)/2K(m_b)$ and reflected left to right:",
     "Place the half-block on $\\mathcal R$, reflected left to right and with its lengths multiplied by $4K(m_b)/L$:"),
    ("The film holds the top face at the linear potential and stops the penetration from that side, so the true value lies towards the upper bound.",
     "The film holds the top face at the linear potential but leaves the slots open below it, so the field still enters them. The analysis proves the bracket and does not place the true value within it; the central value of Section 12 takes its middle."),
    # ---------------------------------------------------------------- Section 9.2 onto
    ("The map is one-to-one because $\\sin\\tilde w_1 = \\sin\\tilde w_2$ with $|\\operatorname{Re}\\tilde w|<\\pi/2$ forces $\\tilde w_1 = \\tilde w_2$.",
     "The map is one-to-one and onto because $\\sin(u + iv) = \\cosh(v + i(\\pi/2 - u))$: on $S$ it is the map of Eq. (P40) with $h = \\pi$, applied to the half-strip $v>0$, $0<\\pi/2 - u<\\pi$, which Section 10.2 shows to be one-to-one onto $\\mathcal H$."),
    # ---------------------------------------------------------------- Section 10.2 (Z) and Joukowski onto
    ("\\zeta = \\cosh\\frac{\\pi q}h = \\frac12\\left(E + \\frac1E\\right),\\qquad E = e^{\\pi q/h},",
     "\\zeta = \\cosh\\frac{\\pi q}h = \\frac12\\left(Z + \\frac1Z\\right),\\qquad Z = e^{\\pi q/h},"),
    ("- $q\\mapsto E$ takes the half-strip onto $\\{|E|>1,\\ 0<\\arg E<\\pi\\}$: the modulus $e^{\\pi x/h}$ exceeds 1 and the argument $\\pi d/h$ lies in $(0,\\pi)$.\n- The Joukowski map $E\\mapsto\\zeta$ takes that region onto $\\mathcal H$. For $E = \\rho e^{i\\vartheta}$ with $\\rho>1$ and $0<\\vartheta<\\pi$, $\\operatorname{Im}\\zeta = \\frac12(\\rho - 1/\\rho)\\sin\\vartheta>0$. $\\zeta$ determines $E$ as the root of $E^2 - 2\\zeta E + 1 = 0$ outside the unit circle; the two roots have product 1, so only one lies outside.",
     "- $q\\mapsto Z$ takes the half-strip onto $\\{|Z|>1,\\ 0<\\arg Z<\\pi\\}$: the modulus $e^{\\pi x/h}$ exceeds 1 and the argument $\\pi d/h$ lies in $(0,\\pi)$.\n- The Joukowski map $Z\\mapsto\\zeta$ takes that region one-to-one onto $\\mathcal H$. For $Z = \\rho e^{i\\vartheta}$ with $\\rho>1$ and $0<\\vartheta<\\pi$, $\\operatorname{Im}\\zeta = \\frac12(\\rho - 1/\\rho)\\sin\\vartheta>0$. Conversely, for $\\zeta\\in\\mathcal H$ the two roots of $Z^2 - 2\\zeta Z + 1 = 0$ have product 1, and neither lies on the unit circle, where $\\zeta = \\cos\\vartheta$ would be real. So exactly one root has $|Z|>1$, and $\\operatorname{Im}\\zeta>0$ then forces $0<\\vartheta<\\pi$."),
    # ---------------------------------------------------------------- Section 10.3
    ("With $\\cosh A - 1 = 2\\sinh^2(A/2)$, $\\cosh A + 1 = 2\\cosh^2(A/2)$ and $\\cosh A - \\cosh B = 2\\sinh\\frac{A + B}2\\sinh\\frac{A - B}2$, their complements take a form that avoids cancellation:",
     "With $\\cosh A - 1 = 2\\sinh^2(A/2)$ and $\\cosh A + 1 = 2\\cosh^2(A/2)$, their complements take a form that avoids cancellation:"),
    ("$q_{\\mathrm{even}}$, however, falls only as $1/\\ln h$: in two dimensions a plane at any finite depth takes a share of the charge (C7).",
     "$q_{\\mathrm{even}}$, however, falls only as $1/\\ln h$. For large $h$, expanding the hyperbolic cosines gives $m_{\\mathrm e}\\approx\\pi^2w(s + w)/4h^2$. With $K(m_{\\mathrm e})\\to\\pi/2$ and $K(1 - m_{\\mathrm e})\\approx\\frac12\\ln(16/m_{\\mathrm e})$ ([P7], §19.12), this gives $q_{\\mathrm{even}}/\\varepsilon_{\\mathrm{pcb}}\\varepsilon_0\\approx\\pi/\\ln[64h^2/\\pi^2w(s + w)]$. In two dimensions a plane at any finite depth therefore takes a share of the charge (C7)."),
    # ---------------------------------------------------------------- Section 10.4
    ("The film, at its linear potential, couples to a plane below through the alumina (in normal mounting), the air under the body and the board. Treated as three dielectric layers in series under the film's area $A_f$ (approximation A10),",
     "The film, at its linear potential, couples to a plane below through the alumina (in normal mounting), the air under the body and the board. Only the part of the film over the pad gap sees the plane; where the film lies over the pads, they shield it. Treated as three dielectric layers in series under that area $A_f$ (approximation A10),"),
    ("By Eq. (P10) the film term is $-C_g/6$. For an 0402 ($A_f = gW$ = 0.30 mm², $\\varepsilon_{\\mathrm{al}}$ = 9.6, $\\varepsilon_{\\mathrm{pcb}}$ = 4.2) over a plane at 0.2 mm, with $t_s$ = 30 µm, $C_g$ is 23 fF with the film up and 34 fF with the film down, so the film term is −3.9 fF or −5.7 fF.",
     "The film term follows from Eq. (P44) of Section 10.5, which weights the coupling of the middle fraction $r_g = \\min(s,g)/g$ of the film. For an 0402 ($A_f = sW$ = 0.20 mm², $r_g = 2/3$, $\\varepsilon_{\\mathrm{al}}$ = 9.6, $\\varepsilon_{\\mathrm{pcb}}$ = 4.2) over a plane at 0.2 mm, with $t_s$ = 30 µm, $C_g$ is 16 fF with the film up and 23 fF with the film down, so the film term is −3.3 fF or −4.9 fF."),
    # ---------------------------------------------------------------- Section 10.5
    ("Its effect on the board region is again a two-electrode problem.",
     "Its effect on the board region is again a two-electrode problem, with the board taken as a half-space. With ground present, the rules of Section 4.3 do not fix the direction of that choice."),
    ("The film couples to the strip only over its middle part, the fraction $r = w_g/g$ of its length. In Eq. (P10) the average of $\\xi(1 - \\xi)$ over $\\xi\\in[\\frac{1 - r}2,\\frac{1 + r}2]$ is $\\frac14 - \\frac{r^2}{12}$ (substitute $\\eta = \\xi - \\frac12$: $\\xi(1 - \\xi) = \\frac14 - \\eta^2$, and $\\eta^2$ averages to $r^2/12$). So",
     "The film couples to the strip only over its middle part, the fraction $r_g = w_g/g$ of its length. In Eq. (P10) the average of $\\xi(1 - \\xi)$ over $\\xi\\in[\\frac{1 - r_g}2,\\frac{1 + r_g}2]$ is $\\frac14 - \\frac{r_g^2}{12}$ (substitute $\\chi = \\xi - \\frac12$: $\\xi(1 - \\xi) = \\frac14 - \\chi^2$, and $\\chi^2$ averages to $r_g^2/12$). So"),
    ("\\Delta C_{\\mathrm{eff}} = -\\left(\\frac14 - \\frac{r^2}{12}\\right)C_g,",
     "\\Delta C_{\\mathrm{eff}} = -\\left(\\frac14 - \\frac{r_g^2}{12}\\right)C_g,"),
    ("which is $-C_g/6$ for $r = 1$.", "which is $-C_g/6$ for $r_g = 1$."),
    # ---------------------------------------------------------------- Section 10.7
    ("The film term of Eq. (P10) grows from −3.2 to −7.1 fF.",
     "The film term of Eq. (P44) grows from −3.2 to −7.1 fF."),
    ("for an 0402 this is 0.6 fF. The totals of Table P1 change by 0.2–1.6 fF across 0201 to 0805.",
     "for an 0402 this is 0.6 fF. The totals of Table P1 change by 0.2–1.6 fF across 0201 to 0805. Two further effects of the same size are left out of that figure. With $g>s$, as in all four sizes, the film overlaps the inner ends of the pads across the solder gap, at a lower potential than theirs; a parallel-plate estimate, $\\varepsilon_0Wt_s^{-1}\\int(\\frac12 - x/g)^2\\,\\mathrm dx$ over the two overlaps, gives 0.3 fF at $t_s$ = 30 µm. And the flattened data of Eq. (P38), applied on the board side, let the film's potential reach the pads' at the pad edges, which the real film, at $\\pm Vs/2g$ there, does not. Both are estimates of size, not bounds."),
    # ---------------------------------------------------------------- Section 11
    ("By Rule 6 they lower the mutual capacitance, so the floating-wall value is an upper estimate within the model.",
     "By Rule 6, which holds with a floating conductor present (Section 4.3), they lower the mutual capacitance. Within the zero-thickness model the real pins therefore lie below the same pins without grounds, which lie below the floating-wall value by Rule 4: the floating-wall value is an upper bound there."),
    # ---------------------------------------------------------------- Section 12 table
    ("| A11 | Pins: zero thickness, side walls as parallel plates, grounded neighbours omitted | Upper estimate (Rule 6) | 14.9–21.0 fF plus 2.1–4.3 fF |",
     "| A11 | Pins: zero thickness (lowers, Rule 2), side walls as parallel plates (not a bound), grounded pin 4 and thermal pad omitted (raises, Rule 6) | Mixed | Within the zero-thickness model the floating-wall value is an upper bound; 14.9–21.0 fF plus 2.1–4.3 fF |"),
    ("| A14 | Gap under the body ($t_s$) ignored except in Section 10 | Small | Tens of µm against gaps of 0.3–1 mm |",
     "| A14 | Gap under the body ($t_s$) ignored except in Section 10; where the pads reach under the body ($g>s$), their coupling to the body's lower face across $t_s$ is cut | Lowers | A parallel-plate estimate of that coupling gives 0.3 fF for an 0402 at $t_s$ = 30 µm; the cut keeps the lower bound rigorous |"),
    # ---------------------------------------------------------------- Section 13.2, Eq. (P49)
    ("Within Eq. (P9) the excess has a simple form. The film's potential follows the current around the meander or the cut, so two film regions on either side of a narrow cut differ by a potential $\\Delta\\varphi$, and the field across the cut stores the energy $\\frac12C'_{\\mathrm{cut}}\\ell_c\\Delta\\varphi^2$. Its share of $2W/V^2$ is",
     "Eqs. (P8) and (P9) still hold for such a film, with $u$ its DC potential when A is at 1 V and B at 0 V, and $v = 1 - u$. By the reciprocity of the resistive sheet, a current drawn from the film at a point P returns to the terminals as the fraction $v(\\mathrm P)$ through B, which is what Eqs. (P6) and (P7) used along a straight film. The film's potential follows the current around the meander or the cut, so the two sides of a narrow cut differ by a potential $\\Delta\\varphi(\\ell)$ that varies along it, falling to zero at the tip of a plunge cut. The field across the cut stores the energy $\\frac12\\int C'_{\\mathrm{cut}}\\Delta\\varphi^2\\,\\mathrm d\\ell$, and its share of $2W/V^2$ is"),
    ("\\Delta C_{\\mathrm{cut}} = C'_{\\mathrm{cut}}\\,\\ell_c\\left(\\frac{\\Delta\\varphi}V\\right)^2,\n\\tag{P49}",
     "\\Delta C_{\\mathrm{cut}} = \\int_{\\mathrm{cut}}C'_{\\mathrm{cut}}\\left(\\frac{\\Delta\\varphi(\\ell)}V\\right)^2\\mathrm d\\ell\\ \\le\\ C'_{\\mathrm{cut}}\\,\\ell_c\\left(\\frac{\\Delta\\varphi_{\\max}}V\\right)^2,\n\\tag{P49}"),
    ("A 0.6-mm cut across which half the voltage drops ($\\Delta\\varphi/V = 0.5$) then adds $137\\times0.6\\times0.25$ = 21 fF. A few such cuts make up the excess measured in the precision 0603.",
     "A 0.6-mm cut with at most half the voltage across it ($\\Delta\\varphi_{\\max}/V = 0.5$) then adds at most $137\\times0.6\\times0.25$ = 21 fF. That is the cut's own share; how much the cut also changes the rest of the field is not estimated, so the comparison is one of size. A few such cuts can account for the excess measured in the precision 0603. If an overcoat of permittivity $\\varepsilon_{\\mathrm{coat}}$ covers the film, the medium above it is not air, which raises $C'_{\\mathrm{cut}}$ by about $(\\varepsilon_{\\mathrm{al}} + \\varepsilon_{\\mathrm{coat}})/(\\varepsilon_{\\mathrm{al}} + 1)$."),
]


def main():
    p = Path(sys.argv[1])
    t = p.read_text(encoding="utf-8")
    for old, new in PAIRS:
        n = t.count(old)
        if n != 1:
            raise SystemExit(f"expected one match, found {n}: {old[:100]!r}")
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8", newline="\n")
    print(f"{len(PAIRS)} replacements applied")


if __name__ == "__main__":
    main()
