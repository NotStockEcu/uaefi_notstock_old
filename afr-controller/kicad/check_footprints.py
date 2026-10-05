#!/usr/bin/env python3
"""Checks that every symbol pin number has a pad in the assigned KiCad footprint.
usage: check_footprints.py afr_frontend.kicad_sch [footprint_dir]"""
import re, sys, os
from kiutils.schematic import Schematic
sch = Schematic.from_file(sys.argv[1]); D = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/kicad/footprints"
libpins = {ls.libId: {str(p.number) for u in ls.units for p in u.pins} for ls in sch.libSymbols}
seen = set(); bad = 0
for s in sch.schematicSymbols:
    ref = [p.value for p in s.properties if p.key == "Reference"][0]
    if ref.startswith("#"): continue
    fp = [p.value for p in s.properties if p.key == "Footprint"][0]
    if (s.libId, fp) in seen: continue
    seen.add((s.libId, fp))
    lib, name = fp.split(":")
    path = f"{D}/{lib}.pretty/{name}.kicad_mod"
    if not os.path.exists(path): print("MISSING footprint", fp); bad += 1; continue
    pads = set(re.findall(r'\(pad\s+"?([^"\s)]+)"?', open(path).read())) - {""}
    extra = libpins[s.libId] - pads
    if extra:
        bad += 1; print(f"PROBLEM {ref} {s.libId} -> {name}: symbol pins without pad {sorted(extra)}; pads {sorted(pads)}")
print("footprint check:", "OK" if not bad else f"{bad} problem(s)")
sys.exit(1 if bad else 0)
