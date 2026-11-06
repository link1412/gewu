# Research brief: WebGPU path tracing vs Blender Cycles, as the renderer inside a reusable "skill"

## Context
We render photoreal macro shots of craft objects for a 20-second film: glazed ceramics (light scattering in a
1-2 mm glaze layer over a dark body, crackle lines inside it), silk embroidery (fibres), cloisonne enamel, gold
leaf. Current renderer: Blender Cycles 5.2, run headless from Python on an Apple M4 Pro GPU (Metal), with
OpenImageDenoise; pbrt-v4 (spectral) is our reference. We will package the method as a reusable "skill" for an
AI coding agent. The question: would a WebGPU + shaders renderer make that skill cheaper or easier to use,
without losing photoreal quality?

## Questions (answer each with sources)
1. As of now (late 2026): does WebGPU (the spec, and what Chrome, Safari and Firefox ship) expose hardware
   ray tracing? Give the status of any ray-tracing extension or proposal (gpuweb GitHub, Chrome Platform
   Status, WebKit blog, Dawn/wgpu notes). Same question for wgpu (Rust) used natively.
2. Survey open-source path tracers that run on WebGPU (or WebGL2), e.g. three-gpu-pathtracer and any others
   you find. For each: features (BVH, MIS, rough dielectric transmission, homogeneous participating media
   bounded by a dielectric surface, subsurface scattering, curve/hair primitives, motion blur, thin-lens depth
   of field, spectral rendering, denoiser); any validation against a reference renderer (pbrt, Mitsuba,
   Cycles); performance figures (Apple Silicon if possible); whether it can render headless to a float image
   (EXR/HDR) from a script; license; maintenance (date of last commit/release).
3. Published comparisons of path tracing in WebGPU compute shaders against native hardware ray tracing
   (Metal ray tracing, Vulkan RT, OptiX): speed ratios, scene sizes.
4. Blender/Cycles as a dependency of a skill: download size, headless command-line rendering on macOS,
   Windows and Linux, GPU backends (Metal and its hardware ray tracing "MetalRT" on which chips, CUDA/OptiX,
   HIP, oneAPI), and any license constraint on separate Python scripts that drive Blender (GPL).
5. Briefly, Mitsuba 3 as an alternative dependency: pip install, spectral variants, which GPU backends
   (does it run on Apple GPUs?).

## Rules


- Do not download or run binaries or installers. Reading web pages, papers, READMEs and source files is fine.
- Every claim gets a URL, and a tag: [sourced] (stated by the source) or [inferred] (your reasoning).
  If you cannot find something, say so; do not guess.
- Time box: about 25 minutes. Then write up what you have.

## Deliverable
Write `report.md` in this directory: a short answer to each question first, then the evidence (quotes with
URLs). End your final message with a 5-line summary.
