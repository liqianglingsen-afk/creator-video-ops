# Jianying/CapCut Operation Notes

Use concrete parameters. Adapt values to the actual source resolution, but do not replace parameters with vague adjectives.

## Subtitle Baseline

For 1080x1920 vertical video:

- Font: 思源黑体 Heavy, 阿里巴巴普惠体 3.0 Bold, or equivalent bold sans.
- Rendered size reference: 58-72px high for normal subtitles; 78-96px high for emphasis words.
- Position: bottom safe area, 170-230px above bottom edge.
- Alignment: center for one speaker; left alignment for dense explanatory lists.
- Stroke: black, 5-8px.
- Shadow: black at 35-45% opacity, distance 3-5, blur 6-10.
- Line length: 9-14 Chinese characters per line for fast oral delivery.
- Keywords: scale 110-125%, use red/yellow/white contrast, keep one emphasis color per beat.
- Animation: 2-4 frame pop-in or fade; avoid slow decorative entrance for fast hooks.

For 2160x3840 vertical video, double values roughly, then adjust visually.

### Font Size Reference Source

Use rendered-pixel measurement, not the editor's nominal font-size number, as the shared reference.

- `scripts/measure_subtitles.py` estimates the subtitle bounding box from extracted frames.
- The script normalizes subtitle height and bottom margin to a 1080x1920 vertical export reference.
- Report both the measured value and the practical Jianying/CapCut adjustment suggestion.
- If subtitle detection is low-confidence, label it as an estimate and verify manually in the exported frame.

Mandatory report note:

> 字号参考基于 1080x1920 竖屏成片的画面渲染尺寸。剪映、CapCut、Premiere、Final Cut、After Effects 等软件的字号单位、字体渲染、缩放逻辑不同，同样字号不一定显示为同样大小；请以最终导出画面中的字幕高度、位置和可读性为准，并根据实际软件微调。

Practical Jianying/CapCut calibration:

1. Export or preview one frame at the final canvas ratio.
2. Measure the visible subtitle height, not only the font-size field.
3. If the measured normal subtitle is below 58px on a 1080x1920 export, increase the editor font-size or scale.
4. If it is above 96px outside emphasis beats, reduce font-size/scale or split lines.
5. Keep the subtitle block 170-230px above the bottom edge unless the platform UI, progress bar, or subject position requires adjustment.

## Highlight Words

Use a separate text layer for the keyword when emphasis must sync with audio.

1. Split the subtitle at the key word.
2. Put the keyword on a separate upper track.
3. Add scale keyframes: 100% -> 118% -> 105% over 6-10 frames.
4. Add a short click/pop sound only when it supports the style.
5. Keep baseline aligned with the main subtitle.

## Camera and Motion

- Static talking head: add scale keyframes every 2-4 seconds only when there is no natural movement.
- Push-in: 100% to 106-112% over 12-24 frames for emphasis.
- Reframe: move subject eyes to upper third; avoid cutting forehead/chin unless intentional.
- Pattern interrupt: cut, zoom, overlay, or prop change every 15-30 seconds for mid-length explainers.

## Masks and Cutout

- Smart cutout: use for people or objects on complex backgrounds.
- Chroma key: use only when background color is clean and separate from subject.
- Mask feather: 8-20 for soft blend, 0-4 for UI screenshot or hard-edge split screen.
- Rectangle mask: use for screenshots, article snippets, comments, and data proof.
- Linear mask: use for before/after reveals.

## Alignment

- Subtitles: center alignment unless building a left-side analysis list.
- UI proof screenshots: align to a 12-column or simple left margin grid; keep edges parallel.
- Multi-layer text: align keyword baseline with the main subtitle baseline.
- Avoid mixed center and left alignment in the same subtitle beat.

## Timeline Checklist

1. Main video on V1.
2. B-roll/proof screenshots on V2.
3. Subtitle base layer on text track 1.
4. Keyword emphasis layer on text track 2.
5. Arrows/callouts/masks on upper visual tracks.
6. Sound effects under emphasis beats only.
7. Add markers at hook, conflict, proof, conclusion, CTA.
8. Review once with sound off and once with eyes closed to check visual and audio emphasis separately.
