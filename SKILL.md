# Color Correct — AI colorist skill

Grade a video file with your AI agent as the colorist: it **looks at frames**, diagnoses what's wrong, authors a grade as a readable ffmpeg filter chain, previews side-by-side, iterates, renders. Non-destructive (writes a new file), audio stream-copied.

The core idea: the agent's superpower isn't running ffmpeg filters — it's the **closed loop**. Extract frames → look → grade → extract again → compare → adjust. Never render blind; never trust a preset without eyeballing it on the actual footage.

## Ways to use it

**1. Pick a look** — "apply Oat Milk to this clip"
Applies one of the nine named looks below (at subtle strength by default).

**2. See the menu** — "show me all the looks on this video"
The agent picks a representative frame, renders all nine looks on it, and returns a labeled 3×3 contact sheet so you choose with your eyes.

**3. Let AI decide** — "color correct this" / "make this look good"
The agent diagnoses the footage (content type, casts, exposure, saturation), decides whether it needs a neutral fix, a look, or both — and *which* look fits the content — then shows you a before/after side-by-side for approval before the full render.

## Inputs
- Path to a video file (ask if not given).
- Optional: a look name, `menu` (contact sheet), or nothing (AI decides).
- Optional: a reference (YouTube URL / screenshot) for Steal mode — see below.

## Tooling
- `ffmpeg` filters: `colortemperature`, `eq`, `colorbalance`, `curves`, `vibrance`, `unsharp`, `hue`, `lut3d`
- `scripts/measure.py` — grade fingerprint of a frame (luma percentiles, per-band casts, saturation)
- `scripts/consensus.py` — multi-frame median fingerprint (for Steal mode)
- `yt-dlp` — for pulling reference sections in Steal mode
- The agent's eyes — the actual instrument

## Working directory
`/tmp/color-correct/<basename>/` — keep frames + the grade chain for debugging.

---

## The grade fingerprint (what to measure)

`python3 scripts/measure.py frame.jpg` prints, per frame:
- **luma p1/p10/p50/p90/p99** → exposure (p50), contrast (p90−p10 spread), matte-ness (p1 > 8 = lifted blacks), highlight ceiling (p99 < 245 = pulled whites)
- **per-band RGB casts** (shadows 0–64 / mids 64–160 / highs 160–255) → R−B = warm/cool tilt, G offset = green/magenta tilt, *per tonal band* (split-toning lives here)
- **mean saturation** + p90 saturation

Numbers back the eyes; eyes make the call. Always read the frame images too — casts hide in skin and neutrals, and stats can't see "this looks cheap".

## Workflow

### Step 0 — Probe + sample
`ffprobe` for codec, bit depth, color space/transfer (**flag log footage** — D-Log/HLG needs a conversion LUT *first*). Extract 4–6 frames across the runtime (lighting changes mid-video more often than you think):
```bash
for t in 2 15 40 ...; do ffmpeg -y -ss $t -i IN.mp4 -frames:v 1 -q:v 2 /tmp/color-correct/$NAME/src_${t}s.jpg; done
```

### Step 1 — Diagnose (look + measure)
Read the frames. Run `measure.py`. Name what's wrong in plain words *before* touching filters: "green webcam cast in mids, blacks crushed, skin under-saturated". **Classify the content**: talking head, b-roll, screen recording, mixed edit. Screen recordings and UI captures should NOT be graded hard — a look that flatters skin will yellow a white webpage. Mixed edits get a conservative global grade.

### Step 2 — Author the grade
Write the chain as an ordered, commented list the user can approve.

**Correction order (always this order):**
1. `colortemperature=temperature=N` — kill the WB cast
2. `colorbalance` — residual green/magenta tint
3. `eq=brightness/contrast/gamma` — exposure + contrast (brightness ±0.06 max; prefer gamma for mids)
4. `vibrance=intensity=N` — saturation that protects already-saturated px + skin (prefer over `eq=saturation`)
5. `curves` — matte lift / highlight rolloff / per-channel split-tones (last)

### Step 2b — The looks

Nine looks, each reverse-engineered from a creator whose color work we admire — via **consensus fingerprinting** (median grade fingerprint over ~18 frames across 3 different videos per creator; only the *invariants* survive, scene-driven casts are discarded). Credits in the README.

