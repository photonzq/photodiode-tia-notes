import math
import numpy as np
import sympy as sp
from scipy.special import ellipk, ellipkm1
from scipy.integrate import quad

def show(label, val, ref=None):
    if ref is None:
        print(f"{label}: {val}")
    else:
        print(f"{label}: {val}  ref {ref}  diff {val - ref:+.3e}")

print("=== constants ===")
show("eps0 fF/mm", 8.8541878128e-12 * 1e15 / 1e3)
show("rel change CODATA2018->2022 (if 2022 = 8.8541878188e-12)", (8.8541878188 - 8.8541878128) / 8.8541878128)
show("air 1.0006 error %", (1.0006 - 1) / 1.0006 * 100)
show("air 1.000536 (20 C) error %", (1.000536 - 1) / 1.000536 * 100)

print("=== parallel plate ===")
D, A, e0 = sp.symbols("D A eps0", positive=True)
d1, d2, e1, e2 = sp.symbols("d1 d2 e1 e2", positive=True)
V = D * (d1 / (e0 * e1) + d2 / (e0 * e2))
C = sp.simplify(A * D / V)
show("C series", C)
print("check vs A eps0/(d1/e1+d2/e2):", sp.simplify(C - A * e0 / (d1 / e1 + d2 / e2)))
# floating slab: d=1, t=0.2 -> eps0*2/0.8
print("floating slab C/eps0 (width 2):", 2 / (0.3 + 0.5))

print("=== coplanar strips ===")
w = s = 0.5
m = (w / (s + w)) ** 2
r1 = ellipk(m) / ellipkm1(m)
k0 = s / (s + 2 * w)
r2 = 0.5 * ellipk(1 - k0 ** 2) / ellipk(k0 ** 2)
show("K(m)/K(1-m)", r1, r2)
x1, x2, x3, x4, z = sp.symbols("x1 x2 x3 x4 z", real=True)
T = (z - x1) * (x3 - x4) / ((z - x4) * (x3 - x1))
mm = sp.simplify(T.subs(z, x2))
sw, ss = sp.symbols("w s", positive=True)
mm_strips = sp.simplify(mm.subs({x1: -ss / 2 - sw, x2: -ss / 2, x3: ss / 2, x4: ss / 2 + sw}))
print("cross ratio for strips:", sp.factor(mm_strips))
for (w_, s_) in [(0.55, 0.40), (0.25, 0.75), (1.0, 0.1)]:
    m_ = (w_ / (s_ + w_)) ** 2
    k0_ = s_ / (s_ + 2 * w_)
    print("  w,s", w_, s_, ellipk(m_) / ellipkm1(m_), 0.5 * ellipk(1 - k0_ ** 2) / ellipk(k0_ ** 2))

print("=== coaxial ===")
r, a_, b_, lam, eps = sp.symbols("r a b lambda eps", positive=True)
Vc = sp.integrate(lam / (2 * sp.pi * eps * r), (r, a_, b_))
print("V =", sp.simplify(Vc), " C' =", sp.simplify(lam / Vc))

print("=== linear block ===")
g, Tt, Vv, epsb, x = sp.symbols("g T V eps x", positive=True)
phi = Vv * x / g
energy = sp.Rational(1, 2) * epsb * sp.diff(phi, x) ** 2 * g * Tt
print("C' from energy:", sp.simplify(2 * energy / Vv ** 2))
# C_F = -a(phi_u, phi_v) with phi_u=(x+g/2)/g, phi_v=1-phi_u
pu = (x + g / 2) / g
pv = 1 - pu
print("C_F = -a(u,v):", sp.simplify(-epsb * sp.diff(pu, x) * sp.diff(pv, x) * g * Tt))

print("=== mirror decomposition (random symmetric K commuting with a mirror) ===")
rng = np.random.default_rng(1)
n = 6
# mirror permutation swapping i <-> n-1-i
Mp = np.eye(n)[::-1]
B = rng.normal(size=(n, n))
K = B @ B.T
K = 0.5 * (K + Mp @ K @ Mp)        # commutes with the mirror
pu_ = rng.normal(size=n)
pv_ = Mp @ pu_                      # mirror image of phi_u is phi_v
pe = 0.5 * (pu_ + pv_)
po = 0.5 * (pu_ - pv_)
a = lambda p, q: p @ K @ q
show("-a(u,v)", -a(pu_, pv_), a(po, po) - a(pe, pe))
show("a(u,u+v)", a(pu_, pu_ + pv_), 2 * a(pe, pe))
show("a(o,e)", a(po, pe), 0.0)

