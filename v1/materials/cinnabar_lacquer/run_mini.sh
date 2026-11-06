#!/bin/bash
# Queue Cycles renders of card frames on the mini: run_mini.sh <run dir> <spp> <frame> [<frame> ...] [-- extra cycles_scene args]
# <run dir> holds geom/ (meshes, maps) and one dir per frame (scene.cycles.json from tools/rgbscene.py). It is rsynced
# to ~/gewu-render/scenes/carving/<run>/ (geom/*.ply only if missing there: they are built on the mini by geom_mini.sh),
# then each frame goes to mini-cycles.sh (GPU, else a CPU slot) with the test copy of cycles_scene.py
# (~/gewu-render/tools-test-carving/). Logs: /tmp/gewu-carving-<run>-<frame>.log; results <frame>/x.exr there.
set -eu
d=$1; spp=$2; shift 2
run=$(basename "$d")
frames=(); extra=()
while [ $# -gt 0 ]; do
  if [ "$1" = "--" ]; then shift; extra=("$@"); break; fi
  frames+=("$1"); shift
done
R=gewu-render/scenes/carving/$run
ssh link "mkdir -p ~/$R ~/gewu-render/tools-test-carving"
scp -q tools/cycles_scene.py link:gewu-render/tools-test-carving/cycles_scene.py
rsync -a --exclude 'dev/' --exclude 'cmp/' --exclude '*.exr' --exclude '*.ply' "$d"/ link:$R/
for f in "${frames[@]}"; do
  ssh link "cd ~/$R/$f && nohup ~/gewu-render/bin/mini-cycles.sh /tmp/gewu-carving-$run-$f.log -b --factory-startup --python-exit-code 1 -P ~/gewu-render/tools-test-carving/cycles_scene.py -- scene.cycles.json --out \$PWD/x.exr --spp $spp ${extra[*]:-} > /dev/null 2>&1 & echo queued $run/$f"
done
