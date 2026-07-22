# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "google-genai>=2.0.0",
#   "playwright>=1.40.0",
#   "yt-dlp>=2025.0.0",
# ]
# ///

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

from google import genai
from google.genai import types


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_PROMPT = """Analyze this video and return valid JSON only.

Include:
- transcript: timestamped verbatim transcript with [MM:SS] markers when possible
- description: visual description of people, setting, camera framing, on-screen text, UI, layout, gestures, scene changes, and pacing
- summary: 2-3 sentence summary
- duration_seconds: estimated duration
- speakers: identified speakers or speaker roles
"""

DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)
VIDEO_EXTENSIONS = (".mp4", ".m4v", ".mov", ".webm", ".m3u8")
IMAGE_KEYWORDS = ("cover", "thumb", "avatar", "image", "img", "poster", "headurl")


def is_youtube_url(url: str) -> bool:
    return bool(re.search(r"(youtube\.com|youtu\.be)", url, re.I))


def is_douyin_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(domain in host for domain in ("douyin.com", "iesdouyin.com", "amemv.com"))


def is_wechat_channels_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "weixin.qq.com" in host and "/sph/" in path:
        return True
    return "channels.weixin.qq.com" in host and "/finder-preview/" in path


def extract_wechat_short_uri(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("id", "shortUri", "short_uri"):
        value = query.get(key)
        if value and value[0]:
            return re.sub(r"[^A-Za-z0-9_-]", "", value[0])
    match = re.search(r"/sph/([A-Za-z0-9_-]+)", parsed.path)
    if match:
        return match.group(1)
    return None


def canonical_wechat_url(url: str) -> str:
    short_uri = extract_wechat_short_uri(url)
    if short_uri:
        return f"https://channels.weixin.qq.com/finder-preview/pages/sph?id={quote(short_uri)}"
    return url


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def truncate(text: str, limit: int = 1600) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def resolve_redirect_url(url: str) -> str | None:
    headers = {
        "User-Agent": MOBILE_UA if is_douyin_url(url) else DESKTOP_UA,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if is_douyin_url(url):
        headers["Referer"] = "https://www.douyin.com/"
    try:
        request = Request(url, headers=headers, method="GET")
        with urlopen(request, timeout=20) as response:
            return response.geturl()
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None


def candidate_urls_for_ytdlp(url: str) -> list[str]:
    candidates = [url]
    resolved = resolve_redirect_url(url) if is_douyin_url(url) else None
    if resolved and resolved not in candidates:
        candidates.append(resolved)
    return candidates


def ytdlp_base_args(url: str, cookies_from_browser: str | None = None) -> list[str]:
    args = [
        "yt-dlp",
        "--no-playlist",
        "--force-ipv4",
        "--user-agent",
        MOBILE_UA if is_douyin_url(url) else DESKTOP_UA,
        "--add-header",
        "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
    ]
    if is_douyin_url(url):
        args.extend(["--referer", "https://www.douyin.com/"])
    if cookies_from_browser:
        args.extend(["--cookies-from-browser", cookies_from_browser])
    return args


def friendly_ytdlp_error(url: str, attempts: list[dict[str, str]]) -> str:
    last_error = attempts[-1]["error"] if attempts else "yt-dlp failed"
    if is_douyin_url(url):
        return (
            "yt-dlp could not access this Douyin link after redirect resolution. "
            "The video may require login, browser cookies, captcha verification, "
            "or it may be private/deleted. Try --cookies-from-browser chrome or "
            "--cookies-from-browser edge, or provide a downloaded MP4. Last error: "
            f"{truncate(last_error)}"
        )
    return truncate(last_error)


def get_metadata(url: str, cookies_from_browser: str | None = None) -> dict[str, Any]:
    if is_wechat_channels_url(url):
        probe = probe_wechat_channel(url)
        metadata = probe.get("metadata") or {"source_url": url}
        metadata["wechat_probe_status"] = probe.get("status")
        return metadata

    attempts: list[dict[str, str]] = []
    for candidate in candidate_urls_for_ytdlp(url):
        proc = run_command(ytdlp_base_args(candidate, cookies_from_browser) + ["--dump-json", candidate])
        if proc.returncode != 0:
            attempts.append({"url": candidate, "error": proc.stderr.strip() or proc.stdout.strip()})
            continue
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            attempts.append({"url": candidate, "error": "yt-dlp returned non-JSON metadata"})
            continue

        keys = [
            "id",
            "title",
            "description",
            "duration",
            "view_count",
            "like_count",
            "comment_count",
            "uploader",
            "channel",
            "upload_date",
            "webpage_url",
            "extractor",
            "tags",
            "categories",
        ]
        metadata = {k: data.get(k) for k in keys if k in data}
        if candidate != url:
            metadata["resolved_url"] = candidate
            metadata["source_url"] = url
        return metadata

    return {
        "metadata_error": friendly_ytdlp_error(url, attempts),
        "source_url": url,
        "attempted_urls": [item["url"] for item in attempts],
    }


def download_video(
    url: str,
    output: str | None,
    max_size_mb: int,
    cookies_from_browser: str | None = None,
) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="video-understanding-"))
    if output:
        out_template = str(Path(output))
    else:
        out_template = str(temp_dir / "video.%(ext)s")

    attempts: list[dict[str, str]] = []
    for candidate in candidate_urls_for_ytdlp(url):
        proc = run_command(
            ytdlp_base_args(candidate, cookies_from_browser)
            + [
                "-f",
                "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
                "--merge-output-format",
                "mp4",
                "--max-filesize",
                f"{max_size_mb}M",
                "-o",
                out_template,
                candidate,
            ]
        )
        if proc.returncode != 0:
            attempts.append({"url": candidate, "error": proc.stderr.strip() or proc.stdout.strip()})
            continue

        if output:
            path = Path(output)
            if path.exists():
                return path

        candidates = sorted(temp_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0]
        attempts.append({"url": candidate, "error": "yt-dlp completed but no downloaded file was found"})

    raise RuntimeError(friendly_ytdlp_error(url, attempts))