print("=== Richardson constant ratio ===")
q, p, r3 = sp.symbols("q p r3", positive=True)
ratio = ((q ** 2 * r3) ** p - (q * r3) ** p) / ((q * r3) ** p - r3 ** p)
print("ratio simplifies to:", sp.simplify(ratio))
for q_ in (2.0, 1.414):
    print(f"  q={q_}: q^0.05={q_**0.05:.4f}, q^8={q_**8:.1f}")

print("=== enclosure: concentric spheres ===")
aa, bb, ee = sp.symbols("a b eps", positive=True)
Cs = 4 * sp.pi * ee * aa * bb / (bb - aa)
print("C/C0 series in a/b:", sp.series((Cs / (4 * sp.pi * ee * aa)).subs(bb, aa / sp.Symbol("t")), sp.Symbol("t"), 0, 3))
R1, R2, Ci, k = sp.symbols("R1 R2 C_inf k", positive=True)
CR = lambda R: Ci + k / R
print("two-size extrapolation:", sp.simplify((R2 * CR(R2) - R1 * CR(R1)) / (R2 - R1)))

print("=== ring counts ===")
he, hc, gg, dd, ll = sp.symbols("h_e h_c g d l", positive=True)
Dmax = (hc - he) / gg
I2 = sp.integrate(2 * sp.pi * dd / (he + gg * dd) ** 2, (dd, 0, Dmax))
print("2-D cells around a corner:", sp.simplify(I2))
I3 = sp.integrate(2 * sp.pi * dd * ll / (he + gg * dd) ** 3, (dd, 0, Dmax))
print("3-D cells around an edge:", sp.simplify(I3))
print("3-D, h_c -> infinity:", sp.limit(I3, hc, sp.oo))
# compare with the code: l/h_e * 2 pi/g^2 * max(ln(hc/he),1) / 4
for (he_, hc_, g_) in [(0.00375, 0.045, 0.3), (0.015, 0.18, 0.3), (0.00375 * 4, 0.045 * 4, 0.3)]:
    code = 1.0 / he_ * 2 * math.pi / g_ ** 2 * max(math.log(hc_ / he_), 1.0) / 4.0
    exact = float(I3.subs({he: he_, hc: hc_, gg: g_, ll: 1.0}))
    print(f"  per mm of edge, h_e={he_}, h_c={hc_}: code {code:.4g}, integral (cells) {exact:.4g}, ratio {code/exact:.3f}; "
          f"x6 tets: {6*exact:.4g} ratio {code/(6*exact):.3f}")

print("=== uniform RC line ===")
th = sp.symbols("theta")
print("theta/sinh(theta):", sp.series(th / sp.sinh(th), th, 0, 8))
wRC = sp.symbols("x", positive=True)
expr = sp.series((th / sp.sinh(th)).subs(th, sp.sqrt(sp.I * wRC)), wRC, 0, 4).removeO()
expr = sp.expand(expr)
print("Re:", sp.simplify(sp.re(expr)), " Im:", sp.simplify(sp.im(expr)))
print("31*6/15120 =", sp.Rational(31 * 6, 15120), "=", 31 * 6 / 15120, "; 31/2520 =", 31 / 2520)

print("=== loss tangent: two layers in series, second order ===")
t1, t2 = sp.symbols("t1 t2", real=True)
Cst = 1 / (d1 / (e1 * (1 - sp.I * t1)) + d2 / (e2 * (1 - sp.I * t2)))
C0s = 1 / (d1 / e1 + d2 / e2)
eps_ = sp.symbols("epsilon", positive=True)
ser = sp.series(Cst.subs({t1: eps_ * t1, t2: eps_ * t2}), eps_, 0, 3).removeO()
re2 = sp.simplify(sp.re(sp.expand(ser)) - C0s)
print("Re C* - C0 to second order:", sp.factor(re2))
print("numeric: d1=d2=1, e1=4.2, e2=1, t1=0.02, t2=0 ->",
      complex(Cst.subs({d1: 1, d2: 1, e1: 4.2, e2: 1, t1: 0.02, t2: 0})).real / float(C0s.subs({d1: 1, d2: 1, e1: 4.2, e2: 1})) - 1)
