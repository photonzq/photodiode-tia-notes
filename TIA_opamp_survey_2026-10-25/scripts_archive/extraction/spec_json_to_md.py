"""Render an op-amp spec JSON record (survey schema) as a Markdown spec sheet.

Usage
-----
python spec_json_to_md.py <spec.json> <out.md>

Every field of the JSON is rendered, in file order, so that every number and
its citation ('src') appears in the Markdown:
* strings and numbers become paragraphs or bullets,
* lists of objects become tables (columns = union of keys, first-seen order),
* objects become bullet lists, nested objects/lists are rendered recursively.
Pipe characters inside cells are escaped.
"""
import json
import sys

TITLES = {
    "part": "Part", "manufacturer": "Manufacturer", "datasheet_file": "Datasheet file",
    "datasheet_id_and_revision": "Datasheet ID and revision", "datasheet_status": "Datasheet status",
    "conventions": "Conventions", "input_type": "Input type", "compensation": "Compensation",
    "min_stable_gain": "Minimum stable gain", "supply": "Supply", "quiescent_current": "Quiescent current",
    "gbw": "Gain-bandwidth product", "open_loop_dc_gain": "Open-loop DC gain",
    "phase_margin_or_crossover": "Phase margin / crossover", "open_loop_curve": "Open-loop gain and phase curve",
    "open_loop_output_impedance": "Open-loop output impedance",
    "closed_loop_output_impedance": "Closed-loop output impedance",
    "closed_loop_small_signal_bw": "Closed-loop small-signal bandwidth", "large_signal_bw": "Large-signal bandwidth",
    "slew_rate": "Slew rate", "rise_fall_settling": "Rise/fall time and settling",
    "overdrive_recovery": "Overdrive recovery", "voltage_noise": "Input voltage noise",
    "current_noise": "Input current noise", "input_capacitance": "Input capacitance",
    "input_bias_current": "Input bias and offset current", "input_offset_voltage": "Input offset voltage",
    "input_common_mode_range": "Input common-mode range", "cmrr_psrr": "CMRR and PSRR",
    "output_swing": "Output swing", "output_swing_vs_load_curve": "Output swing vs load (curve)",
    "output_current": "Output current", "short_circuit_current": "Short-circuit current",
    "distortion": "Harmonic distortion", "imd_or_oip3": "Intermodulation / intercept",
    "capacitive_load": "Capacitive load", "shutdown": "Shutdown / disable", "packages": "Packages",
    "pinout_notes": "Pinout notes", "tia_content": "Transimpedance (TIA) content",
    "application_guidance": "Application guidance", "abs_max_and_input_protection": "Absolute maximum ratings and input protection",
    "other_notes": "Other notes, inconsistencies and uncertainties", "pages_read": "Pages read",
}


def fmt(value):
    """Format a scalar or a small nested value for a table cell or bullet."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        text = f"{value:.6g}"
        return text
    if isinstance(value, (int, str)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(fmt(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}: {fmt(v)}" for k, v in value.items())
    return str(value)


def cell(value):
    return fmt(value).replace("|", "\\|").replace("\n", " ")


def render(value, level, out):
    """Render value at heading depth level into out (list of lines)."""
    if isinstance(value, dict):
        for key, sub in value.items():
            if isinstance(sub, list) and sub and all(isinstance(s, dict) for s in sub):
                out.append(f"{'  ' * (level - 1)}- **{key}**:")
                out.append("")
                table(sub, out)
            elif isinstance(sub, dict):
                out.append(f"{'  ' * (level - 1)}- **{key}**:")
                render(sub, level + 1, out)
            elif isinstance(sub, list):
                out.append(f"{'  ' * (level - 1)}- **{key}**:")
                for item in sub:
                    out.append(f"{'  ' * level}- {fmt(item)}")
            else:
                out.append(f"{'  ' * (level - 1)}- **{key}**: {fmt(sub)}")
        out.append("")
    elif isinstance(value, list):
        if value and all(isinstance(v, dict) for v in value):
            table(value, out)
        else:
            for item in value:
                if isinstance(item, (dict, list)):
                    render(item, level, out)
                else:
                    out.append(f"- {fmt(item)}")
            out.append("")
    else:
        out.append(fmt(value))
        out.append("")


def table(rows, out):
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    out.append("| " + " | ".join(columns) + " |")
    out.append("|" + "---|" * len(columns))
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(c, "")) if c in row else "" for c in columns) + " |")
    out.append("")


def main():
    spec_path, md_path = sys.argv[1], sys.argv[2]
    with open(spec_path, encoding="utf-8") as handle:
        spec = json.load(handle)
    out = [f"# {spec.get('part', 'Part')} spec sheet ({spec.get('manufacturer', '')})", ""]
    out.append("Generated from the JSON record of the same name; every value carries its datasheet citation "
               "(src = PDF page index / printed page / table or plot). See 'Conventions' for type codes.")
    out.append("")
    for key, value in spec.items():
        if key in ("part", "manufacturer"):
            continue
        out.append(f"## {TITLES.get(key, key)}")
        out.append("")
        render(value, 1, out)
    with open(md_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(out).rstrip() + "\n")
    print(f"wrote {md_path} ({len(out)} lines)")


if __name__ == "__main__":
    main()
