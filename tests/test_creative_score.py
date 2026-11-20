from decimal import Decimal
from pathlib import Path
import re
import sys
import unittest

from test_edit_plan import CUT, header

SKILL = Path(__file__).resolve().parents[1] / "skills/short-video-forensic-teardown"
sys.path.insert(0, str(SKILL / "scripts"))
from edit_plan_contract import CURRENT_RUBRIC, WEIGHTS, edit_plan_errors


def report(values, raw, current, route="当前版本已达标", target="85"):
    rows = "".join(
        f'<tr data-contract="score-row"><td>{name}</td><td>{weight}</td><td>{score}</td></tr>'
        for (name, weight), score in zip(WEIGHTS.items(), values)
    )
    return (header(route, raw, current, target)
            + f'<span data-contract="rubric-version">{CURRENT_RUBRIC}</span><table>{rows}</table>')


class CreativeScoreTests(unittest.TestCase):
    def check(self, html):
        return edit_plan_errors(html, Path("."), require_current=True)

    def test_weights_and_subcriteria_match_published_rubric(self):
        rubric = (SKILL / "references/score-rubric.md").read_text()
        rows = re.findall(r"^\| ([^|]+) \| (\d+) \| (.+?) \|$", rubric, re.M)
        self.assertEqual({name: int(weight) for name, weight, _ in rows}, WEIGHTS)
        self.assertEqual(sum(WEIGHTS.values()), 100)
        for name, weight, criteria in rows:
            points = [int(item.rsplit(" ", 1)[1]) for item in criteria.split("；")]
            self.assertEqual(sum(points), int(weight), name)

    def test_direct_boundaries_and_exact_reconciliation(self):
        for total, valid in [("84.99", False), ("85", True), ("99", True), ("100", True)]:
            scores = list(WEIGHTS.values())
            scores[0] -= 100 - Decimal(total)
            with self.subTest(total=total):
                self.assertEqual(not self.check(report(scores, total, total)), valid)
        scores = list(WEIGHTS.values())
        full = report(scores, "100", "100", target="100")
        self.assertFalse(self.check(full))
        self.assertTrue(self.check(full.replace('raw-score">100', 'raw-score">99')))
        self.assertTrue(self.check(full.replace('current-score">100', 'current-score">99.9')))
        self.assertTrue(self.check(full.replace("<td>17</td>", "<td>18</td>", 1)))
        self.assertTrue(self.check(full.replace("前3秒语言心理钩子", "高光句音画同步")))
        self.assertTrue(self.check(report(scores[:-1], "90", "90")))
        self.assertTrue(self.check(full.replace(CURRENT_RUBRIC, "unknown")))

    def test_caps_pending_and_archives(self):
        scores = list(WEIGHTS.values())
        capped = report(scores, "100", "45", route="试剪现有素材")
        capped += CUT + '<pre data-contract="edit-execution">ffmpeg -version</pre>'
        capped += '<span data-contract="overall-cap">45</span>'
        self.assertTrue(self.check(capped))
        capped += '<span data-contract="cap-reason">缺完整视频</span>'
        self.assertEqual(self.check(capped), [])
        self.assertTrue(self.check(capped.replace("试剪现有素材", "当前版本已达标")))
        scores[0] = "待核"
        pending = report(scores, "待核", "待核", route="证据不足待核")
        self.assertFalse(self.check(pending))
        self.assertTrue(self.check(pending.replace('raw-score">待核', 'raw-score">85')))
        archived = header("当前版本已达标", "83.5", "85.2")
        self.assertFalse(edit_plan_errors(archived, Path(".")))
        self.assertTrue(self.check(archived))


