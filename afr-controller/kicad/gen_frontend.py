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
    body.append(f'(label "{net}" (at {snap(x)} {snap(y)} {ang}) {FONT.replace(")))", ") justify left bottom))") if False else FONT} (uuid "{u()}"))')

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
    inst("R", ref, val, x, y, npins=(1, 2), fp=fp)
    tie(top, x, y - 3.81, f"{ref}.1", 90); tie(bot, x, y + 3.81, f"{ref}.2", 270)
def C(ref, val, x, y, top, bot, fp="Capacitor_SMD:C_0603_1608Metric"):
    inst("C", ref, val, x, y, npins=(1, 2), fp=fp)
    tie(top, x, y - 3.81, f"{ref}.1", 90); tie(bot, x, y + 3.81, f"{ref}.2", 270)
def OA(unit, x, y, plus, minus, out, ref="U1"):
    inst("MCP6004", ref, "MCP6004", x, y, unit=unit, npins=(), fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm")
    pp, pm, po = mcp[unit]
    tie(minus, x - 7.62, y - 2.54, f"{ref}{unit}.-", 180)
    tie(plus, x - 7.62, y + 2.54, f"{ref}{unit}.+", 180)
    tie(out, x + 7.62, y, f"{ref}{unit}.out", 0)
def OA_PWR(x, y, ref="U1"):
    inst("MCP6004", ref, "MCP6004", x, y, unit=5, fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm")
    tie("+3V3", x, y - 7.62, f"{ref}5.V+"); tie("GND", x, y + 7.62, f"{ref}5.V-")
def text(t, x, y):
    body.append(f'(text "{t}" (exclude_from_sim no) (at {snap(x)} {snap(y)} 0) (effects (font (size 1.905 1.905)) (justify left)) (uuid "{u()}"))')

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
    tie(n, J - 5.08, Jy + 6.35 - 2.54 * i, f"J1.{i+1}", 180)
text("Interface to MCU board (analog, 3.3 V)", 190.5, 190.5)
J2 = 210.82; J2y = 215.9
inst("Conn_01x09", "J2", "MCU_IF", J2, J2y, npins=range(1, 10), fp="Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical")
for i, n in enumerate(["Ip_dac", "Ip_sense", "Un_sense", "VM", "heater_pwm", "Nernst_esr_drive_49", "VDDA", "+3V3", "GND"]):
    tie(n, J2 - 5.08, J2y + 10.16 - 2.54 * i, f"J2.{i+1}", 180)

# ---------------- output ----------------
out = f'''(kicad_sch (version 20231120) (generator "afr_frontend_gen") (generator_version "1.0")
  (uuid "{ROOT}")
  (paper "A3")
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
dst = sys.argv[1] if len(sys.argv) > 1 else "afr_frontend.kicad_sch"
open(dst, "w").write(out)
if "--pins" in sys.argv: json.dump(pins, open(dst + ".pins.json", "w"))
print("written", dst, len(body), "items")