def first_deep_value(obj: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(obj, dict):
        for key in keys:
            if key in obj and obj[key] not in (None, ""):
                return obj[key]
        for value in obj.values():
            found = first_deep_value(value, keys)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = first_deep_value(item, keys)
            if found not in (None, ""):
                return found
    return None


def find_feed_info(obj: Any) -> dict[str, Any] | None:
    if isinstance(obj, dict):
        feed_info = obj.get("feedInfo") or obj.get("feed_info")
        if isinstance(feed_info, dict):
            return feed_info
        for value in obj.values():
            found = find_feed_info(value)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_feed_info(item)
            if found:
                return found
    return None


def collect_url_entries(obj: Any, path: str = "") -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_path = f"{path}.{key}" if path else str(key)
            entries.extend(collect_url_entries(value, next_path))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            entries.extend(collect_url_entries(value, f"{path}[{index}]"))
    elif isinstance(obj, str) and obj.startswith(("http://", "https://")):
        entries.append({"path": path, "url": obj})
    return entries


def looks_like_image_key(path: str, url: str) -> bool:
    lower_path = path.lower()
    lower_url = url.lower()
    return any(word in lower_path for word in IMAGE_KEYWORDS) or "picformat=" in lower_url


def looks_like_video_url(url: str, path: str = "") -> bool:
    parsed = urlparse(url)
    lower_url = url.lower()
    lower_path = path.lower()
    if looks_like_image_key(path, url):
        return False
    if parsed.path.lower().endswith(VIDEO_EXTENSIONS):
        return True
    if ".m3u8" in lower_url or ".mp4" in lower_url:
        return True
    if "finder.video.qq.com" in parsed.netloc.lower() and any(
        token in lower_path for token in ("video", "media", "url", "stream", "file")
    ):
        return True
    return False


def response_looks_like_video(url: str, content_type: str) -> bool:
    lower_content_type = content_type.lower()
    lower_url = url.lower()
    if lower_content_type.startswith("video/"):
        return True
    if "application/vnd.apple.mpegurl" in lower_content_type or "application/x-mpegurl" in lower_content_type:
        return True
    return any(ext in lower_url for ext in VIDEO_EXTENSIONS)


def find_browser_executable() -> str | None:
    candidates = [
        os.environ.get("CHROME_PATH"),
        os.environ.get("EDGE_PATH"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def compact_feed_info(feed_info: dict[str, Any] | None) -> dict[str, Any]:
    if not feed_info:
        return {}
    keep_keys = [
        "id",
        "exportId",
        "description",
        "nickname",
        "createtime",
        "likeCount",
        "likeCountFmt",
        "favCount",
        "favCountFmt",
        "forwardCount",
        "forwardCountFmt",
        "commentCount",
        "commentCountFmt",
        "coverUrl",
        "isHardAd",
    ]
    compact = {key: feed_info.get(key) for key in keep_keys if key in feed_info}
    object_desc = feed_info.get("objectDesc")
    if isinstance(object_desc, dict):
        compact["objectDesc_keys"] = sorted(object_desc.keys())
        media = object_desc.get("media")
        if isinstance(media, list):
            compact["media_count"] = len(media)
    return compact


def metadata_from_wechat_probe(probe: dict[str, Any]) -> dict[str, Any]:
    feed_info = probe.get("_feed_info") if isinstance(probe.get("_feed_info"), dict) else None
    short_uri = extract_wechat_short_uri(probe.get("source_url", "") or "")
    description = first_deep_value(feed_info, ("description", "desc")) if feed_info else None
    nickname = first_deep_value(feed_info, ("nickname", "nickName")) if feed_info else None
    cover_url = first_deep_value(feed_info, ("coverUrl", "cover_url", "thumbUrl", "poster")) if feed_info else None
    create_time = first_deep_value(feed_info, ("createtime", "createTime", "create_time")) if feed_info else None

    metadata: dict[str, Any] = {
        "id": short_uri,
        "extractor": "wechat_channels_browser_probe",
        "source_url": probe.get("source_url"),
        "webpage_url": probe.get("canonical_url") or probe.get("final_url"),
    }
    if description:
        metadata["title"] = str(description).splitlines()[0][:80]
        metadata["description"] = description
    if nickname:
        metadata["uploader"] = nickname
        metadata["channel"] = nickname
    if cover_url:
        metadata["thumbnail"] = cover_url
    if create_time:
        metadata["timestamp"] = create_time
        try:
            metadata["upload_date"] = datetime.fromtimestamp(int(create_time)).strftime("%Y%m%d")
        except (TypeError, ValueError, OSError):
            pass

    for source_key, target_key in (
        ("likeCount", "like_count"),
        ("commentCount", "comment_count"),
        ("favCount", "favorite_count"),
        ("forwardCount", "share_count"),
        ("likeCountFmt", "like_count_fmt"),
        ("commentCountFmt", "comment_count_fmt"),
        ("favCountFmt", "favorite_count_fmt"),
        ("forwardCountFmt", "share_count_fmt"),
    ):
        value = first_deep_value(feed_info, (source_key,)) if feed_info else None
        if value not in (None, ""):
            metadata[target_key] = value

    if probe.get("video_url"):
        metadata["video_url"] = probe["video_url"]
    if probe.get("page_title"):
        metadata["page_title"] = probe["page_title"]
    if probe.get("page_text"):
        metadata["page_text"] = truncate(probe["page_text"], 1200)
    return {key: value for key, value in metadata.items() if value not in (None, "", [])}


def probe_wechat_channel(url: str, timeout_ms: int = 45000) -> dict[str, Any]:
    canonical_url = canonical_wechat_url(url)
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {
            "status": "playwright_missing",
            "source_url": url,
            "canonical_url": canonical_url,
            "error": f"Playwright is required for WeChat Channels browser probing: {exc}",
        }

    feed_payloads: list[dict[str, Any]] = []
    media_responses: list[dict[str, Any]] = []
    response_errors: list[str] = []
    video_elements: list[dict[str, str]] = []
    page_title = ""
    page_text = ""
    final_url = canonical_url
    cookies_header = ""

    try:
        with sync_playwright() as playwright:
            launch_kwargs: dict[str, Any] = {"headless": True}
            browser_path = find_browser_executable()
            if browser_path:
                launch_kwargs["executable_path"] = browser_path
            browser = playwright.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                user_agent=DESKTOP_UA,
                locale="zh-CN",
                viewport={"width": 1365, "height": 900},
                ignore_https_errors=True,
            )
            page = context.new_page()

            def handle_response(response: Any) -> None:
                response_url = response.url
                headers = {k.lower(): v for k, v in response.headers.items()}
                content_type = headers.get("content-type", "")
                if response_looks_like_video(response_url, content_type):
                    media_responses.append(
                        {
                            "url": response_url,
                            "status": str(response.status),
                            "content_type": content_type,
                            "source": "network_response",
                        }
                    )
                if "feed/get_feed_info" not in response_url:
                    return
                try:
                    text = response.text()
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        payload = {"raw": truncate(text)}
                    feed_payloads.append(
                        {
                            "url": response_url,
                            "status": response.status,
                            "content_type": content_type,
                            "payload": payload,
                        }
                    )
                except Exception as exc:
                    response_errors.append(f"{response_url}: {exc}")

            page.on("response", handle_response)
            try:
                page.goto(canonical_url, wait_until="domcontentloaded", timeout=timeout_ms)
            except PlaywrightTimeoutError:
                response_errors.append("Page load timed out after DOMContentLoaded wait; using captured responses.")
            page.wait_for_timeout(5000)
            final_url = page.url
            try:
                page_title = page.title()
            except PlaywrightError:
                page_title = ""
            try:
                page_text = page.locator("body").inner_text(timeout=5000)
            except PlaywrightError:
                page_text = ""
            try:
                video_elements = page.evaluate(
                    """() => Array.from(document.querySelectorAll('video')).map((video) => ({
                        src: video.getAttribute('src') || '',
                        currentSrc: video.currentSrc || '',
                        poster: video.getAttribute('poster') || video.poster || ''
                    }))"""
                )
            except PlaywrightError:
                video_elements = []

            cookies = context.cookies()
            if cookies:
                cookies_header = "; ".join(f"{cookie['name']}={cookie['value']}" for cookie in cookies)
            context.close()
            browser.close()
    except Exception as exc:
        return {
            "status": "browser_probe_failed",
            "source_url": url,
            "canonical_url": canonical_url,
            "error": str(exc),
        }

    feed_info: dict[str, Any] | None = None
    if feed_payloads:
        for item in reversed(feed_payloads):
            feed_info = find_feed_info(item.get("payload"))
            if feed_info:
                break

    candidates: list[dict[str, str]] = []
    if feed_info:
        for entry in collect_url_entries(feed_info):
            if looks_like_video_url(entry["url"], entry["path"]):
                candidates.append({**entry, "source": "feed_info"})
    for item in media_responses:
        if looks_like_video_url(item["url"]) or response_looks_like_video(item["url"], item.get("content_type", "")):
            candidates.append({"path": item.get("content_type", ""), "url": item["url"], "source": item["source"]})
    for item in video_elements:
        for key in ("currentSrc", "src"):
            value = item.get(key)
            if value and looks_like_video_url(value, key):
                candidates.append({"path": key, "url": value, "source": "video_element"})

    seen: set[str] = set()
    unique_candidates: list[dict[str, str]] = []
    for candidate in candidates:
        candidate_url = candidate["url"]
        if candidate_url not in seen:
            unique_candidates.append(candidate)
            seen.add(candidate_url)

    video_url = unique_candidates[0]["url"] if unique_candidates else None
    probe: dict[str, Any] = {
        "status": "ok" if (feed_info or page_text) else "no_public_feed_response",
        "source_url": url,
        "canonical_url": canonical_url,
        "final_url": final_url,
        "page_title": page_title,
        "page_text": truncate(page_text, 1600) if page_text else "",
        "api_response_count": len(feed_payloads),
        "video_url": video_url,
        "media_candidates": unique_candidates[:5],
        "feed_info": compact_feed_info(feed_info),
        "video_elements": video_elements[:5],
        "response_errors": response_errors[:5],
        "_feed_info": feed_info,
        "_download_headers": {
            "User-Agent": DESKTOP_UA,
            "Referer": canonical_url,
            **({"Cookie": cookies_header} if cookies_header else {}),
        },
    }
    probe["metadata"] = metadata_from_wechat_probe(probe)
    return probe


def public_probe(probe: dict[str, Any]) -> dict[str, Any]:
    clean = {key: value for key, value in probe.items() if not key.startswith("_")}
    if clean.get("page_text"):
        clean["page_text"] = truncate(str(clean["page_text"]), 1200)
    return clean


def extension_from_response(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix
    if suffix and len(suffix) <= 6:
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
    if guessed in {".jpe"}:
        return ".jpg"
    if guessed and guessed not in {".bin"}:
        return guessed
    return ".mp4"


def direct_ytdlp_header_args(headers: dict[str, str]) -> list[str]:
    args: list[str] = []
    for key, value in headers.items():
        if not value:
            continue
        lower = key.lower()
        if lower == "user-agent":
            args.extend(["--user-agent", value])
        elif lower == "referer":
            args.extend(["--referer", value])
        else:
            args.extend(["--add-header", f"{key}: {value}"])
    return args


def download_direct_media(
    url: str,
    output: str | None,
    max_size_mb: int,
    headers: dict[str, str] | None = None,
) -> Path:
    headers = headers or {"User-Agent": DESKTOP_UA}
    lower_url = url.lower()
    if ".m3u8" in lower_url:
        temp_dir = Path(tempfile.mkdtemp(prefix="video-understanding-"))
        out_template = str(Path(output)) if output else str(temp_dir / "video.%(ext)s")
        proc = run_command(
            ["yt-dlp"]
            + direct_ytdlp_header_args(headers)
            + [
                "--max-filesize",
                f"{max_size_mb}M",
                "--merge-output-format",
                "mp4",
                "-o",
                out_template,
                url,
            ]
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "direct media download failed")
        if output and Path(output).exists():
            return Path(output)
        candidates = sorted(temp_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise RuntimeError("direct media download completed but no file was found")
        return candidates[0]

    request = Request(url, headers=headers)
    max_bytes = max_size_mb * 1024 * 1024
    temp_dir = Path(tempfile.mkdtemp(prefix="video-understanding-"))
    downloaded = 0
    path: Path | None = None
    try:
        with urlopen(request, timeout=90) as response:
            content_type = response.headers.get("content-type", "video/mp4")
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > max_bytes:
                raise RuntimeError(f"media exceeds --max-size limit: {content_length} bytes")
            path = Path(output) if output else temp_dir / f"video{extension_from_response(url, content_type)}"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > max_bytes:
                        raise RuntimeError(f"media exceeds --max-size limit: {max_size_mb} MB")
                    handle.write(chunk)
        if not path or not path.exists() or path.stat().st_size == 0:
            raise RuntimeError("direct media download produced an empty file")
        return path
    except Exception:
        if path:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        raise


def build_prompt(question: str | None, prompt: str | None) -> str:
    if prompt:
        return prompt
    if question:
        return DEFAULT_PROMPT + f"\nAlso answer this question in an `answer` field: {question}"
    return DEFAULT_PROMPT


def generate_for_youtube(client: genai.Client, model: str, url: str, prompt: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                parts=[
                    types.Part(file_data=types.FileData(file_uri=url, mime_type="video/mp4")),
                    types.Part(text=prompt),
                ]
            )
        ],
    )
    return response.text or ""


def wait_for_file(client: genai.Client, name: str, timeout_seconds: int = 900) -> Any:
    deadline = time.time() + timeout_seconds
    current = client.files.get(name=name)
    while getattr(getattr(current, "state", None), "name", "") == "PROCESSING":
        if time.time() > deadline:
            raise TimeoutError("Timed out waiting for Gemini to process uploaded video")
        time.sleep(5)
        current = client.files.get(name=name)

    state = getattr(getattr(current, "state", None), "name", "")
    if state and state not in {"ACTIVE", "SUCCEEDED"}:
        raise RuntimeError(f"Gemini file processing ended in state: {state}")
    return current


def generate_for_file(client: genai.Client, model: str, path: Path, prompt: str) -> str:
    uploaded = client.files.upload(file=str(path))
    try:
        ready = wait_for_file(client, uploaded.name)
        response = client.models.generate_content(model=model, contents=[ready, prompt])
        return response.text or ""
    finally:
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass


def maybe_parse_json(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return {"raw": text}


def emit(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text)


def handle_wechat(args: argparse.Namespace) -> int:
    probe = probe_wechat_channel(args.url)
    metadata = probe.get("metadata") or {"source_url": args.url}

    if args.metadata_only:
        emit({"status": "metadata_only", "metadata": metadata, "wechat_probe": public_probe(probe)}, args.output)
        return 0 if probe.get("status") != "browser_probe_failed" else 1

    downloaded_path: Path | None = None
    try:
        if args.download_only:
            video_url = probe.get("video_url")
            if not video_url:
                emit(
                    {
                        "status": "wechat_no_playable_video_url",
                        "message": (
                            "The browser-accessible WeChat Channels page exposed metadata or cover content, "
                            "but no playable video URL. Open the item in WeChat and provide an MP4/screen "
                            "recording, or use a link that plays directly in a browser."
                        ),
                        "metadata": metadata,
                        "wechat_probe": public_probe(probe),
                    },
                    args.output,
                )
                return 3
            downloaded_path = download_direct_media(
                video_url,
                args.output,
                args.max_size,
                headers=probe.get("_download_headers"),
            )
            print(str(downloaded_path))
            return 0

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            emit(
                {
                    "status": "gemini_key_missing",
                    "message": (
                        "GEMINI_API_KEY or GOOGLE_API_KEY is not set; visual and audio Gemini analysis was not run."
                    ),
                    "metadata": metadata,
                    "wechat_probe": public_probe(probe),
                },
                args.output,
            )
            return 2

        video_url = probe.get("video_url")
        if not video_url:
            emit(
                {
                    "status": "wechat_no_playable_video_url",
                    "message": (
                        "The WeChat Channels web page was readable for public metadata, but it did not expose "
                        "a playable video stream to the browser session. Visual analysis cannot run from this "
                        "link alone. Provide an MP4/screen recording, or open the item in WeChat and share a "
                        "browser-playable public video link."
                    ),
                    "metadata": metadata,
                    "wechat_probe": public_probe(probe),
                },
                args.output,
            )
            return 0

        downloaded_path = download_direct_media(video_url, None, args.max_size, headers=probe.get("_download_headers"))
        client = genai.Client(api_key=api_key)
        prompt = build_prompt(args.question, args.prompt)
        result_text = generate_for_file(client, args.model, downloaded_path, prompt)
        analysis = {"raw": result_text} if args.raw else maybe_parse_json(result_text)
        emit({"status": "ok", "metadata": metadata, "wechat_probe": public_probe(probe), "analysis": analysis}, args.output)
        return 0
    except Exception as exc:
        emit({"status": "error", "error": str(exc), "metadata": metadata, "wechat_probe": public_probe(probe)}, args.output)
        return 1
    finally:
        if downloaded_path and not args.keep and "video-understanding-" in str(downloaded_path.parent):
            try:
                downloaded_path.unlink(missing_ok=True)
                downloaded_path.parent.rmdir()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a video URL with Gemini video understanding.")
    parser.add_argument("url", help="Public video URL")
    parser.add_argument("-q", "--question", help="Question to answer about the video")
    parser.add_argument("-p", "--prompt", help="Override the default prompt")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Gemini model")
    parser.add_argument("-o", "--output", help="Output JSON path; with --download-only this is the video path")
    parser.add_argument("--keep", action="store_true", help="Keep downloaded video for non-YouTube URLs")
    parser.add_argument("--download-only", action="store_true", help="Download the video and skip Gemini analysis")
    parser.add_argument("--metadata-only", action="store_true", help="Fetch metadata and skip Gemini analysis")
    parser.add_argument("--max-size", type=int, default=500, help="Max download size in MB")
    parser.add_argument("--raw", action="store_true", help="Print Gemini raw text inside JSON instead of parsing it")
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "edge", "firefox", "brave", "chromium", "vivaldi", "opera", "safari"],
        help="Pass browser cookies to yt-dlp for platforms that require login/captcha cookies.",
    )
    args = parser.parse_args()

    if is_wechat_channels_url(args.url):
        return handle_wechat(args)

    metadata = get_metadata(args.url, cookies_from_browser=args.cookies_from_browser)

    if args.metadata_only:
        emit({"status": "metadata_only", "metadata": metadata}, args.output)
        return 0

    downloaded_path: Path | None = None
    try:
        if args.download_only:
            downloaded_path = download_video(args.url, args.output, args.max_size, args.cookies_from_browser)
            print(str(downloaded_path))
            return 0

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            emit(
                {
                    "status": "gemini_key_missing",
                    "message": "GEMINI_API_KEY or GOOGLE_API_KEY is not set; visual and audio Gemini analysis was not run.",
                    "metadata": metadata,
                },
                args.output,
            )
            return 2

        client = genai.Client(api_key=api_key)
        prompt = build_prompt(args.question, args.prompt)
        if is_youtube_url(args.url):
            result_text = generate_for_youtube(client, args.model, args.url, prompt)
        else:
            downloaded_path = download_video(args.url, None, args.max_size, args.cookies_from_browser)
            result_text = generate_for_file(client, args.model, downloaded_path, prompt)

        analysis = {"raw": result_text} if args.raw else maybe_parse_json(result_text)
        emit({"status": "ok", "metadata": metadata, "analysis": analysis}, args.output)
        return 0
    except Exception as exc:
        emit({"status": "error", "error": str(exc), "metadata": metadata}, args.output)
        return 1
    finally:
        if downloaded_path and not args.keep and "video-understanding-" in str(downloaded_path.parent):
            try:
                downloaded_path.unlink(missing_ok=True)
                downloaded_path.parent.rmdir()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
