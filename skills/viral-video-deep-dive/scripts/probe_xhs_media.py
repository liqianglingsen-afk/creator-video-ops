#!/usr/bin/env python3
"""Probe Xiaohongshu media metadata, hidden streams, and hidden subtitles."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False, encoding="utf-8", errors="replace")


def decode_json_string(raw: str) -> str:
    try:
        return json.loads(f'"{raw}"')
    except json.JSONDecodeError:
        return raw.replace(r"\u002F", "/").replace(r"\/", "/").replace(r"\"", '"')


def extract_media_v2(page_text: str) -> dict[str, Any] | None:
    match = re.search(r'"mediaV2"\s*:\s*"(?P<raw>(?:\\.|[^"\\])*)"', page_text)
    if not match:
        return None
    decoded = decode_json_string(match.group("raw"))
    try:
        return json.loads(decoded)
    except json.JSONDecodeError:
        return None


def extract_urls_from_text(page_text: str, key: str) -> list[str]:
    pattern = rf'{re.escape(key)}\\?"\s*:\s*\\?"(?P<url>.*?)(?:\\?",|\\?"\}})'
    urls = []
    for match in re.finditer(pattern, page_text):
        url = decode_json_string(match.group("url"))
        if url.startswith(("http://", "https://")):
            urls.append(url)
    return sorted(set(urls))


def ytdlp_dump_json(url: str, cookies_from_browser: str | None = None) -> dict[str, Any]:
    args = ["yt-dlp", "--no-playlist", "--dump-json", url]
    if cookies_from_browser:
        args[1:1] = ["--cookies-from-browser", cookies_from_browser]
    proc = run_command(args)
    if proc.returncode != 0:
        return {"_error": proc.stderr.strip() or proc.stdout.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"_error": "yt-dlp returned non-JSON output", "_raw": proc.stdout[:1000]}


def write_pages_dump(url: str, cookies_from_browser: str | None = None) -> tuple[str, str | None]:
    with tempfile.TemporaryDirectory(prefix="xhs-probe-") as temp_name:
        temp_dir = Path(temp_name)
        args = ["yt-dlp", "--write-pages", "--skip-download", "--no-playlist", url]
        if cookies_from_browser:
            args[1:1] = ["--cookies-from-browser", cookies_from_browser]
        proc = run_command(args, cwd=temp_dir)
        dumps = sorted(temp_dir.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not dumps:
            return "", proc.stderr.strip() or proc.stdout.strip() or "no dump file produced"
        return dumps[0].read_text(encoding="utf-8", errors="replace"), None


def ffprobe_url(url: str) -> dict[str, Any] | None:
    proc = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_name,codec_type,width,height,duration,bit_rate",
            "-show_entries",
            "format=duration,size,bit_rate",
            "-of",
            "json",
            url,
        ]
    )
    if proc.returncode != 0:
        return {"_error": proc.stderr.strip() or proc.stdout.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"_error": "ffprobe returned non-JSON output"}


def video_dimensions_from_probe(probe: dict[str, Any] | None) -> tuple[int, int] | None:
    if not probe:
        return None
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video" and stream.get("width") and stream.get("height"):
            return int(stream["width"]), int(stream["height"])
    return None


def flatten_subtitles(subtitles: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(subtitles, dict):
        for language, items in subtitles.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and item.get("url"):
                        rows.append(
                            {
                                "language": item.get("language") or language,
                                "format": item.get("format"),
                                "type": item.get("type"),
                                "url": item.get("url"),
                            }
                        )
    return rows


def compact_metadata(data: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "id",
        "title",
        "duration",
        "view_count",
        "like_count",
        "comment_count",
        "uploader",
        "upload_date",
        "webpage_url",
        "extractor",
    ]
    return {key: data.get(key) for key in keys if key in data}


def visible_formats(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for fmt in data.get("formats") or []:
        rows.append(
            {
                "format_id": fmt.get("format_id"),
                "url": fmt.get("url"),
                "width": fmt.get("width"),
                "height": fmt.get("height"),
                "fps": fmt.get("fps"),
                "filesize": fmt.get("filesize"),
                "tbr": fmt.get("tbr"),
                "vcodec": fmt.get("vcodec"),
                "acodec": fmt.get("acodec"),
                "protocol": fmt.get("protocol"),
            }
        )
    return rows


def choose_selected(visible: list[dict[str, Any]], hidden: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = []
    for item in visible + hidden:
        width = item.get("width") or 0
        height = item.get("height") or 0
        candidates.append((int(width) * int(height), item))
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: row[0], reverse=True)[0][1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Xiaohongshu visible and hidden media streams.")
    parser.add_argument("url", help="Xiaohongshu note URL")
    parser.add_argument("-o", "--output", help="Write JSON output to this path")
    parser.add_argument("--cookies-from-browser", choices=["chrome", "edge", "firefox", "brave", "chromium", "vivaldi", "opera", "safari"])
    parser.add_argument("--no-ffprobe", action="store_true", help="Skip ffprobe on hidden stream URLs")
    args = parser.parse_args()

    ytdlp_data = ytdlp_dump_json(args.url, args.cookies_from_browser)
    page_text, dump_error = write_pages_dump(args.url, args.cookies_from_browser)
    media_v2 = extract_media_v2(page_text) if page_text else None

    visible = visible_formats(ytdlp_data) if "_error" not in ytdlp_data else []
    hidden_streams: list[dict[str, Any]] = []
    subtitles: list[dict[str, Any]] = []
    page_resolution = None

    if media_v2:
        video_info = media_v2.get("video") or {}
        if video_info.get("width") and video_info.get("height"):
            page_resolution = {"width": video_info.get("width"), "height": video_info.get("height")}

        opaque = video_info.get("opaque1") or {}
        for key in ("hd_screencast_stream", "default_screencast_stream"):
            url = opaque.get(key)
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                continue
            row: dict[str, Any] = {"source": key, "url": html.unescape(url)}
            if not args.no_ffprobe:
                probe = ffprobe_url(row["url"])
                row["ffprobe"] = probe
                dims = video_dimensions_from_probe(probe)
                if dims:
                    row["width"], row["height"] = dims
            hidden_streams.append(row)

        subtitles = flatten_subtitles(video_info.get("subtitles"))

    if not hidden_streams and page_text:
        for key in ("hd_screencast_stream", "default_screencast_stream"):
            for url in extract_urls_from_text(page_text, key):
                row = {"source": key, "url": html.unescape(url)}
                if not args.no_ffprobe:
                    probe = ffprobe_url(row["url"])
                    row["ffprobe"] = probe
                    dims = video_dimensions_from_probe(probe)
                    if dims:
                        row["width"], row["height"] = dims
                hidden_streams.append(row)

    selected = choose_selected(visible, hidden_streams)
    payload = {
        "status": "ok" if visible or hidden_streams or media_v2 else "partial",
        "source_url": args.url,
        "metadata": compact_metadata(ytdlp_data) if "_error" not in ytdlp_data else {"metadata_error": ytdlp_data.get("_error")},
        "page_metadata_resolution": page_resolution,
        "visible_formats": visible,
        "hidden_streams": hidden_streams,
        "hidden_subtitles": subtitles,
        "selected_source": selected,
        "dump_error": dump_error,
        "interpretation": (
            "page_metadata_resolution is not the same as the playable/downloaded stream. "
            "Use selected_source or a verified downloaded file as the analysis/frame-extraction source."
        ),
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0 if payload["status"] != "partial" else 1


if __name__ == "__main__":
    raise SystemExit(main())
