# Render it yourself

The frames are not in this repository: they are about 15 GB. Each shot's frames can be rendered again from its script, and `v2/film.py` cuts them into the film. This page covers the picture. For the music, see [Known issues](#known-issues).

## Setup

- [Blender](https://www.blender.org/) 5.2.1, with a GPU that Cycles supports
- Python 3.13 (3.12 also works) and `pip install -r requirements.txt`
- FFmpeg, to cut the film and for the proof clips some scripts write; without it those scripts exit with an error after their frames are done
- For `s76_yidi` and `s69_mutan_raw`, torch and an NVIDIA GPU. `s76_yidi` solves its fluid and writes its frames in about 7 minutes on an RTX 5090

On macOS the scripts look for `/Applications/Blender.app` and use Metal. Elsewhere they run `blender` and use OptiX. To change either:

```sh
export GEWU_BLENDER=/path/to/blender
export GEWU_GPU_API=OPTIX   # METAL, OPTIX, CUDA, HIP or ONEAPI
```

## Render

```sh
python3 v2/render_film.py --list              # every shot and whether its frames are there
python3 v2/render_film.py s73_heisan          # one shot
python3 v2/render_film.py --all               # every shot that has no frames yet
python3 v2/film.py --master                   # lossless, out/v2/film/film_master.mkv
python3 v2/film.py --master --en              # the same with English captions
```

`v2/film.py` without `--master` writes an H.264 proof to `out/v2/film/film.mp4`. A shot with no frames yet shows as a labelled grey card, except the last one, which is needed for the end title.

To check a moving shot quickly, render only its first and last frame:

```sh
GEWU_ENDS=1 python3 v2/render_film.py --force s02_yaobian
```

A shot rendered this way counts as not done, so `--all` will render it again in full. Shots averaged from sub-exposures, such as `s15_zheshan` and `s45_kongque`, render their first and last sub-exposure and then stop with an error about the count. That is expected here.

To try a shot at low quality, run its script directly: `python3 v2/stills/s73_heisan.py preview`. The result is in `out/v2/s73_heisan/`. `v2/stills/README.md` lists every script, including the alternate shots that did not make the cut.

Captions use the macOS fonts Songti and Baskerville. On other systems set `GEWU_FONT_SONG` and `GEWU_FONT_LATIN` to your own font files, and `GEWU_FONT_SONG_INDEX` and `GEWU_FONT_LATIN_INDEX` if they are collections.

## How close it comes

Each shot below was rendered again from this repository at final quality and compared with the film's own frames, on an Apple GPU with Metal (Python 3.13) and on an NVIDIA RTX 5090 with OptiX (Python 3.12). Moving shots were compared on their first and last frames, with `GEWU_ENDS=1`, and the lower number is shown. The numbers are PSNR in dB at 1/4 size, where render noise has mostly gone. As a rule of thumb, a difference is hard to see above 40 dB. The 5090 numbers stop at about 80 to 100 because its reference frames were kept as 16-bit floats, so read those as identical.

| Shot | Metal | RTX 5090 |
|---|---|---|
| `s01_moyun` | – | 86.9 |
| `s02_yaobian` | 71.0 | 99.1 |
| `s05_yinni` | 98 | 80.3 |
| `s06_junyao` | 63.9 | 66.6 |
| `s07_cijing` | 117.6 | 78.9 |
| `s09_yinxing` * | – | 45.0 |
| `s11_jiangdou` | 80.3 | 62.7 |
| `s14_datiehua` | 119.6 | 93.1 |
| `s15_zheshan` * | 87.1 | 89.9 |
| `s16_lizhi_v1` | 51.1 | 51.1 |
| `s19_luodian` | 120.4 | 86.1 |
| `s20_denglong` | 51.5 | 51.5 |
| `s24_jianzhi` | 106.8 | 80.9 |
| `s27_jinbo` | 51.6 | 85.2 |
| `s28_dehua` | 85.3 | 85.0 |
| `s30_huali` | 49.1 | 49.1 |
| `s35_kuangcao` | 120.9 | 79.5 |
| `s36_nanzhu` | 49.5 | 49.5 |
| `s37_jinyu` | 56.3 | 56.3 |
| `s38_richu` | 101.6 | 81.1 |
| `s39_hehua` * | 49.6 | 49.6 |
| `s45_kongque` * | 41.2 | 41.2 |
| `s46_luopan` | 60.0 | 60.0 |
| `s49_falang` | 57.0 | 95.4 |
| `s50_qinghua` | 50.3 | 50.3 |
| `s54_zoumadeng` | 116.7, first frame only | 59.2 |
| `s55_diancui` | 72.0 | 94.0 |
| `s59_suxiu` | 83.5 | 81.8 |
| `s61_tihong` | 107.6 | 76.1 |
| `s63_nanhong` | 55.0 | 55.0 |
| `s66_xieyang` | 71.7 | 86.6 |
| `s69_mutan_raw` | – | 41.5 |
| `s73_heisan` | 114 | 86.4 |
| `s76_yidi` | – | 70.7, all 36 frames |

`*` One sub-exposure against the film's averaged frame, so part of the difference is the averaging.

A shot rendered on the kind of GPU that made its frames for the film comes out nearly identical. On the other kind it is a little further off, and the difference images show mostly noise.

## Known issues

Contributions are welcome.

- **`s69_mutan_raw` is about 3% brighter than the film.** It needs torch and an NVIDIA GPU. The camera matches the film's to every digit and the background is identical, but the glow is brighter. The cause was not found: the script and shaders match the commit made just before the film's frames, and two runs of the heat solve differ in their mean by less than one part in a million. The comparison also reused the crack fields from the original run. They are not in this repository, so a fresh clone solves them again, and that has not been compared.
- **Some shots differ a little on both GPUs.** `s16_lizhi_v1`, `s20_denglong`, `s36_nanzhu`, `s37_jinyu`, `s50_qinghua` and `s63_nanhong` read about the same on Metal and on the 5090 (50 to 56 dB), so something other than GPU noise differs. The cause has not been looked into.
- **`s54_zoumadeng` hung the GPU on Metal.** In the one run tried, Metal reported a GPU hang after 4 frames, so only its first frame was compared there. It runs through on the 5090.
- **`s30_huali` has moved slightly.** The camera and lights differ from the film's render by a hair (the key light's y is -44.028, was -43.97). The script that made the film's frame was not found.
- **The first and last frames of spinning shots have half the motion blur.** They have no keyframe beyond them on one side.
- **Old docstrings.** Many scripts describe paths and steps from while the shot was being made. `v2/render_film.py` is the source of truth for how each frame in the film was made.
- **The music can't be rebuilt from here.** The bass and reed organ come from Keyscape, which is paid, and the offline tools that drive it are not in this repository. See `v2/music/README.md`.
- **Some tools need the original film.** `tools/arc.py --film` and the measuring scripts in `v2/music/` read `ref/opus55.mp4`, which belongs to Anthropic and is not here.
- **`v1/` does not run as it stands.** It assumes the directories and render machines of that time.

Problems in the look of the film itself are listed under 全片已知问题 in [`STACK.md`](STACK.md).
