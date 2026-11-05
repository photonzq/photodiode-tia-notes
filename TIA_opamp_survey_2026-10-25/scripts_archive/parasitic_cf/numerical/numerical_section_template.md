### G.14 Field solutions of the same layouts

The closed forms of Sections G.6 to G.11 solve idealised two-dimensional problems, and Section G.12 adds their results along widths. Two questions remain that no closed form answers. Is each derivation right? And how large are the parts that the model leaves out, such as the field around the ends and sides of the part (approximation 1), the thickness of the pads and terminations, the solder and the stand-off, and the grounded neighbours of the pins? This section answers both with numerical solutions of the electrostatic field equation by the finite-element method.

The solver is the package `pcbcap` at the top level of the repository, which its `README.md` describes; each of its modules derives what it does in its docstring. It uses gmsh for the meshes [A35], scikit-fem for the finite elements [A36] and PyAMG for the linear systems [A37]. The scripts in `scripts_archive/parasitic_cf/numerical/` set up every case of this section and record the results in `data/parasitic_cf/numerical/`, from which the tables and Figures 44–51 are made. The closed forms remain the argument; the field solutions check them and measure what they leave out.

#### G.14.1 What the solver computes

**Electrostatics only.** The solver computes the quantity of the rest of this appendix, the electrostatic capacitance, which is the limit of zero frequency. It fixes the potential of every conductor, solves for the potential between the conductors, and reads off their charges. With no changing magnetic flux, Faraday's law gives $\nabla\times\mathbf E = 0$, so $\mathbf E = -\nabla\varphi$, and Gauss's law with no free charge in the dielectrics gives the field equation of Section G.2.1, $\nabla\cdot(\varepsilon\nabla\varphi) = 0$, with $\varepsilon$ constant in each material. The model therefore contains no magnetic field and no inductance, no current apart from the potential that a resistor's own DC current sets along its film, and one real permittivity per material.

**The field equation in weak form.** Call a function $w$ admissible if it is continuous, vanishes wherever the potential is prescribed (on the conductors, on the film, on the grounded faces of the enclosure and on the mirror plane of an odd drive), and is constant on each floating conductor. Multiply the field equation by an admissible $w$ and integrate over each material region $\mathcal V_k$ separately. The divergence theorem applied to $w\,\varepsilon\nabla\varphi$ gives

$$
0 = -\sum_k\int_{\mathcal V_k} w\,\nabla\cdot(\varepsilon\nabla\varphi)\,\mathrm dV
= \int_{\mathcal V}\varepsilon\,\nabla\varphi\cdot\nabla w\,\mathrm dV - \sum_k\oint_{\partial\mathcal V_k} w\,\varepsilon\,\frac{\partial\varphi}{\partial n_k}\,\mathrm dS ,
$$

with $n_k$ the outward normal of region $k$. The surface terms vanish for three different reasons:

- on the outer boundary, $w = 0$ where the potential is prescribed, and $\varepsilon\,\partial\varphi/\partial n = 0$ on the remaining faces, which are insulating cuts, the mirror plane of an even drive, and open faces of the enclosure;
- on a floating conductor, $w$ is a constant $w_f$, so its term is $-w_f$ times the conductor's net charge, which is zero;
- an interface between two materials appears twice, with opposite normals, and since $w$ has one value there, the two terms add to $w$ times the jump of the normal displacement, which is zero.

Near the edge of a conductor the gradient is singular, as $r^{\nu-1}$ with $0<\nu<1$ (Eq. (G.55) below), but the surface integral over a thin tube of radius $\rho$ around the edge is of order $\rho\cdot\rho^{\nu-1} = \rho^{\nu}$ and vanishes as $\rho\to0$, so the identity holds. What remains is

$$
\int_{\mathcal V}\varepsilon\,\nabla\varphi\cdot\nabla w\,\mathrm dV = 0 \qquad \text{for every admissible } w .
\tag{G.50}
$$

Conversely, a continuous function with the prescribed values that satisfies Eq. (G.50) has a continuous normal displacement at every interface and zero charge on every floating conductor, because $w$ can be chosen nonzero near a single patch of one interface, or on a single floating conductor, and zero elsewhere. These two conditions follow without being imposed. Since $\int\varepsilon|\nabla(\varphi+tw)|^2\,\mathrm dV = \int\varepsilon|\nabla\varphi|^2\,\mathrm dV + 2t\int\varepsilon\nabla\varphi\cdot\nabla w\,\mathrm dV + t^2\int\varepsilon|\nabla w|^2\,\mathrm dV$, Eq. (G.50) is also the condition for the energy of Eq. (G.2) to be stationary, and since the last term is positive, minimal: this is Dirichlet's principle of Section G.4.2.

**Finite elements.** The method imposes Eq. (G.50) on a finite set of trial potentials: continuous functions that are quadratic polynomials on each tetrahedron of a mesh, or on each triangle in two dimensions [B6]. Write $\varphi = \sum_ja_jN_j$, where the $N_j$ are the shape functions and the $a_j$ the values of $\varphi$ at the vertices and edge midpoints, the nodes. Eq. (G.50) with $w = N_i$ becomes

$$
\sum_jK_{ij}a_j = 0,
\qquad
K_{ij} = \int_{\mathcal V}\varepsilon\,\nabla N_i\cdot\nabla N_j\,\mathrm dV ,
\tag{G.51}
$$

for every node $i$ whose value is not prescribed. The prescribed values move to the right-hand side: with $f$ the free and $p$ the prescribed nodes, $K_{ff}\mathbf a_f = -K_{fp}\mathbf a_p$. The conductors enter as follows:

- each conductor of a connected net fixes its nodes at the net's potential, and a film fixes its nodes at its DC potential, which is linear along the film and therefore contained exactly in the quadratic elements;
- a floating conductor, such as pin 2 of the OPA855, shares one unknown among its nodes. Its equation is the sum of its rows of Eq. (G.51), which is $\int\varepsilon\nabla\varphi\cdot\nabla\chi\,\mathrm dV$ with $\chi = \sum N_i$ over its nodes. $\chi$ is 1 on the conductor and 0 on every other boundary, so the divergence theorem turns this integral into the conductor's net charge, and the equation sets that charge to zero.

The mesh follows every boundary between items, so each element lies in one material, and the integrals of Eq. (G.51) are evaluated exactly. The trial potentials are a subset of the admissible ones, and a minimum over a subset is not smaller, the reasoning of Rule 2. Every computed energy therefore exceeds the exact one. That holds for each energy separately; it does not hold for $C_{F,\mathrm{par}}$, which Eq. (G.53) below writes as a difference of two energies, and it does not make successive meshes converge monotonically, because each mesh is generated afresh rather than by subdividing the previous one. How far each result lies from its limit is therefore measured, by refinement.

**The feedback capacitance.** By Eq. (G.2), the quadratic form $\mathbf v^{\mathsf T}\mathbf C\mathbf u$ of Eq. (G.8) equals $\int\varepsilon\,\nabla\varphi_{\mathbf u}\cdot\nabla\varphi_{\mathbf v}\,\mathrm dV$. Here $\varphi_{\mathbf u} = \sum_ju_j\varphi_j$ is the potential with A at 1 V, B at 0 V and the film at its DC potential, and $\varphi_{\mathbf v}$ is the potential with A and B exchanged. Eq. (G.8) therefore reads

