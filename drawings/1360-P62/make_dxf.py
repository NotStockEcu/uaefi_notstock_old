"""Redraw of CB&I connection diagram UNIT 3120 / 1360-P62 (DWG No. 31-00-065-11-1, sheet 0016).

Generates 1360-P62.dxf (A3, mm). Convert to DWG with LibreDWG: dxf2dwg -y 1360-P62.dxf
"""
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

doc = ezdxf.new("R2000", setup=True)
doc.units = ezdxf.units.MM
msp = doc.modelspace()
for name, color, lt in [("FRAME", 7, "CONTINUOUS"), ("WIRE", 7, "CONTINUOUS"),
                        ("CABLE", 1, "CONTINUOUS"), ("BOX", 8, "DASHDOT"),
                        ("SYMBOL", 5, "CONTINUOUS"), ("TEXT", 3, "CONTINUOUS")]:
    doc.layers.add(name, color=color, linetype=lt)
doc.header["$LTSCALE"] = 0.4

OY = 15  # vertical offset of the drawing content above the title block


def P(x, y):
    return (x, y + OY)


def line(a, b, layer="WIRE", width=0.0):
    if width:
        msp.add_lwpolyline([P(*a), P(*b)], dxfattribs={"layer": layer, "const_width": width})
    else:
        msp.add_line(P(*a), P(*b), dxfattribs={"layer": layer})


def poly(pts, layer="WIRE"):
    msp.add_lwpolyline([P(*p) for p in pts], dxfattribs={"layer": layer})


def text(x, y, s, h=2.0, align=TA.MIDDLE_LEFT, layer="TEXT", raw=False):
    # Alignment is resolved here to a plain left/baseline insert point, which
    # survives DXF->DWG conversion unchanged in every CAD program.
    if not raw:
        x, y = P(x, y)
    w = len(s) * h * 0.62
    name = align.name
    if "CENTER" in name:
        x -= w / 2
    elif "RIGHT" in name:
        x -= w
    if name.startswith("MIDDLE"):
        y -= h / 2
    elif name.startswith("TOP"):
        y -= h
    msp.add_text(s, height=h, dxfattribs={"layer": layer, "style": "OpenSans", "insert": (x, y)})


def box(x1, y1, x2, y2, layer="BOX"):
    poly([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)], layer)


def tag(x, y, s):
    """Solid framed location tag, e.g. 3110."""
    box(x - 6, y - 3, x + 6, y + 3, "WIRE")
    text(x, y, s, 2.5, TA.MIDDLE_CENTER)


def term(x, y, label=None, side="left", lbl2=None):
    """Screw terminal: circle with a slash."""
    msp.add_circle(P(x, y), 0.8, dxfattribs={"layer": "SYMBOL"})
    line((x - 1.2, y - 1.2), (x + 1.2, y + 1.2), "SYMBOL")
    if label is not None:
        if side == "left":
            text(x - 2, y, label, 1.8, TA.MIDDLE_RIGHT)
        else:
            text(x - 0.5, y + 2.4, label, 1.6, TA.BOTTOM_CENTER)
    if lbl2 is not None:
        text(x + 4, y + 0.8, lbl2, 1.6, TA.BOTTOM_CENTER)


def bus(x, y1, y2):
    line((x, y1), (x, y2), "CABLE", 0.8)


def cable(x1, x2, y, name):
    line((x1, y), (x2, y), "CABLE", 0.35)
    text((x1 + x2) / 2, y + 1.2, name, 1.8, TA.BOTTOM_CENTER)


def shield(x, y, gnd=True):
    msp.add_ellipse(P(x, y), major_axis=(0, 2.5), ratio=0.4, dxfattribs={"layer": "SYMBOL"})
    if gnd:
        line((x, y - 2.5), (x, y - 6), "SYMBOL")
        ground(x, y - 6)


