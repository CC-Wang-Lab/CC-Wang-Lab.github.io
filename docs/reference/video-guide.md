# The hero video — what we have, what to run, what to film next

## The answer

```bash
ffmpeg -y -ss 30 -t 12 -i CPUCooler.mp4 -an \
  -vf "crop=1084:902:0:26,scale=1440:-2,fps=30" \
  -c:v libx264 -crf 30 -preset slow -pix_fmt yuv420p -movflags +faststart hero.mp4

ffmpeg -y -ss 4 -i hero.mp4 -frames:v 1 -q:v 3 hero-poster.jpg
```

That turns the 61 MB source into **829 KB**. Measured, not estimated.

---

## What we measured

| File | Size | Resolution | fps | Length | Bitrate |
|---|---|---|---|---|---|
| `CPUCooler.mp4` | **61.0 MB** | 1470×980 | 30 | 83.6 s | 5.84 Mbps |
| `EnergyPlus.mp4` | 39.7 MB | 1916×1032 | 30 | 65.6 s | 4.85 Mbps |
| `alpha_v.mp4` (vapour fraction) | 0.17 MB | 600×680 | **5** | 6.2 s | 0.22 Mbps |
| `V_magnitude.mp4` | 0.23 MB | 600×680 | **5** | 6.2 s | 0.29 Mbps |

Encode results, all from a 12-second cut:

| Output | Size | Verdict |
|---|---|---|
| `hero.mp4`, uncropped, 1600 wide | 684 KB | Works, but shows the app window |
| `hero-crop.mp4`, cropped, 1440 wide | **829 KB** | **Use this one** |
| `hero.webm`, VP9, 1600 wide | 1,079 KB | **Drop it.** VP9 came out *bigger* than H.264 here |
| `hero-poster.jpg` | 121 KB | Shown before load, and to reduced-motion users |

**Do not ship WebM.** On this footage it costs 58% more bytes for no gain. That is unusual, and it happens because the scene is mostly flat dark blue with fine particles, which VP9 handles badly at low bitrate.

---

## Why the source needs cropping

`CPUCooler.mp4` is a **screen recording of the whole Makie application window**. The frame contains:

- a Windows title bar reading "Makie"
- a particle-counter text line across the top
- GPU and CPU dial gauges, and a RAM / VRAM / FPS stats block, down the left
- the full Controls panel — sliders for RPM, Trails, Size, Speed, Inlet, Side, Outlet, Alpha — down the right
- a velocity colour bar on the far right
- a mesh legend and an XYZ axis triad along the bottom

The crop `crop=1084:902:0:26` removes the title bar, the Controls panel and the mesh legend. The gauges and the stats block survive, and they still read as "somebody's desktop".

**The 12 s cut starts at t=30 s on purpose.** That is where the streamlines have filled the fan and the scene is busiest.

---

## The bandwidth budget

GitHub Pages allows a 1 GB site and a **soft 100 GB per month**.

```
100 GB / month  /  0.829 MB per hero  =  ~120,000 hero loads / month
100 GB / month  /  61.0 MB            =        1,640 loads / month
```

**The 61 MB file already on `maysam-gholampour.github.io` is worth fixing.** At 1,640 loads it exhausts the monthly allowance, and this lab expects many visitors.

Rule for this site: **hero under 1 MB**. Anything longer than 15 seconds goes to YouTube and gets embedded on the Facilities page, never autoplayed on the home page.

---

## The markup

```html
<video class="hero-video" autoplay muted loop playsinline
       poster="/assets/video/hero-poster.jpg">
  <source src="/assets/video/hero.mp4" type="video/mp4">
</video>
```

`muted` is not optional. **Chrome and Safari refuse to autoplay a video with sound**, and they fail silently, so a hero with an audio track simply never starts. `playsinline` stops iOS Safari taking the video fullscreen.

Accessibility, required:

```css
@media (prefers-reduced-motion: reduce) {
  .hero-video { display: none; }
  .hero { background-image: url("/assets/video/hero-poster.jpg"); }
}
```

---

## The logo is inside the video

The frame carries the lab's own logo: two fish, one orange and one blue, curled into a fan, over the words **CC WANG LAB — INNOVATIVE COOLING SYSTEM**.

Colours sampled from it, and adopted as the site palette:

| Role | Hex | Source |
|---|---|---|
| Heat | `#D89030` | the orange fish |
| Cooling | `#4080A8` | the blue fish |
| Dark ground | `#181828` | the logo background |

**We still need the original logo file** — SVG if it exists, otherwise the largest PNG. The copy pulled out of the video is a JPEG-compressed 220×130 crop and is far too small for a navbar or a favicon.

---

## What to film next, to replace this

The cropped recording is good enough for a first draft. It is not good enough for the finished site, because it still shows a desktop application.

**Cheapest real fix, about one hour:** re-record the Makie app with the Controls panel hidden, the gauges off, and the window fullscreen at 1920×1080. Same scene, no UI. That alone gives a proper hero.

**If real lab footage is wanted, film these five shots.** A phone at 4K 30 fps on a small tripod is enough. Never handheld — a full-bleed hero magnifies every shake.

| # | Shot | Length | Note |
|---|---|---|---|
| 1 | Bubbles rising off a boiling surface, macro, side-lit | 8 s | The single most watchable thing in a thermal lab |
| 2 | Immersion tank, boards submerged, fluid moving | 8 s | This is what data-centre buyers came to see |
| 3 | Slow pan along a wind-tunnel or fin-and-tube test rig | 10 s | Shows scale and seriousness |
| 4 | Infrared camera screen, a hot spot cooling down | 6 s | Colour does the explaining, no caption needed |
| 5 | Two people at a rig, hands and instruments, faces not needed | 8 s | Proves the lab has 60 people, not 6 |

Rules that matter more than the camera:

1. **Lock the tripod.** No handheld, no zoom while recording.
2. **One movement per shot.** A slow pan, or a still frame. Never both.
3. **Light it.** A phone in a dim lab produces noise, and noise destroys compression — a noisy clip encodes three times larger for the same quality.
4. **Shoot 4K even though we publish at 1440.** Downscaling hides noise and lets us re-crop later.
5. **Ignore sound.** The hero is silent by force, so room noise does not matter.
6. **No faces without asking.** A recognisable person in a public hero needs their consent.
