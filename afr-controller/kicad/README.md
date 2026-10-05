# KiCad: LSU 4.9 front-end + napájení + CAN + výstup 0–5 V

`afr_frontend.kicad_sch` se **generuje** skriptem `gen_frontend.py` (zapojení podle rusEFI/FOME wideband modulu rev C, MIT).
Piny jsou propojené síťovými štítky, ne dráty. V KiCadu schéma po otevření uspořádejte; ruční úpravy se při
dalším spuštění generátoru přepíšou, proto upravujte buď skript, nebo po prvním ručním uspořádání už generátor nepoužívejte.

- `./check.sh` – přegeneruje schéma a ověří ho `kicad-cli` (netlist z KiCadu se porovná se zamýšleným zapojením všech
  očíslovaných pinů). Vyžaduje KiCad 7 nebo novější (`kicad-cli`).
- `afr_frontend_preview.pdf` – náhled (export z KiCadu).

ERC v KiCadu 10: druhý běh 0 chyb a 4 varování (neexistující jména footprintů) – opraveno, footprinty teď existují v knihovnách KiCadu 7. První běh hlásil 3 chyby (nenapájené sítě) a 144 varování (chybějící knihovna `Local`). Obojí je opravené (PWR_FLAG, `sym-lib-table` + `afr_local.kicad_sym`); po opravě ERC ještě neběžel.
Neověřeno: simulace, měření na sondě.
Piny a hodnoty TPS54202, pinout konektoru LSU a trim odpor sondy ověřit podle datasheetů.

## Kontroly
- `check_netlist.py` – netlist z KiCadu vs. zamýšlené zapojení + pravidlo „napájecí vstup bez zdroje".
- `check_footprints.py` – každé číslo pinu symbolu má pad ve footprintu.
- **Co kontroly nepokryjí:** zda číslo pinu odpovídá skutečnému pinoutu dílu. Z paměti a neověřeno: REF3033 (SOT-23-3), TPS54202 (SOT-23-6),
  VND14NV04 (footprint TO-252-2 je placeholder), P-MOSFET (hodnota je zástupná, SOT-23 G1/S2/D3), konektor sondy LSU.
- Diody: pin 1 = katoda, pin 2 = anoda (konvence KiCadu a footprintů D_SOD-323 / D_SMB).