def ground(x, y):
    for i, w in enumerate((2.0, 1.4, 0.8)):
        line((x - w, y - i * 0.7), (x + w, y - i * 0.7), "SYMBOL")


def arrowhead(x, y):
    poly([(x - 1.5, y + 0.7), (x, y), (x - 1.5, y - 0.7), (x - 1.5, y + 0.7)], "SYMBOL")


def no_contact(x, y, length=6):
    """Horizontal normally-open contact between x and x+length."""
    line((x, y), (x + length * 0.3, y))
    line((x + length * 0.3, y), (x + length * 0.75, y + 1.8))
    line((x + length * 0.7, y), (x + length, y))


# ------------------------------------------------------------------ frame (A3)
msp.add_lwpolyline([(5, 5), (415, 5), (415, 292), (5, 292), (5, 5)], dxfattribs={"layer": "FRAME"})
msp.add_lwpolyline([(10, 10), (410, 10), (410, 287), (10, 287), (10, 10)],
                   dxfattribs={"layer": "FRAME", "const_width": 0.5})
for i in range(8):
    x = 10 + i * 50
    if i:
        for yy in ((5, 10), (287, 292)):
            msp.add_line((x, yy[0]), (x, yy[1]), dxfattribs={"layer": "FRAME"})
    for yy in (7.5, 289.5):
        text(x + 25, yy, str(i + 1), 2.5, TA.MIDDLE_CENTER, raw=True)
for j, ch in enumerate("ABCDEF"):
    y = 287 - j * 46.17
    if j:
        for xx in ((5, 10), (410, 415)):
            msp.add_line((xx[0], y), (xx[1], y), dxfattribs={"layer": "FRAME"})
    for xx in (7.5, 412.5):
        text(xx, y - 23, ch, 2.5, TA.MIDDLE_CENTER, raw=True)

# title block
tb = [(250, 10), (410, 10), (410, 30), (250, 30), (250, 10)]
msp.add_lwpolyline(tb, dxfattribs={"layer": "FRAME"})
for x in (280, 340):
    msp.add_line((x, 10), (x, 30), dxfattribs={"layer": "FRAME"})
msp.add_line((340, 16), (410, 16), dxfattribs={"layer": "FRAME"})
text(265, 20, "CB&I", 4.0, TA.MIDDLE_CENTER, raw=True)
text(310, 20, "CB&I Lummus s.r.o.", 2.5, TA.MIDDLE_CENTER, raw=True)
text(375, 26.5, "CONNECTION DIAGRAM", 2.5, TA.MIDDLE_CENTER, raw=True)
text(375, 22.5, "UNIT 3120", 2.5, TA.MIDDLE_CENTER, raw=True)
text(375, 18.5, "1360-P62", 2.5, TA.MIDDLE_CENTER, raw=True)
text(342, 13, "A3  DWG No. 31-00-065-11-1", 1.8, TA.MIDDLE_LEFT, raw=True)
text(406, 13, "SHEET 0016", 1.4, TA.MIDDLE_RIGHT, raw=True)

# ------------------------------------------------------------------ RM3110.1/5a  -5aX02
box(25, 257, 55, 264, "WIRE")
text(40, 260.5, "RM3110.1/5a", 2.2, TA.MIDDLE_CENTER)
box(25, 205, 70, 252)
text(42, 247, "-5aX02", 2.0, TA.MIDDLE_CENTER)
for k, (lab, y) in enumerate((("L1", 240), ("L2", 233), ("L3", 226), ("PE", 219))):
    term(43, y, lab)
    line((44, y), (58, y))
    text(52, y + 1.6, ("U", "V", "W", "PE")[k], 1.8, TA.BOTTOM_CENTER)
bus(58, 218, 241)
cable(58, 152, 230, "3110-WL-1360-FC-P62")
arrowhead(152, 230)

