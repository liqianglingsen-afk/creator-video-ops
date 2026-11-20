---
name: short-video-forensic-teardown
description: Use for Chinese short-video forensic teardown when the user says 拆解视频, 视频拆解, 前3秒钩子, 语言心理钩子, 爆款视频, 图文并茂HTML, or asks for 抖音/Douyin/小红书/Xiaohongshu/视频号 visual, shooting, editing, subtitle packaging, highlight-line audio-visual sync, 剪映/CapCut/Jianying beginner replication, or optimization plans. Default output is an image-rich HTML report unless the user asks for text only.
---

# Short Video Forensic Teardown

Use this as the primary workflow for Chinese short-video teardown. The expected result is not a generic critique; it is a frame-evidenced, timestamped, beginner-operable teardown with an HTML artifact.

If the user explicitly invokes `viral-video-deep-dive`, still use this workflow for new Chinese short-video teardown unless they only want to polish an existing report.

## Defaults

- Produce an image-rich HTML report in `outputs/` by default. Skip HTML only when the user explicitly asks for text only.
- Diagnose source quality before any visual claims: page metadata, visible formats, hidden streams, probed source, extracted frame resolution, subtitle/SRT availability.
- Every report must include the original video link/path in `源流质量诊断` under a clearly labeled `视频链接` or `原始视频链接` line. For local files, include both the user-provided path and any workspace-copied MP4 link; for platform links, include the user-provided URL, resolved/canonical URL when available, and the selected analysis media source when it can be linked.
- Treat the first 3 seconds as a mandatory language-psychology hook lab.
- Build a highlight-line audio-visual sync table for 爆点句、结论句、反差句、冲突句、价值句、情绪句、结果句.
- Good parts get 1:1 beginner replication cards.
- Bad parts get optimized replacement cards, not replication cards, unless the user explicitly asks to fully replicate the whole video.
- Prioritize runnable Codex operations. Include concrete timeline parameters that also transfer to 剪映/CapCut; give manual steps when a particular operation requires the editor.
- Set the minimum short-video optimization target to **85/100** (honor a higher brief). Use the ten weights in `score-rubric.md` (creative-100-v1), which sum directly to 100. Compare the exact capped sum to the target. Regrade both cuts on the same rubric for a before/after comparison.
- Build the existing-footage cut first using [the edit-plan contract](references/edit-plan.md). If asked to optimize, render a separate cut with Codex and rescore it. If only asked for analysis, deliver the runnable plan. Escalate to new content only for a documented gap.
- Use the fixed HTML framework template, but adapt CSS variables to the current video's extracted style profile.
- Measure or explicitly estimate subtitle rendered size and bottom safe area from frames when visual evidence is available.

- Follow [传播、美学与剪辑决策](references/editorial-review.md) for hook, CTA, cover, and creative or commercial review. Rank 1–3 edits for the actual goal; preserve convincing shots and disclose every release blocker.
- Score a supplied cover on its own two axes. For optimization use the cover and cut variant renderers, review phone previews, and keep the original as control. Record unavailable traffic or an unverified destination explicitly.

## Required References

Load only the reference needed for the current step:

When running commands below, resolve `<skill-dir>` to this skill folder and
`<skills-root>` to its parent skills folder. This keeps the workflow portable
between Windows and macOS.

- `references/forensic-output-contract.md`: mandatory report sections and acceptance criteria.
- `references/score-rubric.md`: 100-point scoring system.
- `references/jianying-ops.md`: beginner-level subtitle, camera, mask, keyframe, cutout, and alignment parameters.
- `templates/forensic_report_template.html`: fixed HTML framework and required contract markers.
- `scripts/extract_style_profile.py`: extracts a readable report color profile from local frames.
- `scripts/measure_subtitles.py`: estimates subtitle rendered size, bottom margin, and confidence from local frames.
- `scripts/check_report_contract.py`: validates report depth, markers, local images, score dimensions, and weak-part replication rules.
- `scripts/check_report_layout.py`: validates compact header spacing and evidence-image layout safety.

## Workflow

1. Confirm the task type.
   - If the user says `拆解视频` with a link, start immediately.
   - Capture the exact original input video URL or local file path before any probing, redirect resolution, download, cache reuse, or workspace copy.
   - If the user asks for complete replication, enable the weak-part replication exception.
   - If the user only asks to edit an existing artifact, do not rerun video download or analysis unless needed.

2. Acquire the best verified media source.
   - Preserve the source chain:
     - `原始视频链接`: the exact URL or local path supplied by the user.
     - `解析/跳转后链接`: the resolved platform/canonical URL when applicable.
     - `分析源链接`: the selected local MP4/cache/download path or playable stream URL when it is safe and useful to expose.
   - For local videos, copy or reference the file into the workspace when practical and create a relative HTML link to that workspace copy.
   - Use `video-understanding` metadata first when available.
   - For Xiaohongshu, use:

```bash
python "<skills-root>/viral-video-deep-dive/scripts/probe_xhs_media.py" "<video-url>"
```

   - For Douyin, try platform extraction and browser-cookie fallback when needed.
   - If no media can be obtained, state that visual analysis is blocked and ask for an MP4/screen recording. Do not invent visual details.

3. Record source-quality evidence.
   - Original video link/path and workspace analysis-source link. This must appear in the HTML as `视频链接` or `原始视频链接`.
   - Page/platform metadata resolution.
   - `yt-dlp -F` visible formats when relevant.
   - Hidden playable stream candidates.
   - Actual downloaded/probed resolution from `ffprobe`.
   - Extracted frame resolution.
   - Subtitle/SRT source.
   - Explain any mismatch, for example page metadata says 4K but the playable/downloaded source is 1080p.

4. Extract evidence.
   - Extract dense frames for 0-5s.
   - Extract timeline frames for the full video.
   - Create screenshot assets and contact sheets under `outputs/assets/`.
   - Gather transcript from platform SRT, burned-in subtitles, OCR, Whisper, or page text. Mark evidence source for uncertain lines.
   - Keep at least 12 local evidence images for a full HTML report unless the source is blocked.
   - Run subtitle measurement when frames contain burned-in captions:

```bash
python "<skill-dir>/scripts/measure_subtitles.py" "<frames-dir>" -o "<subtitle-measurements.json>"
```

   - Run style profiling for report colors:

```bash
python "<skill-dir>/scripts/extract_style_profile.py" "<frames-dir>" -o "<style-profile.json>"
```

5. Analyze the opening hook.
   - Split 0-3s into 0-1s, 1-2s, 2-3s.
   - Quote the exact opening line when available.
   - Label psychology mechanisms: loss aversion, identity threat, result promise, contrast/conflict, authority, sample size, curiosity gap, specific number, task substitution, emotional naming.
   - Decide whether it is a real retention hook or only background setup.
   - If weak, provide three stronger replacement openings.

6. Build the full teardown.
   - Script structure and retention logic.
   - Shot-by-shot visual timeline with at least 12 `data-contract="shot"` nodes in HTML.
   - Shooting, framing, camera movement, edit rhythm, packaging, subtitles, masks, cutouts, and alignment.
   - Highlight-line audio-visual sync table with at least seven line types when evidence exists: 爆点句、结论句、反差句、冲突句、价值句、情绪句、结果句/CTA.
   - Good-part replication cards: at least 3, only for execution worth copying.
   - Weak-part optimization cards: at least 3, optimized replacement only unless full replication was requested.
   - 100-point score with all 10 fixed dimensions, current score, target score, deductions, evidence, cap rules, and priority improvements.
   - Include the edit decision list, the planned route and any evidence-backed fallback from `references/edit-plan.md`. Show source and revised scores separately.
   - Subtitle section must include 字幕测量, 字号参考来源, and the software-difference note from `jianying-ops.md`.

7. Generate the HTML artifact.
   - Use `templates/forensic_report_template.html` as the fixed framework.
   - Apply CSS variables from `extract_style_profile.py`; if style extraction fails, use a readable neutral fallback and explain the fallback.
   - Use real extracted frames; do not use generic decorative images as evidence.
   - Include the exact sections in `references/forensic-output-contract.md`.
   - In `源流质量诊断`, include a visible `视频链接` line before technical ffprobe details. Do not bury the original URL/path only in prose.
   - Keep copy practical and creator-facing.
   - Use relative image paths from the HTML to `assets/`.
   - Verify all image paths exist.
   - Use a compact report header; do not use viewport-height hero spacing.
   - For side-by-side image/text sections, create fitted evidence grids first. Do not force ultra-wide or ultra-flat screenshots into tall blocks with CSS.
   - Proof-critical images such as subtitles, bills, AI output, score sheets, UI screenshots, and comments must remain fully inspectable. Use complete-display treatment, not evidence-cropping `cover`.
   - Preserve these contract markers in the rendered HTML:
     - `data-contract="shot"`
     - `data-contract="highlight-line"`
     - `data-contract="good-card"`
     - `data-contract="bad-card"`

8. Validate the report contract.
   - Run:

```bash
python "<skill-dir>/scripts/check_report_contract.py" "<html-path>" --require-current-rubric --require-editorial
```

   - Run:

```bash
python "<skill-dir>/scripts/check_report_layout.py" "<html-path>"
```

   - Fix any missing required section, broken image, excessive header whitespace, or unsafe evidence-image cropping before final response.
   - For old pre-upgrade reports only, `--legacy` may be used to inspect compatibility; new reports must pass the strict check.

## Output Rules

- Final response must link the HTML file in `outputs/`.
- The HTML report must expose the original video link/path in the `源流质量诊断` section. If a workspace copy exists, link it too.
- If visual evidence is partial, state exactly which sections are source-backed and which are inference.
- Do not claim platform metrics that were not available.
- Do not conflate metadata resolution with actual media resolution.
- Do not provide a 1:1 tutorial for weak execution unless full replication was explicitly requested.
- Prefer concrete parameter ranges over adjectives like "更大", "更醒目", or "更有节奏".
