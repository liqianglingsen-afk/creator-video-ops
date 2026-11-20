"""Render editable cover variants and inspect how they crop at thumbnail size."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont, ImageOps


def source_frame(video: Path, seconds: float, destination: Path) -> None:
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("取帧时码必须是非负秒数")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(seconds), "-i", str(video),
                    "-frames:v", "1", "-update", "1", str(destination)], check=True)
    if not destination.is_file():
        raise ValueError(f"未能在 {seconds:g}s 取帧")


def previews(image: Image.Image, folder: Path, name: str) -> None:
    for w, h in ((180, 240), (180, 180), (180, 320)):
        preview = ImageOps.fit(image, (w, h), method=Image.Resampling.LANCZOS)
        preview.save(folder / f"{name}-{w}x{h}.jpg", quality=91)


def fit_font(draw, font_path: Path, size: int, text: str, width: int):
    for px in range(size, 19, -1):
        face = ImageFont.truetype(str(font_path), px)
        if draw.textlength(text, font=face) <= width:
            return face
    raise ValueError("标题超出一行可读范围，请拆行或缩短")


def render(plan_file: Path, output: Path) -> None:
    plan_file = plan_file.resolve()
    spec = json.loads(plan_file.read_text(encoding="utf-8"))
    video = (plan_file.parent / spec["video"]).resolve()
    font = (plan_file.parent / spec["font"]).resolve()
    if output.exists() or not video.is_file() or not font.is_file():
        raise ValueError("需要可读视频与字体，以及一个新的输出目录")
    if len(spec["variants"]) < 2:
        raise ValueError("至少提供两种不同点击理由的候选")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as tmp:
        dest = Path(tmp) / "covers"
        dest.mkdir()
        source_frame(video, 0, dest / "first-frame.png")
        with Image.open(dest / "first-frame.png") as image:
            previews(image.convert("RGB"), dest, "first-frame")
        if spec.get("published_cover"):
            with Image.open(plan_file.parent / spec["published_cover"]) as image:
                actual = ImageOps.exif_transpose(image).convert("RGB")
                actual.save(dest / "published.png")
                previews(actual, dest, "published")
        portable = dict(spec, video=str(video), font=str(font))
        if spec.get("published_cover"):
            portable["published_cover"] = str((plan_file.parent / spec["published_cover"]).resolve())
        for idx, variant in enumerate(spec["variants"], 1):
            name = f"cover-{idx}"
            frame = dest / (name + "-frame.png")
            source_frame(video, float(variant["seconds"]), frame)
            lines = variant["headline"]
            if not isinstance(lines, list) or not 1 <= len(lines) <= 3 or not all(isinstance(t, str) and t.strip() for t in lines):
                raise ValueError("每个候选标题需一至三行非空文字")
            for ratio, height in (("3x4", 1200), ("1x1", 900), ("9x16", 1600)):
                canvas = Image.new("RGB", (900, height), variant.get("background", "#173e35"))
                draw = ImageDraw.Draw(canvas)
                top = 50
                for line in lines:
                    face = fit_font(draw, font, 82, line, 814)
                    draw.text((44, top), line, font=face, fill=variant.get("foreground", "#ffffff"), anchor="lt")
                    top += face.size + 22
                if variant.get("subline"):
                    face = fit_font(draw, font, 36, variant["subline"], 814)
                    draw.text((44, top), variant["subline"], font=face, fill=variant.get("foreground", "#ffffff"), anchor="lt")
                    top += face.size + 18
                origin = top + 28
                focus = float(variant.get("focus_y", 0.5))
                if not 0 <= focus <= 1:
                    raise ValueError("focus_y 须在 0 到 1 之间")
                with Image.open(frame) as image:
                    crop = ImageOps.fit(image.convert("RGB"), (900, height - origin), Image.Resampling.LANCZOS,
                                        centering=(0.5, focus))
                canvas.paste(crop, (0, origin))
                if height == 1200:
                    canvas.save(dest / (name + ".png"))
                    previews(canvas, dest, name)
                else:
                    canvas.save(dest / f"{name}-layout-{ratio}.jpg", quality=94)
                    canvas.resize((180, height // 5), Image.Resampling.LANCZOS).save(dest / f"{name}-thumb-{ratio}.jpg", quality=93)
        (dest / "cover-plan.json").write_text(json.dumps(portable, ensure_ascii=False, indent=2), encoding="utf-8")
        dest.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.plan, args.output)