# ------------------------------------------------------------------ 3110 FC + TM31
tag(128, 247, "3110")
text(128, 240, "1360-FC-P62", 1.8, TA.MIDDLE_CENTER)
text(128, 236, "400/400V", 1.8, TA.MIDDLE_CENTER)
box(140, 160, 178, 252)
text(165, 247, "-X0", 1.8, TA.MIDDLE_LEFT)
for k, (lab, n) in enumerate((("U", "1"), ("V", "2"), ("W", "3"))):
    y = 238 - k * 6
    line((153, y), (166, y))
    text(149, y, lab, 1.8, TA.MIDDLE_CENTER)
    term(167, y)
    text(170, y, n, 1.8, TA.MIDDLE_LEFT)
bus(153, 225, 240)
text(160, 216, "-X", 1.8, TA.MIDDLE_LEFT)
for k, lab in enumerate("UVW"):
    y = 210 - k * 6
    term(152, y, lab)
    line((153, y), (164, y))
    text(160, y + 1.4, lab, 1.8, TA.BOTTOM_CENTER)
bus(164, 196, 212)
text(126, 196, "CONTROL", 1.8, TA.MIDDLE_CENTER)
text(126, 192, "SYSTEM", 1.8, TA.MIDDLE_CENTER)
text(126, 186, "PROFIBUS", 1.8, TA.MIDDLE_CENTER)
line((117, 189), (139, 189))
arrowhead(139, 189)
text(159, 168, "TERMINAL", 1.8, TA.MIDDLE_CENTER)
text(159, 164, "MODUL TM31", 1.8, TA.MIDDLE_CENTER)

box(132, 20, 178, 160)
text(155, 156, "-X1", 1.8, TA.MIDDLE_CENTER)
# thermistor input X1:5/6
for n, y in (("5", 147), ("6", 139)):
    term(152, y, n, side="top")
    line((153, y), (162, y))
line((162, 139), (162, 147))
line((162, 143), (167, 143))
bus(167, 140, 146)
shield(170, 143)
# A52 analog output 3/4 -> 1/2
text(136, 121, "A52", 1.8, TA.MIDDLE_LEFT)
for n, m, y in (("3", "1", 125), ("4", "2", 117)):
    term(152, y, n, side="top", lbl2=m)
    line((153, y), (162, y))
line((162, 117), (162, 125))
line((162, 121), (167, 121))
bus(167, 118, 124)
shield(170, 121)
# digital inputs
for lab, n, m, y in (("START", "5", "1", 88), ("STOP", "6", "2", 80),
                     ("M/D", "7", "3", 72), ("+24V", "9", "4", 64)):
    text(134, y, lab, 1.8, TA.MIDDLE_LEFT)
    term(152, y, n, side="top", lbl2=m)
    line((153, y), (165, y))
bus(165, 62, 90)
shield(170, 80)
# -X542 CHOD
text(134, 52, "-X542", 1.8, TA.MIDDLE_LEFT)
text(134, 47, "CHOD", 1.8, TA.MIDDLE_LEFT)
for n, m, y in (("3", "2", 52), ("1", "1", 46)):
    term(152, y, n, side="top", lbl2=m)
    line((153, y), (165, y))
bus(165, 44, 54)
# BLOK
text(134, 36, "BLOK", 1.8, TA.MIDDLE_LEFT)
text(134, 27, "+24V", 1.8, TA.MIDDLE_LEFT)
for n, y in (("8", 36), ("31", 27)):
    term(152, y, n, side="top")
    line((153, y), (162, y))
line((162, 27), (162, 36))
line((162, 31.5), (165, 31.5))
bus(165, 29, 34)
shield(170, 31.5)

