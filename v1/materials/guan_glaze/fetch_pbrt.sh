#!/bin/bash
# Wait for run_pbrt.sh jobs and copy raw.exr back into each DIR: fetch_pbrt.sh TAG DIR...
set -eu
tag=$1; shift
for d in "$@"; do
  n=$(basename "$d")
  log=/tmp/gewu-guan2p-$tag-$n.log
  ssh link "while ! tail -1 $log 2>/dev/null | grep -q '^done'; do sleep 20; done; tail -1 $log"
  scp -q link:gewu-render/scenes/guan2p-$tag/$n/raw.exr "$d/raw.exr"
  echo fetched "$d/raw.exr"
done
