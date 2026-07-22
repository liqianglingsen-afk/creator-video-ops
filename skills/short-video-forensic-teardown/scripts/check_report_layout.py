#!/usr/bin/env python3
"""Layout QA for short-video forensic HTML reports.

This check catches the repeated visual regressions that are hard to express in
the structural contract: oversized landing-page headers, evidence images cropped
for neatness, and ultra-wide subtitle/contact sheets used as primary side-by-side
images.
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


PROOF_CRITICAL_HINTS = [
    "subtitle",
    "字幕",
    "bill",
    "账单",
    "receipt",
    "score",
    "评分",
    "comment",
    "评论",
    "chat",
    "prompt",
    "ai_output",
]


class ImgParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[dict[str, str]] = []
        self._section_stack: list[str] = []
        self._class_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag.lower() == "section":
            self._section_stack.append(data.get("id", ""))
        if tag.lower() == "div":
            self._class_stack.append(data.get("class", ""))
        if tag.lower() == "img":
            self.images.append(
                {
                    "src": data.get("src", ""),
                    "alt": data.get("alt", ""),
                    "section": self._section_stack[-1] if self._section_stack else "",
                    "container_class": " ".join(class_name for class_name in self._class_stack if class_name),
                }
            )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "section" and self._section_stack:
            self._section_stack.pop()
        if tag.lower() == "div" and self._class_stack:
            self._class_stack.pop()


def strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def css_block(html: str, selector: str) -> str:
    pattern = re.compile(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", re.I | re.S)
    match = pattern.search(strip_css_comments(html))
    return match.group(1) if match else ""


def has_large_hero(html: str) -> bool:
    block = css_block(html, ".hero")
    if not block:
        return False
    if re.search(r"min-height\s*:\s*(?:[4-9]\d|[1-9]\d{2,})vh", block, re.I):
        return True
    if re.search(r"height\s*:\s*(?:[4-9]\d|[1-9]\d{2,})vh", block, re.I):
        return True
    return False


def uses_hero_end_alignment(html: str) -> bool:
    block = css_block(html, ".hero")
    return bool(re.search(r"align-items\s*:\s*end", block, re.I))


def proof_critical_image(image: dict[str, str]) -> bool:
    haystack = " ".join([image.get("src", ""), image.get("alt", ""), image.get("section", "")]).lower()
    return any(hint.lower() in haystack for hint in PROOF_CRITICAL_HINTS)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run layout QA for a short-video teardown HTML report.")
    parser.add_argument("report", help="Path to the HTML report.")
    parser.add_argument("--warn-only", action="store_true", help="Print warnings without failing.")
    args = parser.parse_args()

    html_path = Path(args.report).expanduser().resolve()
    if not html_path.exists():
        print(f"FAIL: file not found: {html_path}")
        return 1

    html = html_path.read_text(encoding="utf-8", errors="replace")
    parser_obj = ImgParser()
    parser_obj.feed(html)

    failures: list[str] = []
    warnings: list[str] = []

    if has_large_hero(html):
        failures.append("hero uses viewport-height spacing; use a compact report header instead")
    if uses_hero_end_alignment(html):
        warnings.append("hero aligns content to the end; check for excessive top whitespace")

    if "subtitle_crop_grid" in html.lower():
        failures.append("subtitle_crop_grid appears in the report; use it only as secondary evidence, not the main subtitle image")

    for image in parser_obj.images:
        src = image["src"].lower()
        section = image["section"]
        classes = image["container_class"]
        if section == "source" and "hook_grid" in src and "hook_tall" not in src:
            failures.append("source section uses ultra-wide hook_grid; use a fitted hook_tall/2x2 evidence grid")
        if proof_critical_image(image) and "media-tall" in classes and re.search(r"\.matched-media\.media-tall\s+img\s*\{[^}]*object-fit\s*:\s*cover", html, re.I | re.S):
            failures.append(f"proof-critical image may be cropped by media-tall cover treatment: {image['src']}")
        if proof_critical_image(image) and "cover-evidence" in classes:
            failures.append(f"proof-critical image is marked cover-evidence: {image['src']}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        for warning in warnings:
            print(f"- warning: {warning}")
        return 0 if args.warn_only else 1

    print("PASS")
    print(f"- images checked: {len(parser_obj.images)}")
    if warnings:
        for warning in warnings:
            print(f"- warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
