from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/short-video-forensic-teardown/scripts"
sys.path.insert(0, str(SCRIPTS))
from edit_plan_contract import edit_plan_errors


def header(route="试剪现有素材", raw="77", current="78.6", target="85"):
    values = {"optimization-target": target, "current-score": current, "raw-score": raw, "edit-route": route}
    return "".join(f'<span data-contract="{key}">{value}</span>' for key, value in values.items())


CUT = ('<table><tr data-contract="edit-step"><td>A.mp4 2–3 s</td><td>成片 2 s 切点</td>'
       '<td>trim 与 atrim 联动删除 1 s</td><td>节奏</td><td>动作连续，短 1 s</td></tr></table>')
EXECUTION = '<p data-contract="edit-execution"><a href="edit.py">剪辑脚本</a></p>'


class EditPlanTests(unittest.TestCase):
    def test_cut_needs_complete_row_and_real_script(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            html = header() + CUT + EXECUTION
            self.assertTrue(edit_plan_errors(html, directory))
            (directory / "edit.py").touch()
            self.assertEqual(edit_plan_errors(html, directory), [])
            self.assertTrue(edit_plan_errors(html.replace("<td>节奏</td>", "<td> </td>"), directory))
            self.assertTrue(edit_plan_errors(header(), directory))
            self.assertTrue(edit_plan_errors(header() + CUT, directory))
            for command, valid in [("稍后手工重新剪一下", False), ("ffmpeg -n -i a.mp4 -t 2 b.mp4", True)]:
                inline = f'<pre data-contract="edit-execution">{command}</pre>'
                self.assertEqual(not edit_plan_errors(header() + CUT + inline, directory), valid)

    def test_raw_score_and_minimum_boundaries(self):
        directory = Path(".")
        for raw, current, target in [("83.30", "85.0", "85"), ("84", "85.7", "85"), ("98", "100", "100")]:
            self.assertEqual(edit_plan_errors(header("当前版本已达标", raw, current, target), directory), [])
        for raw, current, target in [("83.29", "85.0", "85"), ("85", "86.7", "90"),
                                     ("86", "87.8", "84"), ("101", "100", "85"),
                                     ("NaN", "99", "85"), ("84", "95", "85")]:
            self.assertTrue(edit_plan_errors(header("当前版本已达标", raw, current, target), directory))

    def test_evidence_and_pickup_routes(self):
        directory = Path(".")
        self.assertEqual(edit_plan_errors(header("证据不足待核", "待核", "待核"), directory), [])
        self.assertTrue(edit_plan_errors(header("当前版本已达标", "待核", "待核"), directory))
        brief = '<p data-contract="pickup-brief">同机位补拍秤放稳，1 秒，接入第 2 秒并看全盘沿。</p>'
        limit = '<p data-contract="edit-limit">原片 0–2 秒被手遮住，逐帧与裁切均无法辨认盘沿。</p>'
        self.assertTrue(edit_plan_errors(header("需补充素材") + brief, directory))
        self.assertTrue(edit_plan_errors(header("需补充素材") + limit, directory))
        self.assertEqual(edit_plan_errors(header("需补充素材") + limit + brief, directory), [])
