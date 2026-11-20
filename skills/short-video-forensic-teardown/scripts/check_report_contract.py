#!/usr/bin/env python3
"""Validate a short-video forensic teardown HTML against the skill contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import unquote, urlsplit

from revision_contract import revision_check
from edit_plan_contract import WEIGHTS, edit_plan_errors


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


class EditorialFields(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}
        self.counts = {}
        self.visible = {}
        self.active = None

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        name = attr.get("data-contract")
        names = {"editorial-goal", "hook-payoff", "action-path", "revision-priorities", "preserve-shots",
                 "editorial-json", "editorial-report", "editorial-pending", "hook-marks", "cover-source", "release-status", "current-score", "raw-score"}
        if name in names:
            self.counts[name] = self.counts.get(name, 0) + 1
            self.visible[name] = ""
            self.active = (name, tag)
            if tag == "a":
                self.links[name] = attr.get("href") or ""

    def handle_data(self, data):
        if self.active:
            self.visible[self.active[0]] += data

    def handle_endtag(self, tag):
        if self.active and tag == self.active[1]:
            self.active = None


def editorial_errors(html, directory, *, current=False):
    data = EditorialFields()
    data.feed(html)
    errors = []
    for key in ("editorial-goal", "hook-payoff", "action-path", "revision-priorities", "preserve-shots"):
        if not data.visible.get(key, "").strip():
            errors.append("missing editorial field: " + key)
    if any(n > 1 for n in data.counts.values()):
        errors.append("duplicate editorial fields")
    if data.visible.get("editorial-pending", "").strip() and not data.links:
        return errors + (["新版综合报告须附实片审片数据"] if current else [])
    companion_hash = None
    for name in ("editorial-report", "editorial-json"):
        link = urlsplit(data.links.get(name, ""))
        path = directory / unquote(link.path)
        if link.scheme or link.netloc or not path.is_file():
            errors.append("missing local review artifact: " + name)
        elif name == "editorial-report":
            companion = path.read_text(encoding="utf-8")
            if current and 'data-criteria="0.5"' not in companion:
                errors.append("评分附件缺 0.5 证据区")
            match = re.search(r'data-source-sha256="([0-9a-f]{64})"', companion)
            companion_hash = match.group(1) if match else None
        elif name == "editorial-json":
            try:
                record = json.loads(path.read_text(encoding="utf-8"))["editorial"]
                if record["schema_version"] not in {"editorial-0.3", "editorial-0.5"} or not record["status"] or len(record["checks"]) != 8:
                    errors.append("incomplete editorial review")
                if record.get("source_sha256") != companion_hash:
                    errors.append("editorial HTML and JSON use different sources")
                if current:
                    if record["schema_version"] != "editorial-0.5" or not record.get("content"):
                        errors.append("须提供 0.5 综合审片数据与内容分")
                    else:
                        criteria = record["criteria"]
                        keys = ("主体与动作", "受众相关", "继续观看理由", "前三秒可信线索")
                        scores = [criteria["hook"][k]["score"] for k in keys]
                        if sum(scores) != Decimal(record["content"]["marks"]["前3秒语言心理钩子"]["score"]):
                            errors.append("钩子四项与十维评分不一致")
                        for key, value in [("cover-source", record["cover_status"]), ("release-status", record["status"]),
                                           ("hook-marks", " / ".join(map(str, scores)))]:
                            if data.visible.get(key, "").strip() != value:
                                errors.append("首页与评分附件不一致：" + key)
                if record.get("content"):
                    for field, key in (("current-score","total"), ("raw-score","raw")):
                        if Decimal(data.visible[field].strip()) != Decimal(record["content"][key]):
                            errors.append("editorial content score mismatch: " + field)
            except (ValueError, InvalidOperation, KeyError, TypeError):
                errors.append("invalid editorial JSON")
    return errors


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate a short-video teardown HTML report.")
    parser.add_argument("report", help="Path to the HTML report.")
    parser.add_argument("--revision-stage",choices=("plan","comparison"),help="Validate a v0.4 plan or paired review and its evidence.")
    parser.add_argument("--require-editorial", action="store_true", help="Validate v0.3 editorial decisions and linked evidence.")
    parser.add_argument("--require-v05", action="store_true", help="核对新版评分、封面来源和首页发布结论")
    parser.add_argument("--require-v06", action="store_true",help="校验 0.6 同源报告及可见分项")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-current-rubric", action="store_true",
                      help="Require a versioned direct-100 score table for a new report.")
    mode.add_argument(
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

    if not any((args.require_v05,args.require_v06,args.legacy)):
        sidecar = html_path.with_suffix(".json")
        if sidecar.is_file():
            try:
                data = json.loads(sidecar.read_text(encoding="utf-8"))
                args.require_v06 = ((data.get("editorial") or {}).get("schema_version") == "editorial-0.6"
                                    or data.get("schema_version") == "revision-0.6")
                if args.require_v06 and data.get("kind") in {"plan","comparison"}:
                    args.revision_stage = args.revision_stage or data["kind"]
            except (ValueError,OSError,AttributeError):
                pass
    if args.require_v06:
        try:
            if args.revision_stage:
                if not revision_check(html_path,args.revision_stage,current=True,version="revision-0.6"):
                    raise ValueError("请提交实际标准方案或复评页")
            else:
                from postscore.models import ReviewReport
                from postscore.report import render_html
                from postscore.editorial import Creative
                record = ReviewReport.model_validate_json(html_path.with_suffix(".json").read_text(encoding="utf-8"))
                ed = record.editorial or {}
                if ed.get("schema_version") != "editorial-0.6" or not ed.get("brief"):
                    raise ValueError("须提供当前同名 0.6 简报与报告")
                if ed.get("content"):
                    c = ed["content"]
                    obj = Creative.model_validate({k:v for k,v in c.items() if k in Creative.model_fields})
                    if obj.result(c["target"]) != c or obj.version != "creative-100-v2":
                        raise ValueError("评分分项、证据或合计不一致")
                actual = html_path.read_text(encoding="utf-8")
                if actual != render_html(record,html_path.parent):
                    raise ValueError("报告显示与同源证据、分数或方案不一致，请从 JSON 重出")
                images = ImageParser()
                images.feed(actual)
                if any(not resolve_image_path(html_path,s).is_file() for s in images.srcs if not is_external_src(s)):
                    raise ValueError("缺本地证据图")
            print("PASS: 0.6 同源报告")
            return 0
        except (ImportError,ValueError,OSError,KeyError,TypeError) as exc:
            print("FAIL: "+str(exc))
            return 1
    if args.revision_stage:
        if args.legacy:
            parser.error("新版方案或复评不能使用旧报告的宽松校验")
        try:
            if revision_check(html_path,args.revision_stage, current=args.require_v05):
                print("PASS: verified "+args.revision_stage+" packet")
                return 0
        except (ValueError, OSError, KeyError, TypeError) as exc:
            print("FAIL: "+str(exc))
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

    failures: list[str] = editorial_errors(html, html_path.parent, current=args.require_v05) if args.require_editorial or args.require_v05 else []
    if missing_terms:
        failures.append("missing required terms: " + ", ".join(missing_terms))
    if broken_images:
        failures.append("broken local image paths: " + ", ".join(broken_images[:20]))
    minimums = LEGACY_MINIMUMS if args.legacy else STRICT_MINIMUMS
    if local_images < minimums["local_images"]:
        failures.append(f"expected at least {minimums['local_images']} local evidence images, found {local_images}")

    missing_score_dimensions = [dimension for dimension in WEIGHTS if dimension not in visible]
    if not args.legacy and missing_score_dimensions:
        failures.append("missing fixed score dimensions: " + ", ".join(missing_score_dimensions))

    if not args.legacy:
        failures.extend(edit_plan_errors(html, html_path.parent, require_current=args.require_current_rubric))
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
        print(f"- fixed score dimensions present: {len(WEIGHTS)}")
        for marker, count in marker_counts.items():
            print(f"- {marker}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
