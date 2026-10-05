#!/usr/bin/env python3
"""Generates afr_frontend.kicad_sch (LSU 4.9 analog front-end).

Topology follows the MIT-licensed rusEFI/FOME wideband module rev C
(github.com/rusefi/wideband, Copyright (c) 2023 Matthew Kennedy), see ../FRONTEND.md.
Every pin is tied to its net by a net label or power symbol (no drawn wires).
"""
import uuid, sys, json

PROJECT = "afr_frontend"
ROOT = str(uuid.uuid4())
G = 1.27
def snap(v):
    r = round(v / G) * G
    assert abs(r - v) < 1e-6, f"off-grid coordinate {v}"
    return round(r, 4)
def sr(v): return round(round(v / G) * G, 4)
def u(): return str(uuid.uuid4())
FONT = "(effects (font (size 1.27 1.27)))"
HFONT = "(effects (font (size 1.27 1.27)) hide)"

lib = []      # lib_symbols text
body = []     # placed items
pins = []     # (net, x, y, desc) for self-check
refs = {}

def prop(name, val, x, y, hide=False, ang=0):
    return f'(property "{name}" "{val}" (at {x} {y} {ang}) {HFONT if hide else FONT})'

# ---------------- library symbols ----------------
def pin(typ, x, y, ang, ln, name, num, hide=False):
    h = " hide" if hide else ""
    return (f'(pin {typ} line (at {x} {y} {ang}) (length {ln}){h} '
            f'(name "{name}" {FONT}) (number "{num}" {FONT}))')

def sym_header(name, ref, value, power=False, extra=""):
    p = "(power) " if power else ""
    return (f'(symbol "Local:{name}" {p}{extra}(exclude_from_sim no) (in_bom {"no" if power else "yes"}) (on_board yes)\n'
            f'  {prop("Reference", ref, 0, 0, hide=power)}\n  {prop("Value", value, 0, 0)}\n'
            f'  {prop("Footprint", "", 0, 0, True)}\n  {prop("Datasheet", "", 0, 0, True)}\n')

lib.append(sym_header("R", "R", "R", extra="(pin_numbers hide) (pin_names (offset 0)) ") +
 '''  (symbol "R_0_1" (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none))))
  (symbol "R_1_1" ''' + pin("passive", 0, 3.81, 270, 1.27, "~", 1) + pin("passive", 0, -3.81, 90, 1.27, "~", 2) + "))")
lib.append(sym_header("C", "C", "C", extra="(pin_numbers hide) (pin_names (offset 0.254)) ") +
 '''  (symbol "C_0_1" (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
    (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none))))
  (symbol "C_1_1" ''' + pin("passive", 0, 3.81, 270, 3.048, "~", 1) + pin("passive", 0, -3.81, 90, 3.048, "~", 2) + "))")

def power_sym(name, up):
    gfx = ('(polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27) (xy 0 0)) (stroke (width 0) (type default)) (fill (type none)))'
           if up else
           '(polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))')
    return (sym_header(name, "#PWR", name, power=True, extra="(pin_names (offset 0) hide) ") +
            f'  (symbol "{name}_0_1" {gfx})\n  (symbol "{name}_1_1" ' +
            pin("power_in", 0, 0, 90 if up else 270, 0, name, 1, hide=True) + "))")
for n in ("+3V3", "+5V", "VDDA", "VBAT"): lib.append(power_sym(n, True))
lib.append(power_sym("GND", False))
lib.append(sym_header("PWR_FLAG", "#FLG", "PWR_FLAG", power=True, extra="(pin_names (offset 0) hide) ") +
  '  (symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none))))\n  (symbol "PWR_FLAG_1_1" ' +
  pin("power_out", 0, 0, 90, 0, "pwr", 1, hide=True) + "))")

