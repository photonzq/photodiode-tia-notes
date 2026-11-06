"""Check that TIA_high_gain_survey.md equals a fresh assembly of parts/ by assemble_note.py, without writing the note.

Usage: python check_assembly.py

Run it after editing the note and its part files together: it executes assemble_note.py with its output redirected
to a temporary file, compares the bytes with the note, and prints the result and both lengths.
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    src = (HERE / "assemble_note.py").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "assembled.md"
        old_out = 'OUT = ROOT / "TIA_high_gain_survey.md"'
        old_root = "pathlib.Path(__file__).resolve().parent.parent"
        assert src.count(old_out) == 1 and src.count(old_root) == 1, "assemble_note.py changed; update this check"
        src = src.replace(old_out, f"OUT = pathlib.Path(r'{out}')").replace(old_root, f"pathlib.Path(r'{ROOT}')")
        exec(compile(src, "assemble_note.py", "exec"), {"__name__": "__main__"})
        fresh, note = out.read_bytes(), (ROOT / "TIA_high_gain_survey.md").read_bytes()
    print(f"fresh assembly equals the note: {fresh == note} ({len(fresh)} and {len(note)} bytes)")
    return 0 if fresh == note else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
