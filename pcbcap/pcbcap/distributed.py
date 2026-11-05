"""The feedback resistor as a distributed RC network: the film beyond first order in frequency.

Why this module exists
----------------------
capacitance.two_port holds the resistor's film at its DC potential, the linear profile.  That is
exact to first order in omega R C, with R the film's resistance and C the capacitance that loads the
film (geometry.LinearProfile; companion note, Eqs. (G.6)-(G.10)).  When a grounded conductor lies
close under the film, as the guard does in the guard layouts that amplifier makers publish, C can be
several times C_F.  At a transimpedance amplifier's own bandwidth, where omega R C_F is about 1, the
product omega R C is then not small: the film behaves as an RC line, and the admittance between its
terminations is no longer 1/R + j omega C_F.  This module computes that admittance from the field
solution, at any frequency.

The model
---------
Finite elements along the film.  Let u in [0, 1] be the position along the film from its lo end to
its hi end (its LinearProfile).  The film's potential is written as
    V(u) = sum_j V_j h_j(u),     h_j(u) = max(0, 1 - |n u - j|),     j = 0 .. n,              (1)
the hat functions of n equal elements.  Node 0 is the lo termination (with its pad, trace and lead:
the whole net), node n the hi one, and nodes 1 .. n-1 are points of the film.  The potential is
taken as uniform across the film's width: the hat functions depend on u only.  This holds when the
surroundings of the film do not vary across its width, as for a guard trace that crosses under the
resistor at right angles to its axis.  The hat functions sum to 1, and sum_j (j/n) h_j(u) = u, so the
DC profile is exactly the node vector u_j = j/n.

How the hats are imposed.  split_film divides the film into n films, film k covering
[(k-1)/n, k/n] with its own linear profile from node k-1 (its lo net) to node k (its hi net).  The
internal nodes are nets with no conductor of their own (nets "n1" .. "n(n-1)"); a film takes its
potential from its terminal nets (fem.Problem.dirichlet, rule 3), so a solve with node j at 1 V and
every other net at 0 V puts exactly h_j on the film.  Each sub-film is its own sheet, so the kinks of
the hat functions lie on mesh lines and the quadratic elements reproduce them exactly (the same
reason as for the LinearProfile's end points).

Capacitance matrix.  With psi_j the field of that solve (node j at 1 V, everything else at 0 V),
    C_jk = a(psi_j, psi_k) = int eps grad psi_j . grad psi_k dV,                              (2)
which is capacitance.maxwell_matrix over the node nets (its Eq. (1)).  C_jk is the charge that the
conductors and film segments of node j carry, weighted by h_j, when node k is at 1 V: the Galerkin
form of the film's capacitance.  Its row sums are the capacitances of the nodes to everything else,
i.e. to ground.

Conductance matrix.  At the frequencies of interest the film conducts along u only, with resistance R
between its ends (sheet resistance R_s, length g, width w, R = R_s g / w).  The power it dissipates,
    P = (1/R_s) int (dV/ds)^2 dA = (w / R_s) int_0^g (dV/ds)^2 ds,
is in the basis (1) P = V^T G V with G assembled from n elements of length g/n.  On one element V is
linear from V_a to V_b, so dV/ds = (V_b - V_a) n / g, and the integral of its square over the
element's length g/n is (V_b - V_a)^2 n / g.  Since R = R_s g / w, the factor w / R_s equals g / R, and
each element contributes
    (n / R) (V_b - V_a)^2,   i.e. the element matrix (n / R) [[1, -1], [-1, 1]].              (3)
Assembled, G is (n / R) times the Laplacian of the path 0 - 1 - ... - n: each element is a resistor
R / n between neighbouring nodes.  (Check: with the linear profile, V_j = j / n, P = n (n / R) (1/n)^2
= 1 / R, the power of 1 V across R.)

Admittance.  At angular frequency omega the nodal equations are (G + j omega C) V = I, with I the
current injected at each node.  Only the two end nodes connect to the circuit.  In a transimpedance
amplifier the input end (the inverting input) is held at 0 V and the output end at V_out; with
V_out = 1, the internal nodes carry no injected current, so
    Y_II V_I = -Y_Io,     V_I = -Y_II^-1 Y_Io,                                                  (4)
and the current that the network delivers into the input node (the current the amplifier must sink
there) is
    y_F = -(Y_io + Y_iI V_I),     Z_F = 1 / y_F,                                                (5)
with o and i the output and input nodes and I the internal ones.  Z_F is the feedback impedance; with
an ideal amplifier the transimpedance is -Z_F.

Low frequencies.  Expanding (4)-(5) to first order in omega: at omega = 0 the internal nodes sit at
the DC profile u and y_F = 1/R; the first-order term is j omega (-v^T C u) with v = 1 - u, the
expression of capacitance.py, Eq. (3).  Because the node vector u reproduces the linear profile
exactly, -v^T C u equals capacitance.two_port's C_F on the same mesh up to rounding; ladder() checks
this.  The second-order terms, absent from two_port, are what this module adds.

Input admittance and the film's noise.  The second quantity a transimpedance amplifier needs from its
feedback network is the admittance at the input node with the output node held at 0 V.  With the
input at 1 V and again no current injected at the internal nodes,
    Y_II V_I = -Y_Ii,     V_I = -Y_II^-1 Y_Ii,     y_11 = Y_ii + Y_iI V_I,                       (6)
the current that the input must supply.  Its real part sets the film's Johnson noise: a passive
network in thermal equilibrium at temperature T, with every terminal but one held at a fixed
potential, drives into that terminal, held at its own potential, a noise current of one-sided
spectral density 4 k_B T Re{y} (Nyquist's theorem), with y the admittance seen there.  In this model
only the film dissipates (the dielectrics are lossless, materials.py), so Re{y_11} is the film's
own: 1/R at DC, larger at frequencies where the capacitance along the film shunts part of it.  The
high-gain note derives the same for a uniform line (its Eq. (27)).

An error estimate from the same solves.  A hat function of n/m elements is a combination of the hat
functions of n elements with the coefficients of linear interpolation,
    H_J(u) = sum_j P_jJ h_j(u),     P_jJ = max(0, 1 - |j - m J| / m),                            (7)
exactly, because H_J is linear between coarse nodes, which are also fine nodes.  The field equation
and its boundary conditions are linear, so the field of the film potential H_J is sum_j P_jJ psi_j,
and the capacitance matrix (2) of the coarse elements is P^T C P: the same field solutions, with no
new solve (coarsen()).  The end nodes stay the same nets.  With linear elements the error falls as
1/n^2, so y_n = y + K/n^2 and y_(n/2) = y + 4K/n^2, and the error of n elements is estimated by
Richardson's rule as (y_(n/2) - y_n) / 3.  check_uniform_line() also compares this estimate with
the true error.

The uniform RC line as a check.  For a film coupled only to ground, with total capacitance C_g spread
uniformly, the exact line equations give y_F = (theta / sinh theta) / R and y_11 = (theta coth theta)
/ R, with theta^2 = j omega R C_g (high-gain note, Eq. (25), there with the end-to-end capacitance
C_ee added to both).  check_uniform_line() builds (2) for that case from the consistent Galerkin mass
matrix of the hat functions, (C_g / n) [[1/3, 1/6], [1/6, 1/3]] per element (the integral of
c_g h_j h_k over one element of length 1/n, with c_g = C_g per unit of u), evaluates (5) and (6), and
compares both with the exact formulas as n grows.  The error of linear elements falls as 1/n^2;
pcbcap.checks runs this comparison as the check uniform_rc_line.
"""
from __future__ import annotations

