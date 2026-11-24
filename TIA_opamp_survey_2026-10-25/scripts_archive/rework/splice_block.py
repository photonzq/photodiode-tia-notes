"""Replace the block of a source file that starts at the line equal to START and ends before the line equal to END
with the text of a second file, and report whether the code is unchanged apart from comments and docstrings.

Usage: python splice_block.py TARGET NEW_BLOCK START END [--dry-run]

Used to put the commented versions of tia_pulse_response.py's and compare_opa846_1k5_board.py's modelling code in
place.  START and END must each match exactly one line of TARGET.  After the splice the script parses the old and the
new file, removes every docstring, and compares the syntax trees function by function: a comment cannot change the
tree, so 'identical' means that only comments and docstrings changed.
"""
import ast
import sys
from pathlib import Path


def tree_by_function(src):
    """{qualified name: ast.dump without docstrings} for every function and class, and the module's own statements."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    out = {}

    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                out[name] = ast.dump(child, include_attributes=False)
                visit(child, name + ".")
    visit(tree, "")
    out["<module>"] = ast.dump(tree, include_attributes=False)
    return out


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    target, block, start, end = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    dry = "--dry-run" in sys.argv
    old = target.read_bytes().decode("utf-8")
    lines = old.split("\n")
    s = [i for i, ln in enumerate(lines) if ln == start]
    e = [i for i, ln in enumerate(lines) if ln == end]
    if len(s) != 1 or len(e) != 1 or e[0] <= s[0]:
        sys.exit(f"START found {len(s)} times, END {len(e)} times; nothing written")
    new_block = block.read_bytes().decode("utf-8").replace("\r\n", "\n").rstrip("\n").split("\n")
    new = "\n".join(lines[:s[0]] + new_block + ["", ""] + lines[e[0]:])
    a, b = tree_by_function(old), tree_by_function(new)
    changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    print(f"replaced lines {s[0] + 1}-{e[0]} with {len(new_block)} lines")
    print("syntax trees without docstrings: " + ("identical" if not changed else "DIFFER in " + ", ".join(changed)))
    if dry or changed:
        print("nothing written" if changed else "dry run; nothing written")
        return
    target.write_bytes(new.encode("utf-8"))
    print("written")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
