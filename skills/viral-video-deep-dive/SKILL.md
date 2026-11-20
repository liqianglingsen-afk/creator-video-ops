---
name: viral-video-deep-dive
description: Use as the legacy/router skill for viral-video-deep-dive requests and platform source-quality helpers. When the user says 拆解视频, 视频拆解, analyze/deconstruct a Chinese short-video link, 抖音, 小红书, 图文并茂HTML, 前3秒钩子, or asks about visuals, shooting, editing, captions, packaging, camera movement, highlight-line sync, replication, optimization, or creator strategy, route new teardown work to short-video-forensic-teardown by default and use this skill's scripts only as needed.
---

# Viral Video Deep Dive

Use this as the main entrypoint whenever the user asks to `拆解视频`, sends a public video link for teardown, or asks for a creator-facing analysis of visuals, shooting, editing, captions, packaging, camera movement, highlight-line sync, replication, or optimization.

Default stance: good parts teach the user how to copy; bad parts teach the user how to improve. Only teach exact replication of bad parts when the user explicitly asks to completely replicate the original video.

## Routing Rule

For new Chinese short-video teardown, use `short-video-forensic-teardown` as the primary workflow. This skill remains available for legacy explicit `viral-video-deep-dive` invocations, platform extraction helpers, Xiaohongshu source-quality probing, and generic creator-strategy analysis.

If both skills are active:

- Follow `short-video-forensic-teardown` for the output contract, default HTML deliverable, first-3-seconds language psychology hook, highlight-line sync table, good-part replication cards, weak-part optimization cards, scoring, and final report validation.
- Use this skill's `scripts/probe_xhs_media.py` and references only for platform/source-quality diagnostics.
- Do not produce a lighter Markdown-only report unless the user explicitly asks for text only.

## Workflow

When running commands below, resolve `<skills-root>` to the parent folder that
contains the installed skill directories. On macOS this is typically
`$HOME/.agents/skills` for user-installed skills.

1. Extract the video URL from the user request.
   - Preserve the exact original user-supplied URL or local video path. New teardown reports must display it in `源流质量诊断` as `视频链接` or `原始视频链接`.
2. Fetch public metadata first through `video-understanding`, because WeChat Channels and Douyin need platform-specific handling:

```bash
uv run "<skills-root>/video-understanding/scripts/analyze_video.py" "<video-url>" --metadata-only
```

3. Run source-quality diagnostics before claiming any resolution or using frames:

   - Always distinguish:
     - original user-supplied video URL/path
     - resolved/canonical platform URL when available
     - platform/page metadata resolution
     - formats visible to `yt-dlp -F`
     - hidden playable streams
     - actual downloaded/probed stream resolution
     - frame extraction source resolution
   - For Xiaohongshu links, run:

```bash
python "<skills-root>/viral-video-deep-dive/scripts/probe_xhs_media.py" "<video-url>"
```

   - Prefer the highest verified playable stream for analysis and frame extraction. Never call the downloaded stream "original resolution" unless it matches a verified original file.
   - See `references/xiaohongshu-source-quality.md` for the required interpretation rules.

4. Gather transcript evidence in this order:

   - platform-exposed subtitles or hidden SRT, if available
   - burned-in subtitle inspection from frame crops
   - local Whisper or equivalent transcription when needed
   - page description/caption text

   If signals conflict, state which source each line came from.

5. If `GEMINI_API_KEY` or `GOOGLE_API_KEY` exists, run multimodal analysis:

```bash
uv run "<skills-root>/video-understanding/scripts/analyze_video.py" "<video-url>" -p "Return valid JSON only. Analyze this video for a Chinese creator strategy report. Include transcript with timestamps, core thesis, hook, script structure, retention mechanics, emotional beats, visual layout, camera/framing, on-screen text, editing rhythm, product or promotion signals, proof elements, trust builders, calls to action, weak points, and concrete optimization suggestions."
```

6. If Gemini is unavailable, blocked, or returns an API/proxy error, do not stop. Use the local fallback:

   - download the highest verified playable stream
   - run `ffprobe` and record the actual source resolution
   - extract key frames, a timeline grid, and subtitle-area crops with `ffmpeg`
   - use subtitle/SRT/Whisper evidence for spoken lines
   - mark visual analysis as locally frame-verified instead of Gemini-verified

7. If the Gemini key is missing and no local media can be downloaded, downgrade clearly:
   - For YouTube, run:

```bash
python "<skills-root>/youtube-video-analyst/scripts/fetch_transcript.py" "<video-url>"
```

   - For non-YouTube, use `yt-dlp --write-auto-subs --write-subs --skip-download "<video-url>"` when subtitles are available.
   - State that visual analysis was not completed.