print("numeric: t1=0.041, t2=0 ->",
      complex(Cst.subs({d1: 1, d2: 1, e1: 4.2, e2: 1, t1: 0.041, t2: 0})).real / float(C0s.subs({d1: 1, d2: 1, e1: 4.2, e2: 1})) - 1)

print("=== strips: truncation by an open (Neumann) circle of radius R ===")
a_s, b_s = 0.25, 0.75
kk = a_s / b_s
Kp = ellipk(1 - kk ** 2)
Q_int = quad(lambda t: 1 / math.sqrt((t * t - a_s ** 2) * (b_s ** 2 - t * t)), a_s, b_s, limit=200)[0]
p_int = quad(lambda t: t / math.sqrt((t * t - a_s ** 2) * (b_s ** 2 - t * t)), a_s, b_s, limit=200)[0]
show("int sigma (shape)", Q_int, Kp / b_s)
show("int x sigma (shape)", p_int, math.pi / 2)
d_eff = 2 * p_int / Q_int
print("charge-centroid separation d =", d_eff)
Cprime_over_eps0 = 2 * r1
coef = Cprime_over_eps0 / (2 * math.pi)
for R in (200.0, 6.0, 60.0):
    print(f"  R={R}: dC/C ~ -{coef:.4f} (d/R)^2 = {-coef * (d_eff / R) ** 2:.3e};  (1/R)^2 = {(1/R)**2:.3e}")

print("=== facet key overflow ===")
print("2^21 =", 2 ** 21, " (2^21)^3 = 2^63:", (2 ** 21) ** 3 == 2 ** 63, " 2e6^3 < 2^63-1:", (2_000_000) ** 3 < 2 ** 63 - 1)

print("=== Kron reduction: first-order admittance = E^T C E ===")
rng = np.random.default_rng(7)
N = 8   # A=0, B=1, film pieces 2..7
# film chain conductances A-2-3-...-7-B
Gm = np.zeros((N, N))
chain = [0] + list(range(2, N)) + [1]
for i, j in zip(chain[:-1], chain[1:]):
    gval = 1.0
    Gm[i, i] += gval; Gm[j, j] += gval; Gm[i, j] -= gval; Gm[j, i] -= gval
Bc = rng.normal(size=(N, N)) * 0.1
Cm = -np.abs(Bc + Bc.T)
np.fill_diagonal(Cm, 0)
Cm -= np.diag(Cm.sum(axis=1)) - np.diag(rng.uniform(0.05, 0.2, N))   # diagonally dominant: ground caps
T_ = [0, 1]; I_ = list(range(2, N))
def yred(om):
    Y = Gm + 1j * om * Cm
    return Y[np.ix_(T_, T_)] - Y[np.ix_(T_, I_)] @ np.linalg.solve(Y[np.ix_(I_, I_)], Y[np.ix_(I_, T_)])
E = np.zeros((N, 2)); E[0, 0] = 1; E[1, 1] = 1
E[I_, :] = -np.linalg.solve(Gm[np.ix_(I_, I_)], Gm[np.ix_(I_, T_)])
Cred = E.T @ Cm @ E
om = 1e-4
print("Im(Yred)/omega:\n", (yred(om).imag / om).round(6), "\nE^T C E:\n", Cred.round(6))
u = E[:, 0]; v = E[:, 1]
print("v^T C u =", v @ Cm @ u, " ; u+v = 1:", np.allclose(u + v, 1))

print("=== shares as sensitivities: series plates, Euler ===")
Cfun = lambda e1_, e2_: 1 / (0.4 / e1_ + 0.6 / e2_)
e1_, e2_ = 4.0, 1.0
h = 1e-6
s1 = e1_ * (Cfun(e1_ * (1 + h), e2_) - Cfun(e1_ * (1 - h), e2_)) / (2 * h * e1_)
s2 = e2_ * (Cfun(e1_, e2_ * (1 + h)) - Cfun(e1_, e2_ * (1 - h))) / (2 * h * e2_)
# energy shares: D uniform, energy_k = D^2 d_k/(e_k) ... share_k = C^2 d_k/e_k
Cv = Cfun(e1_, e2_)
print("e_k dC/de_k:", s1, s2, " energy shares C^2 d_k/e_k:", Cv ** 2 * 0.4 / e1_, Cv ** 2 * 0.6 / e2_, " sum", s1 + s2, "C", Cv)

print("=== stiffness scaling with length unit ===")
L = sp.symbols("lambda", positive=True)
for dim in (2, 3):
    print(f"  dim {dim}: K scales as lambda^{dim-2}")
