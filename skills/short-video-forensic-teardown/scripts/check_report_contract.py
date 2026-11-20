#!/usr/bin/env python3
"""Validate a short-video forensic teardown HTML against the skill contract."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from edit_plan_contract import edit_plan_errors


REQUIRED_TERMS = [
    "源流质量诊断",
    "视频链接",
    "结论摘要",
    "前3秒",
    "语言心理钩子",
    "综合评分",
    "脚本结构",
    "逐镜头",
    "高光句",
    "音画同步",
    "表现好的地方",
    "1:1",
    "表现不好的地方",
    "优化",
    "字幕",
    "字体",
    "字号",
    "字幕测量",
    "字号参考来源",
    "剪映",
    "风格匹配",
    "HTML包装",
    "软件",
    "小白",
]

LEGACY_REQUIRED_TERMS = [
    "源流质量诊断",
    "结论摘要",
    "前3秒",
    "语言心理钩子",
    "综合评分",
    "脚本结构",
    "逐镜头",
    "高光句",
    "音画同步",
    "表现好的地方",
    "1:1",
    "表现不好的地方",
    "优化",
    "字幕",
    "字体",
    "字号",
    "剪映",
    "小白",
]

REQUIRED_SCORE_DIMENSIONS = [
    "前3秒语言心理钩子",
    "选题/标题/封面承诺",
    "脚本结构与信息递进",
    "高光句音画同步",
    "视觉画面与审美",
    "拍摄与运镜",
    "剪辑节奏与留存",
    "字幕与包装",
    "证据链与可信度",
    "转化/关注/评论引导",
]

STRICT_MINIMUMS = {
    "local_images": 12,
    "shot": 12,
    "highlight-line": 7,
    "good-card": 3,
    "bad-card": 3,
}

LEGACY_MINIMUMS = {
    "local_images": 3,
}


class ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        data = dict(attrs)
        src = data.get("src")
        if src:
            self.srcs.append(src)


def strip_html(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.I | re.S)
    return re.sub(r"<[^>]+>", " ", text)


def count_contract_marker(html: str, marker: str) -> int:
    pattern = rf"\bdata-contract\s*=\s*(['\"]){re.escape(marker)}\1"
    return len(re.findall(pattern, html, flags=re.I))


def is_external_src(src: str) -> bool:
    return src.startswith(("http://", "https://", "data:", "blob:"))


def resolve_image_path(html_path: Path, src: str) -> Path:
    candidate = Path(src)
    if candidate.is_absolute():
        return candidate
    return (html_path.parent / src).resolve()


def weak_section_contains_replication(visible: str) -> bool:
    start = visible.find("表现不好的地方")
    if start < 0:
        return False
    end_candidates = [
        index
        for index in [
            visible.find("字幕字体", start + 1),
            visible.find("拍摄剪辑", start + 1),
            visible.find("风格匹配", start + 1),
            visible.find("小白照做", start + 1),
        ]
        if index > start
    ]
    end = min(end_candidates) if end_candidates else len(visible)
    weak_section = visible[start:end]
    full_replication_requested = "完全复刻" in visible or "full replication" in visible.lower()
    return "1:1" in weak_section and not full_replication_requested


def source_section_has_video_link(html: str) -> bool:
    match = re.search(
        r"<section\b[^>]*\bid\s*=\s*(['\"])source\1[^>]*>(.*?)</section>",
        html,
        flags=re.I | re.S,
    )
    section_html = match.group(2) if match else html
    section_visible = strip_html(section_html)
    has_label = any(label in section_visible for label in ["视频链接", "原始视频链接", "原始视频", "输入链接", "本地路径"])
    has_reference = bool(
        re.search(
            r"href\s*=|https?://|file://|[A-Za-z]:\\|/[^\s<]+\.(?:mp4|mov|m4v|webm)",
            section_html + "\n" + section_visible,
            flags=re.I,
        )
    )
    return has_label and has_reference


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate a short-video teardown HTML report.")
    parser.add_argument("report", help="Path to the HTML report.")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use a lighter compatibility check for pre-upgrade reports.",
    )
    parser.add_argument(
        "--allow-weak-replication",
        action="store_true",
        help="Allow 1:1 replication guidance inside weak-part sections.",
    )
    args = parser.parse_args()

    html_path = Path(args.report).expanduser().resolve()
    if not html_path.exists():
        print(f"FAIL: file not found: {html_path}")
        return 1

    html = html_path.read_text(encoding="utf-8", errors="replace")
    visible = strip_html(html)

    required_terms = LEGACY_REQUIRED_TERMS if args.legacy else REQUIRED_TERMS
    missing_terms = [term for term in required_terms if term not in visible]

    parser = ImageParser()
    parser.feed(html)

    broken_images: list[str] = []
    local_images = 0
    for src in parser.srcs:
        if is_external_src(src):
            continue
        local_images += 1
        image_path = resolve_image_path(html_path, src)
        if not image_path.exists():
            broken_images.append(src)

    marker_counts = {
        "shot": count_contract_marker(html, "shot"),
        "highlight-line": count_contract_marker(html, "highlight-line"),
        "good-card": count_contract_marker(html, "good-card"),
        "bad-card": count_contract_marker(html, "bad-card"),
    }

    failures: list[str] = []
    if missing_terms:
        failures.append("missing required terms: " + ", ".join(missing_terms))
    if broken_images:
        failures.append("broken local image paths: " + ", ".join(broken_images[:20]))
    minimums = LEGACY_MINIMUMS if args.legacy else STRICT_MINIMUMS
    if local_images < minimums["local_images"]:
        failures.append(f"expected at least {minimums['local_images']} local evidence images, found {local_images}")

    missing_score_dimensions = [dimension for dimension in REQUIRED_SCORE_DIMENSIONS if dimension not in visible]
    if not args.legacy and missing_score_dimensions:
        failures.append("missing fixed score dimensions: " + ", ".join(missing_score_dimensions))

    if not args.legacy:
        failures.extend(edit_plan_errors(html, html_path.parent))
        for marker in ["shot", "highlight-line", "good-card", "bad-card"]:
            found = marker_counts[marker]
            expected = minimums[marker]
            if found < expected:
                failures.append(f"expected at least {expected} data-contract={marker!r} nodes, found {found}")

    if not args.legacy and not source_section_has_video_link(html):
        failures.append("source section must include a visible original video link/path labeled 视频链接 or 原始视频链接")

    if not args.legacy and not args.allow_weak_replication and weak_section_contains_replication(visible):
        failures.append("weak-part section contains 1:1 replication guidance without a full-replication request")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        print("- metrics:")
        print(f"  local evidence images: {local_images}")
        for marker, count in marker_counts.items():
            print(f"  {marker}: {count}")
        return 1

    print("PASS")
    print(f"- required terms present: {len(required_terms)}")
    print(f"- local evidence images: {local_images}")
    if not args.legacy:
        print(f"- fixed score dimensions present: {len(REQUIRED_SCORE_DIMENSIONS)}")
        for marker, count in marker_counts.items():
            print(f"- {marker}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
