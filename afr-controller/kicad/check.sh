#!/bin/sh
# Regenerates the schematic and validates it with kicad-cli (KiCad 7 needs a down-converted copy).
set -e
cd "$(dirname "$0")"; T=$(mktemp -d)
python3 gen_frontend.py afr_frontend.kicad_sch --pins
sed -e 's/(version 20231120)/(version 20230121)/' -e 's/ (exclude_from_sim no)//g' -e 's/ (generator_version "1.0")//' afr_frontend.kicad_sch > $T/v7.kicad_sch
kicad-cli sch export netlist --format kicadsexpr -o $T/v7.net $T/v7.kicad_sch
python3 check_netlist.py $T/v7.net afr_frontend.kicad_sch.pins.json
python3 check_footprints.py afr_frontend.kicad_sch
rm -f afr_frontend.kicad_sch.pins.json
