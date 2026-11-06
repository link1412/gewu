#!/bin/bash
# Run one Blender (Cycles) job on the GPU (mini-gpu.sh: one job at a time, shared with shici), or on a CPU slot
# (mini-cpu.sh) when the GPU stays busy, so previews do not queue behind a long GPU job. Measured S3 on a simple
# scene: 960x540 at 512 spp takes 7 s on the GPU and 66 s on a 4-thread CPU slot (slots have all 12 threads since S5,
# about 2.3x faster when alone), so it waits GEWU_GPU_WAIT seconds (default 10) for the GPU before it takes a CPU
# slot. A heavy render should go to mini-gpu.sh directly.
#   mini-cycles.sh <log> <blender args...>          the same arguments as mini-gpu.sh
# The log's last line is "done <exit code> <seconds>"; a line "slot /tmp/gewu-cpu.N" at the top means it ran on
# the CPU. The two devices agree statistically, not bit for bit: a same-seed comparison needs one device.
log=$1; shift
: > "$log"
slots=${GEWU_CPU_SLOTS:-3}
deadline=$(( $(date +%s) + ${GEWU_GPU_WAIT:-10} ))
while true; do
  if [ ! -d /tmp/mini-render.lock ] && ! pgrep -f "tools/render.mjs" >/dev/null; then
    exec ~/gewu-render/bin/mini-gpu.sh "$log" "$@"
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    for i in $(seq 0 $((slots - 1))); do
      [ -d /tmp/gewu-cpu.$i ] || exec ~/gewu-render/bin/mini-cpu.sh "$log" blender "$@"
    done
  fi
  sleep 2
done