class EditorialAttachmentTests(unittest.TestCase):
    def test_linked_reports_must_share_evidence_and_score(self):
        import json
        from tempfile import TemporaryDirectory
        from check_report_contract import editorial_errors
        base = "".join(f'<span data-contract="{key}">evidence</span>' for key in (
            "editorial-goal","hook-payoff","action-path","revision-priorities","preserve-shots"))
        section = base + header("当前版本已达标","85","85")
        section += '<a data-contract="editorial-json" href="r.json">审片数据</a><a data-contract="editorial-report" href="r.html">审片</a>'
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            record = dict(schema_version="editorial-0.3",status="发布前须改",checks=dict.fromkeys(range(8),"实测"),
                          source_sha256="a"*64,content=dict(raw="85",total="85"))
            (directory/"r.json").write_text(json.dumps(dict(editorial=record)))
            html_path=directory/"r.html"
            html_path.write_text('<section data-source-sha256="' + "a"*64 + '">审片</section>')
            self.assertFalse(editorial_errors(section,directory))
            self.assertTrue(editorial_errors(section.replace('current-score">85','current-score">99'),directory))
            html_path.write_text('<section data-source-sha256="' + "b"*64 + '">审片</section>')
            self.assertTrue(editorial_errors(section,directory))
            self.assertFalse(editorial_errors(base+'<p data-contract="editorial-pending">缺素材，待核</p>',directory))
            self.assertTrue(editorial_errors(base,directory))


class CurrentEvidenceTests(unittest.TestCase):
    def test_no_artifact_cannot_pass_as_current(self):
        from tempfile import TemporaryDirectory
        from check_report_contract import editorial_errors
        with TemporaryDirectory() as tmp:
            errors = editorial_errors('<p data-contract="editorial-pending">未评</p>', Path(tmp), current=True)
            self.assertIn("新版综合报告须附实片审片数据", errors)

    def test_scores_cover_and_release_match_companion(self):
        from tempfile import TemporaryDirectory
        from check_report_contract import editorial_errors
        import json
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            identity = "b" * 64
            (folder / "review.html").write_text(f'<section data-criteria="0.5" data-source-sha256="{identity}"></section>')
            cover_status="无独立封面 · N/A ｜ 平台实显待核"
            focus="前3秒语言心理钩子"
            keys=("主体与动作","受众相关","继续观看理由","前三秒可信线索")
            record=dict(schema_version="editorial-0.5",source_sha256=identity,status="发布前须改",
                        checks=dict.fromkeys(range(8),"已核"),cover_status=cover_status,
                        content=dict(total="68",raw="68",marks={focus:dict(score="10")}),
                        criteria=dict(hook={k:dict(score=v) for k,v in zip(keys,[3,4,2,1])}))
            (folder/"review.json").write_text(json.dumps({"editorial":record}))
            fields=dict.fromkeys(["editorial-goal","hook-payoff","action-path","revision-priorities","preserve-shots"], "本次实片依据")
            fields.update({"current-score":"68","raw-score":"68","hook-marks":"3 / 4 / 2 / 1","cover-source":cover_status,"release-status":"发布前须改"})
            html="".join(f'<span data-contract="{k}">{v}</span>' for k,v in fields.items())
            html+='<a data-contract="editorial-json" href="review.json">JSON</a><a data-contract="editorial-report" href="review.html">HTML</a>'
            self.assertEqual(editorial_errors(html,folder,current=True),[])
            self.assertTrue(editorial_errors(html.replace(cover_status,"封面达标"),folder,current=True))
            self.assertTrue(editorial_errors(html.replace("3 / 4 / 2 / 1","4 / 4 / 4 / 1"),folder,current=True))


class CoverLayoutTests(unittest.TestCase):
    def test_photo_layout_and_normalized_crop(self):
        from tempfile import TemporaryDirectory
        try:
            from PIL import Image, ImageFont
            from cover_variants import draw_layout, preview_page
        except ImportError:
            self.skipTest("封面渲染需 Pillow")
        candidates = ["DejaVuSans.ttf", "Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]
        font = None
        for candidate in candidates:
            try:
                font = ImageFont.truetype(candidate, 20).path
                break
            except OSError:
                pass
        if not font:
            self.skipTest("需系统字体")
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/"cover.png"
            photo = Image.new("RGB",(200,400),"white")
            photo.paste("red",(0,300,200,400))
            photo.save(path)
            variant = {"layout":"photo","source_crop":[0,0,1,0.74],"text_x":0.1,"text_y":0.05}
            layout = draw_layout(path,font,variant,["Product"],1200)
            self.assertEqual(layout.getpixel((899,1199)),(255,255,255))
            with self.assertRaises(ValueError):
                draw_layout(path,font,variant | dict(source_crop=[1,0,1,1]),["Product"],1200)
            self.assertIn("模拟列表",preview_page([dict(headline=["Product"])]))
