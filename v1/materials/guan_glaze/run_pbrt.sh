#!/bin/bash
# Render card scenes with pbrt on the mini's CPU slots (round 2; pbrt is the reference: see docs/materials/guan_glaze.md,
# "Cycles and pbrt"): run_pbrt.sh TAG "PBRT OPTIONS" DIR...
#   copies each DIR (scene.pbrt and its meshes and maps) to ~/gewu-render/scenes/guan2p-TAG/<name>/ and queues one
#   mini-pbrt.sh job per DIR (they take CPU slots as they free up); each writes raw.exr there and its log
#   /tmp/gewu-guan2p-TAG-<name>.log ends with "done <code> <seconds>". Fetch with fetch_pbrt.sh TAG DIR...
# e.g. run_pbrt.sh c1 "--spp 256 --seed 1" out/materials/guan_glaze/r2/excavated_s1
set -eu
tag=$1; opts=$2; shift 2
R=gewu-render/scenes/guan2p-$tag
for d in "$@"; do
  n=$(basename "$d")
  ssh link "mkdir -p ~/$R/$n && rm -f ~/$R/$n/raw.exr"
  (cd "$d" && scp -q scene.pbrt $(ls *.ply *.exr 2>/dev/null | grep -v '^raw' | grep -v '^cyc' || true) link:$R/$n/)
  ssh link "cd ~ && nohup ~/gewu-render/bin/mini-pbrt.sh ~/$R/$n scene.pbrt /tmp/gewu-guan2p-$tag-$n.log $opts > /dev/null 2>&1 & echo queued $tag $n"
done
