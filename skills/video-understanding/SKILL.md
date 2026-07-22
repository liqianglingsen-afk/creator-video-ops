---
name: video-understanding
description: Analyze videos with Google Gemini multimodal AI. Use when Codex needs to watch, transcribe, summarize, describe, or answer questions about a video URL from YouTube, TikTok/Douyin, WeChat Channels, Vimeo, X/Twitter, Instagram, Loom, Bilibili, or other yt-dlp-supported sources. Requires yt-dlp, ffmpeg, Python 3.10+, uv, and GEMINI_API_KEY for multimodal analysis.
---

# Video Understanding

Use this skill to turn a public video URL into structured transcript and visual analysis using Gemini.

## Requirements

- `yt-dlp`
- `ffmpeg`
- Python 3.10+
- `uv`
- `playwright` for WeChat Channels browser probing
- `GEMINI_API_KEY` for Gemini video analysis

## Commands

When running commands below, resolve `<skill-dir>` to this skill folder. On
macOS, user-installed skills usually live under `$HOME/.agents/skills`.

Analyze a video and return structured JSON:

```bash
uv run "<skill-dir>/scripts/analyze_video.py" "<video-url>"
```

Ask a focused question:

```bash
uv run "<skill-dir>/scripts/analyze_video.py" "<video-url>" -q "What product is shown?"
```

Override the prompt:

```bash
uv run "<skill-dir>/scripts/analyze_video.py" "<video-url>" -p "Describe the hook, visual layout, and call to action." --raw
```

Download only:

```bash
uv run "<skill-dir>/scripts/analyze_video.py" "<video-url>" --download-only -o video.mp4
```

Metadata only:

```bash
uv run "<skill-dir>/scripts/analyze_video.py" "<video-url>" --metadata-only
```

Use browser cookies when Douyin or another platform requires login/captcha cookies:

```bash
uv run "<skill-dir>/scripts/analyze_video.py" "<video-url>" --cookies-from-browser chrome
```

## Behavior

- YouTube URLs are sent directly to Gemini when possible.
- Douyin short links are resolved before `yt-dlp` runs, with mobile browser headers and Douyin referer headers.
- WeChat Channels links are probed with a local browser session. If the web page exposes a playable stream, it is downloaded, uploaded to Gemini Files API, analyzed, then cleaned up. If the web page exposes only metadata/cover content, return `wechat_no_playable_video_url` instead of a generic unsupported-link error.
- Other video URLs are downloaded with `yt-dlp`, uploaded to Gemini Files API, analyzed, then cleaned up.
- If `GEMINI_API_KEY` is missing, return metadata-only output and clearly state that visual analysis was not run.
- Keep temporary downloads only when `--keep` is passed.

## Default Output

Return JSON with these fields when Gemini analysis succeeds:

- `transcript`: timestamped spoken content
- `description`: people, setting, scene flow, on-screen text, framing, UI, and visual structure
- `summary`: short content summary
- `duration_seconds`
- `speakers`
- `answer`: only when `--question` is used