# MCP6004: units 1-4 = op-amps, unit 5 = power
OA_GFX = '(polyline (pts (xy -5.08 5.08) (xy -5.08 -5.08) (xy 5.08 0) (xy -5.08 5.08)) (stroke (width 0.254) (type default)) (fill (type background)))'
mcp = {1: (3, 2, 1), 2: (5, 6, 7), 3: (10, 9, 8), 4: (12, 13, 14)}  # (+, -, out)
s = sym_header("MCP6004", "U", "MCP6004", extra="(pin_names (offset 0.254)) ")
for un, (pp, pm, po) in mcp.items():
    s += (f'  (symbol "MCP6004_{un}_1" {OA_GFX} ' +
          pin("input", -7.62, 2.54, 0, 2.54, "-", pm) + pin("input", -7.62, -2.54, 0, 2.54, "+", pp) +
          pin("output", 7.62, 0, 180, 2.54, "~", po) + ")\n")
s += ('  (symbol "MCP6004_5_1" (rectangle (start -2.54 -5.08) (end 2.54 5.08) (stroke (width 0.254) (type default)) (fill (type background))) ' +
      pin("power_in", 0, 7.62, 270, 2.54, "V+", 4) + pin("power_in", 0, -7.62, 90, 2.54, "V-", 11) + "))")
lib.append(s)
# AD8628 (SOT-23-5)
lib.append(sym_header("AD8628", "U", "AD8628", extra="(pin_names (offset 0.254)) ") +
  f'  (symbol "AD8628_0_1" {OA_GFX})\n  (symbol "AD8628_1_1" ' +
  pin("input", -7.62, 2.54, 0, 2.54, "-", 4) + pin("input", -7.62, -2.54, 0, 2.54, "+", 3) +
  pin("output", 7.62, 0, 180, 2.54, "~", 1) + pin("power_in", 0, 7.62, 270, 5.08, "V+", 5) +
  pin("power_in", 0, -7.62, 90, 5.08, "V-", 2) + "))")
lib.append(sym_header("OPAMP5", "U", "OPAMP5", extra="(pin_names (offset 0.254)) ") +
  f'  (symbol "OPAMP5_0_1" {OA_GFX})\n  (symbol "OPAMP5_1_1" ' +
  pin("input", -7.62, 2.54, 0, 2.54, "-", 4) + pin("input", -7.62, -2.54, 0, 2.54, "+", 3) +
  pin("output", 7.62, 0, 180, 2.54, "~", 1) + pin("power_in", 0, 7.62, 270, 5.08, "V+", 5) +
  pin("power_in", 0, -7.62, 90, 5.08, "V-", 2) + "))")
# REF3033
lib.append(sym_header("REF3033", "U", "REF3033", extra="(pin_names (offset 0.254)) ") +
  '  (symbol "REF3033_0_1" (rectangle (start -5.08 -3.81) (end 5.08 3.81) (stroke (width 0.254) (type default)) (fill (type background))))\n  (symbol "REF3033_1_1" ' +
  pin("power_in", -7.62, 1.27, 0, 2.54, "IN", 1) + pin("power_out", 7.62, 1.27, 180, 2.54, "OUT", 2) +
  pin("power_in", 0, -6.35, 90, 2.54, "GND", 3) + "))")
# VND14NV04 (self-protected low-side switch)
lib.append(sym_header("VND14NV04", "Q", "VND14NV04", extra="(pin_names (offset 0.254)) ") +
  '  (symbol "VND14NV04_0_1" (rectangle (start -5.08 -5.08) (end 5.08 5.08) (stroke (width 0.254) (type default)) (fill (type background))))\n  (symbol "VND14NV04_1_1" ' +
  pin("input", -7.62, 0, 0, 2.54, "IN", 1) + pin("open_collector", 0, 7.62, 270, 2.54, "OUT", 2) +
  pin("power_in", 0, -7.62, 90, 2.54, "GND", 3) + "))")
