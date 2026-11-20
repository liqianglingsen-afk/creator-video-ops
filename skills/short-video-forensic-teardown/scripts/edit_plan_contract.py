"""Inspect visible edit-plan fields in a rendered teardown, without executing its content."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


FIELDS = {"optimization-target", "raw-score", "current-score", "edit-route", "edit-execution",
          "edit-limit", "pickup-brief", "rubric-version", "overall-cap", "cap-reason"}
CURRENT_RUBRIC = "creative-100-v1"
WEIGHTS = {
    "前3秒语言心理钩子": 17,
    "选题/标题/封面承诺": 10,
    "脚本结构与信息递进": 12,
    "高光句音画同步": 8,
    "视觉画面与审美": 10,
    "拍摄与运镜": 6,
    "剪辑节奏与留存": 10,
    "字幕与包装": 8,
    "证据链与可信度": 9,
    "转化/关注/评论引导": 10,
}
ROUTES = {"试剪现有素材", "需补充素材", "当前版本已达标", "证据不足待核"}


class EditPlanParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, str] = {}
        self.duplicates: set[str] = set()
        self.rows: list[list[str]] = []
        self.score_rows: list[list[str]] = []
        self.links: list[str] = []
        self.field = self.field_tag = ""
        self.nested = 0
        self.active_row: list[str] | None = None
        self.in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        marker = data.get("data-contract")
        if marker in FIELDS:
            if marker in self.fields:
                self.duplicates.add(marker)
            self.field, self.field_tag, self.nested = marker, tag, 1
            self.fields[marker] = ""
        elif self.field and tag == self.field_tag:
            self.nested += 1
        if tag == "tr" and marker in {"edit-step", "score-row"}:
            self.active_row = []
            rows = self.rows if marker == "edit-step" else self.score_rows
            rows.append(self.active_row)
        if self.active_row is not None and tag == "td":
            self.active_row.append("")
            self.in_cell = True
        if self.field == "edit-execution" and tag == "a":
            self.links.append(data.get("href") or "")

    def handle_endtag(self, tag: str) -> None:
        if self.field and tag == self.field_tag:
            self.nested -= 1
            if self.nested == 0:
                self.field = self.field_tag = ""
        if tag == "td":
            self.in_cell = False
        if tag == "tr":
            self.active_row = None
            self.in_cell = False

    def handle_data(self, data: str) -> None:
        if self.field:
            self.fields[self.field] += data
        if self.in_cell and self.active_row is not None:
            self.active_row[-1] += data


def number_in(text: str, maximum: int) -> Decimal | None:
    try:
        value = Decimal(text)
        if value.is_finite() and 0 <= value <= maximum:
            return value
    except InvalidOperation:
        pass
    return None


def direct_score_errors(rows: list[list[str]], fields: dict[str, str],
                        raw: Decimal | None, current: Decimal | None, pending: bool) -> list[str]:
    errors = []
    seen: set[str] = set()
    total = Decimal(0)
    has_unknown = False
    for row in rows:
        if len(row) < 3:
            errors.append("score-row requires dimension, weight and score")
            continue
        name, weight, score = (cell.strip() for cell in row[:3])
        if name in seen or name not in WEIGHTS:
            errors.append("duplicate or unknown score dimension: " + name)
            continue
        seen.add(name)
        if number_in(weight, 100) != WEIGHTS[name]:
            errors.append("incorrect weight: " + name)
        value = number_in(score, WEIGHTS[name])
        if value is None:
            has_unknown = True
            if not (pending and score == "待核"):
                errors.append("invalid dimension score: " + name)
        else:
            total += value
    if WEIGHTS.keys() != seen:
        errors.append("score table requires all ten fixed dimensions")
    if has_unknown:
        if raw is not None or current is not None:
            errors.append("incomplete score table cannot have a numeric total")
    elif raw != total:
        errors.append("raw-score must equal the ten dimension scores")
    cap = number_in(fields.get("overall-cap", "100"), 100)
    if cap is None or ("overall-cap" in fields and not fields.get("cap-reason")):
        errors.append("overall-cap requires a valid number and a reason")
    if cap is not None and raw is not None and current != min(raw, cap):
        errors.append("current-score must equal the exact capped total")
    return errors


def edit_plan_errors(html: str, directory: Path, *, require_current: bool = False) -> list[str]:
    parser = EditPlanParser()
    parser.feed(html)
    fields = {name: value.strip() for name, value in parser.fields.items()}
    errors = [f"duplicate edit-plan field: {name}" for name in sorted(parser.duplicates)]
    target = number_in(fields.get("optimization-target", ""), 100)
    if target is None or target < 85:
        errors.append("optimization-target must be a visible number from 85 to 100")
    route = fields.get("edit-route", "")
    if route not in ROUTES:
        errors.append("missing or invalid edit-route")
    version = fields.get("rubric-version")
    direct = version == CURRENT_RUBRIC
    if not direct and (require_current or version is not None or parser.score_rows):
        errors.append("missing or unsupported rubric-version")
    raw = number_in(fields.get("raw-score", ""), 100 if direct else 98)
    current = number_in(fields.get("current-score", ""), 100)
    pending = route == "证据不足待核"
    for name, value in [("raw-score", raw), ("current-score", current)]:
        if value is None and not (pending and fields.get(name) == "待核"):
            errors.append(f"missing or invalid {name}")
    if direct:
        errors.extend(direct_score_errors(parser.score_rows, fields, raw, current, pending))
    if raw is not None and current is not None:
        percentage = raw if direct else raw * 100 / 98
        if not direct and current > percentage + Decimal("0.05"):
            errors.append("current-score exceeds normalized raw-score")
        if route == "当前版本已达标" and target is not None and min(percentage, current) < target:
            errors.append("current version falls below the optimization target")
    if route == "试剪现有素材" and not parser.rows:
        errors.append("existing-footage route requires an edit-step")
    for index, row in enumerate(parser.rows, 1):
        if len(row) != 5 or any(not cell.strip() for cell in row):
            errors.append(f"edit-step {index} requires five populated cells")
    if parser.rows:
        execution = fields.get("edit-execution", "")
        command_line = re.search(r"""(?m)^\s*(?:[A-Za-z_./\\][^\s]*|"[^"]+"|'[^']+')\s+\S""", execution)
        if not execution or not (parser.links or command_line):
            errors.append("cut list requires a runnable command or linked execution file")
        for link in parser.links:
            uri = urlsplit(link)
            if uri.scheme or uri.netloc or not uri.path or not (directory / unquote(uri.path)).is_file():
                errors.append("invalid local edit-execution link: " + link)
    if route == "需补充素材" and not (fields.get("edit-limit") and fields.get("pickup-brief")):
        errors.append("new footage requires edit-limit evidence and a pickup-brief")
    return errors
