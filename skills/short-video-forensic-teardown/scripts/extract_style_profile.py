#!/usr/bin/env python3
"""Extract a readable report color profile from video frames.

This script intentionally uses only ffmpeg plus the Python standard library so
it can run in the Codex skill environment without extra package installation.
It samples average colors from local evidence frames, classifies the visual
mood, and returns CSS variables for the fixed teardown HTML template.
"""

from __future__ import annotations

import argparse
import colorsys
import json
import subprocess
import sys
from pathlib import Path
from statistics import mean


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def hls_to_hex(h: float, l: float, s: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h % 1.0, clamp(l), clamp(s))
    return rgb_to_hex((round(r * 255), round(g * 255), round(b * 255)))


def hex_from_float_rgb(rgb: tuple[float, float, float]) -> str:
    return rgb_to_hex(tuple(round(clamp(channel / 255.0) * 255) for channel in rgb))  # type: ignore[arg-type]


def collect_images(paths: list[Path], max_samples: int) -> list[Path]:
    images: list[Path] = []
    for path in paths:
        path = path.expanduser().resolve()
        if path.is_dir():
            for item in sorted(path.rglob("*")):
                if item.suffix.lower() in IMAGE_EXTS:
                    images.append(item)
        elif path.suffix.lower() in IMAGE_EXTS:
            images.append(path)

    # Spread samples across the list so long timelines do not overweight the
    # opening frames.
    if len(images) <= max_samples:
        return images
    step = (len(images) - 1) / max(max_samples - 1, 1)
    selected = [images[round(i * step)] for i in range(max_samples)]
    return list(dict.fromkeys(selected))


def average_color_ffmpeg(image_path: Path) -> tuple[int, int, int] | None:
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(image_path),
        "-vf",
        "scale=1:1",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "pipe:1",
    ]
    try:
        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("FAIL: ffmpeg not found. Install ffmpeg or add it to PATH.", file=sys.stderr)
        raise SystemExit(2)

    if proc.returncode != 0 or len(proc.stdout) < 3:
        return None
    r, g, b = proc.stdout[:3]
    return int(r), int(g), int(b)


def classify_style(rgb: tuple[int, int, int]) -> dict[str, str]:
    r, g, b = [value / 255.0 for value in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hue = h * 360

    if s < 0.16 and l > 0.68:
        return {
            "style_label": "bright-minimal",
            "mood": "明亮留白、轻信息密度",
            "category": "生活/口播/轻知识",
            "accent_family": "warm",
        }
    if s < 0.24 and 20 <= hue <= 70:
        return {
            "style_label": "warm-paper",
            "mood": "温润纸感、人文审美",
            "category": "艺术/文化/展览/旅行",
            "accent_family": "ochre",
        }
    if 75 <= hue <= 160:
        return {
            "style_label": "earth-nature",
            "mood": "自然、户外、松弛",
            "category": "旅行/自然/生活方式",
            "accent_family": "green",
        }
    if 175 <= hue <= 255:
        return {
            "style_label": "cool-structured",
            "mood": "冷静、科技、秩序感",
            "category": "AI/工具/商业分析",
            "accent_family": "blue",
        }
    if hue < 20 or hue > 330:
        return {
            "style_label": "high-emotion",
            "mood": "强情绪、冲突、传播感",
            "category": "观点/营销/剧情冲突",
            "accent_family": "red",
        }
    return {
        "style_label": "balanced-editorial",
        "mood": "内容感、编辑部、稳定叙事",
        "category": "泛知识/品牌/人物故事",
        "accent_family": "editorial",
    }


def build_palette(rgb: tuple[int, int, int], style: dict[str, str]) -> dict[str, str]:
    r, g, b = [value / 255.0 for value in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    family = style["accent_family"]

    if family == "ochre":
        accent_h, accent_s = 34 / 360, 0.62
    elif family == "green":
        accent_h, accent_s = 138 / 360, 0.55
    elif family == "blue":
        accent_h, accent_s = 214 / 360, 0.62
    elif family == "red":
        accent_h, accent_s = 352 / 360, 0.66
    elif family == "warm":
        accent_h, accent_s = 28 / 360, 0.58
    else:
        accent_h, accent_s = h, max(0.46, min(0.68, s + 0.18))

    bg_h = h
    bg_s = min(0.18, max(0.05, s * 0.35))
    paper_h = h
    paper_s = min(0.12, max(0.03, s * 0.2))

    return {
        "bg": hls_to_hex(bg_h, 0.955, bg_s),
        "paper": hls_to_hex(paper_h, 0.985, paper_s),
        "ink": "#20252B",
        "muted": "#667085",
        "line": hls_to_hex(bg_h, 0.86, max(0.05, bg_s)),
        "accent": hls_to_hex(accent_h, 0.38, accent_s),
        "accent_2": hls_to_hex((accent_h + 0.08) % 1.0, 0.44, max(0.42, accent_s - 0.1)),
        "highlight": hls_to_hex(accent_h, 0.92, max(0.16, accent_s * 0.4)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract report style CSS variables from evidence frames.")
    parser.add_argument("paths", nargs="+", help="Image files or directories containing extracted frames.")
    parser.add_argument("-o", "--output", help="Write JSON profile to this path.")
    parser.add_argument("--max-samples", type=int, default=32, help="Maximum frame samples. Default: 32.")
    args = parser.parse_args()

    images = collect_images([Path(path) for path in args.paths], args.max_samples)
    if not images:
        print("FAIL: no image frames found.", file=sys.stderr)
        return 1

    colors: list[tuple[int, int, int]] = []
    skipped: list[str] = []
    for image in images:
        color = average_color_ffmpeg(image)
        if color is None:
            skipped.append(str(image))
        else:
            colors.append(color)

    if not colors:
        print("FAIL: ffmpeg could not read any image frames.", file=sys.stderr)
        return 1

    avg = (
        int(mean(color[0] for color in colors)),
        int(mean(color[1] for color in colors)),
        int(mean(color[2] for color in colors)),
    )
    style = classify_style(avg)
    css_variables = build_palette(avg, style)
    result = {
        "sample_count": len(colors),
        "skipped_count": len(skipped),
        "dominant_color": rgb_to_hex(avg),
        "style_label": style["style_label"],
        "mood": style["mood"],
        "visual_category": style["category"],
        "css_variables": css_variables,
        "reason": "Profile derived from ffmpeg 1x1 average-color sampling of local extracted frames; CSS values are adjusted for report readability and contrast.",
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).expanduser().resolve().write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
