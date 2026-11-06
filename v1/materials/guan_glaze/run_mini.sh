#!/bin/bash
# queue a card render on the mini (CPU, tools/mini-pbrt.sh): run_mini.sh <card dir> [pbrt options]
# copies the dir to ~/gewu-render/scenes/guan_glaze-<name>, queues, and returns; the log is /tmp/gewu-guan_glaze-<name>.log
set -eu
d=$1; shift
n=$(basename "$d")
ssh link "mkdir -p ~/gewu-render/scenes/guan_glaze-$n"
scp -q "$d"/*.ply "$d"/*.exr "$d"/scene.pbrt "$d"/optics.json link:gewu-render/scenes/guan_glaze-$n/ 2>/dev/null || scp -q "$d"/*.ply "$d"/h.exr "$d"/scene.pbrt "$d"/optics.json link:gewu-render/scenes/guan_glaze-$n/
ssh link "cd ~ && nohup ~/gewu-render/bin/mini-pbrt.sh ~/gewu-render/scenes/guan_glaze-$n scene.pbrt /tmp/gewu-guan_glaze-$n.log $* > /dev/null 2>&1 & echo queued $n"