def conn_sym(n):
    top = (n - 1) * 1.27
    s = sym_header(f"Conn_01x{n:02d}", "J", f"Conn_01x{n:02d}", extra="(pin_names (offset 1.016) hide) ")
    s += (f'  (symbol "Conn_01x{n:02d}_1_1" (rectangle (start -1.27 {round(top+1.27,3)}) (end 1.27 {round(-top-1.27,3)}) '
          '(stroke (width 0.254) (type default)) (fill (type background))) ')
    for i in range(n):
        s += pin("passive", -5.08, round(top - 2.54 * i, 3), 0, 3.81, f"Pin_{i+1}", i + 1)
    return s + "))"
lib.append(conn_sym(6)); lib.append(conn_sym(9))

# ---------------- placement helpers ----------------
def inst(libid, ref, val, x, y, unit=1, npins=(), fp=""):
    x, y = snap(x), snap(y)
    refs.setdefault(ref, 0)
    pl = "\n    ".join(f'(pin "{n}" (uuid "{u()}"))' for n in npins)
    body.append(f'''(symbol (lib_id "Local:{libid}") (at {x} {y} 0) (unit {unit}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")
    {prop("Reference", ref, x + 3.81, y - 1.27)}
    {prop("Value", val, x + 3.81, y + 1.27)}
    {prop("Footprint", fp, x, y, True)}
    {prop("Datasheet", "", x, y, True)}
    {pl}
    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit {unit})))))''')

def label(net, x, y, ang=0):
    body.append(f'(label "{net}" (at {snap(x)} {snap(y)} {ang}) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "{u()}"))')

pwr_n = [0]
POWER = {"+3V3": 1, "+5V": 1, "VDDA": 1, "VBAT": 1, "GND": 0}
def tie(net, x, y, desc, up_ang=0):
    x, y = snap(x), snap(y)
    pins.append((net, x, y, desc))
    if net in POWER:
        pwr_n[0] += 1
        r = f"#PWR{pwr_n[0]:03d}"
        # power symbol sits on the pin point, graphic extends away from it
        body.append(f'''(symbol (lib_id "Local:{net}") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{u()}")
    {prop("Reference", r, x, y, True)}
    {prop("Value", net, x + 1.27, y + (-3.81 if POWER[net] else 3.81))}
    (pin "1" (uuid "{u()}"))
    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{r}") (unit 1)))))''')
    else:
        label(net, x, y, up_ang)

def R(ref, val, x, y, top, bot, fp="Resistor_SMD:R_0603_1608Metric"):
    x, y = sr(x), sr(y)
    inst("R", ref, val, x, y, npins=(1, 2), fp=fp)
    tie(top, x, y - 3.81, f"{ref}.1", 90); tie(bot, x, y + 3.81, f"{ref}.2", 270)
def C(ref, val, x, y, top, bot, fp="Capacitor_SMD:C_0603_1608Metric"):
    x, y = sr(x), sr(y)
    inst("C", ref, val, x, y, npins=(1, 2), fp=fp)
    tie(top, x, y - 3.81, f"{ref}.1", 90); tie(bot, x, y + 3.81, f"{ref}.2", 270)
