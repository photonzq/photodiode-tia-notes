"""Load ngspice as a shared library and print its version (no simulation)."""
import ctypes
import sys

dll_path = sys.argv[1]
out = []

SendChar = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
SendStat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
ControlledExit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int,
                                  ctypes.c_void_p)


@SendChar
def send_char(text, ident, user):
    out.append(text.decode(errors="replace"))
    return 0


@SendStat
def send_stat(text, ident, user):
    return 0


@ControlledExit
def controlled_exit(status, unload, quit_, ident, user):
    return 0


lib = ctypes.CDLL(dll_path)
lib.ngSpice_Init.argtypes = [SendChar, SendStat, ControlledExit, ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p]
lib.ngSpice_Command.argtypes = [ctypes.c_char_p]
lib.ngSpice_Init(send_char, send_stat, controlled_exit, None, None, None, None)
lib.ngSpice_Command(b"version")
print("\n".join(line for line in out if line.strip()))
