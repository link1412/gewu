#!/bin/bash
# Run one pbrt render on the Mac mini, in one of the CPU slots (mini-cpu.sh: several gewu CPU jobs at once, each
# with its share of the cores, niced so shici's GPU renders on the same machine keep their CPU).
#   ~/gewu-render/bin/mini-pbrt.sh <dir> <scene.pbrt> <log> [pbrt options...]
# The log's last line is "done <exit code> <seconds>".
dir=$1; scene=$2; log=$3; shift 3
exec ~/gewu-render/bin/mini-cpu.sh "$log" pbrt "$dir" "$scene" "$@"