import copy

import numpy as np

from .capacitance import maxwell_matrix
from .geometry import Film, LinearProfile, Sheet


def split_film(layout, n: int, prefix: str = "n"):
    """A copy of ``layout`` whose one film is divided along its length into n films joined at the
    virtual nets prefix1 .. prefix(n-1) (module docstring).  Returns (layout, node nets), the node
    nets ordered from the film's lo end to its hi end: [lo net, prefix1, ..., prefix(n-1), hi net]."""
    if n < 1:
        raise ValueError("n must be at least 1")
    lay = copy.deepcopy(layout)
    films = [k for k, it in enumerate(lay.items) if isinstance(it.role, Film)]
    if len(films) != 1:
        raise ValueError(f"split_film needs exactly one film, found {len(films)}")
    k0 = films[0]
    sheet = lay.items[k0]
    film = sheet.role
    p = film.profile
    if not isinstance(p, LinearProfile):
        raise TypeError("split_film needs a film with a LinearProfile")
    nodes = [film.lo] + [f"{prefix}{j}" for j in range(1, n)] + [film.hi]
    pieces = []
    for j in range(1, n + 1):
        s0 = p.start + (j - 1) * (p.end - p.start) / n
        s1 = p.start + j * (p.end - p.start) / n
        spans = dict(sheet.spans)
        spans[p.axis] = (min(s0, s1), max(s0, s1))
        role = Film(hi=nodes[j], lo=nodes[j - 1], profile=LinearProfile(p.axis, s0, s1))
        pieces.append(Sheet(sheet.normal, sheet.at, spans, role, f"{sheet.name}-{j}", [], sheet.mesh_size))
    lay.items[k0:k0 + 1] = pieces
    return lay, nodes


