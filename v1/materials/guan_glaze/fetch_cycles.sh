#!/bin/bash
# Wait for a run_cycles.sh job on the mini and copy its renders back: fetch_cycles.sh TAG DIR...
set -eu
tag=$1; shift
R=gewu-render/scenes/guan2-$tag
ssh link "while [ ! -f ~/$R/DONE ]; do sleep 15; done; cat ~/$R/times.txt"
for d in "$@"; do
  n=$(basename "$d")
  scp -q "link:$R/$n/cyc*.exr" "$d/" || echo "no renders for $n"
  scp -q "link:$R/$n/cyc*.json" "$d/" 2>/dev/null || true
done
