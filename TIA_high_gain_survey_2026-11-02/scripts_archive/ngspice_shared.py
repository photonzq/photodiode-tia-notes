"""Run ngspice decks through ngspice loaded as a shared library.

KiCad bundles ngspice as a shared library (on Windows, <KiCad>/bin/ngspice.dll), so no
separate ngspice installation is needed.  The library is located, in this order, from:
  1. the path given to NgSpice(library=...);
  2. the NGSPICE_LIBRARY environment variable;
  3. the system library search (ctypes.util.find_library("ngspice"));
  4. the default install folders of KiCad and of ngspice packages.

Decks are ordinary ngspice input files.  Their .control section runs when the deck is
sourced; results are written with wrdata.  PSpice compatibility (ngbehavior=psa) is set
before any deck is read, which the TI and National Semiconductor PSpice models need.

The XSPICE code models (*.cm) are loaded explicitly, because the shared library finds no
start-up file of its own; PSpice switches are translated to the code model pswitch.  They
are taken from the NGSPICE_CODEMODELS folder if set, else from the folder that KiCad
installs beside the library (<KiCad>/lib/ngspice).

Usage as a script prints the ngspice version:  python ngspice_shared.py [library]
"""
import ctypes
import ctypes.util
import glob
import os
import sys
from pathlib import Path

DEFAULT_LOCATIONS = [
    "C:/Program Files/KiCad/*/bin/ngspice.dll",
    "C:/Program Files/ngspice*/bin/ngspice.dll",
    "/Applications/KiCad/KiCad.app/Contents/Frameworks/libngspice*.dylib",
    "/usr/lib/x86_64-linux-gnu/libngspice.so*",
    "/usr/lib/libngspice.so*",
    "/usr/local/lib/libngspice.so*",
]

_SEND_CHAR = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_SEND_STAT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_EXIT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)


def find_library(library=None):
    """Return the path of the ngspice shared library, or raise FileNotFoundError."""
    if library:
        return str(library)
    if os.environ.get("NGSPICE_LIBRARY"):
        return os.environ["NGSPICE_LIBRARY"]
    found = ctypes.util.find_library("ngspice")
    if found:
        return found
    for pattern in DEFAULT_LOCATIONS:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    raise FileNotFoundError("ngspice shared library not found: pass its path or set NGSPICE_LIBRARY")


def _no_spaces(path):
    """Path as ngspice commands accept it: forward slashes and, on Windows, the short (8.3)
    form when the long one contains spaces."""
    text = str(path)
    if " " in text and sys.platform == "win32":
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(text, buf, 1024):
            text = buf.value
    return text.replace("\\", "/")


def find_codemodels(library_path):
    """Return the code-model files (*.cm) to load, or an empty list."""
    folders = []
    if os.environ.get("NGSPICE_CODEMODELS"):
        folders.append(Path(os.environ["NGSPICE_CODEMODELS"]))
    lib = Path(library_path)
    folders += [lib.parent.parent / "lib" / "ngspice", lib.parent / "ngspice", lib.parent.parent / "lib64" / "ngspice"]
    for folder in folders:
        hits = sorted(folder.glob("*.cm")) if folder.is_dir() else []
        if hits:
            return hits
    return []


class NgSpice:
    """One ngspice instance.  run_deck() sources a deck file and returns ngspice's output."""

    def __init__(self, library=None, pspice_compat=True):
        self.lines = []
        self._callbacks = (_SEND_CHAR(self._on_char), _SEND_STAT(self._on_stat), _EXIT(self._on_exit))
        self.path = find_library(library)
        if hasattr(os, "add_dll_directory") and Path(self.path).is_file():
            # the code models load further runtime libraries that sit beside ngspice (KiCad's bin folder)
            self._dll_dir = os.add_dll_directory(str(Path(self.path).resolve().parent))
        self.lib = ctypes.CDLL(self.path)
        self.lib.ngSpice_Init.argtypes = [_SEND_CHAR, _SEND_STAT, _EXIT, ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.c_void_p]
        self.lib.ngSpice_Command.argtypes = [ctypes.c_char_p]
        self.lib.ngSpice_Init(*self._callbacks, None, None, None, None)
        self.codemodels = find_codemodels(self.path)
        self.lines = []
        if self.codemodels and sys.platform == "win32":
            # the code models are loaded with the classic Windows search, which needs an absolute
            # path and finds their runtime libraries through PATH (this process only)
            os.environ["PATH"] = str(Path(self.path).resolve().parent) + os.pathsep + os.environ.get("PATH", "")
        for cm in self.codemodels:
            self.command(f"codemodel {_no_spaces(cm.resolve())}")
        self.codemodel_log = "".join(self.lines)
        if pspice_compat:
            self.command("set ngbehavior=psa")

    def _on_char(self, text, ident, user):
        self.lines.append(text.decode(errors="replace"))
        return 0

    def _on_stat(self, text, ident, user):
        return 0

    def _on_exit(self, status, unload, quit_, ident, user):
        return 0

    def command(self, cmd):
        return self.lib.ngSpice_Command(cmd.encode())

    def version(self):
        self.lines = []
        self.command("version")
        return "\n".join(line for line in self.lines if line.strip())

    def run_deck(self, deck_path):
        """Source a deck from its own folder (so relative .include and wrdata paths
        resolve there), then remove the circuit.  Returns ngspice's console output."""
        deck_path = Path(deck_path).resolve()
        cwd = os.getcwd()
        self.lines = []
        os.chdir(deck_path.parent)
        try:
            self.command(f"source {deck_path.name}")
        finally:
            os.chdir(cwd)
        out = "".join(self.lines)
        self.command("destroy all")
        self.command("remcirc")
        return out


if __name__ == "__main__":
    print(NgSpice(sys.argv[1] if len(sys.argv) > 1 else None).version())
