#!/usr/bin/env python3
"""Estimate burned-in subtitle size and safe-area position from frames.

The detector is deliberately conservative. It looks for bright or saturated
subtitle-like pixels in the lower part of vertical frames, estimates a bounding
box, and normalizes the measured pixel height to a 1080x1920 export reference.
Use the result as report evidence with confidence labels, not as OCR.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from statistics import median


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SOFTWARE_SIZE_NOTE = (
    "字号参考基于 1080x1920 竖屏成片的画面渲染尺寸。剪映、CapCut、Premiere、Final Cut、"
    "After Effects 等软件的字号单位、字体渲染、缩放逻辑不同，同样字号不一定显示为同样大小；"
    "请以最终导出画面中的字幕高度、位置和可读性为准，并根据实际软件微调。"
)


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

    if len(images) <= max_samples:
        return images
    step = (len(images) - 1) / max(max_samples - 1, 1)
    selected = [images[round(i * step)] for i in range(max_samples)]
    return list(dict.fromkeys(selected))


def probe_dimensions(image_path: Path) -> tuple[int, int] | None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(image_path),
    ]
    try:
        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        print("FAIL: ffprobe not found. Install ffmpeg or add it to PATH.", file=sys.stderr)
        raise SystemExit(2)
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
        stream = data["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except (KeyError, IndexError, ValueError, json.JSONDecodeError):
        return None


def read_scaled_rgb(image_path: Path, detect_height: int) -> tuple[bytes, int, int] | None:
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(image_path),
        "-vf",
        f"scale=-2:{detect_height}",
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
    if proc.returncode != 0 or not proc.stdout:
        return None
    width = len(proc.stdout) // (detect_height * 3)
    if width <= 0:
        return None
    return proc.stdout, width, detect_height


def is_subtitle_candidate(r: int, g: int, b: int) -> bool:
    high = max(r, g, b)
    low = min(r, g, b)
    mean = (r + g + b) / 3
    spread = high - low
    bright_neutral = mean >= 182 and spread <= 72
    yellow = r >= 210 and g >= 165 and b <= 125
    red = r >= 205 and g <= 125 and b <= 150
    cyan_or_green = g >= 180 and b >= 145 and r <= 165
    return bright_neutral or yellow or red or cyan_or_green


def merge_row_groups(groups: list[dict[str, int]], max_gap: int = 34) -> list[dict[str, int]]:
    if not groups:
        return []
    merged = [groups[0].copy()]
    for group in groups[1:]:
        current = merged[-1]
        if group["y1"] - current["y2"] <= max_gap:
            current["y2"] = group["y2"]
            current["pixels"] += group["pixels"]
            current["min_x"] = min(current["min_x"], group["min_x"])
            current["max_x"] = max(current["max_x"], group["max_x"])
        else:
            merged.append(group.copy())
    return merged


def detect_subtitle_bbox(raw: bytes, width: int, height: int, search_start_ratio: float) -> dict[str, float | int | str]:
    start_y = int(height * search_start_ratio)
    end_y = int(height * 0.98)
    row_threshold = max(12, int(width * 0.018))

    row_counts = [0] * height
    row_min_x = [width] * height
    row_max_x = [-1] * height

    for y in range(start_y, end_y):
        base = y * width * 3
        count = 0
        min_x = width
        max_x = -1
        for x in range(width):
            idx = base + x * 3
            r, g, b = raw[idx], raw[idx + 1], raw[idx + 2]
            if is_subtitle_candidate(r, g, b):
                count += 1
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
        if row_threshold <= count <= int(width * 0.86):
            row_counts[y] = count
            row_min_x[y] = min_x
            row_max_x[y] = max_x

    groups: list[dict[str, int]] = []
    active: dict[str, int] | None = None
    for y in range(start_y, end_y):
        if row_counts[y]:
            if active is None:
                active = {
                    "y1": y,
                    "y2": y,
                    "pixels": row_counts[y],
                    "min_x": row_min_x[y],
                    "max_x": row_max_x[y],
                }
            else:
                active["y2"] = y
                active["pixels"] += row_counts[y]
                active["min_x"] = min(active["min_x"], row_min_x[y])
                active["max_x"] = max(active["max_x"], row_max_x[y])
        elif active is not None:
            groups.append(active)
            active = None
    if active is not None:
        groups.append(active)

    candidates: list[dict[str, float | int | str]] = []
    for group in merge_row_groups(groups):
        bbox_h = group["y2"] - group["y1"] + 1
        bbox_w = group["max_x"] - group["min_x"] + 1
        if bbox_h < 8 or bbox_h > 180:
            continue
        if bbox_w < width * 0.12:
            continue
        bbox_area = max(1, bbox_w * bbox_h)
        density = group["pixels"] / bbox_area
        y_center_ratio = ((group["y1"] + group["y2"]) / 2) / height
        score = group["pixels"] * (0.8 + y_center_ratio)
        confidence = max(0.28, min(0.95, 0.24 + density * 1.8 + min(0.18, bbox_w / width * 0.2)))
        candidates.append(
            {
                "x1": group["min_x"],
                "y1": group["y1"],
                "x2": group["max_x"],
                "y2": group["y2"],
                "height_px": bbox_h,
                "width_px": bbox_w,
                "candidate_pixels": group["pixels"],
                "density": round(density, 3),
                "y_center_ratio": round(y_center_ratio, 3),
                "score": score,
                "confidence": round(confidence, 2),
            }
        )

    if not candidates:
        return {"status": "not_detected", "confidence": 0.0}

    best = max(candidates, key=lambda item: float(item["score"]))
    best["status"] = "detected"
    return best


def safe_area_status(bottom_margin_1080p: float) -> str:
    if bottom_margin_1080p < 140:
        return "偏低，容易被平台按钮/进度条干扰"
    if bottom_margin_1080p < 170:
        return "略低，建议上移到 170-230px"
    if bottom_margin_1080p <= 230:
        return "安全区合格"
    if bottom_margin_1080p <= 280:
        return "略高，可按画面主体微调"
    return "偏高，可能挤压主体画面"


def size_status(height_1080p: float) -> str:
    if height_1080p < 50:
        return "偏小"
    if height_1080p <= 76:
        return "常规字幕合格"
    if height_1080p <= 102:
        return "强调字幕区间"
    return "偏大，检查遮挡和压迫感"


def measure_frame(image: Path, detect_height: int, search_start_ratio: float) -> dict[str, object]:
    original = probe_dimensions(image)
    scaled = read_scaled_rgb(image, detect_height)
    base = {
        "frame": image.name,
        "path": str(image),
        "original_width": original[0] if original else None,
        "original_height": original[1] if original else None,
    }
    if scaled is None:
        return {**base, "status": "unreadable", "confidence": 0.0}

    raw, width, height = scaled
    bbox = detect_subtitle_bbox(raw, width, height, search_start_ratio)
    if bbox["status"] != "detected":
        return {**base, "detect_width": width, "detect_height": height, **bbox}

    scale_to_1080p = 1920 / height
    height_1080p = float(bbox["height_px"]) * scale_to_1080p
    bottom_margin = height - float(bbox["y2"]) - 1
    bottom_margin_1080p = bottom_margin * scale_to_1080p
    return {
        **base,
        "detect_width": width,
        "detect_height": height,
        **bbox,
        "normalized_1080p_height_px": round(height_1080p, 1),
        "bottom_margin_px": round(bottom_margin, 1),
        "bottom_margin_1080p_px": round(bottom_margin_1080p, 1),
        "safe_area_status": safe_area_status(bottom_margin_1080p),
        "size_status": size_status(height_1080p),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate subtitle rendered size and bottom safe area from frames.")
    parser.add_argument("paths", nargs="+", help="Image files or directories containing extracted frames.")
    parser.add_argument("-o", "--output", help="Write JSON measurements to this path.")
    parser.add_argument("--max-samples", type=int, default=24, help="Maximum frame samples. Default: 24.")
    parser.add_argument("--detect-height", type=int, default=1280, help="Scaled detection height. Default: 1280.")
    parser.add_argument(
        "--search-start-ratio",
        type=float,
        default=0.52,
        help="Vertical ratio where subtitle search starts. Default: 0.52, the lower half of the frame.",
    )
    args = parser.parse_args()

    images = collect_images([Path(path) for path in args.paths], args.max_samples)
    if not images:
        print("FAIL: no image frames found.", file=sys.stderr)
        return 1

    measurements = [measure_frame(image, args.detect_height, args.search_start_ratio) for image in images]
    detected = [item for item in measurements if item.get("status") == "detected"]
    summary: dict[str, object] = {
        "sample_count": len(measurements),
        "detected_count": len(detected),
        "reference": {
            "normal_subtitle_height_1080p_px": "58-72",
            "emphasis_word_height_1080p_px": "78-96",
            "bottom_safe_area_1080p_px": "170-230",
            "source": "Rendered-pixel measurement normalized to 1080x1920 vertical export, using local extracted frames.",
            "software_size_note": SOFTWARE_SIZE_NOTE,
            "search_start_ratio": args.search_start_ratio,
        },
    }
    if detected:
        summary["median_normalized_height_px"] = round(
            median(float(item["normalized_1080p_height_px"]) for item in detected), 1
        )
        summary["median_bottom_margin_1080p_px"] = round(
            median(float(item["bottom_margin_1080p_px"]) for item in detected), 1
        )
        summary["median_confidence"] = round(median(float(item["confidence"]) for item in detected), 2)

    result = {"summary": summary, "measurements": measurements}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).expanduser().resolve().write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
