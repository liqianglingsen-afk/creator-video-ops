"""Verify a v0.4 companion, or a forensic report's explicit link to it."""

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.markers = []
        self.reports = []
        self.images = []
        self.editorial = []
        self.rows = {}
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr" and "data-revision-dimension" in a:
            self.row = a["data-revision-dimension"]
            if self.row in self.rows:
                raise ValueError("重复的维度评分行")
            self.rows[self.row] = []
        if self.row is not None and tag == "td":
            self.cell = []
        if tag == "main" and a.get("data-revision"):
            self.markers.append(a)
        if tag == "a" and a.get("data-contract") == "revision-report":
            self.reports.append(a.get("href", ""))
        if tag == "a" and a.get("data-contract") == "editorial-json":
            self.editorial.append(a.get("href", ""))
        if tag == "img":
            self.images.append(a.get("src", ""))

    def handle_data(self, value):
        if self.cell is not None:
            self.cell.append(value)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.rows[self.row].append("".join(self.cell).strip())
            self.cell = None
        if tag == "tr":
            self.row = None


def local(root, href):
    link = urlsplit(href)
    if link.scheme or link.netloc or not link.path:
        raise ValueError("需要本地复评附件")
    return root / unquote(link.path)


def revision_check(path, stage, *, current=False):
    parser = Links()
    parser.feed(path.read_text(encoding="utf-8"))
    linked = not parser.markers
    datafile = None
    if linked:
        if len(parser.reports) != 1 or len(parser.editorial) != 1:
            raise ValueError("缺匹配的全片方案/原改报告与审片数据")
        datafile = local(path.parent, parser.editorial[0])
        path = local(path.parent, parser.reports[0])
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
    if len(parser.markers) != 1 or parser.markers[0].get("data-revision") != stage:
        raise ValueError("该交付不是所需的标准方案/原改对照")
    doc = json.loads((path.parent / (stage + ".json")).read_text(encoding="utf-8"))
    identity = hashlib.sha256(
        json.dumps(doc, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()
    marker = parser.markers[0]
    if (
        doc["schema_version"] != "revision-0.4"
        or doc["kind"] != stage
        or identity != marker.get("data-record-sha256")
        or doc["seal"] != marker.get("data-plan-seal")
    ):
        raise ValueError("报告与数据快照不一致")
    if current:
        sides = [doc["baseline"]] + ([doc["after"]] if stage == "comparison" else [])
        for side in sides:
            c = side.get("criteria")
            if not c or not c.get("cover_source") or len(c.get("hook", {})) != 4:
                raise ValueError("新版交付缺封面来源与四项钩子证据")
            if sum(m["score"] for m in c["hook"].values()) != float(side["content"]["marks"]["前3秒语言心理钩子"]["score"]):
                raise ValueError("新版交付的钩子得分不一致")
        if stage == "comparison" and doc["after"]["blockers"] and doc["status"] != "发布前须改":
            raise ValueError("有发布前错误的改片不能通过")
    base = doc["baseline"]["content"]["marks"]
    if len(base) != 10 or set(parser.rows) != set(base):
        raise ValueError("缺少完整十维可见评分表")
    for name, mark in base.items():
        cells = parser.rows[name]
        if len(cells) < 5 or cells[0] != name or cells[2] != str(mark["score"]):
            raise ValueError("原片分项显示与数据不一致")
        if stage == "comparison" and cells[4] != str(doc["after"]["content"]["marks"][name]["score"]):
            raise ValueError("改版分项显示与数据不一致")
        f = doc["plan"]["forecast"].get(name)
        expected = f"{f['expected']}（{f['low']}–{f['high']}）" if f else "未存"
        if cells[3] != expected:
            raise ValueError("剪前预测显示与快照不一致")
    if stage == "plan" and (
        doc["plan"]["forecast_context"] != "剪前预测" or len(doc["plan"]["forecast"]) != 10
    ):
        raise ValueError("缺剪前十维预测的历史快照只能用于历史对照")
    if stage == "plan" and (
        set(doc["plan"].get("packaging_plan", {})) != {"行动收益", "手机易读性", "画面美感"}
        or not doc["plan"].get("placement_plan")
    ):
        raise ValueError("缺少剪前包装或版位避让设计")
    if stage == "comparison" and not all(
        k in doc for k in ("after", "assets", "packaging", "placements", "status", "pending", "fixes")
    ):
        raise ValueError("缺成对复评数据")
    if datafile:
        sha = doc["plan"]["source_sha256"] if stage == "plan" else doc["revised_sha256"]
        if json.loads(datafile.read_text(encoding="utf-8"))["editorial"]["source_sha256"] != sha:
            raise ValueError("拆解与对照报告属于不同成片")
    if any(not local(path.parent, x).is_file() for x in parser.images):
        raise ValueError("对照报告缺证据图")
    return not linked
