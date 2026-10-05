# KiCad: LSU 4.9 front-end + napájení + CAN + výstup 0–5 V

`afr_frontend.kicad_sch` se **generuje** skriptem `gen_frontend.py` (zapojení podle rusEFI/FOME wideband modulu rev C, MIT).
Piny jsou propojené síťovými štítky, ne dráty. V KiCadu schéma po otevření uspořádejte; ruční úpravy se při
dalším spuštění generátoru přepíšou, proto upravujte buď skript, nebo po prvním ručním uspořádání už generátor nepoužívejte.

- `./check.sh` – přegeneruje schéma a ověří ho `kicad-cli` (netlist z KiCadu se porovná se zamýšleným zapojením všech
  očíslovaných pinů). Vyžaduje KiCad 7 nebo novější (`kicad-cli`).
- `afr_frontend_preview.pdf` – náhled (export z KiCadu).

Neověřeno: ERC (kicad-cli 7 ho nemá), simulace, měření na sondě.
Piny a hodnoty TPS54202, pinout konektoru LSU a trim odpor sondy ověřit podle datasheetů.
