# Forensic Output Contract

涉及优化建议或改后复评，采用 [0.4.0 全片方案与对照验收](full-revision.md) 的预测、保留资产、版位与报告约定。历史报告沿用生成时的口径。


Use this contract for every Chinese short-video teardown unless the user explicitly asks for a lighter text-only answer.

The report is a forensic artifact, not a generic opinion article. It must be frame-evidenced, timestamped, score-standardized, and beginner-operable.

## Mandatory HTML Sections

1. `源流质量诊断`
   - Original video link/path from the user, labeled `视频链接` or `原始视频链接`.
   - Workspace-copied MP4/link or selected playable analysis source when available.
   - Resolved/canonical platform URL when it differs from the user-provided URL.
   - Page/platform metadata resolution.
   - Visible public formats.
   - Hidden playable streams and subtitles, if checked.
   - Selected analysis source.
   - Actual probed/downloaded media resolution.
   - Extracted frame resolution.
   - Explanation for any mismatch between claimed/original/platform metadata and playable/downloaded source.

2. `结论摘要`
   - One-sentence verdict.
   - Current score and target score.
   - Biggest growth blocker.
   - Highest-leverage fix.
   - Score band interpretation.
   - Include the editorial decision section from the template: goal, entry, hook payoff, CTA benefit and destination, evidence-led priorities and preserved shots. Link the matched Framecheck JSON and HTML, or document partial review when unavailable. See `editorial-review.md` for cover and experiment requirements.

3. `前3秒语言心理钩子`
   - 0-1s, 1-2s, 2-3s breakdown.
   - Exact line or best available transcript evidence.
   - Psychology mechanism labels.
   - Whether audio, subtitle, visual, and edit emphasis are synchronized.
   - Three stronger opening rewrites when the original is weak.

4. `综合评分体系`
   - Use the fixed 100-point rubric in `score-rubric.md`.
   - Include all 10 fixed dimensions and their scores.
   - Include evidence for every deduction.
   - Show the rubric version, ten scored rows, their sum / 100, the exact current score after any documented cap, the target ≥85 and the priority order. See `edit-plan.md` for required HTML fields, including the cut list and fallback branch.
   - Do not change scoring weights by video category.

5. `脚本结构与留存`
   - Hook, setup, conflict/problem, evidence/story, conclusion, CTA.
   - Retention devices and where they appear.
   - Reusable script skeleton.

6. `逐镜头视觉拆解`
   - Minimum 12 nodes; recommended 16-24 nodes when the video has enough shot changes.
   - Every node must include timestamp, screenshot, shot size/framing, camera movement, main visual focus, subtitle/on-screen text, retention function, and replication-or-optimization note.
   - In HTML, mark each node with `data-contract="shot"` to support deterministic contract checking.

7. `高光句音画同步`
   - Must cover at least these seven line types when evidence exists: 爆点句、结论句、反差句、冲突句、价值句、情绪句、结果句/CTA.
   - Each row must include timestamp, line, audio emphasis, visual emphasis, subtitle emphasis, edit emphasis, sync verdict, and fix.
   - In HTML, mark each row/card with `data-contract="highlight-line"`.

8. `表现好的地方：1:1图文复刻`
   - Minimum 3 cards.
   - Only include parts worth copying.
   - Each card must include frame evidence, why it works, shot setup, subtitle packaging, edit timing, and Jianying/CapCut steps.
   - In HTML, mark each card with `data-contract="good-card"`.

9. `表现不好的地方：优化后方案`
   - Minimum 3 cards.
   - Current issue screenshot.
   - Why it hurts retention/trust/conversion.
   - Link each proposed fix to the cut list. State which deduction it addresses; label any estimated score change as provisional.
   - Do not teach 1:1 weak execution unless full replication was requested.
   - In HTML, mark each card with `data-contract="bad-card"`.

10. `字幕字体字号位置包装`
    - Font, rendered size, color, stroke, shadow, background/mask, position, safe area, line breaks, keyword emphasis, animation.
    - Include a `字幕测量` subsection using measured or explicitly estimated subtitle region data.
    - Include `字号参考来源` and the software-difference note from `jianying-ops.md`.

