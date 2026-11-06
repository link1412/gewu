#!/bin/zsh
# Run one Blender (Cycles) job on the mini's GPU, taking turns with shici's GPU renders:
#  - shici's renders hold /tmp/mini-render.lock (mkdir is atomic; a lock whose owner is gone is cleared), and two
#    GPU renders at once starve the window server: wait for that lock and for no tools/render.mjs to be running;
#  - while ours runs, watch for a new WindowServer or panic report and kill it at once (shici's guard: the
#    watchdog panics the machine about a minute after that report);
#  - nice 10. Our CPU lock (/tmp/gewu-render.lock, mini-pbrt.sh) is separate: a pbrt job may run alongside.
# usage: mini-gpu.sh <log> <blender args...>     the log's last line: done <exit code> <seconds>
log=$1; shift
lock=/tmp/mini-render.lock
B=/Applications/Blender.app/Contents/MacOS/Blender
n=0
while true; do
  if mkdir $lock 2>/dev/null; then
    echo $$ > $lock/pid
    if pgrep -f "tools/render.mjs" >/dev/null; then rm -rf $lock; else break; fi
  else
    p=$(cat $lock/pid 2>/dev/null)
    if [ -n "$p" ] && ! kill -0 $p 2>/dev/null; then rm -rf $lock; continue; fi
  fi
  sleep 4; n=$((n+1)); [ $n -gt 1800 ] && { echo "WAITED-OUT"; echo "done 4 0"; } >> $log && exit 4
done
trap 'rm -rf $lock' EXIT
reports() { ls /Library/Logs/DiagnosticReports 2>/dev/null | grep -c -E "WindowServer|panic"; }
before=$(reports)
start=$(date +%s)
nice -n 10 $B "$@" >> $log 2>&1 &
pid=$!
while kill -0 $pid 2>/dev/null; do
  if [ "$(reports)" != "$before" ]; then
    kill $pid 2>/dev/null
    { echo "GUARD: window server report appeared; render killed"; echo "done 5 $(( $(date +%s) - start ))"; } >> $log
    exit 5
  fi
  sleep 2
done
wait $pid
rc=$?
echo "done $rc $(( $(date +%s) - start ))" >> $log