$$
C_{F,\mathrm{par}} = -\int_{\mathcal V}\varepsilon\,\nabla\varphi_{\mathbf u}\cdot\nabla\varphi_{\mathbf v}\,\mathrm dV ,
\tag{G.52}
$$

and the capacitances to ground are $C_{A0} = \int\varepsilon\,\nabla\varphi_{\mathbf u}\cdot\nabla(\varphi_{\mathbf u} + \varphi_{\mathbf v})\,\mathrm dV$ and, with $\mathbf u$ and $\mathbf v$ exchanged, $C_{B0}$. These are the shunts $\mathbf u^{\mathsf T}\mathbf C(\mathbf u + \mathbf v)$ and $\mathbf v^{\mathsf T}\mathbf C(\mathbf u + \mathbf v)$ of Section G.2.3.

**Halves and quarters.** A resistor centred on its pads is unchanged by the reflection $x\to-x$ if A and B are exchanged, and by the reflection $y\to-y$. Define the odd and even drives of Eq. (G.8):

- $\varphi_o = (\varphi_{\mathbf u} - \varphi_{\mathbf v})/2$, with A at $+\tfrac12$ V and B at $-\tfrac12$ V;
- $\varphi_e = (\varphi_{\mathbf u} + \varphi_{\mathbf v})/2$, with both at $\tfrac12$ V.

Substitute $\varphi_{\mathbf u} = \varphi_e + \varphi_o$ and $\varphi_{\mathbf v} = \varphi_e - \varphi_o$. In Eq. (G.52) the integrand becomes $(\nabla\varphi_e + \nabla\varphi_o)\cdot(\nabla\varphi_e - \nabla\varphi_o) = |\nabla\varphi_e|^2 - |\nabla\varphi_o|^2$: the cross terms cancel identically. In $C_{A0}$ they do not, since $\nabla\varphi_{\mathbf u}\cdot\nabla(\varphi_{\mathbf u}+\varphi_{\mathbf v}) = 2|\nabla\varphi_e|^2 + 2\nabla\varphi_o\cdot\nabla\varphi_e$, and here the symmetry is needed. The mirror image of a solution solves the mirrored problem, which is the same problem, and the solution is unique, so $\varphi_o$ is odd and $\varphi_e$ even in $x$. Their gradients' scalar product is then odd in $x$, and its integral over the symmetric volume vanishes. Under $y\to-y$ both drives are even. An odd potential vanishes on its mirror plane and an even one has zero normal derivative there, so each drive is found on the half $x\ge0$, and on the quarter $y\ge0$, with that condition on each cut plane. Each squared gradient is even under both reflections, so its integral is $f$ times its value over the computed part, and

$$
C_{F,\mathrm{par}} = f\left[a_h(\varphi_o) - a_h(\varphi_e)\right],
\qquad
C_{A0} = C_{B0} = 2f\,a_h(\varphi_e),
\tag{G.53}
$$

where $a_h(\varphi) = \int\varepsilon|\nabla\varphi|^2\,\mathrm dV$ over the computed part and $f$ is 2 for one mirror plane and 4 for two. This is the second form of Eq. (G.8) evaluated on a half or a quarter of the volume, and nothing in it is approximated.

**What the material shares mean.** The integrand of Eq. (G.52), summed over the elements of one material $k$, gives that material's share $S_k$ of $C_{F,\mathrm{par}}$, and the shares add up to $C_{F,\mathrm{par}}$. They are not the capacitances of separate problems, and not energies, since a share can be negative where the even field is stronger than the odd one. Their exact meaning is a sensitivity:

$$
S_k = \varepsilon_k\,\frac{\partial C_{F,\mathrm{par}}}{\partial\varepsilon_k} .
\tag{G.54}
$$

Each energy of Eq. (G.53) is a minimum over potentials whose prescribed values do not depend on the permittivities. To first order, a change of $\varepsilon_k$ changes such a minimum only through the explicit $\varepsilon_k$ in the integral, not through the minimiser, whose first-order change leaves a stationary value unchanged. So $\varepsilon_k$ times the derivative of each energy with respect to $\varepsilon_k$ is that energy's part in material $k$, and applying this to both energies of Eq. (G.53) gives Eq. (G.54). The shares add up to $C_{F,\mathrm{par}}$ because scaling every permittivity by the same factor scales $C_{F,\mathrm{par}}$ by that factor, and for such a function Euler's theorem gives $\sum_k\varepsilon_k\,\partial C_{F,\mathrm{par}}/\partial\varepsilon_k = C_{F,\mathrm{par}}$. A share therefore answers a design question exactly: raising the permittivity of material $k$ by 1 % raises $C_{F,\mathrm{par}}$ by $S_k$ times 1 %.

**Edges, meshes and their refinement.** Near an edge of a conductor or film the potential varies as $r^{\nu}$ with the distance $r$ from the edge. With one material filling the angle $\alpha$ around the edge, the separable solutions of the field equation are $V + c\,r^{\nu}\sin(\nu\theta)$, and $\varphi = V$ on both faces of the conductor, $\theta = 0$ and $\theta = \alpha$, requires $\sin(\nu\alpha) = 0$, so $\nu = \pi/\alpha$: $\tfrac23$ at the edge of a box ($\alpha = 3\pi/2$) and $\tfrac12$ at the edge of a sheet ($\alpha = 2\pi$). Where two materials meet at the edge, $\varepsilon_1$ over the angle $\alpha_1$ next to one face and $\varepsilon_2$ over $\alpha_2$ next to the other, the solutions $A\sin(\nu\theta)$ and $B\sin(\nu(\alpha_1+\alpha_2-\theta))$ must have equal values and equal normal displacements on the interface $\theta = \alpha_1$. Dividing the second condition by the first gives

$$
\varepsilon_1\cot(\nu\alpha_1) + \varepsilon_2\cot(\nu\alpha_2) = 0 .
\tag{G.55}
$$

A pad's lower edge on FR-4 (4.2 over $\pi$, air over $\pi/2$) has $\nu = 0.56$, and the film's edge at the corner of the alumina (9.7 over $\pi/2$, air over $3\pi/2$) has $\nu = 0.63$.

The meshes are graded. The element size is $h_{\mathrm{edge}}$ along every edge of a conductor or film and grows as $h_{\mathrm{edge}} + 0.3\,(d - h_{\mathrm{edge}})$ with the distance $d$ from it, so neighbouring elements differ in size by at most a factor 1.3, up to a core size $h_{\mathrm{core}}$ in a box around the parts and a far size $h_{\mathrm{far}}$ beyond. A refinement factor $r$ multiplies $h_{\mathrm{edge}}$, $h_{\mathrm{core}}$ and $h_{\mathrm{far}}$, but not the growth rate 0.3: the graded zone keeps its shape, and its extent scales with $r$. How the error then scales follows in two steps. First, the error of a computed energy is the energy of the error, $a(\varphi_h) - a(\varphi) = a(\varphi_h - \varphi)$, because the cross term $2\int\varepsilon\nabla\varphi\cdot\nabla(\varphi_h - \varphi)\,\mathrm dV$ vanishes by Eq. (G.50); and the computed potential is the best approximation in this energy, so the error is at most the energy of the error of interpolating $\varphi$ on the mesh. Second, near an edge that interpolation error has three parts:

- in the elements touching the edge, the energy of $r^{\nu}$ within $r < h_{\mathrm{edge}}$, of order $h_{\mathrm{edge}}^{2\nu}$;
- in the graded zone, where the element size at distance $\rho$ is about $0.3\rho$, a density of order $(0.3\rho)^4$ times the square of the third derivatives of $\rho^{\nu}$, i.e. $\rho^{2\nu-2}$, whose integral out to the zone's edge at $\rho \approx h_{\mathrm{core}}/0.3$ is of order $h_{\mathrm{core}}^{2\nu}$;
- in the core beyond, where the size is $h_{\mathrm{core}}$, again of order $h_{\mathrm{core}}^{2\nu}$.

All three scale as $r^{2\nu}$, while the smooth field far from the edges contributes in proportion to $r^4$. Every result is therefore expected to behave as

$$
C(r) = C_\infty + k\,r^{p},\quad p = 2\nu_{\min},
\qquad
\frac{C_1 - C_2}{C_2 - C_3} = \frac{r_1^p - r_2^p}{r_2^p - r_3^p},
\tag{G.56}
$$

with $\nu_{\min}$ the smallest edge exponent in the layout, which puts $p$ between about 1.1 and $\tfrac43$ for the edges named above. The second part of Eq. (G.56) is the difference of the first at three meshes, $r_1 > r_2 > r_3$. It gives the observed order $p$ by a root search, after which $k = (C_2 - C_3)/(r_2^p - r_3^p)$ and $C_\infty = C_3 - k\,r_3^p$ [A38]. The extrapolation is made only when $C_1 - C_2$ and $C_2 - C_3$ have the same sign and $0.05 < p < 4$. The upper limit is the order of the energy error of quadratic elements in a smooth field, which no singular problem exceeds; below the lower one the extrapolation step would exceed 28 times the last difference for meshes a factor 2 apart, more than any measured difference supports. The difference between $C_\infty$ and the finest mesh is quoted as the discretisation error.

Two limits apply. The edge size is capped at the layout's thinnest feature, the 15 µm of the termination metal (10 µm in the variant of Table G.12 with a 10-µm stand-off), so that no element has to bridge a feature thinner than itself. A level whose edge size would exceed the cap does not refine with its factor, and the solver refuses such levels in a convergence study. And only the four sizes of Section G.14.6 are computed on three meshes: Tables G.12 and G.13 use one mesh, and the OPA855 and OPA846 networks one or two meshes at the capped edge size. For those the discretisation error is not measured here; Section G.14.5 gives its size for the 0402.

**The enclosure.** The computation ends at a grounded box. In a layout without a ground of its own, part of the even drive's field ends on that box, which lowers $C_{F,\mathrm{par}}$ by Rule 6. How much follows from the potential of a unit charge inside the grounded box: the free-space potential plus that of the charges induced on the walls, which, near a layout much smaller than the box, is nearly constant, $-1/(4\pi\varepsilon R_{\mathrm{eff}})$, with $R_{\mathrm{eff}}$ proportional to the box's half-width $R$. A conductor with free-space capacitance $C_0$ and charge $Q$ then sits at $V = Q/C_0 - Q/(4\pi\varepsilon R_{\mathrm{eff}})$, so

$$
C(R) = \frac QV = \frac{C_0}{1 - C_0/(4\pi\varepsilon R_{\mathrm{eff}})} \approx C_0 + \frac{C_0^2}{4\pi\varepsilon R_{\mathrm{eff}}} .
$$

For a sphere of radius $a$ in a grounded sphere of radius $b$ this is exact, $4\pi\varepsilon ab/(b - a) = C_0/(1 - a/b)$. The odd drive carries no net charge, so its far field is a dipole field, its image in the walls produces a field of order $p_d/R^3$ at the layout ($p_d$ the dipole moment), and its energy changes only as $R^{-3}$. Only the even drive feels the walls at order $1/R$, and by Eq. (G.53) a change of $a_h(\varphi_e)$ alone changes $C_{A0}$ by $-2$ times what it changes $C_{F,\mathrm{par}}$. Each result is computed with the walls at $R$ = 8, 16 and 32 mm from the centre laterally, and as far above the board and below it, and extrapolated with

$$
C(R) = C_\infty + k_R\,R^{-q}
\tag{G.57}
$$

in the way of Eq. (G.56), with $1/R$ in the role of $r$, which measures the order $q$ instead of assuming $q = 1$. The enclosure correction $C_\infty - C(8\ \mathrm{mm})$ is computed on the coarsest mesh and added to the mesh-extrapolated value at 8 mm. Its own mesh error follows from the formula above: the correction is proportional to $C_0^2$, so a relative mesh error $\delta$ of the capacitance to ground makes an error of about $2\delta$ of the correction, which for the 0402 is about 1 % of it (Section G.14.5). The $1/R$ law holds only in three dimensions. Per unit length, the capacitance to a distant ground falls only as $1/\ln R$ and has no finite limit, so the two-dimensional comparisons of Section G.14.2 are made at a fixed enclosure. The limit describes a layout with no ground nearby. A real board has grounds near the network, such as planes outside a cut-out or grounded pins, and those belong in the layout itself, as in Sections G.14.9 and G.14.10.

#### G.14.2 Checks against exact solutions

Before it is used on the resistor, the solver reproduces problems whose answers are known. Table G.9 lists the checks of the package itself, against exact solutions derived in its module `analytic.py` and against identities that the method must satisfy. Each check prints its numbers and is run alone (`python -m pcbcap.checks run <name>`). Table G.10 compares each closed form of Sections G.6 to G.11 that is the exact solution of an idealised problem with the numerical solution of the same problem, built exactly as the derivation states it: a half-plane, a cut layer, a block with insulating faces, a floating wall. The parallel-plate estimates, Eqs. (G.42), (G.44) and (G.47), are not exact solutions of any problem and are not compared. Both tables are drawn from the records in `data/parasitic_cf/numerical/`.

*Table G.9. Checks of the solver. The relative error is that of the computed value against the exact one. Where the elements contain the exact solution, the tolerance $10^{-9}$ leaves room only for rounding. For the two-dimensional strips it is three times the error of their first run ($1.0\times10^{-4}$), a margin against changes of the mesh generator rather than a proof of accuracy, which the fall of the error with the element size shows instead. For the three-dimensional check the tolerance is the error that Eq. (G.56) itself reports, so that the check tests the error bars quoted for every three-dimensional result.*

| Check | What it exercises | Relative error | Tolerance |
|---|---|---|---|
<<table_checks>>

