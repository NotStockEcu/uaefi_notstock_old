"""
Dvoudílné kolečko k vysavači – parametrický model (CadQuery).
  naboj = vnitřní náboj z tvrdého plastu (PETG / ASA)
  pneu  = obruč z měkkého materiálu (TPU 85A–95A)
  kryt  = jen pokud DOME_SEPARATE = True: kopule zvlášť (nalepí se do náboje)

Spuštění:  pip install cadquery && python3 kolecko.py
Vytvoří STEP + STL do stejné složky. Všechny rozměry v mm.

Osa Z: z = 0 je čelo kolečka (venkovní strana s kopulí),
       z = W je vnitřní strana, odkud vyčnívá pouzdro se zácvakem.
"""
import os
import cadquery as cq

# ---------------- PARAMETRY ----------------
D_OUT      = 64.0   # vnější průměr celého kolečka
W          = 25.0   # šířka kolečka (bez vyčnívajícího pouzdra)
T_TIRE     = 5.0    # tloušťka měkké obruče na běhounu (radiálně)
# --- čelo (vzor jako originál: gumový lem, tmavá drážka, lesklá kopule) ---
LIP_T      = 2.5    # tloušťka předního gumového lemu (osově)
LIP_RIN    = 24.5   # vnitřní poloměr předního gumového lemu
FRONT_FIL  = 2.5    # zaoblení přední hrany pneu
GROOVE_W   = 2.5    # šířka drážky mezi gumou a kopulí (radiálně)
DOME_H     = 2.5    # výška kopule (vrchol je v rovině čela gumy)
DOME_SEPARATE = False  # True = kopule jako samostatný díl (tiskne se naplocho, lesklejší)
# --- náboj ---
FLANGE_H   = 2.0    # zadní lem náboje (drží obruč) – o kolik je nad dosedací plochou
FLANGE_W   = 2.0    # šířka zadního lemu
RIM_T      = 2.5    # tloušťka věnce náboje
FACE_T     = 2.0    # tloušťka čelní stěny náboje (za kopulí)
N_RIBS     = 8      # počet žeber
RIB_T      = 1.8    # tloušťka žebra
N_KEYS     = 12     # podélné klíny proti protáčení obruče
KEY_H      = 0.8    # výška klínu
KEY_W      = 2.0    # šířka klínu
AXLE_D     = 7.0    # průměr osy
BORE_CLR   = 0.3    # vůle díry na ose (7.3 mm díra)
BORE_THROUGH = False  # False = díra slepá (čelo zavřené jako originál)
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
R_FLNG  = R_SEAT + FLANGE_H       # poloměr zadního lemu
R_RIMIN = R_SEAT - RIM_T
R_DOME  = LIP_RIN - GROOVE_W      # poloměr kopule
Z_PLATE = LIP_T                   # přední plocha čelní stěny náboje
BORE_D  = AXLE_D + BORE_CLR
TIRE_W  = W - FLANGE_W            # pneu jde od čela až k zadnímu lemu


def ring(r_out, r_in, h, z0=0.0):
    return (cq.Workplane("XY").workplane(offset=z0)
            .circle(r_out).circle(r_in).extrude(h))


def make_dome(z_base):
    """Kulový vrchlík: základna v rovině z_base, vrchol o DOME_H blíž k čelu."""
    rs = (R_DOME ** 2 + DOME_H ** 2) / (2 * DOME_H)          # poloměr koule
    ball = cq.Workplane("XY").sphere(rs).translate((0, 0, z_base - DOME_H + rs))
    box = cq.Workplane("XY").box(2 * R_DOME + 2, 2 * R_DOME + 2, DOME_H,
                                 centered=(True, True, False)).translate((0, 0, z_base - DOME_H))
    return ball.intersect(box)