8. Apply the `youtube-video-analyst` forensic framework to the transcript, visuals, and media evidence.

9. If the user asks for HTML, generate a static, image-rich report in `outputs/` with assets under `outputs/assets/`. Use relative image paths, verify every referenced asset exists, and include source-quality notes.

## Replication vs Optimization Rules

Default split:

1. Good parts:
   - Explain why they work.
   - Provide a 1:1 beginner replication plan.
   - Include timestamp/frame evidence and exact implementation details: Jianying/CapCut steps, font, size, position, color, animation, camera movement, shot duration, and cut rhythm.

2. Bad parts:
   - Do not provide a replication plan by default.
   - Provide the optimized replacement plan instead.
   - Include exact steps for the improved version.

3. Full-replication exception:
   - If the user explicitly asks to fully replicate the whole video, including weak parts, provide:
     - original replication method
     - why it is weak
     - optimized replacement method
   - Never present weak original choices as recommended practice.

## Report Format

Return the report in Chinese with these sections:

1. `源流质量诊断`
   - `视频链接` / `原始视频链接`: user-supplied URL or local path, plus workspace-copied MP4/playable source when available
   - Page/platform metadata resolution
   - Visible `yt-dlp` formats
   - Hidden streams/subtitles found
   - Selected analysis source and extraction resolution
   - Any gap between "metadata resolution" and "actual playable stream"

2. `结论摘要`
   - One-sentence verdict
   - Why it likely worked or failed
   - Whether it has promotion/sales intent

3. `数据表现`
   - Title, creator/channel, duration, upload date, views, likes, comments when available
   - Note unavailable fields instead of inventing numbers

4. `综合评分体系`
   - Use the current [ten-dimension rubric](../short-video-forensic-teardown/references/score-rubric.md) for new work; the historical rubric is for comparison within a previously scored report.
   - Score every dimension with timestamp/frame/text evidence
   - Set a minimum optimization goal of 85/100. Use the [existing-footage edit plan](../short-video-forensic-teardown/references/edit-plan.md) and keep forecasts separate from exported-file scores.

5. `核心观点`
   - Main claim
   - Audience pain point
   - Promise or payoff

6. `脚本结构`
   - Hook
   - Setup
   - Evidence or story blocks
   - Turning points
   - CTA
   - Reusable script template

7. `口播文案`
   - Extract memorable lines
   - Summarize the spoken script
   - Provide a polished Chinese rewrite if useful

8. `视觉画面`
   - Framing, scene layout, people, props, product placement, subtitles, UI, on-screen text
   - Editing rhythm and visual retention devices
   - If Gemini was unavailable, mark this section as locally frame-verified or not visually verified

9. `高光句音画同步`
   - 爆点句、结论句、反差句、冲突句、价值句、情绪句、结果句
   - For each: audio emphasis, visual emphasis, subtitle emphasis, edit/cut emphasis

10. `表现好的地方：1:1 图文复刻`
   - Only include parts that are actually worth copying
   - Give beginner-operable steps with timestamps/frames

11. `表现不好的地方：优化后方案`
   - Do not teach copying bad execution unless full replication is explicitly requested
   - Give the improved version and exact implementation steps

12. `拉高数据的细节`
   - Retention hooks
   - Curiosity gaps
   - Pattern interrupts
   - Authority/trust signals
   - Emotional triggers

13. `字幕字体/字号/位置包装`
   - Font, size, position, color, stroke, shadow, highlight, line breaks, safe areas

14. `拍摄、剪辑、运镜、蒙版、抠像、对齐、剪映操作`
   - Beginner-level steps
   - Use exact tool names and parameter ranges when possible

15. `优化建议`
   - 3-7 concrete edits
   - Suggested opening rewrite
   - Suggested title/thumbnail or first-frame direction when relevant

## Rules

- Do not claim visual details unless they came from `video-understanding` output or actual media inspection.
- Do not invent platform metrics missing from metadata.
- Never conflate page metadata resolution with actual playable/downloaded stream resolution.
- For Xiaohongshu, check hidden media fields before concluding that only `yt-dlp -F` formats are available.
- If the user only asks to edit, polish, or reformat an existing report/artifact and does not request fresh video analysis, do not rerun downloads, probes, frame extraction, or transcription.
- For non-YouTube sources, warn that temporary download/upload may be required for Gemini analysis.
- For WeChat Channels, the script first probes the web page with a browser. If it returns `wechat_no_playable_video_url`, use the available metadata/page text only and ask for an MP4 or screen recording for visual analysis.
- For Douyin, the script resolves short links and tries stronger mobile headers. If Douyin still blocks access, ask for `--cookies-from-browser chrome` or `--cookies-from-browser edge`, or ask the user to provide an MP4.
- Keep the final report practical and creator-facing, not academic.