# ------------------------------------------------------------------ 3119 motor 1360-M-P62
tag(192, 192, "3119")
box(205, 133, 262, 200)
text(207, 197, "1360-M-P62", 1.8, TA.MIDDLE_LEFT)
cable(164, 238, 204, "1360-WL-P62")
line((238, 204), (238, 192), "CABLE", 0.35)
line((238, 204), (247, 204), "CABLE", 0.35)
ground(247.5, 204)
line((247.5, 204), (247.5, 204))
# motor terminal board
xs = {"PE": 222, "W": 232, "V": 238, "U": 244}
for k in ("W", "V", "U"):
    term(xs[k], 186)
    term(xs[k], 179)
    text(xs[k] - 2.5, 186, k, 1.6, TA.MIDDLE_RIGHT)
    text(xs[k] - 2.5, 179, k, 1.6, TA.MIDDLE_RIGHT)
    line((xs[k], 192), (xs[k], 187), "CABLE", 0.35)
poly([(232, 192), (244, 192)], "CABLE")
term(222, 182)
text(220, 186, "PE", 1.6, TA.BOTTOM_CENTER)
line((222, 181), (222, 163))
line((222, 163), (232, 163))
cx, cy = 238, 160
msp.add_circle(P(cx, cy), 6, dxfattribs={"layer": "SYMBOL"})
text(cx, cy + 1.5, "M", 3.0, TA.MIDDLE_CENTER)
text(cx, cy - 2.5, "3~", 2.0, TA.MIDDLE_CENTER)
for k, dx in (("W", -3), ("V", 0), ("U", 3)):
    poly([(xs[k], 178), (xs[k], 172), (cx + dx, 172), (cx + dx, cy + 5.3)])
text(247, 162, "400V", 1.8, TA.MIDDLE_LEFT)
text(247, 158, "22kW", 1.8, TA.MIDDLE_LEFT)
# thermistor (PTC)
box(222, 137, 252, 149, "WIRE")
msp.add_lwpolyline([P(238, 140), P(238, 146), P(242, 146), P(242, 140), P(238, 140)],
                   dxfattribs={"layer": "SYMBOL"})
line((235, 139), (245, 147), "SYMBOL")
text(246, 145, "ϑ", 2.0, TA.MIDDLE_LEFT)
cable(167, 218, 143, "1360-WS-P62.3")
bus(220, 140, 146)
line((220, 143), (222, 143))

# ------------------------------------------------------------------ 3120 local station 1360-MS-P62
tag(290, 135, "3120")
text(305, 142, "1360-MS-P62", 1.8, TA.MIDDLE_LEFT)
box(300, 56, 358, 139)
text(320, 133, "-X1", 1.8, TA.MIDDLE_CENTER)
cable(167, 302, 121, "1360-WS-P62.2")
bus(302, 117, 125)
# PA01 ammeter
box(306, 109, 352, 129, "WIRE")
for n, y in (("1", 126), ("2", 113)):
    term(318, y, n, side="top")
    text(312, y + 0.8, n, 1.6, TA.BOTTOM_CENTER)
    line((306, y), (317, y))
msp.add_circle(P(338, 113), 3, dxfattribs={"layer": "SYMBOL"})
text(338, 113, "A", 2.2, TA.MIDDLE_CENTER)
text(338, 108, "4-20mA", 1.5, TA.TOP_CENTER)
text(338, 119, "-PA01", 1.8, TA.BOTTOM_CENTER)
poly([(319, 126), (350, 126), (350, 113), (341, 113)])
line((319, 113), (335, 113))
text(333, 114, "2", 1.4, TA.BOTTOM_CENTER)
text(343, 114, "1", 1.4, TA.BOTTOM_CENTER)
term(318, 101, "3", side="top")
# control terminals 4..8
rows = {"4": 92, "5": 85, "6": 77, "7": 69, "8": 62}
for n, y in rows.items():
    term(318, y, n, side="top")
    text(312, y + 0.8, n, 1.6, TA.BOTTOM_CENTER)
    line((306, y), (317, y))
