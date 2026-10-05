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
# ERC-like: every net with a power_in pin needs a power_out pin somewhere (e.g. PWR_FLAG or regulator output)
nets = {}
cur = None
for line in net_txt.splitlines():
    m = re.match(r'\s*\(net \(code "\d+"\) \(name "([^"]*)"\)', line)
    if m: cur = m.group(1); nets[cur] = []
    m = re.search(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\).*?\(pintype "([^"]+)"\)', line)
    if m and cur is not None: nets[cur].append((m.group(1), m.group(2), m.group(3)))
flagged = {net for net, x, y, desc in intended if desc.startswith('#FLG')}
for n, nodes in nets.items():
    types = {t for _, _, t in nodes}
    if "power_in" in types and "power_out" not in types and n not in flagged:
        bad += 1; print(f"POWER NOT DRIVEN net {n}: {[f'{r}.{p}' for r, p, t in nodes if t == 'power_in']}")
    if "power_out" in {t for _,_,t in nodes} and sum(1 for _,_,t in nodes if t=="power_out") > 1:
        print(f"note: net {n} has several power_out pins: {[f'{r}.{p}' for r,p,t in nodes if t=='power_out']}")
print(f"checked {checked} pins, mismatches/errors {bad}")
sys.exit(1 if bad else 0)