**Strength: the chains below are the SUBTLE (~50%) versions — the shipping default.** Full-strength consensus references are in the table's last column as multipliers. Go full only when the user asks for "more" or the footage is very flat. If a side-by-side screams, halve everything.

| Look | Character | Chain (subtle, default) |
|---|---|---|
| **Golden Hour** | filmic warmth, rolled-off whites, green-gold highlights | `colortemperature=temperature=6150,curves=master='0/0.018 0.6/0.59 1/0.94',colorbalance=rs=0.015:gh=0.015,vibrance=intensity=0.08` |
| **Honey** | soft warm matte, gentle contrast | `colortemperature=temperature=6050,curves=master='0/0.023 0.5/0.5 1/0.95',vibrance=intensity=0.04,colorbalance=gm=0.01:gh=0.01` |
| **Linen** | soft rolled whites, quiet warmth, magenta-leaning highlights | `curves=master='0/0.018 0.5/0.5 1/0.915',colortemperature=temperature=6100,colorbalance=gh=-0.015,eq=saturation=0.965` |
| **Super 8** | film-stock compression, warm, heavy highlight rolloff | `curves=master='0/0.02 0.5/0.51 1/0.9',colortemperature=temperature=5900,colorbalance=gs=-0.01:gm=-0.01,vibrance=intensity=0.05` |
| **Oat Milk** | creamy editorial: warm shadows → cool milky highlights (inverted split-tone) | `curves=master='0/0.035 0.5/0.51 1/0.915',colorbalance=rs=0.02:rm=0.015:rh=-0.03:bh=0.025,eq=saturation=0.985` |
| **Espresso** | moody: darker mids, warm skin against neutral shadows | `eq=contrast=1.03:saturation=0.95,colorbalance=rm=0.025:bm=-0.015,curves=master='0/0.02 0.5/0.485 1/0.94'` |
| **Velvet** | lifted matte blacks, pulled whites, warm mids | `curves=master='0/0.035 0.5/0.5 1/0.935',colortemperature=temperature=6000,colorbalance=gs=-0.01:gh=0.015,vibrance=intensity=0.04` |
| **Popsicle** | bright pop: full whites, punchy spread, sunny highlights | `eq=brightness=0.01:contrast=1.03,curves=master='0/0.025 0.5/0.515 1/1',vibrance=intensity=0.06,colorbalance=gh=0.015` |
| **Terracotta** | warm + contrasty, magenta-leaning shadows, rich | `eq=contrast=1.035,colortemperature=temperature=5850,colorbalance=gs=-0.02:gm=-0.01,curves=master='0/0.01 0.5/0.5 1/0.99'` |

**Full strength** = double every parameter's distance from neutral (temp toward the value 2× further from 6500, curve offsets ×2, colorbalance ×2, vibrance ×2, contrast 1.03 → 1.06, saturation 0.95 → 0.9).

**Faster path:** every look also exists as a `.cube` LUT in `luts/{subtle,full}/` — `lut3d=luts/subtle/golden-hour.cube` applies identically to the chain (verified ~1/255). Use the chains when you need to *adapt* a look to the footage; use the LUTs for straight application or for handing to an NLE. Regenerate after editing chains: `scripts/gen_luts.sh` (uses `scripts/chain2cube.py`, HALD-CLUT method — per-pixel filters only, no spatial filters like `unsharp` in a LUT-able chain).

### Step 2c — The menu (visualise all)
Pick the most representative frame (a talking head with skin + some background depth beats a flat wall). Render all nine looks on it + label + tile 3×3:
```bash
# per look: ffmpeg -y -i frame.jpg -vf "$CHAIN,scale=768:-2" -q:v 2 look.jpg
# then tile with PIL/ImageMagick, label each tile with the look name
```
Show the sheet; the user picks with their eyes. (Labeling via PIL is the portable path — many ffmpeg builds ship without `drawtext`.)

### Step 2d — AI decides (auto mode)
The agent's decision tree:
1. **Footage has a cast / exposure problem** → Fix first, always.
2. **Content is a screen recording or mixed edit** → conservative fix only, or nothing. Say why.
3. **Talking head, clean** → pick the look whose character fits the content's energy (bright tutorial → Popsicle; cozy desk → Honey/Velvet; cinematic vlog → Golden Hour/Super 8; editorial → Oat Milk/Linen; moody tech → Espresso). Name the reasoning in one line.
4. Always show the side-by-side before the full render.