def ladder(problem, nodes: list[str]) -> dict:
    """The capacitance matrix (2) between the node nets (fF) and its first-order check.

    Returns dict(nodes, u, C, C_F_dc, C_lo0, C_hi0, ground): u the node positions (0 at the lo end);
    C_F_dc = -v^T C u (module docstring); C_hi0 = u^T C (u + v) and C_lo0 = v^T C (u + v), the
    first-order capacitances of the two ends to ground (capacitance.py, Eq. (5), with u the DC
    potentials when the hi end is at 1 V and v when the lo end is); and ground, the row sums of C,
    each node's capacitance to everything outside the node set."""
    names, C = maxwell_matrix(problem, nodes)
    n = len(nodes) - 1
    u = np.arange(n + 1) / n                    # DC potential with the hi end at 1 V
    v = 1.0 - u                                 # DC potential with the lo end at 1 V
    return dict(nodes=names, u=u.tolist(), C=C.tolist(), C_F_dc=float(-v @ C @ u),
                C_hi0=float(u @ C @ (u + v)), C_lo0=float(v @ C @ (u + v)),
                ground=C.sum(axis=1).tolist())


def conductance(n: int, R: float) -> np.ndarray:
    """G of Eq. (3): (n / R) times the Laplacian of the path of n + 1 nodes."""
    G = np.zeros((n + 1, n + 1))
    for j in range(n):
        G[j, j] += n / R
        G[j + 1, j + 1] += n / R
        G[j, j + 1] -= n / R
        G[j + 1, j] -= n / R
    return G


def feedback_admittance(C_fF, R: float, freqs, output_end: str = "hi") -> np.ndarray:
    """y_F of Eq. (5) at the frequencies ``freqs`` (Hz) for the node capacitance matrix ``C_fF`` (fF)
    and the film resistance R (ohm).  ``output_end`` says which end node is the amplifier's output,
    "hi" (the last node) or "lo" (the first); the other end is the input, held at 0 V."""
    C = np.asarray(C_fF, dtype=float) * 1e-15
    n = C.shape[0] - 1
    G = conductance(n, R)
    o, i = (n, 0) if output_end == "hi" else (0, n)
    inner = list(range(1, n))
    out = []
    for f in np.atleast_1d(freqs):
        Y = G + 1j * 2.0 * np.pi * f * C
        if inner:
            V_I = np.linalg.solve(Y[np.ix_(inner, inner)], -Y[inner, o])
            y = -(Y[i, o] + Y[i, inner] @ V_I)
        else:
            y = -Y[i, o]
        out.append(y)
    return np.array(out)


