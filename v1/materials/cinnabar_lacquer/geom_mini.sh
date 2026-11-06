#!/bin/bash
# Build a card's geometry on the mini in a CPU slot: geom_mini.sh <run name> [card.py geom options]
# Copies the code it needs (card.py, lacquer.py, material.json, crafts/carving/*.py) to ~/gewu-render/carving-code/,
# runs 'card.py geom --out ~/gewu-render/scenes/carving/<run>/geom' there; the log is /tmp/gewu-carving-<run>-geom.log.
# card.py looks for the photo's measurement (out/materials/cinnabar_lacquer/measured_cma.json) only in 'scene'.
set -eu
run=$1; shift
C=gewu-render/carving-code
ssh link "mkdir -p ~/$C/materials/cinnabar_lacquer ~/$C/crafts/carving ~/gewu-render/scenes/carving/$run"
scp -q materials/cinnabar_lacquer/{card.py,lacquer.py,material.json} link:$C/materials/cinnabar_lacquer/
scp -q crafts/carving/{carve.py,patterns.py} link:$C/crafts/carving/
ssh link "cd ~ && nohup ~/gewu-render/bin/mini-cpu.sh /tmp/gewu-carving-$run-geom.log run ~/$C python3 -I materials/cinnabar_lacquer/card.py geom --out ~/gewu-render/scenes/carving/$run/geom $* > /dev/null 2>&1 & echo queued geom $run"