line((306, 62), (306, 92))
cable(262, 304, 77, "1360-WS-P62.1")
bus(304, 74, 80)
ground(318, 60)
# -S13 LOCAL key switch on row 4
line((319, 92), (326, 92))
no_contact(326, 92, 7)
text(329, 96, "LOCAL", 1.6, TA.BOTTOM_CENTER)
text(345, 98, "-S13", 1.8, TA.MIDDLE_LEFT)
line((333, 92), (352, 92))
line((352, 92), (352, 69))
# -SA selector STOP 0 / AUT / START 2
text(329, 89.5, "STOP 0", 1.4, TA.MIDDLE_LEFT)
text(329, 87.5, "START 2", 1.4, TA.MIDDLE_LEFT)
text(346, 86, "-SA", 1.8, TA.MIDDLE_LEFT)
line((319, 85), (334, 85))
text(336, 83, "1", 1.3, TA.MIDDLE_CENTER)
no_contact(334, 85, 6)
text(338, 83, "2", 1.3, TA.MIDDLE_CENTER)
line((340, 85), (344, 85))
line((344, 85), (344, 92))
line((319, 77), (334, 77))
text(334, 75.5, "3", 1.3, TA.MIDDLE_CENTER)
no_contact(334, 77, 6)
text(340, 75.5, "4", 1.3, TA.MIDDLE_CENTER)
line((340, 77), (352, 77))
line((330, 89), (330, 79), "SYMBOL")  # mechanical link
line((319, 69), (352, 69))
# SA truth table
text(372, 105, "-SA", 2.2, TA.MIDDLE_CENTER)
for k, lab in enumerate(("STOP", "AUT", "START")):
    x = 366 + k * 6
    msp.add_text(lab, height=1.6, dxfattribs={"layer": "TEXT", "rotation": 90, "style": "OpenSans",
                                               "insert": P(x + 0.6, 94)})
    line((x, 80), (x, 93))
text(358, 88, "1-2", 1.5, TA.MIDDLE_LEFT)
text(358, 83, "3-4", 1.5, TA.MIDDLE_LEFT)
line((357, 86.5), (384, 86.5))
line((372, 88), (378, 88), "CABLE", 0.6)
for (x, y) in ((372, 88), (378, 88), (378, 83)):
    msp.add_circle(P(x, y), 0.7, dxfattribs={"layer": "SYMBOL"})
    msp.add_solid([P(x - .5, y - .5), P(x + .5, y - .5), P(x - .5, y + .5), P(x + .5, y + .5)],
                  dxfattribs={"layer": "SYMBOL"})

# ------------------------------------------------------------------ RP3110 / SO3110 relay box
text(197, 116.5, "RP3110", 2.4, TA.MIDDLE_LEFT)
text(214, 116.5, "SO3110", 1.8, TA.MIDDLE_LEFT)
box(196, 27, 262, 113)
cable(165, 198, 80, "1360-WS-P62.5")
bus(198, 64, 90)


def relay(y, name, left_n, right_n):
    """Relay: changeover contact 11/12/14 (left) and coil A1/A2 (right)."""
    box(210, y - 12, 250, y + 6, "WIRE")
    text(215, y + 7.5, name, 1.8, TA.MIDDLE_LEFT)
    text(206, y + 6, left_n, 1.6, TA.MIDDLE_CENTER)
    for n, dy in (("14", 3), ("12", -2), ("11", -8)):
        term(214, y + dy)
        text(212, y + dy + 1, n, 1.3, TA.BOTTOM_RIGHT)
    poly([(215, y - 8), (222, y - 8), (226, y + 2)], "SYMBOL")
    poly([(215, y + 3), (227, y + 3)], "SYMBOL")
    poly([(215, y - 2), (224, y - 2), (224, y - 4)], "SYMBOL")
    for n, dy in (("A1", 2), ("A2", -3)):
        text(239, y + dy, n, 1.3, TA.MIDDLE_RIGHT)
        term(243, y + dy)
    msp.add_lwpolyline([P(246, y - 4), P(249, y - 4), P(249, y + 3), P(246, y + 3), P(246, y - 4)],
                       dxfattribs={"layer": "SYMBOL"})
    text(253, y + 4, right_n, 1.6, TA.MIDDLE_CENTER)
    line((244, y + 2), (255, y + 2))


