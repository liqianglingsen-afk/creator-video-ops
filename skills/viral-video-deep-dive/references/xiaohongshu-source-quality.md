# Xiaohongshu Source Quality Rules

Xiaohongshu pages can expose different media facts at the same time. Do not treat them as interchangeable.

## Required Distinctions

1. Page metadata resolution:
   - Often appears inside `mediaV2.video.width` and `mediaV2.video.height`.
   - This may represent the uploaded/original media record.
   - It is not proof that a playable stream of that resolution is available.

2. Visible extractor formats:
   - Usually from `yt-dlp -F` or `yt-dlp --dump-json`.
   - These may only include ordinary webpage streams, for example 720x1280 h264.

3. Hidden playable streams:
   - Can appear inside page dump `mediaV2.video.opaque1`, such as `hd_screencast_stream`.
   - Must be probed or downloaded and verified with `ffprobe`.

4. Actual analysis source:
   - The stream finally used for frames/transcript/media inspection.
   - Report this as "本次分析源" or "抽帧源", not "原片规格" unless verified from an original file.

5. Hidden subtitles:
   - `yt-dlp --list-subs` may show no subtitles.
   - `mediaV2.video.subtitles` may still expose SRT URLs.
   - Prefer hidden SRT over Whisper when available, then use burned-in subtitles and Whisper for cross-checking.

## Default Commands

```bash
yt-dlp -F "<xhs-url>"
python "<skills-root>/viral-video-deep-dive/scripts/probe_xhs_media.py" "<xhs-url>"
ffprobe -v error -show_entries stream=index,codec_name,codec_type,width,height,duration,bit_rate -show_entries format=duration,size,bit_rate -of json "<downloaded-video>"
```

## Report Language

Use precise wording:

- Good: `页面元数据为 2160x3840；当前可下载高清流为 1080x1920；公开 extractor 默认流为 720x1280。`
- Bad: `原片是 720x1280。`

If true 4K is requested but not exposed:

`当前公开网页没有暴露 2160x3840 可播放 CDN。要做真正 4K 逐帧拆解，需要原始 MP4，或提供能访问 4K 流的登录态/平台侧资源。`