def make_hub():
    # věnec + zadní lem
    hub = ring(R_SEAT, R_RIMIN, W - Z_PLATE, Z_PLATE)
    hub = hub.union(ring(R_FLNG, R_RIMIN, FLANGE_W, W - FLANGE_W))
    # podélné klíny proti protočení obruče
    for i in range(N_KEYS):
        key = (cq.Workplane("XY").workplane(offset=Z_PLATE)
               .center(R_SEAT + KEY_H / 2 - 0.3, 0)
               .rect(KEY_H + 0.6, KEY_W).extrude(W - Z_PLATE)
               .rotate((0, 0, 0), (0, 0, 1), i * 360 / N_KEYS))
        hub = hub.union(key)
    # čelní stěna – celá zavřená
    hub = hub.union(ring(R_RIMIN + 0.5, 0.01, FACE_T, Z_PLATE))
    # kopule vpředu
    if not DOME_SEPARATE:
        hub = hub.union(make_dome(Z_PLATE))
    else:
        # mělké vybrání pro nalepení kopule (vystředění)
        hub = hub.cut(ring(R_DOME + 0.15, 0.01, 0.6, Z_PLATE))
    # žebra
    for i in range(N_RIBS):
        rib = (cq.Workplane("XY").workplane(offset=Z_PLATE)
               .center((BOSS_D / 2 + R_RIMIN) / 2, 0)
               .rect(R_RIMIN - BOSS_D / 2 + 1.0, RIB_T).extrude(W - 1.0 - Z_PLATE)
               .rotate((0, 0, 0), (0, 0, 1), i * 360 / N_RIBS + 360 / N_RIBS / 2))
        hub = hub.union(rib)
    # středové pouzdro
    boss_len = W + BOSS_EXT
    z_split = boss_len - SNAP_L if SNAP else boss_len
    hub = hub.union(cq.Workplane("XY").workplane(offset=Z_PLATE)
                    .circle(BOSS_D / 2).extrude(z_split - Z_PLATE))
    if SNAP:
        hub = hub.union(ring(SNAP_OD / 2, BORE_D / 2, SNAP_L, z_split))
    z_bore = 0 if BORE_THROUGH else Z_PLATE + FACE_T
    hub = hub.cut(cq.Workplane("XY").workplane(offset=z_bore - DOME_H - 1)
                  .circle(BORE_D / 2).extrude(boss_len - z_bore + DOME_H + 1)
                  if BORE_THROUGH else
                  cq.Workplane("XY").workplane(offset=z_bore)
                  .circle(BORE_D / 2).extrude(boss_len - z_bore))

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


def circle_edge(shape, r, z):
    """Vybere kruhovou hranu o poloměru r v rovině z."""
    return [e for e in shape.Edges()
            if e.geomType() == "CIRCLE" and abs(e.radius() - r) < 0.05
            and abs(e.Center().z - z) < 0.05]


def make_tire():
    r_in = R_SEAT + TIRE_CLR
    # běhoun + přední lem přetažený přes čelo náboje
    tire = ring(R_OUT, r_in, TIRE_W)
    tire = tire.union(ring(R_OUT, LIP_RIN, LIP_T))
    # drážky pro klíny náboje
    for i in range(N_KEYS):
        g = (cq.Workplane("XY").workplane(offset=LIP_T)
             .center(r_in + (KEY_H + 0.2) / 2 - 0.3, 0)
             .rect(KEY_H + 0.2 + 0.6, KEY_W + 0.3).extrude(TIRE_W - LIP_T)
             .rotate((0, 0, 0), (0, 0, 1), i * 360 / N_KEYS))
        tire = tire.cut(g)
    # zaoblení: přední hrana výrazně (jako originál), zadní mírně, vnitřní hrana lemu
    t = tire.val().Solids()[0]
    t = t.fillet(FRONT_FIL, circle_edge(t, R_OUT, 0))
    t = t.fillet(1.2, circle_edge(t, R_OUT, TIRE_W))
    t = t.fillet(0.8, circle_edge(t, LIP_RIN, 0))
    tire = cq.Workplane("XY").add(t)
    return tire


def make_cap():
    # samostatná kopule, tiskne se plochou stranou dolů
    cap = make_dome(DOME_H).translate((0, 0, -DOME_H))     # z: -DOME_H..0
    cap = cap.union(cq.Workplane("XY").circle(R_DOME).extrude(0.6))
    return cap.mirror("XY").translate((0, 0, 0.6))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    parts = [("kolecko_naboj", make_hub()), ("kolecko_pneu", make_tire())]
    if DOME_SEPARATE:
        parts.append(("kolecko_kryt", make_cap()))
    for name, part in parts:
        cq.exporters.export(part, os.path.join(here, name + ".step"))
        cq.exporters.export(part, os.path.join(here, name + ".stl"),
                            tolerance=0.02, angularTolerance=0.1)
        bb = part.val().BoundingBox()
        print(f"{name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, "
              f"z {bb.zmin:.1f}..{bb.zmax:.1f}, valid={part.val().isValid()}")
