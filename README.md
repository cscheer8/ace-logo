# ACE standalone animation

An independent, deterministic 5.5-second brand asset project. No ACE website code, Lovable connection, website checkout, or website dependency is used.

**Current exports are DEVELOPMENT PREVIEWS, not brand-approved deliverables.** The supplied reference image is visible in the task conversation, but its original image bytes were not exposed as a downloadable workspace asset. No official source logo exists in this repository. The final slate explicitly says “OFFICIAL ARTWORK REQUIRED / DEVELOPMENT PLACEHOLDER”; it is not a fabricated ACE logo. Supply the official portrait PNG with alpha and run the export command below to produce the real final state. Do not trace the reference or recreate its lettering.

## Deliverables

- `exports/ace-hero-animation.webm`: VP9, 768 × 1024, 30 fps, 5.5 seconds, alpha, no audio.
- `exports/ace-hero-animation.mp4`: H.264/yuv420p, same size/timing, opaque #0a0c10 background, fast-start metadata.
- `exports/ace-hero-final-frame.png`: transparent RGBA still, identical to the uncompressed completed animation frame.
- `exports/contact-sheet.jpg`: actual rendered key frames with timestamps; background is for inspection only.
- `exports/render-manifest.json`: artwork identity/hash, timing and export status.
- `exports/validation.json`: checks performed on the exported files.
- `scripts/render_machine.py`: procedural Blender source; separate machine root and door hinge controls, named geometry and materials.
- `scripts/export.py`: logo-plane perspective transition, compositing, video encoding and still export.
- `src/timing.json`: shared timing, resolution, frame rate and framing controls.
- `src/player.js`: optional framework-independent, once-only browser player.

There is no grid, heading, UI, or audio baked into the assets. The local preview has an inspection checkerboard only. Video files do not encode an automatic repeat instruction; the embedding application must omit `loop`.

## Reproduce

Tested with Blender 4.3.2, Python 3 with Pillow 12.3.0 and NumPy 2.3.5, and FFmpeg with `libvpx-vp9` and `libx264`. Use the existing isolated checkout; no Git worktree is necessary.

```sh
cd /workspace/ace-logo
python -m venv .build/venv
.build/venv/bin/pip install -r requirements.txt
.build/venv/bin/python scripts/export.py
.build/venv/bin/python scripts/validate.py
```

`blender`, `ffmpeg`, and `ffprobe` must be on PATH. This is a headless Blender Workbench studio render with beveled geometry, cavity shading, shadows and specular highlights. It needs a working EGL/software OpenGL backend, not a physical GPU. Four render threads are used. This is intentionally a lightweight stylized product render, not a photorealistic ray-traced simulation.

For official artwork, preserve the original file unchanged, including its alpha channel:

```sh
cp /path/to/original-official-logo.png assets/ace-logo-official.png
.build/venv/bin/python scripts/export.py --logo assets/ace-logo-official.png --reuse-machine
.build/venv/bin/python scripts/validate.py
```

Only use `--reuse-machine` when `.build/machine/` comes from the current Blender source and timing settings. A clean export rebuilds the machine. Changing geometry, framing, FPS, duration or timing requires a full export. All videos and diagnostics are regenerated together; source assets are never overwritten. The exporter validates the expected portrait aspect ratio. A wide logo requires explicit framing adjustments. An image with a baked background remains opaque; the exporter does not silently remove it or alter the artwork. Official artwork should ideally be at least 840 px tall; a higher resolution is preferred.

The reproducible source is the Blender Python script. `.build/ace-machine.blend` is generated as a convenience and is not a required source file. The logo is projected as an unmodified textured plane, then held as a direct aspect-preserving resize of the original source. No generated lettering or approximation is used for an official export. Official visual fidelity cannot be approved until the real file is supplied and the exports regenerated and inspected.

## Sequence and controls

