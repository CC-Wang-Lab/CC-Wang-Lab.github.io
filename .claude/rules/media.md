# Media — video, images, and the bandwidth limit

## The limit that decides everything

GitHub Pages allows a **1 GB site** and a **soft 100 GB per month** of traffic.

```
100 GB / month  /  0.996 MB hero  =  ~100,000 hero loads / month
100 GB / month  /  61 MB          =        1,640 loads / month
```

**Rule: the hero video stays under 1 MB.** Anything longer than 15 seconds goes to YouTube and is
embedded on a page, never autoplayed on the home page.

## The hero recipe

```bash
ffmpeg -y -ss 8 -t 10 -i source.mp4 -an -vf "hue=s=0,scale=1280:-2,fps=25" \
  -c:v libx264 -crf 36 -preset veryslow -pix_fmt yuv420p -movflags +faststart \
  _assets/video/hero-boiling.mp4

ffmpeg -y -ss 5 -i _assets/video/hero-boiling.mp4 -frames:v 1 -q:v 4 \
  _assets/video/hero-poster.jpg
```

**Do not ship WebM.** Measured on this footage, VP9 came out 58% LARGER than H.264 (1,079 KB
against 684 KB). High-speed macro bubbles are thousands of moving specular highlights, which VP9
handles badly at low bitrate. Check before assuming WebM is smaller.

## The markup, and why each attribute is there

```html
<video autoplay muted loop playsinline poster="/assets/video/hero-poster.jpg">
  <source src="/assets/video/hero-boiling.mp4" type="video/mp4">
</video>
```

- `muted` is **not optional**. Chrome and Safari refuse to autoplay video with an audio track, and
  they fail silently, so a hero with sound simply never starts.
- `playsinline` stops iOS Safari taking the video fullscreen.
- `poster` is what a reduced-motion visitor sees instead.

Always pair it with:

```css
@media (prefers-reduced-motion: reduce) {
  .hero-video { display: none; }
  .hero { background-image: url("/assets/video/hero-poster.jpg"); }
}
```

## Caption the footage

Scientific footage must say what it is. Unlabelled high-speed boiling is just bubbles to a visitor
who does not already know what they are looking at. The caption string lives in
`_data/ui.toml` under `[hero] caption_en / caption_zh`.

## Screen recordings need cropping

`CPUCooler.mp4` is a recording of a whole Makie application window: title bar, sliders, gauges,
stats. Crop before use — `crop=1084:902:0:26` removes the title bar, the control panel and the
mesh legend. Better still, re-record with the UI hidden and the window fullscreen.
