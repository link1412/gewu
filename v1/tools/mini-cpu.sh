#!/bin/bash
# Run one CPU job on the Mac mini (M4 Pro: 8 performance + 4 efficiency cores) in one of several CPU slots, so
# several gewu jobs share the cores at once instead of queueing. The GPU stays one job at a time (mini-gpu.sh,
# shared with shici). Slots are /tmp/gewu-cpu.<i> (mkdir is atomic; a slot whose owner is gone is cleared); each
# job gets THREADS threads and runs niced, so shici's renders and our GPU job keep their share.
# THREADS is all the cores: a job alone uses the whole machine and the system shares the cores when several run.
# Measured S5 (pbrt, the Guan card at 480x270, 64 spp): alone, 4 threads 44 s, 12 threads 19 s; three at once,
# 3 x 4 threads 58 s, 3 x 12 threads 57 s. So fixed 4-thread slots only left cores idle when fewer jobs ran.
#   mini-cpu.sh <log> pbrt <dir> <scene.pbrt> [pbrt options...]   pbrt with --nthreads THREADS, run in <dir>
#   mini-cpu.sh <log> blender <blender args...>                    Blender with -t THREADS, Cycles on the CPU
#                                                                  (--device CPU is appended to the script's args)
#   mini-cpu.sh <log> run <dir> <command...>                       anything else, e.g. python3 -I sim.py, in <dir>
# The log is emptied first; its last line is "done <exit code> <seconds>".
# GEWU_CPU_SLOTS (default 3) and GEWU_CPU_THREADS (default: all cores) override; mini-cycles.sh reads the slots.
set -u
log=$1; kind=$2; shift 2
slots=${GEWU_CPU_SLOTS:-3}
threads=${GEWU_CPU_THREADS:-$(sysctl -n hw.ncpu)}
B=/Applications/Blender.app/Contents/MacOS/Blender
: > "$log"
slot=""
while [ -z "$slot" ]; do
  for i in $(seq 0 $((slots - 1))); do
    d=/tmp/gewu-cpu.$i
    if mkdir "$d" 2>/dev/null; then
      echo $$ > "$d/pid"; slot=$d; break
    fi
    p=$(cat "$d/pid" 2>/dev/null)
    if [ -n "$p" ]; then
      kill -0 "$p" 2>/dev/null || rm -rf "$d"
    elif [ -n "$(find "$d" -maxdepth 0 -mmin +1 2>/dev/null)" ]; then
      rm -rf "$d"                       # made but never given a pid (its owner died at once)
    fi
  done
  [ -z "$slot" ] && sleep 3
done
trap 'rm -rf "$slot"' EXIT
start=$(date +%s)
echo "slot $slot, $threads threads, $(date)" >> "$log"
case $kind in
  pbrt)
    dir=$1; scene=$2; shift 2
    cd "$dir" && nice -n 10 ~/gewu-render/bin/pbrt --quiet --nthreads "$threads" "$@" "$scene" >> "$log" 2>&1 ;;
  blender)
    nice -n 10 "$B" -t "$threads" "$@" --device CPU >> "$log" 2>&1 ;;
  run)
    dir=$1; shift
    cd "$dir" && nice -n 10 "$@" >> "$log" 2>&1 ;;
  *)
    echo "mini-cpu.sh: unknown kind $kind (pbrt, blender, run)" >> "$log"; false ;;
esac
rc=$?
echo "done $rc $(( $(date +%s) - start ))" >> "$log"