relay(100, "-KA08.3 M/D", "3", "4")
relay(78, "-KA08.2 STOP", "2", "5")
relay(56, "-KA08.1 START", "4", "6")
# left-side wiring from P62.5 bus to contacts
poly([(198, 88), (206, 88), (206, 103), (213, 103)])     # 3 -> KA08.3 14
poly([(198, 80), (204, 80), (204, 81), (213, 81)])       # 2 -> KA08.2 14
poly([(198, 72), (205, 72), (205, 59), (213, 59)])       # 4 -> KA08.1 14
poly([(198, 66), (202, 66), (202, 48), (213, 48)])       # common 11 of START
line((202, 70), (213, 70))                               # common 11 of STOP
line((202, 70), (202, 92))
line((202, 92), (213, 92))                               # common 11 of M/D
# coils A2 common to N, A1 to 230V via P62.1
line((244, 97), (257, 97)); line((244, 75), (257, 75)); line((244, 53), (257, 53))
line((257, 53), (257, 97))
poly([(255, 102), (259, 102), (259, 78)])
poly([(255, 80), (260, 80)])
poly([(255, 58), (260, 58), (260, 80)])
bus(262, 70, 84)
line((259, 77), (262, 77))

# 230 V AC supply
cable(165, 198, 49, "1360-WS-P62.7")
bus(198, 34, 51)
text(203, 41, "1", 1.4, TA.MIDDLE_CENTER)
text(203, 36, "2", 1.4, TA.MIDDLE_CENTER)
text(206, 47, "-FA9", 1.8, TA.MIDDLE_LEFT)
text(206, 44.5, "2A/B", 1.3, TA.MIDDLE_LEFT)
text(206, 39, "230V AC", 1.3, TA.MIDDLE_LEFT)
line((198, 42), (212, 42))
no_contact(212, 42, 8)
line((217, 44), (219, 45), "SYMBOL")
line((220, 42), (233, 42))
text(232, 45, "-X1", 1.8, TA.MIDDLE_RIGHT)
term(236, 42, "9", side="top")
text(244, 43, "7", 1.4, TA.BOTTOM_CENTER)
line((237, 42), (257, 42))
line((257, 42), (257, 53))
line((198, 36), (233, 36))
term(236, 36, "N", side="top")
line((237, 36), (247, 36))
text(249, 39, "-KA08.2", 1.6, TA.MIDDLE_LEFT)
no_contact(247, 36, 6)
poly([(253, 36), (258, 36), (258, 31), (198, 31)])
line((198, 31), (198, 34))
cable(165, 302, 31.5, "1360-WS-P62.6")

# ------------------------------------------------------------------ 3110 pressure switch
tag(290, 53, "3110")
text(304, 53, "3110-C-MCC01", 1.8, TA.MIDDLE_LEFT)
box(300, 21, 358, 50)
bus(302, 29, 34)
for n, y in (("7", 45), ("8", 37)):
    term(312, y, n, side="top")
    line((302, 31.5), (305, 31.5))
poly([(305, 31.5), (305, 45), (311, 45)])
line((305, 37), (311, 37))
poly([(313, 45), (330, 45), (330, 43)])
no_contact(322, 37, 8)
line((313, 37), (322, 37))
poly([(330, 37), (345, 37), (345, 45), (330, 45)])
text(320, 25 + 1, "PRESSURE", 1.8, TA.MIDDLE_CENTER)
text(320, 22.5, "1360 PI 62-51", 1.8, TA.MIDDLE_CENTER)

doc.saveas(__file__.replace("make_dxf.py", "1360-P62.dxf"))
print("written")
