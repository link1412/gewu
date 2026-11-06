#!/bin/bash
# Render card scenes with Cycles on the mini (round 2): run_cycles.sh TAG "SEEDS" "CYCLES OPTIONS" DIR...
#   copies each DIR (scene.cycles.json and its meshes and maps) to ~/gewu-render/scenes/guan2-TAG/<name>/, then one
#   background job on the mini renders them one after another through mini-cycles.sh (the GPU, or a CPU slot when
#   the GPU stays busy), each seed to cyc<seed>.exr, with the test copy of cycles_scene.py in
#   ~/gewu-render/tools-test-guan/ (not the shared tools/); the job writes ~/gewu-render/scenes/guan2-TAG/DONE.
#   Fetch with: fetch_cycles.sh TAG DIR...
#   LANE=cpu run_cycles.sh ...: straight to a CPU slot (mini-cpu.sh), for long renders while the GPU is wanted
#   elsewhere; the default is mini-cycles.sh (the GPU, or a CPU slot after 10 s).
# e.g. run_cycles.sh lt1 "1 2" "--spp 512" out/materials/guan_glaze/lt/gap_v out/materials/guan_glaze/lt/dep_v
set -eu
tag=$1; seeds=$2; opts=$3; shift 3
R=gewu-render/scenes/guan2-$tag
ssh link "mkdir -p ~/gewu-render/tools-test-guan ~/$R && rm -f ~/$R/DONE"
scp -q "$(dirname "$0")/../../tools/cycles_scene.py" link:gewu-render/tools-test-guan/cycles_scene.py
if [ "${LANE:-}" = cpu ]; then runner=mini-cpu.sh; kind=blender; else runner=mini-cycles.sh; kind=""; fi
names=""
for d in "$@"; do
  n=$(basename "$d")
  ssh link "mkdir -p ~/$R/$n"
  (cd "$d" && scp -q scene.cycles.json $(ls *.ply *.exr *.npz 2>/dev/null | grep -v '^cyc' | grep -v '^raw' || true) link:$R/$n/)
  names="$names $n"
done
ssh link "cat > ~/$R/job.sh" <<EOF
cd ~/$R
for n in $names; do
  for s in $seeds; do
    ~/gewu-render/bin/$runner /tmp/gewu-guan2-$tag-\$n-\$s.log $kind -b --factory-startup --python-exit-code 1 \
      -P ~/gewu-render/tools-test-guan/cycles_scene.py -- \$PWD/\$n/scene.cycles.json --out \$PWD/\$n/cyc\$s.exr --seed \$s $opts
    tail -1 /tmp/gewu-guan2-$tag-\$n-\$s.log | sed "s/^/\$n \$s /" >> times.txt
  done
done
echo done > DONE
EOF
ssh link "cd ~/$R && nohup bash job.sh > job.log 2>&1 & echo queued $tag:$names"
