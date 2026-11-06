#!/bin/sh
# Put the music on the film. The picture is copied, not encoded again: it takes seconds and changes no frame.
#     sh v2/music/bake.sh [VIDEO] [MIX] [OUT]
# Defaults: out/v2/film/film.mp4, out/v2/music/mix_G_mit3.wav, out/v2/film/film_music.mp4
# If the cut has changed since the mix was rendered, the mix no longer matches the cut: the lengths are compared here and a mismatch is an error.
set -eu
cd "$(dirname "$0")/../.."
V=${1:-out/v2/film/film.mp4}
M=${2:-out/v2/music/mix_G_mit3.wav}
O=${3:-out/v2/film/film_music.mp4}
len() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }
python3 -I -c "import sys; a, b = float(sys.argv[1]), float(sys.argv[2]); abs(a - b) < 0.05 or sys.exit(f'video {a:.3f} s, music {b:.3f} s: the mix does not match this cut')" "$(len "$V")" "$(len "$M")"
ffmpeg -v error -y -i "$V" -i "$M" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k -movflags +faststart "$O"
echo "$O"