11. `拍摄剪辑运镜抠像蒙版对齐剪映操作`
    - Track layout.
    - Keyframe timing.
    - Scale/position values.
    - Mask shape and feather.
    - Smart cutout or chroma key choice.
    - Alignment mode.
    - Transition duration.
    - Speed curve and sound effect if needed.

12. `风格匹配与HTML包装`
    - Report the video style profile: dominant color, accent color, mood, visual category, and selected CSS variables.
    - The HTML report can use a fixed framework, but colors should follow the current video's visual style while preserving readability and contrast.
    - Use a compact report header. Do not use landing-page hero spacing such as `min-height: 58vh`; the first evidence section should be visible without excessive scrolling on a desktop viewport.
    - For left-image/right-text layouts, image height should visually match the adjacent text panel. Do not rely on CSS stretching alone; generate a better-suited evidence image first when the source image aspect ratio is too different from the layout.
    - Evidence images must remain inspectable. Subtitles, bills, AI output screenshots, score tables, comments, and UI proof images must use complete-display treatment, not `object-fit: cover` cropping.
    - If a wide contact sheet is placed in a tall side-by-side slot, regenerate it as a 2x2, vertical stack, or other fitted evidence grid. Do not hard-stretch ultra-wide or ultra-flat images.

13. `小白照做清单`
    - Ordered execution checklist.
    - Reusable parameters.
    - What to copy and what to improve.

## Evidence Rules

- Every visual claim must be backed by a frame, contact sheet, local inspection, deterministic measurement, or multimodal model output.
- Every report must preserve the source chain: original user-supplied video URL/path, resolved platform URL when applicable, and selected analysis source. The original source must be visible in `源流质量诊断` as `视频链接` or `原始视频链接`.
- Every spoken-line claim must cite transcript/SRT/OCR/Whisper/page text or be marked as approximate.
- If a video source is blocked, the report must say what could not be verified.
- HTML should contain real video frames, not only decorative layout.
- Use relative image paths from the HTML file to local `assets/`.
- Do not conflate metadata resolution with actual downloaded/probed media resolution.
- Do not crop away evidence content for visual neatness. If the layout requires a taller image, create a taller evidence grid from full frames instead of cropping one frame.

## Layout QA Rules

- Report headers should be compact: no viewport-height hero block; use content-based spacing.
- In any side-by-side evidence/text block, use matched media containers and fitted evidence assets.
- Use `object-fit: contain` for proof-critical images: subtitles, bills, AI chats, score sheets, UI screenshots, and comments.
- Use `object-fit: cover` only for non-proof visual context where cropping does not remove evidence.
- Ultra-wide or ultra-flat images should not be the primary image in a tall block. Use them as secondary evidence or regenerate a fitted grid.
- After manual HTML edits, update the generator script or template that produced the report.

## Fixed Minimums

- Local evidence images: at least 12 for a full report.
- Shot nodes: at least 12, marked with `data-contract="shot"`.
- Highlight-line rows/cards: at least 7, marked with `data-contract="highlight-line"`.
- Good replication cards: at least 3, marked with `data-contract="good-card"`.
- Weak-part optimization cards: at least 3, marked with `data-contract="bad-card"`.
- Score dimensions: all 10 fixed dimensions from `score-rubric.md`.
- Subtitle measurement: required unless visual evidence is blocked; if blocked, state why.
- Original video link/path: required in strict reports, labeled `视频链接` or `原始视频链接`.

## Replication vs Optimization

Default:

- Good execution: 1:1 replication plan.
- Weak execution: optimized replacement only.

Exception:

- If the user asks for full replication, include weak-part replication, but label it as weak and still include the optimized replacement.

## HTML Contract Markers

Future reports should use these markers so the checker can validate depth deterministically:

```html
<article data-contract="shot">...</article>
<tr data-contract="highlight-line">...</tr>
<article data-contract="good-card">...</article>
<article data-contract="bad-card">...</article>
```

Use semantic tags as preferred by the template, but keep the `data-contract` attributes unchanged.