- 0–0.35 s: machine with partially open door and visible product shelves.
- 0.35–1.45 s: hinge closes with a smooth heavy movement.
- 1.45–1.7 s: restrained sub-degree latch settle.
- 1.7–3.65 s: cabinet rotates; an edge-on crossfade at 2.55–2.85 s conceals the geometry handoff to the artwork plane.
- 3.65–4.55 s: artwork makes a restrained 3.5% scale settle without overshoot.
- 4.55–5.5 s: completely stationary final frame.

The machine, door, and logo are separate controls. Adjust the `pose()` function in `scripts/render_machine.py` for machine/door motion; change named boxes/materials for styling. Adjust `src/timing.json` for timing and dimensions, and `logo_height` for size. Adjust `logo_layer()` in `scripts/export.py` for perspective and final scale. The final still is also the integration fallback. There is no recurring floating or pulsing animation.

## Local inspection

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Open `index.html` through that server in your browser. The preview is separate from exported content. Replay is explicit and respects reduced-motion preferences. The player reserves 3:4 space, does not run React animation updates, and exposes a cleanup function. It falls back to the still if playback fails or autoplay is blocked. If the official image itself is missing, the brand cannot be restored by code; deploy the exported still together with the videos.

## Later Lovable integration (instructions only)

Copy the two videos and still into the target site's public assets, for example `public/ace/`, then import `mountACEAnimation` into the existing hero component. Keep all hero layout, text and links unchanged. In a React effect, call it once on a stable container and return its cleanup function:

```jsx
const host = useRef(null);
useEffect(() => {
  return mountACEAnimation(host.current, { baseURL: '/ace/' });
}, []);
return <div ref={host} style={{ width: '100%', maxWidth: 480 }} />;
```

Import React's `useRef`/`useEffect` and the player from wherever you copy `src/player.js`. Ordinary rerenders do not replay it. Remounting the component deliberately creates a new playback lifecycle. `prefers-reduced-motion` displays the final still without loading video. The `ended` event replaces the video with the still indefinitely. No external animation libraries are required.

VP9 alpha support varies by browser/platform. H.264 has no alpha; it is the compatibility fallback, with its documented dark background. Safari may select/decode WebM without alpha depending on version, so test on your actual target browsers or explicitly choose MP4 there. HEVC alpha is not exported by this pipeline. The PNG fallback is portable. Do not rely solely on ffprobe's WebM pixel-format label: use the libvpx decoder to verify the actual alpha plane, as the validator does.

## Validation scope

`python scripts/validate.py` checks both full decodes, dimensions, codecs, frame counts, durations, decoded WebM alpha extrema, visible final content, PNG equality and a pixel-identical uncompressed final hold. With a repository-local official logo, it also compares the final raw pixels with a direct proportional resize of that source. Visual inspection uses the contact sheet and individual rendered frames. Browser/device playback and official brand approval remain separate checks; do not infer those from a successful encode. There is no framework build or lint toolchain to run; this project builds through its renderer/exporter.

For automated browser validation, install `requirements-dev.txt` and run `python tests/browser.py`. The test uses `/usr/bin/chromium`; adjust `executable_path` for another supported local installation. It checks real playback completion, explicit replay, a live reduced-motion preference change, the mobile static fallback and layout, and JavaScript page errors. Browser evidence is saved under `exports/browser-*.png` and `exports/browser-validation.json`. Browser preview UI and inspection backgrounds are not included in any video or final-frame export.

Current preview validation: 165 frames per video, both 5.500 seconds at 768 × 1024. Full streams decode successfully. VP9 decoded alpha spans 0–255. The final uncompressed hold is stationary and matches the PNG exactly. Final video-frame mean absolute RGB error against the PNG composited over the MP4 backing is approximately 1.07/255 (WebM) and 1.75/255 (MP4). Headless Chromium passes playback completion, replay, reduced-motion switching, 360 px mobile layout, and both-video-sources-failed fallback with no JavaScript page errors. The contact sheet and desktop/mobile screenshots are included as visual evidence. Firefox, Safari, iOS and Android device tests have not been run. Official logo fidelity is unverified because these preview exports use the explicit development placeholder.
