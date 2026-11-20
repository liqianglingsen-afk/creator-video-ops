import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/short-video-forensic-teardown/scripts"))
from revision_contract import revision_check


class RevisionContractTests(unittest.TestCase):
    def test_technical_report_or_wrong_visible_scores_cannot_finish(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "comparison.html"
            path.write_text("<main>技术评分 91</main>")
            with self.assertRaises(ValueError):
                revision_check(path, "comparison")
            from edit_plan_contract import WEIGHTS

            marks = {k: dict(score=str(v)) for k, v in WEIGHTS.items()}
            doc = dict(
                kind="comparison",
                schema_version="revision-0.4",
                seal="abc",
                plan=dict(forecast={}),
                baseline=dict(content=dict(marks=marks)),
                after=dict(content=dict(marks=marks)),
                assets=[],
                packaging={},
                placements=[],
                status="待核",
                pending=[],
                fixes=[],
            )
            (root / "comparison.json").write_text(json.dumps(doc))
            digest = hashlib.sha256(
                json.dumps(doc, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()
            ).hexdigest()
            rows = "".join(
                f'<tr data-revision-dimension="{k}"><td>{k}</td><td>{v}</td><td>{v}</td><td>未存</td><td>{v}</td></tr>'
                for k, v in WEIGHTS.items()
            )
            html = f'<main data-revision="comparison" data-record-sha256="{digest}" data-plan-seal="abc"><table>{rows}</table></main>'
            path.write_text(html)
            self.assertTrue(revision_check(path, "comparison"))
            path.write_text(html.replace("<td>未存</td>", "<td>85</td>", 1))
            with self.assertRaises(ValueError):
                revision_check(path, "comparison")