### Step 2e — Steal mode (fit a new look from any creator)
A single reference frame confounds the *grade* with the *scene* (a warm cabin frame reads as a warm grade). The grade is what stays constant while scenes change:
1. **Sample wide**: 2–3 videos from the channel, different environments. 3 sections each, 2 frames per section → ~18 frames. Use `yt-dlp -f "bv*[height<=1080][vcodec^=avc1]"` (AV1 section downloads can produce undecodable files). Contact-sheet the frames — drop motion graphics / screen recordings / title cards before measuring.
2. `python3 scripts/consensus.py <dir>` → per-frame stats + MEDIAN + IQR. **Read the IQR like a signal**: tight IQR = grade signature; wide IQR = scene-driven, IGNORE it.
3. Author the chain from the invariants only. Typical real signatures: highlight rolloff point, saturation ceiling, black floor, small consistent band tints (±3–10). Typical fakes: big warmth (weather), casts that flip sign between scenes.
4. Verify side-by-side on the target footage, 2–3 iterations. Save the fitted look at subtle strength.

### Step 3 — Preview (never full-render first)
```bash
ffmpeg -y -ss T -t 5 -i IN.mp4 -vf "$CHAIN" -c:v libx264 -crf 18 preview.mp4
ffmpeg -y -i src_frame.jpg -i graded_frame.jpg -filter_complex hstack sbs.jpg
```
Read the side-by-side. Check in order: **skin first**, then neutrals (walls/whites), then blacks, then overall vibe. Re-measure the graded frame — did the numbers move where predicted? Show the user before the full render.

### Step 3.5 — Skin gate (MANDATORY when a person is in frame)
Eyes are the first check; this makes it mechanical:
```bash
python3 scripts/skincheck.py src_frame.jpg graded_frame.jpg
```
Detects skin pixels in the original (tightened YCbCr box + saturation bounds — the classic box false-positives on beige walls) and measures how the grade moved them:
- **PASS** (exit 0) — hue shift < 6°, sat change < 25% → proceed
- **SOFTEN** (exit 1) — halve the look strength, re-render the preview, re-check
- **FAIL** (exit 2) — the grade breaks skin. Don't just soften: diagnose. Usually means WB wasn't corrected first, or the look is wrong for this footage.
- **SKIP** — <2% skin in frame (b-roll): judge by neutrals instead.

Run the gate on 2–3 frames across the runtime (lighting changes move skin too). White balance is protected by the same mechanism upstream: the Fix pass neutralizes casts *before* any look, and the gate catches it if that step was skipped — a look on top of a cast fails the hue check immediately.

### Step 4 — Render
```bash
ffmpeg -y -hwaccel videotoolbox -i IN.mp4 -vf "$CHAIN,format=yuv420p" \
  -c:v libx264 -preset fast -crf 18 \
  -c:a copy -movflags +faststart OUT_graded.mp4
```
Audio stream-copied; bt709 tags preserved. Verify frame pairs at 3 timestamps across the runtime.

## Taste rules
- **Correct, then grade.** A look on top of a cast = the cast, warmer.
- **Skin is the referee.** Any move that breaks skin loses.
- **Subtle wins.** If the side-by-side screams, halve everything.
- **Matte = lifted blacks + pulled whites**, not low contrast.
- **Split-tone via `colorbalance` bands**, warmth via `colortemperature`, mids via `gamma` — one job per filter, in order.
- **Never grade log footage directly** — convert (lut3d) first.
- Don't grade UI/screen-recordings hard; white interfaces show every cast.

## Gotchas (earned the hard way)
- **`curves` needs anchors at both ends** (`0/x ... 1/y`) — a single-point curve extrapolates into a blown-out frame.
- **macOS bash 3.2 silently breaks `declare -A`** (all keys collapse to index 0). Use `case` statements in download scripts.
- **Renderer color-shift paranoia check**: encoders (x264 vs hardware) don't shift color (<0.3/255 measured) — but color *metadata* does. Preserve bt709/range tags; judge grades in the player your audience uses (browsers ≠ QuickTime gamma).
