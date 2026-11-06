# Render it yourself

The frames are not in this repository: they are about 15 GB. Each shot's frames can be rendered again from its script, and `v2/film.py` cuts them into the film. This page covers the picture. For the music, see [Known issues](#known-issues).

## Setup

- [Blender](https://www.blender.org/) 5.2.1, with a GPU that Cycles supports
- Python 3.13 and `pip install -r requirements.txt`
- FFmpeg, to cut the film

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

Each shot below was rendered again from this repository at final quality and compared with the film's own frames. Moving shots were compared on their first and last frames, with `GEWU_ENDS=1`. The numbers are PSNR at 1/4 size, where render noise has mostly gone. As a rule of thumb, a difference is hard to see above 40 dB.

| Shot | PSNR (dB) |
|---|---|
| `s35_kuangcao` | 120.9 |
| `s19_luodian` | 120.4 |
| `s07_cijing` | 117.6 |
| `s73_heisan` | 114 |
| `s61_tihong` | 107.6 |
| `s05_yinni` | 98 |
| `s15_zheshan` | 87.1 |
| `s11_jiangdou` | 80.3 |
| `s55_diancui` | 72.0 |
| `s66_xieyang` | 71.7 |
| `s06_junyao` | 63.9 |
| `s49_falang` | 57.0 |
| `s20_denglong` | 51.5 |
| `s16_lizhi_v1` | 51.1 |
| `s50_qinghua` | 50.3 |
| `s36_nanzhu` | 49.5 |
| `s30_huali` | 49.1 |
| `s59_suxiu` | 46.5 |
| `s28_dehua` | 44.3 |
| `s45_kongque` | 41.2, one sub-exposure against the film's averaged frame |

The same code on the same machine gives nearly identical frames. Path-tracing noise differs between GPUs, so yours will be close rather than bit-identical.

## Known issues

Contributions are welcome.

- **Shots not compared yet.** These have recipes in `v2/render_film.py`, but no comparison is recorded above: `s01_moyun`, `s02_yaobian`, `s09_yinxing`, `s14_datiehua`, `s24_jianzhi`, `s27_jinbo`, `s37_jinyu`, `s38_richu`, `s39_hehua`, `s46_luopan`, `s54_zoumadeng`, `s63_nanhong`.
- **`s76_yidi` and `s69_mutan_raw` need torch and an NVIDIA GPU, and have not been rendered again.** Their code is the code that made the film's frames, going by the commit times, but nothing has been compared. The fluid and fracture solvers may be sensitive to the GPU and the torch version, so the fine detail could differ; this has not been tested.
- **`s30_huali` has moved slightly.** The camera and lights differ from the film's render by a hair (the key light's y is -44.028, was -43.97). The script that made the film's frame was not found.
- **The first and last frames of spinning shots have half the motion blur.** They have no keyframe beyond them on one side.
- **Old docstrings.** Many scripts describe paths and steps from while the shot was being made. `v2/render_film.py` is the source of truth for how each frame in the film was made.
- **The music can't be rebuilt from here.** The bass and reed organ come from Keyscape, which is paid, and the offline tools that drive it are not in this repository. See `v2/music/README.md`.
- **Some tools need the original film.** `tools/arc.py --film` and the measuring scripts in `v2/music/` read `ref/opus55.mp4`, which belongs to Anthropic and is not here.
- **`v1/` does not run as it stands.** It assumes the directories and render machines of that time.

Problems in the look of the film itself are listed under 全片已知问题 in [`STACK.md`](STACK.md).
