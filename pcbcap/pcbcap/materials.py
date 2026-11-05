"""Dielectric materials: relative permittivities with their sources.

Why this module exists
----------------------
The capacitance of a layout depends on the relative permittivity eps_r of every insulator in it.
A model is only as good as those numbers, so each material here carries, next to its value, the
range that the manufacturers' documents support and the documents the numbers come from.  A study
can then run a layout at the nominal value and at both ends of the range without re-typing data.

How a value is chosen
---------------------
* ``eps_r`` is the value used when nothing else is asked for.  The entry's ``source`` says how it was
  chosen: a typical value printed in the frequency band where the designs use their feedback
  capacitance (0.1-1 GHz for the OPA855-class designs of the companion survey; the high-gain note
  works below 100 MHz, where 1-MHz data apply more directly), or, where no in-band value exists, the
  midpoint of the stated set of values.
* ``eps_range`` is (lowest, highest) over the values the entry names.  It is not a statistical
  interval, and where a document gives only a manufacturing or measurement tolerance band, that band
  is left out and the entry says so.
* Only values printed by manufacturers or measured in the cited literature are used.  No value here
  is computed or simulated.  The pages of every document are in the companion note's collection
  data/parasitic_cf/geometry_and_permittivity.md, which the companion note's Table G.3 summarises.

Assumptions about the materials, and their size
-----------------------------------------------
* Frequency independence.  Each material has one eps_r.  For 99.5 % alumina this is supported by
  CoorsTek's data, 9.7-9.8 at 1 MHz and 9.8 at 4-5 GHz (companion note, approximation 13).  For FR-4
  the values below are read at 100 MHz and 1 GHz directly.  For the mould compound and the solder
  mask only 1-MHz values were found, so their use at 0.1-1 GHz is an assumption; their ranges are
  wide enough to cover the dispersion that epoxies show.
* No loss.  The documents give loss tangents t = tan(delta) from about 1e-4 (alumina) through about
  0.01 (mould compound CEL-9220HF10, 1.1 %) to 0.02-0.042 (Taiyo PSR-4000 masks).  Loss changes the
  real capacitance only at second order.  Write each permittivity as eps_k (1 - j t_k).  The
  capacitance is a function C(eps_1, ..., eps_n), homogeneous of degree 1 (scaling every eps by s
  scales every field energy, hence C, by s).  To first order,
      C* = C - j sum_k t_k eps_k dC/deps_k,
  and every eps_k dC/deps_k is real, so the first-order change is purely imaginary: a loss
  conductance, not a change of capacitance.  The real part changes at second order, and not at all
  when every t_k is the same, since then C* = (1 - j t) C exactly by homogeneity.  For two layers in
  series (thicknesses d_1, d_2), expanding 1 / (d_1/eps_1* + d_2/eps_2*) to second order gives
      Re C* / C - 1 = d_1 d_2 eps_1 eps_2 (t_1 - t_2)^2 / (d_1 eps_2 + d_2 eps_1)^2  <=  (t_1 - t_2)^2 / 4,
  where the bound uses a b / (a + b)^2 <= 1/4.  Even the largest spread here, 0.042 against air,
  gives at most 4.4e-4.
* Size against wavelength.  The electrostatic model neglects induction and retardation.  The
  quantitative test is the one in the package docstring, (2 pi f)^2 L C << 1 for the inductance L of
  the charging path.  For orientation, the wavelength at 1 GHz is 300 mm in vacuum, 96 mm in alumina
  (300 mm / sqrt(9.7)) and 146 mm in FR-4 (300 mm / sqrt(4.2)), against layouts of 1-10 mm.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Material:
    """A homogeneous, isotropic, lossless dielectric.

    Attributes
    ----------
    name : short identifier used in layouts and result tables.
    eps_r : relative permittivity used by default.
    eps_range : (low, high) relative permittivity spanned by the values the entry names, or None when
        a single value is exact enough (air).
    source : the documents and values behind eps_r and eps_range, and how eps_r was chosen.  The
        pages are in the collection named in the module docstring.
    """

    name: str
    eps_r: float
    eps_range: tuple[float, float] | None = None
    source: str = ""
    notes: str = field(default="", compare=False)

    def at(self, which: str = "nominal") -> float:
        """Return the permittivity at 'nominal', 'low' or 'high'.

        'low' and 'high' fall back to the nominal value when no range is documented, so that a
        corner study over several materials never fails for lack of a range.
        """
        if which == "nominal":
            return self.eps_r
        if self.eps_range is None:
            return self.eps_r
        if which == "low":
            return self.eps_range[0]
        if which == "high":
            return self.eps_range[1]
        raise ValueError(f"unknown corner {which!r}; use 'nominal', 'low' or 'high'")


# ------------------------------------------------------------------------------------------------
# The library.  Each entry states its source.  The resistor, board, mould and mask values are the
# ones collected for Appendix G of the companion note (its Table G.3 and the collection
# data/parasitic_cf/geometry_and_permittivity.md, where every value has its document and page).
# ------------------------------------------------------------------------------------------------
LIBRARY: dict[str, Material] = {}


def register(material: Material) -> Material:
    """Add a material to the library (or replace one of the same name) and return it."""
    LIBRARY[material.name] = material
    return material


register(Material(
    name="air",
    eps_r=1.0,
    eps_range=None,
    source=("Air is taken as vacuum. Dry air measures 1.00059 at 0 degC and 1 atm (Hector and Schultz, "
            "Physics 7, 133 (1936), as quoted in standard tables; the paper was not read here). eps_r - 1 "
            "is proportional to the gas density, which at 20 degC is 273.15/293.15 of that at 0 degC, so "
            "eps_r - 1 = 5.5e-4 at room temperature. Taking 1.0 changes a capacitance by "
            "(S_air/C) x 5.5e-4, where S_air is the air's share of it (capacitance.py), e.g. about "
            "6e-5 for an 0402, whose air share is a tenth of C_F."),
))

register(Material(
    name="alumina",
    eps_r=9.7,
    eps_range=(9.4, 10.0),
    source=("Resistor substrate, values at 1 MHz. 96 %: Kyocera A476 9.4; CeramTec Rubalit 708S 9.8. "
            "99.5-99.6 %: Kyocera A479S 9.9 and A479U 10; CoorsTek AD-995 9.7-9.8 (and 9.8 at 4-5 GHz). "
            "Range = lowest and highest of these typical values. CeramTec prints its 9.8 with a +/-10 % "
            "measurement tolerance and gives bands of 8.3-11.3 (708 grades) and 8.5-11.5 (710F) at "
            "10 MHz-1 GHz; these are symmetric tolerance bands about 9.8 and 10.0, not data on the "
            "typical value, so they are left out of the range. Nominal 9.7 = CoorsTek AD-995 at 1 MHz, "
            "near the middle of the range."),
))

register(Material(
    name="FR4",
    eps_r=4.2,
    eps_range=(3.65, 4.6),
    source=("Nominal 4.2 = Isola 370HR at 100 MHz (4.24) and 1 GHz (4.17), rounded; a core value. "
            "Range = the 1-GHz values of Panasonic's tables: R-1650V prepregs 3.65-4.02 and R-1755V cores "
            "3.95-4.63 (upper end rounded to 4.6), as in the companion note's Table G.3. Values outside "
            "it: Ventec VT-47 prepregs reach 3.45 and cores 4.35 at 1 GHz; R-1755V reaches 4.70 at "
            "100 MHz and 1 MHz. The resin-rich prepreg that lies directly under the outer copper of a "
            "foil-built board is 3.5-4.0 at 1 GHz, so the low corner, not the nominal value, describes "
            "that layer."),
))

register(Material(
    name="mould",
    eps_r=3.55,
    eps_range=(3.1, 4.0),
    source=("Epoxy mould compound of IC packages, values at 1 MHz. Resonac (Hitachi) CEL-9220HF10: 3.1; "
            "Panasonic CV8710: 4.0. No vendor states the value for a QFN, WSON or SOT-23 package; nominal "
            "= midpoint of the two."),
))

register(Material(
    name="solder_mask",
    eps_r=4.0,
    eps_range=(3.2, 4.9),
    source=("Taiyo PSR-4000 grades: 3.5-4.5 dry and up to 4.9 after humidity, at 1 MHz; an LPI mask "
            "(Taiyo America 'LPI C'): 3.22-3.48 at 3.2 GHz (IPC paper S12-2, Intel and Taiyo America "
            "2005, p. 7, Fig. 10). Range = lowest and highest of these. Nominal 4.0 = midpoint of the dry "
            "1-MHz values 3.5-4.5, because the humid and 3.2-GHz values describe other conditions; the "
            "midpoint of the whole range would be 4.05."),
))


def get(name_or_material: str | Material) -> Material:
    """Look a material up by name, or pass a Material through unchanged.

    Raises KeyError with the list of known names, so that a typo in a configuration file is
    reported clearly instead of silently using a wrong permittivity.
    """
    if isinstance(name_or_material, Material):
        return name_or_material
    try:
        return LIBRARY[name_or_material]
    except KeyError:
        known = ", ".join(sorted(LIBRARY))
        raise KeyError(f"unknown material {name_or_material!r}; known: {known}") from None


def custom(name: str, eps_r: float, source: str = "user value") -> Material:
    """Make a one-off material (for example a sweep point) without adding it to the library.

    A passive (lossless or lossy) dielectric has eps_r >= 1 at zero frequency.  This follows from the
    Kramers-Kronig relation evaluated at omega = 0,
        eps_r(0) - 1 = (2/pi) int_0^inf eps''(omega) / omega d omega,
    because the loss part eps'' is never negative in a passive medium.  A value below 1 is therefore
    a typing error, and it is refused."""
    if eps_r < 1.0:
        raise ValueError("a passive dielectric has eps_r >= 1")
    return Material(name=name, eps_r=float(eps_r), eps_range=None, source=source)
