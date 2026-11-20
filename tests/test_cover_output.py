"""Check the actual editable images delivered by the cover CLI."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image, ImageFont
except ImportError:
    Image = ImageFont = None

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/short-video-forensic-teardown/scripts/cover_variants.py"
)


@unittest.skipUnless(ImageFont is not None, "cover rendering requires Pillow")
class CoverOutputTests(unittest.TestCase):
    def test_motive_only_change_fails_and_distinct_frames_export(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("requires ffmpeg")
        for candidate in (
            "DejaVuSans.ttf",
            "Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ):
            try:
                font = ImageFont.truetype(candidate, 20).path
                break
            except OSError:
                continue
        else:
            self.skipTest("requires a font")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "motion.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=s=120x180:r=10:d=2",
                    "-c:v",
                    "libx264",
                    str(video),
                ],
                check=True,
            )
            a = {"seconds": 0, "headline": [], "layout": "photo", "motive": "预测运动"}
            b = a | {"motive": "查看结果"}
            spec = {"video": str(video), "font": str(font), "variants": [a, b]}
            plan = root / "input.json"
            output = root / "covers"

            def render():
                plan.write_text(json.dumps(spec), encoding="utf-8")
                return subprocess.run(
                    [sys.executable, str(SCRIPT), str(plan), "--output", str(output)],
                    capture_output=True,
                )

            self.assertNotEqual(render().returncode, 0)
            self.assertFalse(output.exists())
            b["seconds"] = 1
            res = render()
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue((output / "cover-plan.json").is_file())
            for index in (1, 2):
                with Image.open(output / f"cover-{index}-180x240.jpg") as thumb:
                    self.assertEqual(thumb.size, (180, 240))