def input_admittance(C_fF, R: float, freqs, output_end: str = "hi") -> np.ndarray:
    """y_11 of Eq. (6) at the frequencies ``freqs`` (Hz): the admittance at the input node with the
    output node held at 0 V; 4 k_B T Re{y_11} is the film's noise current into the input (module
    docstring).  Arguments as for feedback_admittance."""
    C = np.asarray(C_fF, dtype=float) * 1e-15
    n = C.shape[0] - 1
    G = conductance(n, R)
    o, i = (n, 0) if output_end == "hi" else (0, n)
    inner = list(range(1, n))
    out = []
    for f in np.atleast_1d(freqs):
        Y = G + 1j * 2.0 * np.pi * f * C
        if inner:
            V_I = np.linalg.solve(Y[np.ix_(inner, inner)], -Y[inner, i])
            y = Y[i, i] + Y[i, inner] @ V_I
        else:
            y = Y[i, i]
        out.append(y)
    return np.array(out)


def coarsen(C_fF, factor: int) -> np.ndarray:
    """The capacitance matrix (2) of n / factor elements from that of n elements, P^T C P with P the
    interpolation matrix of Eq. (7) (module docstring); exact, no solve."""
    C = np.asarray(C_fF, dtype=float)
    n = C.shape[0] - 1
    if factor < 1 or n % factor:
        raise ValueError(f"factor {factor} does not divide the {n} elements")
    j = np.arange(n + 1)[:, None]
    J = np.arange(n // factor + 1)[None, :]
    P = np.maximum(0.0, 1.0 - np.abs(j - factor * J) / factor)
    return P.T @ C @ P


def uniform_line_matrix(n: int, C_g_fF: float) -> np.ndarray:
    """The capacitance matrix (2) of n hat elements for a film whose only capacitance is C_g (fF),
    spread uniformly to ground: the consistent mass matrix (C_g / n) [[1/3, 1/6], [1/6, 1/3]] per
    element (module docstring)."""
    C = np.zeros((n + 1, n + 1))
    for j in range(n):
        C[np.ix_([j, j + 1], [j, j + 1])] += (C_g_fF / n) * np.array([[1 / 3, 1 / 6], [1 / 6, 1 / 3]])
    return C


def check_uniform_line(R: float = 1e9, C_g_fF: float = 100.0, ns=(4, 8, 16, 32), thetas=(0.5, 1.0, 2.0, 4.0)):
    """Compare Eqs. (5) and (6) with the exact uniform RC line, y_F = (theta / sinh theta) / R and
    y_11 = (theta coth theta) / R, theta^2 = j omega R C_g, for a film coupled only to ground (module
    docstring).  Returns rows (n, |theta|, relative error of y_F, relative error of y_11), each error
    |y - exact| / |exact|."""
    rows = []
    for n in ns:
        C = uniform_line_matrix(n, C_g_fF)
        for th in thetas:
            omega = th ** 2 / (R * C_g_fF * 1e-15)           # |theta|^2 = omega R C_g
            f = omega / (2 * np.pi)
            y_f = feedback_admittance(C, R, [f])[0]
            y_11 = input_admittance(C, R, [f])[0]
            t = np.sqrt(1j * omega * R * C_g_fF * 1e-15)
            exact_f = (t / np.sinh(t)) / R
            exact_11 = (t / np.tanh(t)) / R
            rows.append((n, th, float(abs(y_f - exact_f) / abs(exact_f)),
                         float(abs(y_11 - exact_11) / abs(exact_11))))
    return rows
