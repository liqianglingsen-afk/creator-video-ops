"""Inspect visible edit-plan fields in a rendered teardown, without executing its content."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


FIELDS = {"optimization-target", "raw-score", "current-score", "edit-route", "edit-execution",
          "edit-limit", "pickup-brief"}
ROUTES = {"试剪现有素材", "需补充素材", "当前版本已达标", "证据不足待核"}


class EditPlanParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, str] = {}
        self.duplicates: set[str] = set()
        self.rows: list[list[str]] = []
        self.links: list[str] = []
        self.field = self.field_tag = ""
        self.nested = 0
        self.in_row = self.in_cell = False

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
        if tag == "tr" and marker == "edit-step":
            self.rows.append([])
            self.in_row = True
        if self.in_row and tag == "td":
            self.rows[-1].append("")
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
            self.in_row = self.in_cell = False

    def handle_data(self, data: str) -> None:
        if self.field:
            self.fields[self.field] += data
        if self.in_cell:
            self.rows[-1][-1] += data


def number_in(text: str, maximum: int) -> Decimal | None:
    try:
        value = Decimal(text)
        if value.is_finite() and 0 <= value <= maximum:
            return value
    except InvalidOperation:
        pass
    return None


def edit_plan_errors(html: str, directory: Path) -> list[str]:
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
    raw = number_in(fields.get("raw-score", ""), 98)
    current = number_in(fields.get("current-score", ""), 100)
    pending = route == "证据不足待核"
    for name, value in [("raw-score", raw), ("current-score", current)]:
        if value is None and not (pending and fields.get(name) == "待核"):
            errors.append(f"missing or invalid {name}")
    if raw is not None and current is not None:
        percentage = raw * 100 / 98
        if current > percentage + Decimal("0.05"):
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
