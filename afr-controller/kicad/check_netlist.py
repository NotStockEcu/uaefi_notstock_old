#!/usr/bin/env python3
"""Compares KiCad's own netlist with the intended pin->net map written by gen_frontend.py --pins.
usage: check_netlist.py <netlist.net> <pins.json>"""
import re, sys, json
net_txt = open(sys.argv[1]).read(); intended = json.load(open(sys.argv[2]))
actual = {}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)\n    \)', net_txt + "\n    )", re.S):
    pass
cur = None
for line in net_txt.splitlines():
    m = re.match(r'\s*\(net \(code "\d+"\) \(name "([^"]*)"\)', line)
    if m: cur = m.group(1)
    m = re.search(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', line)
    if m and cur is not None: actual[(m.group(1), m.group(2))] = cur
bad = 0; checked = 0
for net, x, y, desc in intended:
    m = re.fullmatch(r'([A-Z]+\d+)\.(\d+)', desc)
    if not m: continue
    checked += 1
    got = actual.get((m.group(1), m.group(2)))
    if got is None or got.lstrip("/") != net:
        bad += 1; print(f"MISMATCH {desc}: intended {net}, KiCad has {got}")
print(f"checked {checked} pins, mismatches {bad}")
sys.exit(1 if bad else 0)
