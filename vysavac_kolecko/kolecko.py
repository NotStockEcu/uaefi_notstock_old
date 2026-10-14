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
# --- zácvak na osu (jako originál: 4 pružné prsty se zobáčkem dovnitř) ---
SNAP       = True   # False = hladká díra bez zácvaku
SNAP_N     = 4      # počet prstů
SNAP_L     = 10.0   # délka prstů (od konce pouzdra)
SNAP_OD    = 10.5   # vnější průměr pouzdra v oblasti prstů (tenčí stěna = pružnější)
SNAP_SLOT  = 1.2    # šířka zářezu mezi prsty
SNAP_ID    = 6.0    # vnitřní průměr zobáčku (= průměr dna drážky na ose, spíš o 0,1–0,2 menší)
SNAP_LIP_W = 1.5    # šířka zobáčku (= šířka drážky na ose, o 0,2 menší)
SNAP_POS   = 0.0    # vzdálenost zobáčku od konce pouzdra
SNAP_LEAD  = 1.0    # náběh (zkosení) na vstupu, aby osa prsty rozevřela
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
    z_split = boss_len - SNAP_L if SNAP else boss_len
    hub = hub.union(cq.Workplane("XY").circle(BOSS_D / 2).extrude(z_split))
    if SNAP:
        hub = hub.union(cq.Workplane("XY").workplane(offset=z_split - 1.0)
                        .circle(BOSS_D / 2).workplane(offset=1.0)
                        .circle(SNAP_OD / 2).loft())
        hub = hub.union(ring(SNAP_OD / 2, BORE_D / 2, SNAP_L, z_split))
    hub = hub.cut(cq.Workplane("XY").circle(BORE_D / 2).extrude(boss_len))

    if SNAP:
        # žebra nesmí držet prsty – vyříznout kolem prstů mezeru
        hub = hub.cut(ring(SNAP_OD / 2 + 1.0, SNAP_OD / 2, boss_len, z_split))
        # zobáček dovnitř: náběh ze strany vstupu osy, rovná zadní plocha
        z_lip_top = boss_len - SNAP_POS
        z_lip_bot = z_lip_top - SNAP_LIP_W
        lead = min(SNAP_LEAD, SNAP_LIP_W - 0.3)
        lip = (cq.Workplane("XZ")
               .polyline([(SNAP_ID / 2, z_lip_bot),
                          (BORE_D / 2 + 0.01, z_lip_bot),
                          (BORE_D / 2 + 0.01, z_lip_top),
                          (BORE_D / 2 - 0.05, z_lip_top),
                          (SNAP_ID / 2, z_lip_top - lead)]).close()
               .revolve(360, (0, 0, 0), (0, 1, 0)))
        hub = hub.union(lip)
        # zářezy mezi prsty
        for i in range(SNAP_N):
            slot = (cq.Workplane("XY").workplane(offset=z_split)
                    .center(SNAP_OD / 2, 0).rect(SNAP_OD, SNAP_SLOT)
                    .extrude(SNAP_L + 1)
                    .rotate((0, 0, 0), (0, 0, 1), i * 360 / SNAP_N + 45))
            hub = hub.cut(slot)
    else:
        # sražení vstupu díry
        hub = hub.cut(cq.Workplane("XY").workplane(offset=boss_len - 0.8)
                      .circle(BORE_D / 2).workplane(offset=0.8)
                      .circle(BORE_D / 2 + 0.8).loft())
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
