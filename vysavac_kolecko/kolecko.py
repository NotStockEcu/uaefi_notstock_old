"""
Dvoudílné kolečko k vysavači – parametrický model (CadQuery).
  hub   = vnitřní náboj z tvrdého plastu (PETG / PLA / ASA)
  pneu  = obruč z měkkého materiálu (TPU 85A–95A)

Spuštění:  pip install cadquery && python3 kolecko.py
Vytvoří STEP + STL pro oba díly do stejné složky.
Všechny rozměry v mm – uprav podle svého měření.
"""
import os
import cadquery as cq

# ---------------- PARAMETRY ----------------
D_OUT      = 64.0   # vnější průměr celého kolečka
W          = 25.0   # šířka kolečka
T_TIRE     = 5.0    # tloušťka měkké obruče (radiálně)
FLANGE_H   = 2.0    # o kolik jsou boční lemy náboje vyšší než dosedací plocha
FLANGE_W   = 2.0    # šířka bočních lemů
RIM_T      = 2.5    # tloušťka věnce náboje
FACE_T     = 2.0    # tloušťka čelní (venkovní) stěny
N_RIBS     = 8      # počet žeber
RIB_T      = 1.8    # tloušťka žebra
N_KEYS     = 12     # podélné drážky proti protáčení obruče
KEY_H      = 0.8    # výška klínu
KEY_W      = 2.0    # šířka klínu
AXLE_D     = 7.0    # průměr osy
BORE_CLR   = 0.3    # vůle díry na ose (7.3 mm díra)
BOSS_D     = 13.0   # vnější průměr středového pouzdra
BOSS_EXT   = 5.0    # o kolik pouzdro přečnívá na vnitřní straně (jako originál)
SNAP       = False  # True = rozříznuté pouzdro se zobáčky dovnitř (do drážky na ose)
SNAP_LIP   = 0.5    # o kolik zobáček zužuje díru
SNAP_SLOT_L= 6.0    # délka zářezů
TIRE_CLR   = 0.1    # vůle mezi obručí a nábojem (TPU se navléká s předpětím)
# --------------------------------------------

R_OUT   = D_OUT / 2
R_SEAT  = R_OUT - T_TIRE          # dosedací poloměr obruče na náboji
R_FLNG  = R_SEAT + FLANGE_H       # poloměr bočních lemů
R_RIMIN = R_SEAT - RIM_T
BORE_D  = AXLE_D + BORE_CLR
TIRE_W  = W - 2 * FLANGE_W


def ring(r_out, r_in, h, z0=0.0):
    return (cq.Workplane("XY").workplane(offset=z0)
            .circle(r_out).circle(r_in).extrude(h))


def make_hub():
    # věnec + boční lemy
    hub = ring(R_SEAT, R_RIMIN, W)
    hub = hub.union(ring(R_FLNG, R_RIMIN, FLANGE_W))
    hub = hub.union(ring(R_FLNG, R_RIMIN, FLANGE_W, W - FLANGE_W))
    # podélné klíny proti protočení obruče
    for i in range(N_KEYS):
        key = (cq.Workplane("XY")
               .center(R_SEAT + KEY_H / 2 - 0.3, 0)
               .rect(KEY_H + 0.6, KEY_W).extrude(W)
               .rotate((0, 0, 0), (0, 0, 1), i * 360 / N_KEYS))
        hub = hub.union(key)
    # čelní stěna (z = 0, tisknout touto stranou dolů)
    hub = hub.union(ring(R_RIMIN + 0.5, BOSS_D / 2 - 0.5, FACE_T))
    # žebra
    for i in range(N_RIBS):
        rib = (cq.Workplane("XY")
               .center((BOSS_D / 2 + R_RIMIN) / 2, 0)
               .rect(R_RIMIN - BOSS_D / 2 + 1.0, RIB_T).extrude(W - 1.0)
               .rotate((0, 0, 0), (0, 0, 1), i * 360 / N_RIBS + 360 / N_RIBS / 2))
        hub = hub.union(rib)
    # středové pouzdro
    boss_len = W + BOSS_EXT
    hub = hub.union(cq.Workplane("XY").circle(BOSS_D / 2).extrude(boss_len))
    hub = hub.cut(cq.Workplane("XY").circle(BORE_D / 2).extrude(boss_len))
    # sražení vstupu díry
    hub = hub.cut(cq.Workplane("XY").workplane(offset=boss_len - 0.8)
                  .circle(BORE_D / 2).workplane(offset=0.8)
                  .circle(BORE_D / 2 + 0.8).loft())

    if SNAP:
        # 4 zářezy + zobáček dovnitř na konci pouzdra
        for a in (0, 90):
            slot = (cq.Workplane("XY").workplane(offset=boss_len - SNAP_SLOT_L)
                    .rect(BOSS_D + 2, 1.2).extrude(SNAP_SLOT_L)
                    .rotate((0, 0, 0), (0, 0, 1), a))
            hub = hub.cut(slot)
        lip = ring(BORE_D / 2, BORE_D / 2 - SNAP_LIP, 1.5, boss_len - 2.5)
        cut_slots = None
        for a in (0, 90):
            s = (cq.Workplane("XY").workplane(offset=boss_len - SNAP_SLOT_L)
                 .rect(BOSS_D + 2, 1.2).extrude(SNAP_SLOT_L)
                 .rotate((0, 0, 0), (0, 0, 1), a))
            cut_slots = s if cut_slots is None else cut_slots.union(s)
        hub = hub.union(lip.cut(cut_slots))
    return hub


def make_tire():
    r_in = R_SEAT + TIRE_CLR
    tire = ring(R_OUT, r_in, TIRE_W)
    # drážky pro klíny náboje
    for i in range(N_KEYS):
        g = (cq.Workplane("XY")
             .center(r_in + (KEY_H + 0.2) / 2 - 0.3, 0)
             .rect(KEY_H + 0.2 + 0.6, KEY_W + 0.3).extrude(TIRE_W)
             .rotate((0, 0, 0), (0, 0, 1), i * 360 / N_KEYS))
        tire = tire.cut(g)
    # zaoblené hrany běhounu
    tire = tire.edges(cq.selectors.RadiusNthSelector(-1)).fillet(1.2)
    return tire


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for name, part in (("kolecko_naboj", make_hub()), ("kolecko_pneu", make_tire())):
        cq.exporters.export(part, os.path.join(here, name + ".step"))
        cq.exporters.export(part, os.path.join(here, name + ".stl"),
                            tolerance=0.02, angularTolerance=0.1)
        bb = part.val().BoundingBox()
        print(f"{name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