def OA(unit, x, y, plus, minus, out, ref="U1"):
    x, y = sr(x), sr(y)
    inst("MCP6004", ref, "MCP6004", x, y, unit=unit, npins=(), fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm")
    pp, pm, po = mcp[unit]
    tie(minus, x - 7.62, y - 2.54, f"{ref}{unit}.-", 180)
    tie(plus, x - 7.62, y + 2.54, f"{ref}{unit}.+", 180)
    tie(out, x + 7.62, y, f"{ref}{unit}.out", 0)
def OA_PWR(x, y, ref="U1"):
    inst("MCP6004", ref, "MCP6004", x, y, unit=5, fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm")
    tie("+3V3", x, y - 7.62, f"{ref}5.V+"); tie("GND", x, y + 7.62, f"{ref}5.V-")
def text(t, x, y):
    body.append(f'(text "{t}" (exclude_from_sim no) (at {sr(x)} {sr(y)} 0) (effects (font (size 1.905 1.905)) (justify left)) (uuid "{u()}"))')

# ---------------- circuit ----------------
text("LSU 4.9 analog front-end  -  topology after rusEFI/FOME wideband module rev C (MIT). See FRONTEND.md", 25.4, 20.32)

# 3.3 V analog reference
text("Analog reference VDDA = 3.3 V", 25.4, 30.48)
inst("REF3033", "U3", "REF3033", 48.26, 50.8, npins=(1, 2, 3), fp="Package_TO_SOT_SMD:SOT-23")
tie("+5V", 48.26 - 7.62, 50.8 - 1.27, "U3.IN"); tie("VDDA", 48.26 + 7.62, 50.8 - 1.27, "U3.OUT"); tie("GND", 48.26, 50.8 + 6.35, "U3.GND")
C("C17", "1u", 33.02, 55.88, "+5V", "GND"); C("C7", "1u", 63.5, 55.88, "VDDA", "GND"); C("C9", "100n", 73.66, 55.88, "VDDA", "GND")

# Virtual ground VM = VDDA/2
text("Virtual ground VM = VDDA/2", 25.4, 78.74)
R("R1", "1k", 33.02, 93.98, "VDDA", "VM_MID"); R("R2", "1k", 33.02, 109.22, "VM_MID", "GND")
C("C1", "1u", 45.72, 101.6, "VM_MID", "GND")
OA(4, 66.04, 99.06, "VM_MID", "VM", "VM")          # U1D follower (- tied to out via net VM)
R("R9", "10", 88.9, 99.06, "VM", "LSU_Vm"); C("C4", "1u", 101.6, 106.68, "LSU_Vm", "GND")

# Pump driver: Howland current source
text("Pump driver: Howland current source,  I = -(R33/R31)*(Ip_dac - VM)/R8", 25.4, 127)
R("R31", "68k", 33.02, 142.24, "Ip_dac", "PD_INV"); R("R32", "68k", 33.02, 157.48, "VM", "PD_NI")
OA(1, 66.04, 149.86, "PD_NI", "PD_INV", "PD_OUT")
R("R33", "10k", 88.9, 137.16, "PD_OUT", "PD_INV"); C("C3", "33n", 101.6, 137.16, "PD_OUT", "PD_INV")
R("R8", "47", 88.9, 157.48, "PD_OUT", "LSU_Rtrim"); R("R34", "10k", 101.6, 165.1, "PD_NI", "LSU_Rtrim")

# Pump current sense
text("Pump current sense: Ip_sense = VM + 10*(V_Ip - V_Rtrim), shunt 61.9 ohm", 134.62, 127)
R("R10", "61.9", 144.78, 149.86, "LSU_Rtrim", "LSU_Ip", fp="Resistor_SMD:R_0805_2012Metric")
R("R11", "10k", 160.02, 142.24, "LSU_Rtrim", "IS_N"); R("R12", "10k", 160.02, 157.48, "LSU_Ip", "IS_P")
R("R15", "100k", 172.72, 165.1, "VM", "IS_P"); R("R17", "100k", 187.96, 137.16, "IS_N", "IS_OUT")
inst("AD8628", "U5", "AD8628", 187.96, 152.4, npins=(1, 2, 3, 4, 5), fp="Package_TO_SOT_SMD:SOT-23-5")
tie("IS_N", 187.96 - 7.62, 152.4 - 2.54, "U5.-", 180); tie("IS_P", 187.96 - 7.62, 152.4 + 2.54, "U5.+", 180)
tie("IS_OUT", 187.96 + 7.62, 152.4, "U5.out", 0); tie("+3V3", 187.96, 152.4 - 7.62, "U5.V+"); tie("GND", 187.96, 152.4 + 7.62, "U5.V-")
R("R24", "3.3k", 213.36, 144.78, "IS_OUT", "Ip_sense"); C("C11", "100n", 223.52, 152.4, "Ip_sense", "GND")

# Nernst sense
text("Nernst sense: Un_sense = 2.7*(Un - VM), target Un-VM = 0.45 V", 134.62, 30.48)
R("R3", "10k", 144.78, 48.26, "VM", "NS_N"); R("R4", "10k", 144.78, 63.5, "LSU_Un_sense", "NS_P")
R("R5", "27k", 160.02, 71.12, "NS_P", "GND"); R("R7", "27k", 172.72, 40.64, "NS_N", "Un_sense")
OA(2, 177.8 + 10.16, 55.88, "NS_P", "NS_N", "Un_sense")
text("Nernst buffer, bias current (62k) and Ri injection (22k + 100n)", 134.62, 91.44)
OA(3, 160.02, 109.22, "LSU_Un", "LSU_Un_sense", "LSU_Un_sense")
R("R14", "62k", 185.42, 104.14, "+3V3", "LSU_Un"); C("C2", "100n", 198.12, 104.14, "ESR_BUS", "LSU_Un")
R("R6", "22k", 210.82, 96.52, "Nernst_esr_drive_49", "ESR_BUS")
OA_PWR(236.22, 109.22); C("C5", "100n", 251.46, 109.22, "+3V3", "GND")

# Heater low-side switch
text("Heater switch", 25.4, 190.5)
inst("VND14NV04", "Q1", "VND14NV04", 66.04, 215.9, npins=(1, 2, 3), fp="Package_TO_SOT_SMD:TO-252-2")
tie("HEATER_GATE", 66.04 - 7.62, 215.9, "Q1.IN", 180); tie("LSU_Hminus", 66.04, 215.9 - 7.62, "Q1.OUT", 90); tie("GND", 66.04, 215.9 + 7.62, "Q1.GND")
R("R25", "1k", 43.18, 205.74, "heater_pwm", "HEATER_GATE"); R("R26", "1k", 43.18, 223.52, "HEATER_GATE", "GND")

# Connectors
text("LSU 4.9 connector (pin order to be verified against the Bosch datasheet)", 134.62, 190.5)
J = 154.94; Jy = 213.36
inst("Conn_01x06", "J1", "LSU_4.9", J, Jy, npins=range(1, 7), fp="Connector_Molex:Molex_Micro-Fit_3.0_43650-0600")
for i, n in enumerate(["LSU_Ip", "LSU_Vm", "LSU_Hminus", "VBAT", "LSU_Un", "LSU_Rtrim"]):
    tie(n, J - 5.08, Jy - 6.35 + 2.54 * i, f"J1.{i+1}", 180)
text("Interface to MCU board (analog, 3.3 V)", 190.5, 190.5)
J2 = 210.82; J2y = 215.9
inst("Conn_01x09", "J2", "MCU_IF", J2, J2y, npins=range(1, 10), fp="Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical")
for i, n in enumerate(["Ip_dac", "Ip_sense", "Un_sense", "VM", "heater_pwm", "Nernst_esr_drive_49", "VDDA", "+3V3", "GND"]):
    tie(n, J2 - 5.08, J2y - 10.16 + 2.54 * i, f"J2.{i+1}", 180)


# ============ generic IC / 2-pin symbols for power, CAN and output sections ============
IC = {}   # name -> {pinnum: (px, py)} in library coordinates
def make_ic(name, ref, left, right, w=12.7, fp=""):
    n = max(len(left), len(right)); top = (n - 1) * 1.27; h = top + 2.54
    s = sym_header(name, ref, name, extra="(pin_names (offset 0.254)) ")
    s += (f'  (symbol "{name}_0_1" (rectangle (start {-w/2} {round(h,3)}) (end {w/2} {round(-h,3)}) '
          '(stroke (width 0.254) (type default)) (fill (type background))))\n')
    s += f'  (symbol "{name}_1_1" '
    pos = {}
    for i, (num, pn, typ) in enumerate(left):
        y = round(top - 2.54 * i, 3); pos[num] = (-w/2 - 2.54, y)
        s += pin(typ, -w/2 - 2.54, y, 0, 2.54, pn, num)
    for i, (num, pn, typ) in enumerate(right):
        y = round(top - 2.54 * i, 3); pos[num] = (w/2 + 2.54, y)
        s += pin(typ, w/2 + 2.54, y, 180, 2.54, pn, num)
    lib.append(s + "))"); IC[name] = pos
def ic_inst(name, ref, val, x, y, nets, fp=""):
    x, y = sr(x), sr(y)
    inst(name, ref, val, x, y, npins=tuple(IC[name].keys()), fp=fp)
    for num, (px, py) in IC[name].items():
        net = nets.get(str(num))
        if net:
            tie(net, x + px, y - py, f"{ref}.{num}", 180 if px < 0 else 0)
def two_pin(name, ref0, gfx):
    lib.append(sym_header(name, ref0, name, extra="(pin_numbers hide) (pin_names (offset 0)) ") +
      f'  (symbol "{name}_0_1" {gfx})\n  (symbol "{name}_1_1" ' +
      pin("passive", 0, 3.81, 270, 1.27, "1", 1) + pin("passive", 0, -3.81, 90, 1.27, "2", 2) + "))")
RECT = '(rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
two_pin("Fuse", "F", RECT)
two_pin("L", "L", RECT)
DIODE = ('(polyline (pts (xy -1.27 1.27) (xy 1.27 1.27) (xy 0 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))'
         '(polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))')
two_pin("D", "D", DIODE)       # pin 1 = anode (top), pin 2 = cathode (bottom): anode up -> drawn triangle points down
make_ic("TPS54202", "U", [(3, "VIN", "power_in"), (5, "EN", "input"), (4, "FB", "input"), (1, "GND", "power_in")],
        [(6, "BOOT", "passive"), (2, "SW", "output")])
make_ic("AP2112K-3.3", "U", [(1, "VIN", "power_in"), (3, "EN", "input"), (2, "GND", "power_in")], [(5, "VOUT", "power_out"), (4, "NC", "no_connect")])
make_ic("TJA1051T-3", "U", [(1, "TXD", "input"), (4, "RXD", "output"), (3, "VCC", "power_in"), (5, "VIO", "power_in"), (2, "GND", "power_in")],
        [(7, "CANH", "bidirectional"), (6, "CANL", "bidirectional"), (8, "S", "input")])
make_ic("PESD2CAN", "D", [(1, "IO1", "passive"), (2, "IO2", "passive")], [(3, "GND", "passive")], w=10.16)
make_ic("Q_PMOS", "Q", [(1, "G", "input")], [(2, "D", "passive"), (3, "S", "passive")], w=7.62)
lib.append(conn_sym(2)); lib.append(conn_sym(4)); lib.append(conn_sym(3))
def two(libid, ref, val, x, y, top, bot, fp=""):
    x, y = sr(x), sr(y)
    inst(libid, ref, val, x, y, npins=(1, 2), fp=fp)
    tie(top, x, y - 3.81, f"{ref}.1", 90); tie(bot, x, y + 3.81, f"{ref}.2", 270)
def conn(n, ref, val, x, y, names, fp):
    x, y = sr(x), sr(y)
    inst(f"Conn_01x{n:02d}", ref, val, x, y, npins=range(1, n + 1), fp=fp)
    top = (n - 1) * 1.27
    for i, nm in enumerate(names): tie(nm, x - 5.08, y - top + 2.54 * i, f"{ref}.{i+1}", 180)

# ---------------- power input and protection ----------------
Y0 = 254.0
text("Power input: fuse, reverse-polarity P-MOSFET, TVS", 25.4, Y0)
conn(4, "J3", "PWR_CAN", 38.1, Y0 + 20.32, ["VBAT_IN", "GND", "CAN_H_EXT", "CAN_L_EXT"], "Connector_Molex:Molex_Micro-Fit_3.0_43650-0400")
two("Fuse", "F1", "3A", 60.96, Y0 + 15.24, "VBAT_IN", "VBAT_F", fp="Fuse:Fuse_1206_3216Metric")
ic_inst("Q_PMOS", "Q2", "P-MOS 60V (e.g. DMP6050)", 88.9, Y0 + 22.86, {"1": "PMOS_G", "2": "VBAT_F", "3": "VBAT"}, fp="Package_TO_SOT_SMD:SOT-23")
R("R40", "10k", 88.9, Y0 + 38.1, "PMOS_G", "GND")
two("D", "D1", "Zener 12V", 101.6, Y0 + 38.1, "PMOS_G", "VBAT", fp="Diode_SMD:D_SOD-323")
two("D", "D2", "SMBJ24A", 114.3, Y0 + 38.1, "VBAT", "GND", fp="Diode_SMD:D_SMB")
C("C20", "10u 50V", 127.0, Y0 + 38.1, "VBAT", "GND", fp="Capacitor_SMD:C_1206_3216Metric")

# ---------------- 5 V buck ----------------
text("5 V buck (TPS54202; pinout and values from memory - VERIFY against datasheet)", 25.4, Y0 + 55.88)
ic_inst("TPS54202", "U6", "TPS54202", 63.5, Y0 + 76.2, {"3": "VBAT", "5": "VBAT", "4": "FB5", "1": "GND", "6": "BOOT5", "2": "SW5"}, fp="Package_TO_SOT_SMD:SOT-23-6")
C("C21", "100n", 91.44, Y0 + 66.04, "BOOT5", "SW5")
two("L", "L1", "15u (verify)", 104.14, Y0 + 76.2, "SW5", "+5V", fp="Inductor_SMD:L_Bourns_SRN6045")
C("C22", "22u", 116.84, Y0 + 83.82, "+5V", "GND", fp="Capacitor_SMD:C_1206_3216Metric")
R("R41", "73.2k", 129.54, Y0 + 70.0 + 0.0, "+5V", "FB5"); R("R42", "10k", 129.54, Y0 + 85.0 + 0.0, "FB5", "GND")

# ---------------- 3.3 V LDO ----------------
text("3.3 V LDO", 150.0, Y0 + 55.88)
ic_inst("AP2112K-3.3", "U7", "AP2112K-3.3", 175.26, Y0 + 76.2, {"1": "+5V", "3": "+5V", "2": "GND", "5": "+3V3"}, fp="Package_TO_SOT_SMD:SOT-23-5")
C("C23", "1u", 154.94, Y0 + 83.82, "+5V", "GND"); C("C24", "2.2u", 198.12, Y0 + 83.82, "+3V3", "GND")

# ---------------- CAN ----------------
text("CAN (rusEFI wideband protocol)", 225.0, Y0)
ic_inst("TJA1051T-3", "U8", "TJA1051T/3", 254.0, Y0 + 20.32, {"1": "CAN_TX", "4": "CAN_RX", "3": "+5V", "5": "+3V3", "2": "GND", "7": "CANH", "6": "CANL", "8": "CAN_S"}, fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
R("R43", "10k", 279.4, Y0 + 27.94, "CAN_S", "GND")
C("C25", "100n", 238.76, Y0 + 33.02, "+5V", "GND")
ic_inst("PESD2CAN", "D3", "PESD2CAN", 302.26, Y0 + 20.32, {"1": "CANH", "2": "CANL", "3": "GND"}, fp="Package_TO_SOT_SMD:SOT-23")
R("R44", "120", 292.1, Y0 + 40.64, "CANH", "CAN_TERM"); conn(2, "J5", "CAN_TERM_JMP", 304.8, Y0 + 40.64, ["CAN_TERM", "CANL"], "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
R("R45", "0", 317.5, Y0 + 12.7, "CANH", "CAN_H_EXT", fp="Resistor_SMD:R_0603_1608Metric"); R("R46", "0", 317.5, Y0 + 27.94, "CANL", "CAN_L_EXT")

# ---------------- 0-5 V analog output ----------------
text("0-5 V AFR output: 10..20 AFR = 0..5 V, DAC 0-3.3 V x1.51", 225.0, Y0 + 55.88)
x9, y9 = sr(254.0), sr(Y0 + 83.82)
inst("OPAMP5", "U9", "MCP6001", x9, y9, npins=(1, 2, 3, 4, 5), fp="Package_TO_SOT_SMD:SOT-23-5")
tie("AFR_DAC", x9 - 7.62, y9 + 2.54, "U9.+", 180); tie("AFR_FB", x9 - 7.62, y9 - 2.54, "U9.-", 180)
tie("AFR_AMP", x9 + 7.62, y9, "U9.out", 0); tie("+5V", x9, y9 - 7.62, "U9.V+"); tie("GND", x9, y9 + 7.62, "U9.V-")
R("R47", "5.1k", 238.76, Y0 + 70.0, "AFR_AMP", "AFR_FB"); R("R48", "10k", 238.76, Y0 + 95.0, "AFR_FB", "GND")
R("R49", "220", 279.4, Y0 + 83.82 - 3.81 + 3.81, "AFR_AMP", "AFR_OUT"); C("C26", "100n", 292.1, Y0 + 90.0, "AFR_OUT", "GND")
conn(2, "J4", "AFR_OUT_0_5V", 308.0, Y0 + 90.0, ["AFR_OUT", "GND"], "Connector_Molex:Molex_Micro-Fit_3.0_43650-0200")
C("C27", "100n", 266.7, Y0 + 70.0, "+5V", "GND")

# ---------------- MCU digital interface ----------------
text("Interface to MCU board (digital)", 330.0, Y0)
conn(4, "J6", "MCU_DIG", 343.0, Y0 + 22.86, ["AFR_DAC", "CAN_TX", "CAN_RX", "GND"], "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")


flag_n = [0]
def flag(net, x, y):
    x, y = sr(x), sr(y); flag_n[0] += 1; r = f"#FLG{flag_n[0]:02d}"
    body.append(f'''(symbol (lib_id "Local:PWR_FLAG") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{u()}")
    {prop("Reference", r, x, y, True)}
    {prop("Value", "PWR_FLAG", x + 1.27, y - 3.81)}
    (pin "1" (uuid "{u()}"))
    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{r}") (unit 1)))))''')
    tie(net, x, y, r)
text("Power flags (ERC: nets fed from connectors / regulators)", 304.8, 30.48)
flag("+5V", 304.8, 40.64); flag("VBAT", 320.04, 40.64); flag("GND", 335.28, 40.64)

# ---------------- output ----------------
out = f'''(kicad_sch (version 20231120) (generator "afr_frontend_gen") (generator_version "1.0")
  (uuid "{ROOT}")
  (paper "A2")
  (title_block (title "LSU 4.9 analog front-end") (date "2026-10-05") (rev "0.1")
    (comment 1 "Topology after rusEFI/FOME wideband module rev C (MIT)")
    (comment 2 "Draft - NOT verified by ERC/simulation/bench"))
  (lib_symbols
{chr(10).join("    " + l.replace(chr(10), chr(10) + "    ") for l in lib)}
  )
  {chr(10).join("  " + b.replace(chr(10), chr(10) + "  ") for b in body)}
  (sheet_instances (path "/" (page "1")))
)
'''
import os
_d = os.path.dirname(os.path.abspath(sys.argv[1])) if len(sys.argv) > 1 else "."
_libsyms = [l.replace('(symbol "Local:', '(symbol "', 1) for l in lib]
open(os.path.join(_d, "afr_local.kicad_sym"), "w").write(
    '(kicad_symbol_lib (version 20231120) (generator "afr_frontend_gen") (generator_version "1.0")\n' +
    "\n".join("  " + l.replace("\n", "\n  ") for l in _libsyms) + "\n)\n")
open(os.path.join(_d, "sym-lib-table"), "w").write(
    '(sym_lib_table\n  (version 7)\n  (lib (name "Local")(type "KiCad")(uri "${KIPRJMOD}/afr_local.kicad_sym")(options "")(descr "AFR controller generated symbols"))\n)\n')
dst = sys.argv[1] if len(sys.argv) > 1 else "afr_frontend.kicad_sch"
open(dst, "w").write(out)
if "--pins" in sys.argv: json.dump(pins, open(dst + ".pins.json", "w"))
print("written", dst, len(body), "items")