*Table G.10. The closed forms of Appendix G against numerical solutions of the same two-dimensional problems, per unit permittivity ($C'/\varepsilon_0\varepsilon_r$), for the 0402 dimensions of Table G.2 (`g_closed_forms_2d.py`). In the plane rows the mutual capacitance is a small difference of two large numbers, <<g41_frac_min>>–<<g41_frac_max>> of the capacitance to ground, which agrees to <<g41_ground>>; in the guard row the capacitance to ground agrees to <<g43_ground>>.*

| Equation | Problem | Closed form | Field solution | Relative difference |
|---|---|---|---|---|
<<table_closed>>

Every closed form is reproduced. The relative differences are <<cf_min>> to <<cf_max>> for the pads, the body's bounds, the air and the pins, and up to <<g41_max>> for the mutual capacitances over a plane, which agree to <<g41_abs>> per unit permittivity in absolute terms. Eq. (G.28), whose exact potential the elements contain, agrees to rounding. The guard of Eq. (G.43) agrees to <<g43_rel>>, closer than the edge error, so that agreement must partly be a cancellation. The differences are the discretisation error at the edges. The edge elements are 0.1 µm long; the strips of Table G.9 showed $1.0\times10^{-4}$ at 0.5 µm, and with the error proportional to the edge size (order 1 for a sheet edge, Eq. (G.56)), 0.1 µm gives about $2\times10^{-5}$. The open boundary 200 mm away contributes less. A zero-flux circle around the dipole of the odd drive lowers $C'$ of a half-plane problem by $C'^2d^2/(\pi\varepsilon_0R^2)$, the full-plane result of the strips' check applied to half the problem, with $d$ the distance between the charge centroids of the two pads; for the pads of Eq. (G.25), $d$ = 0.86 mm and $C'/\varepsilon_0$ = 0.856 give $5\times10^{-6}$.

The same fall with the element size appears in three dimensions (Figure 46b). A model uniform along $y$ converges to the two-dimensional value. Against that exact value, its error falls by the factors <<extr_ratio1>> and <<extr_ratio2>> between the three meshes, each a factor 2 finer than the last: local orders of <<extr_local1>> and <<extr_local2>>, close to the order 1 of a sheet edge. Eq. (G.56), which does not know the exact value, finds the order <<extr_order>> from the three meshes and extrapolates to within <<extr_diff>> of the exact value, inside the error of <<extr_reported>> that it reports. The derivations of Sections G.6 to G.11 are thus confirmed independently of the algebra that produced them.

![Figure 46](figures/fig46_parasitic_cf_numerical_validation.png)

*Figure 46. Checks of the field solver. (a) The relative difference between each closed form of Appendix G and the numerical solution of the same two-dimensional problem (Table G.10). Eq. (G.28) is contained exactly in the elements and agrees to rounding. (b) A three-dimensional model that is uniform along $y$, against the two-dimensional solution: its relative error halves with the element size at the edges (dashed: slope 1), the order that Eq. (G.56) gives for a sheet edge.*

#### G.14.3 What the closed forms could only bracket

Three quantities of the estimate had only bounds or a direction. The numerical solutions of the same idealised problems give their values.

**The body with the film's potential.** Section G.8 bracketed the block between two bounds: Eq. (G.32), with the film's potential released, and Eq. (G.28), with the slots filled. With the film's linear potential kept and the slots open, the field solution gives <<g8_val>> per unit permittivity, <<g8_pos>> % of the way from the lower bound (<<g8_lo>>) to the upper one (<<g8_hi>>). For the 0402 at $\varepsilon_{\mathrm{al}}$ = 9.7 that is <<g8_fF>> fF against a bracket of <<g8_lo_fF>>–<<g8_hi_fF>> fF. The central value of Section G.12, which takes the middle of the bracket, therefore overstates the body term by about <<g8_over>> fF. The film fixes only the top face, and the field still enters the slots under the wraps, as Figure 41 shows for the lower-bound problem.

**The pins.** Section G.11 bounded pins 1 and 3 between two models: pin 2 removed (<<g45>> per unit permittivity) and pin 2 as a floating wall (<<g46>>). Pin 2 as what it is, a thin floating strip in the same row, gives <<thin_val>>, <<thin_pos>> % of the way from the lower bound to the upper one. Grounding pin 4 lowers each of the three models by <<pin4_min>>–<<pin4_max>> %. Rule 6 gave only the direction of that change.

**The pads under the body (approximation 14).** Where the pads reach under the body ($g > s$), the cut model of Section G.8 drops their coupling to the body's lower face across the stand-off. Solving the block above the pads with the gap included adds <<a14_30>> fF for an 0402 at a stand-off of 30 µm, and <<a14_10>> fF at 10 µm. Table G.6 gave 0.3 fF from a parallel-plate estimate; the field solution is <<a14_ratio>> times that. The direction is unchanged, since the cut lowers the capacitance, and so is the rigour of the lower bound.

#### G.14.4 The three-dimensional model

Figure 44 shows the model of an 0402 on its pads. The dimensions are the nominal values of Table G.2. The permittivities are 9.7 for the alumina (CoorsTek AD-995 at 1 MHz) and 4.2 for the FR-4 (Isola 370HR at 0.1–1 GHz), both within the ranges of Table G.3. The construction rests on the following assumptions:

- the body is an alumina block of the overall height $T$, as in approximation 15;
- each termination is metal 15 µm thick over the end face and over the length $a$ of the top and bottom faces, with no wraps onto the side faces;
- the film is a sheet on the top face between the wraps, at the linear potential of a plain film;
- the pads are copper 35 µm thick, and the body stands 30 µm above them, with solder under the bottom wraps and air elsewhere;
- the board is 1.6 mm of FR-4 with no planes, as the OPA855 datasheet asks under the feedback network (p. 29), and has no solder mask;
- the enclosure is grounded 8 mm from the centre laterally and 8 mm above the board's top and below its bottom; larger ones enter through Eq. (G.57).

Section G.14.7 varies the termination's thickness, side wraps, the stand-off, a solder fillet, the copper's thickness, a solder mask, the side the film faces and the permittivities. The body's height, the board's thickness and the plain film are not varied. The two mirror planes reduce each solution to a quarter (Eq. (G.53)). The finest mesh of the 0402 has <<n_elem_0402>> tetrahedra and <<n_dofs_0402>> unknowns.

![Figure 44](figures/fig44_parasitic_cf_numerical_model.png)

*Figure 44. The three-dimensional model of an 0402 on its pads (Section G.14.4). (a) The model around the part: the board (green, translucent), the copper pads and the terminations of A (red) and B (blue), the alumina body (light grey, translucent, so that the inner faces of the terminations show through it) and the film (purple) on its top face. (b) The cross-section through the resistor's axis, in the same colours. (c) The mesh on that plane at the termination of A, at the middle refinement of the convergence study: the elements shrink towards every edge of a conductor.*

Figure 45 shows the field on the plane through the resistor's axis, on the middle mesh of Figure 44c, where $C_{F,\mathrm{par}}$ is <<fr_total>> fF. In the odd drive (a) the potential falls from A to B in two places: between the inner edges of the two top wraps, where the film holds the top face at its linear potential, and between the facing edges of the pads, through the stand-off and the FR-4 below. Inside each termination, enclosed by its top wrap, end face and bottom wrap, the alumina stays near the termination's potential; in the outer half of that space the odd potential lies between <<fr_phi_min>> and 0.5 V.

The density of $C_{F,\mathrm{par}}$ in (b), the integrand of Eqs. (G.52) and (G.53), follows the same pattern. Its integral over regions of the whole volume (`field_regions.py`) puts <<fr_al_in>> fF, <<fr_al_in_pct>> % of the total, in the alumina between the wraps and only <<fr_al_cap>> fF in the alumina inside the two terminations. The FR-4 under the gap between the pads, across the pads' width and through the board's whole thickness, holds <<fr_bd_gap>> fF and the rest of the FR-4 <<fr_bd_else>> fF; the air under the body holds <<fr_air_under>> fF and the rest of the air <<fr_air_else>> fF. The density is largest at the edges and corners of the conductors, where the field is singular (Eq. (G.55)); the largest element value lies at an inner corner of a pad, just inside the board.

The density is not positive everywhere. It is the difference of the two drives' energy densities, and the even drive's field, that of a charged body, falls off with distance more slowly than the odd drive's, that of a pair of opposite charges (Section G.14.1). The elements within 1 mm of the part's centre, taken 0.2 mm above the board, add up to <<fr_in1>> fF, and their negative values sum to only <<fr_neg_in1>> fF. The elements beyond 1 mm add up to <<fr_out1>> fF, and beyond 2 mm every element is negative. The negative values sum to <<fr_neg_board>> fF in the FR-4 and <<fr_neg_air>> fF in the air. On the plane and within the window of Figure 45b the density is positive. Each material's share in Section G.14.6 is the sum of both signs over that material.

![Figure 45](figures/fig45_parasitic_cf_numerical_field.png)

*Figure 45. The field of the 0402 model of Figure 44 on the plane through its axis. (a) The potential of the odd drive, with A at $+\tfrac12$ V and B at $-\tfrac12$ V; equipotentials every 0.05 V. (b) The density of $C_{F,\mathrm{par}}$, $\varepsilon(|\nabla\varphi_o|^2 - |\nabla\varphi_e|^2)$, the integrand of Eqs. (G.52) and (G.53), as its mean over each element; the colour scale is linear within $10^{-4}$ of the largest magnitude and logarithmic beyond, over four decades on each side. Within this window the density is positive; beyond about 1 mm from the part it is negative (Section G.14.4).*

#### G.14.5 Convergence and the enclosure

On its three meshes the 0402 gives <<conv_0402>> fF with the enclosure at 8 mm. Eq. (G.56) finds an observed order of <<order_0402>> and a discretisation error of <<err_0402>> fF (Figure 47a). At the coarsest mesh, whose edge size is the 15 µm of every network of Sections G.14.9 and G.14.10, the 0402 lies <<bias4_0402>> fF (<<bias4_pct_0402>> %) above its extrapolated value. The enclosure at 8, 16 and 32 mm gives <<enc_vals_0402>> fF on the coarsest mesh. Eq. (G.57) finds $q$ = <<enc_order_0402>>, the order of the argument of Section G.14.1, and a correction of <<enc_0402>> fF (Figure 47b). Between the enclosures, $C_{A0}$ changes by <<dA0dF_0402>> times as much as $C_{F,\mathrm{par}}$, close to the $-2$ expected if only the even drive feels the walls. With $q = 1$ assumed instead, from the two largest enclosures, the correction would differ by <<q1_change_0402>> fF. At the coarsest mesh $C_{A0}$ lies <<a0_bias4_0402>> % above its extrapolated value, so by the argument of Section G.14.1 the correction carries a mesh error of about twice that, <<enc_mesh_err_0402>> fF.

The other sizes behave alike (Table G.11). From 0201 to 0805 the observed orders are <<orders_all>>, the discretisation errors <<errs_all>> fF, and the enclosure corrections <<enc_pct_all>> % of the value with no ground nearby, with $q$ = <<q_all>>. The 0603 and 0805 are computed on meshes only a factor 1.19 apart, which amplifies the scatter between meshes: with the order fixed at 1 instead, from their two finest meshes, their limits would move by <<p1_change_0603>> and <<p1_change_0805>> fF. A ground 8 mm away thus takes <<enc_pct_min>>–<<enc_pct_max>> % off the coupling.

![Figure 47](figures/fig47_parasitic_cf_numerical_convergence.png)

*Figure 47. Convergence of the 0402 result (Section G.14.5). (a) $C_{F,\mathrm{par}}$ on three meshes whose element sizes scale together, against the number of unknowns, with its extrapolation by Eq. (G.56) (dashed). (b) $C_{F,\mathrm{par}}$ in grounded enclosures of half-width $R$ = 8, 16 and 32 mm, on the coarsest mesh, against $1/R$, with the fit of Eq. (G.57) and its limit at $1/R = 0$.*

#### G.14.6 The four sizes against the estimate

Table G.11 and Figure 48 compare the field solutions with the estimate of Section G.12, evaluated at the same permittivities, so that its range shows only the modelling bounds. For every size the field solution lies inside the bracket, <<pos_min>>–<<pos_max>> % of the way from the lower bound to the upper estimate, and <<below_min>>–<<below_max>> % below the central value. The two-dimensional model therefore brackets the three-dimensional value although it leaves out the field around the ends and sides (approximation 1).

The 0805 couples <<ratio_0805_0402>> times as much as the 0402: <<best_0805>> fF against <<best_0402>> fF with no ground nearby.

*Table G.11. $C_{F,\mathrm{par}}$ of the resistor and its pads (fF): the field solution against the estimate of Section G.12 at the same permittivities ($\varepsilon_{\mathrm{al}}$ = 9.7, $\varepsilon_{\mathrm{pcb}}$ = 4.2), planes removed, film up. The finest mesh and the extrapolation are with the enclosure at 8 mm; the last field-solution column adds the enclosure correction of Eq. (G.57). The position is that of the bold value between the lower bound and the upper estimate.*

| Size | Finest mesh | Extrapolated, Eq. (G.56) | Order $p$ | Discretisation error | Enclosure correction | Order $q$ | No ground nearby | Appendix G: lower bound, central, upper estimate | Position |
|---|---|---|---|---|---|---|---|---|---|
<<table_sizes>>

![Figure 48](figures/fig48_parasitic_cf_numerical_sizes.png)

*Figure 48. The field solution for each size against the estimate of Section G.12 at the same permittivities ($\varepsilon_{\mathrm{al}}$ = 9.7, $\varepsilon_{\mathrm{pcb}}$ = 4.2). The bar spans the lower bound to the upper estimate, and the line marks the central value. Open circles: field solution with a grounded enclosure 8 mm away, extrapolated in the mesh. Filled circles: no ground nearby (Eq. (G.57)).*

The material shares of the 0402, at the finest mesh with the enclosure at 8 mm, are <<shares_0402>> fF. By Eq. (G.54), raising the board's permittivity by 1 % would raise $C_{F,\mathrm{par}}$ by <<board_1pct_0402>> fF. The substrate cases of Section G.14.8 confirm this reading: between boards of permittivity <<fd_lo>> and <<fd_hi>>, $C_{F,\mathrm{par}}$ of the 0402 changes by <<fd_board_0402>> fF per unit of $\ln\varepsilon_{\mathrm{pcb}}$, against a board share of <<board_share_mid_0402>> fF. The corresponding terms of the estimate are <<an_terms_0402>> fF. The body and air shares lie within or close to the estimate's terms, and the board share lies below the board term. The shares belong to one field, not to the separate problems whose solutions the estimate adds, so only their sum compares directly.

#### G.14.7 The details of the construction

Table G.12 changes one assumption of Section G.14.4 at a time, on the middle mesh of the 0402 study with the enclosure at 8 mm. Each variant is meshed afresh, and at that mesh the reference lies <<det_noise>> fF above its extrapolated value, so changes much smaller than that are not resolved. The solder fillet's <<fillet_delta>> fF is among them. Side wraps and thicker copper raise $C_{F,\mathrm{par}}$ most, by up to <<det_max>> fF: both add metal surface that faces the other terminal. The stand-off acts in two ways. A thinner gap brings the bottom wraps closer to the opposite pad, and a thicker one makes the solder under the wraps taller, so that more metal faces across the gap. The 10-µm and 50-µm variants therefore both lie above the 30-µm reference, by <<so10_delta>> and <<so50_delta>> fF, the second at about the level of the mesh scatter.

Mounting the part upside down changes $C_{F,\mathrm{par}}$ by <<film_down>> fF. The air share falls by <<fd_air>> fF, and the body and board shares change by <<fd_body>> and <<fd_board>> fF. Section G.10.7 estimated its main term as +0.6 fF, from moving the film's potential from the air half-plane to the board half-plane, and named two further effects of the same size that it did not evaluate. The field solution shows that together they reverse the sign. The size, below 1 fF, confirms the conclusion of Section G.10.7 that flipping makes no difference in the recommended layout; the direction of its estimate does not hold.

The permittivity corners of Table G.3 move $C_{F,\mathrm{par}}$ by <<eps_low_pct>> % and <<eps_high_pct>> %, more than any construction detail.

*Table G.12. The 0402 with one assumption changed at a time ($C_{F,\mathrm{par}}$ in fF, middle mesh, enclosure 8 mm).*

| Change | $C_{F,\mathrm{par}}$ | Change |
|---|---|---|
<<table_details>>

#### G.14.8 Other board materials

Table G.13 and Figure 49 replace the FR-4 by the low-loss laminates whose permittivities the collection `data/parasitic_cf/substrate_permittivity.md` gives, each with its document and page. The body's share hardly moves, <<alumina_share_range_0402>> fF for the 0402 across all boards. The board's share grows with its permittivity, and the air's share falls a little as the board takes more of the field: from <<air_eps1_0402>> fF with no board to <<air_eps46_0402>> fF at a permittivity of 4.6 for the 0402, and from <<air_eps1_0805>> to <<air_eps46_0805>> fF for the 0805. A Rogers RO4350B board lowers $C_{F,\mathrm{par}}$ by <<sub_4350>> %, and a PTFE board (RT/duroid 5880) by <<sub_ptfe>> %. Even with no dielectric under the parts at all, the reduction is only <<sub_air>> %. A smaller part helps more: an 0805 on PTFE couples <<sub_0805_ptfe>> fF, against <<sub_0402_fr4>> fF for an 0402 on FR-4. The estimate's central value follows the same trend (Figure 49, dashed). Relative to FR-4, it differs from the field solution by <<dev_eps1_0402>> % (0402) and <<dev_eps1_0805>> % (0805) with no board, and by at most <<dev_max_22>> % for permittivities of 2.2 and above, so Section G.12 alone predicts the change well.

These ratios are taken with the enclosure at 8 mm. With no ground nearby they change, because the enclosure correction grows with the square of the capacitance to ground (Section G.14.1), which a board of lower permittivity reduces. For the 0402 the correction is <<enc_air>> fF with no board, <<enc_ptfe>> fF on RT/duroid 5880 and <<enc_fr4>> fF on FR-4, so with no ground nearby the ratios to FR-4 become <<ratio_free_air>> and <<ratio_free_ptfe>>, instead of the <<ratio8_air>> and <<ratio8_ptfe>> of Table G.13.

*Table G.13. $C_{F,\mathrm{par}}$ (fF) on other board materials, with the ratio to FR-4 at 4.2 in parentheses: middle mesh of each size's study, enclosure 8 mm, planes removed. The relative permittivities are those of the manufacturers' documents, at the frequencies stated there: RT/duroid 5880 at 1 MHz and 10 GHz, RO3003 at 10 GHz, I-Tera MT40 at 2–10 GHz, MEGTRON 6 at 1 GHz. Rogers quotes RO4350B at 3.48 by its 10-GHz test method and at 3.66 for design over 8–40 GHz, and its 1-GHz chart reads about 3.76 for 20-mil laminate; the table uses the design value, and 3.76 would move the ratio by about 0.01. DuPont's flexible polyimide Pyralux AP, 3.4 at 1 MHz and 3.2 at 10 GHz [A43, p. 2], lies between the RO3003 and I-Tera rows.*

| Board | Relative permittivity in the documents | Value used | 0402 | 0805 |
|---|---|---|---|---|
<<table_substrates>>

![Figure 49](figures/fig49_parasitic_cf_numerical_substrates.png)

*Figure 49. $C_{F,\mathrm{par}}$ against the relative permittivity of the board, relative to FR-4 at 4.2, for the 0402 and the 0805: field solutions (solid) and the central value of the estimate of Section G.12 (dashed). The materials are those of Table G.13.*

#### G.14.9 The OPA855 feedback network

Figure 50 shows the layout of Figure 43 in three dimensions. The 0402 is joined to pins 1 and 3 of the OPA855 by traces 0.2 mm wide, pin 2 floats, pin 4 and the thermal pad are grounded, and the package's mould lies over them, with a relative permittivity of 3.55, the middle of the range of Table G.3. The package follows its drawing at nominal dimensions (OPA855 pp. 38–39), with the terminals' side-wall metal 0.2 mm high, the larger of the drawing's two options. Three choices are assumptions, because the datasheet's layout example does not dimension them: the traces' width, the resistor's position, centred on pin 2 with its pads 0.35 mm from the pin pads, and the solder under the package's terminals. Figure 43 draws the resistor's pads 0.50 mm long with a 0.50-mm gap; the model keeps the land pattern of Table G.2. Pins 5–8 lie 1.9 mm away and are left out: OUT, at the output's potential, would raise $C_{F,\mathrm{par}}$ (Rule 2) and the three AC grounds would lower it (Rule 6), so even the sign of the omission is unknown. No mirror symmetry applies, so the whole volume is computed, on two meshes that share the capped 15-µm edge size and differ in the core and far sizes.

With the enclosure at 8 mm, the resistor and its pads alone give <<o855_alone>> fF and the whole network <<o855_net>> fF. The traces, the pins and the package therefore add <<o855_added>> fF, the same within <<o855_added_diff>> fF on the other mesh. These values are not extrapolated in the mesh. The two meshes share the edge size, which carries the dominant error, and at that edge size the 0402 alone lies <<bias4_0402>> fF above its limit (Section G.14.5); the added amount, a difference on one mesh, carries less of that error. It is less than the 15–21 fF of the two-dimensional pin models of Section G.11, which leave out the grounded pin 4 and thermal pad; in two dimensions, grounding pin 4 alone takes about a third off (Section G.14.3). The enclosure correction is <<o855_enc>> fF (Eq. (G.57), $q$ = <<o855_enc_order>>), so the network gives about <<o855_free>> fF with no ground nearby, of which up to about <<bias4_0402>> fF may be the mesh error just described.

A ground plane 0.2 mm below, cut out 0.5 mm around the network, lowers $C_{F,\mathrm{par}}$ to <<o855_plane>> fF. It raises the summing node's capacitance $C_{B0}$ from <<o855_B0>> fF to <<o855_plane_B0>> fF, the trade of Section G.10.6. The capacitances to ground converge more slowly than $C_{F,\mathrm{par}}$: in the size studies their observed orders were <<a0_orders>>, so their mesh error is less certain than that of $C_{F,\mathrm{par}}$. The plane's cut-out border is meshed more coarsely than the parts; halving its element size, at the coarser of the two meshes, changes $C_{F,\mathrm{par}}$ by <<plane_edge_change>> fF.

![Figure 50](figures/fig50_parasitic_cf_numerical_opa855.png)

*Figure 50. (a) The feedback network of Figure 43 in three dimensions: the 0402 with its traces to pins 1 and 3 of the OPA855, pin 2 floating, pin 4 and the thermal pad grounded, under the package's mould (brown, translucent). (b) $C_{F,\mathrm{par}}$ of the resistor and its pads alone, of the whole network, and of the network over a ground plane 0.2 mm below cut out 0.5 mm around it, with a grounded enclosure 8 mm away, on the finer of the two meshes.*

#### G.14.10 The OPA846 in SOT-23-5

The OPA846, the amplifier of the bench board of Section 3.10 and of the design of Section 4.4, has no FB pin. In its SOT-23-5 package the output, pin 1, and the inverting input, pin 4, sit at diagonally opposite corners, 2.6 mm apart across the package and 1.9 mm along it (OPA846 pp. 2 and 27), so the feedback resistor needs a route between them, and the route carries part of $C_{F,\mathrm{par}}$. Section G.13.5 infers about 0.3 pF on the bench board, but that board's layout is not recorded and may be a poor one, so the value is no benchmark for the layouts computed here. The datasheet asks for the feedback resistor to sit close to the output pin or, where both sides of the board carry parts, directly under the package on the other side (p. 18, item c). Figure 51 shows three layouts that follow that advice:

- in layout (a), $R_F$ sits on the bottom side under the package, reached through vias beside pins 1 and 4;
- in layout (b), $R_F$ sits above pin 1 on the top side, with a trace from its far pad under the package body, between the two rows of pins, to pin 4;
- in layout (c), $R_F$ sits below pin 4 on the top side, with a trace from pin 1 around the outside of the package.

Each layout is computed with an 0402 and with an 0603 on the land patterns of Table G.2. The board is FR-4 1.6 mm thick with ground planes 0.2 mm inside each face. The datasheet asks for windows in the ground and power planes around the signal pins (p. 18, item a), and the model cuts both planes out 0.5 mm beyond the package's pads and the network. Pins 2 ($-V_S$) and 5 ($+V_S$) are at AC ground through their decoupling capacitors, and so is pin 3, the non-inverting input of a transimpedance amplifier (pin functions on p. 2). The package follows its drawing at the middle of each tolerance, with the body 1.1 mm high, the drawing's reference value (pp. 26–27), and with gull-wing leads of the drawn width and thickness under the mould of Section G.14.9; its lead frame, die and bond wires are left out, since no drawing gives them. The datasheet does not dimension the rest, so the following are assumptions: traces 0.2 mm wide, 0.3 mm between a pin's pad and the resistor's pads, vias with a 0.3-mm drill and square pads 0.55 mm wide, and a four-layer stack with its planes 0.2 mm inside the faces.

A via's round barrel is modelled as a square barrel with the same far field. Seen from a distance large against its width, a long conductor of any cross-section has the field of a round wire whose radius is the cross-section's conformal radius $c$: the conformal map $f$ from the outside of the unit circle onto the outside of the cross-section, normalised so that $f(w)\approx c\,w$ far away, scales distances there by $c$. For a square the Schwarz–Christoffel formula gives $f'(w) = c\,(1+w^{-4})^{1/2}$, and a side is the image of the quarter of the unit circle between two points that map to corners, $w = e^{i\pi/4}$ and $w = e^{3i\pi/4}$. On the circle $|f'(e^{i\theta})| = c\,(2|\cos2\theta|)^{1/2}$, so the side is

$$
s = c\sqrt2\int_{\pi/4}^{3\pi/4}|\cos2\theta|^{1/2}\,\mathrm d\theta
= c\sqrt2\int_0^{\pi/2}\cos^{1/2}u\,\mathrm du
= c\sqrt2\,\frac{\sqrt\pi}{2}\,\frac{\Gamma(3/4)}{\Gamma(5/4)}
= \frac{4\pi^{3/2}}{\Gamma(1/4)^2}\,c ,
\tag{G.58}
$$

where the substitution $u = 2\theta - \pi$ gives the second form, the integral $\int_0^{\pi/2}\cos^p u\,\mathrm du = \tfrac{\sqrt\pi}{2}\,\Gamma(\tfrac{p+1}{2})/\Gamma(\tfrac p2 + 1)$ with $p = \tfrac12$ the third, and $\Gamma(\tfrac14)\Gamma(\tfrac34) = \pi\sqrt2$ with $\Gamma(\tfrac54) = \tfrac14\Gamma(\tfrac14)$ the last. By Eq. (G.58), $c = 0.5902\,s$. A round barrel of diameter $d$ has $c = d/2$, so the square with the same far field has the side $s = 0.8472\,d$, 0.254 mm for the 0.3-mm drill. The two shapes differ near the barrel, but the nearest conductor of another net is 0.52 mm from the barrel, almost twice the drill.

Table G.14 gives the results, each on one mesh at the capped 15-µm edge size with the enclosure at 8 mm. A finer core and far mesh changes the value of layout (b) with the 0402 by <<o846_fine_change>> %, and an enclosure at 16 mm changes it by <<o846_enc_change>> %, since most of the even drive's field ends on the planes. The edge size, which carries the dominant error, is not varied; at that size the 0402 alone lies <<bias4_pct_0402>> % above its extrapolated value (Section G.14.5), and an error of that order is expected here.

With the 0402 the trace under the body gives the most, <<o846_under_body_0402>> fF, the resistor under the package <<o846_double_sided_0402>> fF and the trace around the package <<o846_around_0402>> fF. The routing makes the difference. Without the resistor, but with the pins, traces and vias, the three layouts give <<o846_nores_under_body>>, <<o846_nores_double_sided>> and <<o846_nores_around>> fF. The trace under the body runs 0.40 mm from the inner end of pin 1's pad, the output, and passes between the package's two rows of leads; layouts (a) and (c) keep the routing of one net away from the pin of the other. Removing the package's leads and body, with its pads kept, lowers $C_{F,\mathrm{par}}$ to <<o846_nopkg_under_body>>, <<o846_nopkg_double_sided>> and <<o846_nopkg_around>> fF. Removing the planes raises it to <<o846_nopl_under_body>>, <<o846_nopl_double_sided>> and <<o846_nopl_around>> fF and lowers $C_{B0}$, the trade of Section G.10.6.

With the 0603, layouts (a) and (c) give <<o846_double_sided_0603>> and <<o846_around_0603>> fF, a few femtofarads more than with the 0402, as the larger part couples more by itself (Table G.11). Layout (b) gives less, <<o846_under_body_0603>> fF. Its trace under the body starts at the resistor's far pad, which for the 0603 lies 0.65 mm farther from pin 1, so the trace runs 1.05 mm from pin 1's pad instead of 0.40 mm.

The layout around the package gives the lowest $C_{F,\mathrm{par}}$ and also the lowest capacitance to ground at the summing node, $C_{B0}$ = <<o846B0_around_0402>> fF against <<o846B0_double_sided_0402>> and <<o846B0_under_body_0402>> fF, because its long trace belongs to the output, where it adds <<o846A0_around_0402>> fF to $C_{A0}$. The summing node's capacitance is part of $C_{\mathrm{PCB}}$ and so of $C_T$ (Table 1.1), whereas the output's capacitance loads the amplifier's output. All six values of $C_{F,\mathrm{par}}$ lie between <<o846_min>> and <<o846_max>> fF. The package interior, its lead frame, die and bond wires, adds its own coupling in every layout (Section G.11).

The OPA846 also comes in SO-8 (OPA846 p. 2). The side note [*Feedback networks in eight-lead packages and under guard rings*](../TIA_feedback_layouts/TIA_feedback_layouts.md) computes three layouts in that package with the same 0402, board and planes, with coarser meshes on the leads; on layout (a) of this section those meshes change $C_{F,\mathrm{par}}$ by +0.21 % (its Section 2.3). With the resistor under the package and the vias in the pads it gives 56.1 fF, the same as layout (a) in SOT-23-5. With the vias under the body it gives 66.5 fF, because the two via barrels then stand 2.7 mm apart instead of 4.4 mm. With the resistor beyond pins 4 and 5 and both traces under the body it gives 57.5 fF, against 72.0 fF for layout (b), because the wider body lets the two traces run 2.65 mm apart along opposite rows of pins. The last three rows of Table G.14 give these values. The same side note estimates the inductance of the leads, which the electrostatic model leaves out: at the 308-MHz crossover of the 2-kΩ design of Section 4.5 it changes the effect of the 0.75-pF feedback capacitance by 2.3 % in SOT-23-5, 2.9 % in SOIC-8 and 4.0 % in PDIP-8, inside the design's ±0.1-pF tolerance (its Section 4).

*Table G.14. The OPA846 in SOT-23-5 with its feedback resistor in the three layouts of Figure 51 (fF): $C_{F,\mathrm{par}}$ with an 0402 and an 0603; with the 0402, the capacitances to ground of the output's net ($C_{A0}$) and of the summing node's net ($C_{B0}$); and $C_{F,\mathrm{par}}$ of the 0402 layout without the resistor, without the package's leads and body, and without the planes. One mesh at the capped 15-µm edge size, enclosure 8 mm. The last three rows give the OPA846 in SO-8 with the 0402, from the side note on eight-lead packages (its Section 3), with coarser meshes on the leads; the 0603 and the parts left out were not computed there.*

| Layout | $C_{F,\mathrm{par}}$, 0402 | $C_{F,\mathrm{par}}$, 0603 | $C_{A0}$, 0402 | $C_{B0}$, 0402 | Without $R_F$ | Without the package | Without the planes |
|---|---|---|---|---|---|---|---|
<<table_opa846>>
| SO-8: $R_F$ on the bottom side under the package, vias in the pads | 56.1 | – | 304 | 304 | – | – | – |
| SO-8: the same with the vias under the body | 66.5 | – | 297 | 298 | – | – | – |
| SO-8: $R_F$ beyond pins 4 and 5, traces under the body | 57.5 | – | 286 | 363 | – | – | – |

![Figure 51](figures/fig51_parasitic_cf_numerical_opa846.png)

*Figure 51. The OPA846 in SOT-23-5 with its feedback resistor, an 0402, in three layouts (Section G.14.10): (a) on the bottom side under the package, through vias beside pins 1 and 4; (b) above pin 1, with a trace under the package body to pin 4; (c) below pin 4, with a trace around the package from pin 1. The output's net is red, the summing node's net blue and the grounded pins dark grey; the board with its two planes (green) and the package's mould (brown) are drawn translucent. (d) $C_{F,\mathrm{par}}$ of each layout with an 0402 and an 0603, enclosure 8 mm.*

#### G.14.11 What the field solutions show

The field solutions confirm the closed forms where these are exact, give values where they only bracketed, and add the parts of the layout that the two-dimensional model leaves out.

- The two-dimensional closed forms of Sections G.6–G.11 are reproduced to a relative difference of at most <<cf_max>>, and <<g41_max>> for the mutual capacitances over a plane (Section G.14.2).
- In three dimensions the resistor and its pads lie inside the bracket of Section G.12 for every size, <<pos_min>>–<<pos_max>> % of the way from the lower bound to the upper estimate and <<below_min>>–<<below_max>> % below the central value. With no ground nearby they give <<best_0201>>, <<best_0402>>, <<best_0603>> and <<best_0805>> fF from 0201 to 0805 (Section G.14.6).
- No construction detail that the drawings leave open moves $C_{F,\mathrm{par}}$ of an 0402 by more than <<det_max>> fF, while the permittivity corners of Table G.3 move it by <<eps_low_pct>> % and <<eps_high_pct>> % (Section G.14.7).
- A board of lower permittivity lowers $C_{F,\mathrm{par}}$ by <<sub_4350>> % (RO4350B) to <<sub_ptfe>> % (PTFE), and by <<sub_air>> % with no dielectric under the parts at all; a smaller part lowers it more (Section G.14.8).
- The traces, pins and package of the OPA855 network add <<o855_added>> fF to the resistor's <<o855_alone>> fF, and the network gives about <<o855_free>> fF with no ground nearby. A plane cut out around the network lowers that to <<o855_plane>> fF and raises the summing node's capacitance (Section G.14.9).
- The OPA846 layouts give <<o846_min>>–<<o846_max>> fF in SOT-23-5 and 56–67 fF in SO-8, and their routing sets most of the differences between them (Section G.14.10).
- The networks' own capacitance to ground at the summing node, $C_{B0}$, is <<o855_B0>> fF for the OPA855 network and <<o846B0_min>>–<<o846B0_max>> fF for the OPA846 layouts, with the enclosure at 8 mm. It is part of $C_{\mathrm{PCB}}$, which also holds the photodiode's pads and traces and which Table 1.1 takes as 0.35 pF, with corners at 0.2 and 0.5 pF.

For the layout that Table 1.1 describes, an 0402 beside the OPA855's pins with the planes removed under the network, the field solution gives about <<o855_free>> fF. It does not include the package interior, which no source quantifies (Section G.11), and it lies between the lower corner and the nominal value that Table 1.1 gives for $C_{F,\mathrm{par}}$, 0.05 and 0.08 pF.
