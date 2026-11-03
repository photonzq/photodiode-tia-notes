from pathlib import Path
import shutil

src = Path(__file__).resolve().parents[1] / "schematic_style.py"
s = src.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep('OPTIONAL = COLORS["neutral"]         # optional parts (drawn dashed)\n',
    'OPTIONAL = COLORS["neutral"]         # optional parts (drawn dashed)\n'
    'NOISE = COLORS["purple_accent"]      # noise sources\n')

old_tr = '''    def npn(self, base_at, mirror: bool = False, name: str | None = None, side: str = "right"):
        e = elm.BjtNpn(circle=True).right().scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("base").at(base_at))
        self._tlabel(e, name, side)
        return e

    def pnp(self, base_at, mirror: bool = False, name: str | None = None, side: str = "right"):
        e = elm.BjtPnp(circle=True).right().scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("base").at(base_at))
        self._tlabel(e, name, side)
        return e

    def njfet(self, gate_at, mirror: bool = False, name: str | None = None, side: str = "right"):
        e = elm.JFetN(circle=True).right().scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("gate").at(gate_at))
        self._tlabel(e, name, side)
        return e
'''
new_tr = '''    def npn(self, base_at, mirror: bool = False, name: str | None = None, side: str = "right",
            angle: float = 0.0):
        """NPN with its base at base_at; angle rotates it counter-clockwise (degrees)."""
        e = elm.BjtNpn(circle=True).theta(angle).scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("base").at(base_at))
        self._tlabel(e, name, side)
        return e

    def pnp(self, base_at, mirror: bool = False, name: str | None = None, side: str = "right",
            angle: float = 0.0):
        e = elm.BjtPnp(circle=True).theta(angle).scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("base").at(base_at))
        self._tlabel(e, name, side)
        return e

    def njfet(self, gate_at, mirror: bool = False, name: str | None = None, side: str = "right",
              angle: float = 0.0):
        e = elm.JFetN(circle=True).theta(angle).scale(BJT_SCALE)
        if mirror:
            e = e.reverse()
        e = self.add(e.anchor("gate").at(gate_at))
        self._tlabel(e, name, side)
        return e

    def switch(self, p1, p2, closed: bool = False, text=None, side=None, color=None):
        """Single-pole switch, drawn open or closed."""
        return self._two(elm.Switch(nc=closed), p1, p2, text, side, color, False)

    def led(self, p_anode, p_cathode, text=None, side=None, color=None):
        return self._two(elm.LED(), p_anode, p_cathode, text, side, color, False)
'''
rep(old_tr, new_tr)
src.write_text(s, encoding="utf-8", newline="\n")
for dst in (Path(__file__).resolve().parents[3] / "TIA_high_gain_survey_2026-11-02" / "hv_output_stage" / "scripts" / "schematic_style.py",
            Path(__file__).resolve().parents[3] / "TIA_high_gain_survey_2026-11-02" / "scripts_archive" / "schematic_style.py"):
    shutil.copyfile(src, dst)
print("ok")
