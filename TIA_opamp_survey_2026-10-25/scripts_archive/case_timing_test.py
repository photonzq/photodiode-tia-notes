"""Timing and sanity test of case_studies.py building blocks (throwaway)."""
import sys
import time
from pathlib import Path

ARCH = Path(sys.argv[1])
sys.path.insert(0, str(ARCH))
import case_studies as cs  # noqa: E402
from ngspice_shared import NgSpice  # noqa: E402
from spice_tia_checks import prepared_model  # noqa: E402

spice = ARCH.parent / "spice"
ng = NgSpice(None)
for part in cs.CASES:
    prepared_model(part, spice)
for part, c in cs.CASES.items():
    t0 = time.time()
    out = cs.spice_ac(ng, spice, part, c["R_F"], cs.C_D_NOM, c["C_F"], c["vs"], kind="test")
    t1 = time.time()
    fn, inn, onn, err = cs.spice_noise(ng, spice, part, c["R_F"], cs.C_D_NOM, c["C_F"], c["vs"])
    t2 = time.time()
    ts, v, serr = cs.spice_step(ng, spice, part, c["R_F"], cs.C_D_NOM, c["C_F"], c["vs"])
    t3 = time.time()
    an = cs.Analytic(part)
    ta, va = an.step(c["R_F"], cs.C_D_NOM, c["C_F"])
    t4 = time.time()
    print(part, {k: (round(x, 2) if isinstance(x, float) else x) for k, x in out.items()})
    print("   noise 100 MHz", round(cs.spot(fn, inn, 100e6) * 1e12, 3), "pA; errors", err, serr)
    print("   step SPICE", {k: round(x, 2) for k, x in cs.step_metrics(ts, v).items()})
    print("   step model", {k: round(x, 2) for k, x in cs.step_metrics(ta, va).items()})
    print("   model loop", {k: (round(x, 2) if isinstance(x, float) else x) for k, x in an.loop(c["R_F"], cs.C_D_NOM, c["C_F"]).items()})
    print(f"   times: ac {t1 - t0:.2f} s, noise {t2 - t1:.2f} s, step {t3 - t2:.2f} s, model step {t4 - t3:.2f} s")
