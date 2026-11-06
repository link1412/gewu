#!/bin/bash
# Wait for card frames on the mini, pull x.exr, develop and compare: pull.sh <run dir> <frame> [<frame> ...]
# (exposure: each frame's camera.json, written by 'card.py scene --raw-ref')
set -u
d=$1; shift
run=$(basename "$d")
for f in "$@"; do
  ssh link "L=/tmp/gewu-carving-$run-$f.log; while ! tail -1 \$L 2>/dev/null | grep -q '^done'; do sleep 5; done; tail -1 \$L"
  scp -q link:gewu-render/scenes/carving/$run/$f/x.exr "$d/$f/" || { echo "$f: no x.exr"; continue; }
  python3 -I materials/cinnabar_lacquer/card.py develop "$d/$f" > /dev/null
  python3 -I materials/cinnabar_lacquer/card.py compare "$d/$f" > /dev/null && echo "$f compared"
done
