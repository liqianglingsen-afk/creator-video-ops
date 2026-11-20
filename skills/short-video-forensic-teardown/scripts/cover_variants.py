"""Render editable cover variants and inspect how they crop at thumbnail size."""
from __future__ import annotations

import argparse
import hashlib
import json
from html import escape
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


def draw_layout(frame, font, variant, lines, height):
    mode = variant.get("layout", "panel")
    if mode not in {"panel", "photo"}:
        raise ValueError("layout 取 panel 或 photo")
    fx, fy = (float(variant.get(key, 0.5)) for key in ("focus_x", "focus_y"))
    x, y = (float(variant.get(key, default)) for key, default in (("text_x", 44/900), ("text_y", 50/height)))
    if not all(0 <= f <= 1 for f in (fx, fy, x, y)):
        raise ValueError("裁切焦点和文字位置须在 0 到 1 之间")
    canvas = Image.new("RGB", (900, height), variant.get("background", "#173e35"))
    with Image.open(frame) as source:
        photo = source.convert("RGB")
    if "source_crop" in variant:
        left, upper, right, lower = map(float, variant["source_crop"])
        if not (0 <= left < right <= 1 and 0 <= upper < lower <= 1):
            raise ValueError("source_crop 须为归一化的左、上、右、下边界")
        photo = photo.crop((round(left*photo.width), round(upper*photo.height),
                            round(right*photo.width), round(lower*photo.height)))
    if mode == "photo":
        canvas = ImageOps.fit(photo, canvas.size, Image.Resampling.LANCZOS, centering=(fx, fy))
    draw = ImageDraw.Draw(canvas)
    left, top = round(900*x), round(height*y)
    width = 900 - left - 42
    texts = [(line, 82) for line in lines]
    if variant.get("subline"):
        texts.append((variant["subline"], 36))
    for line, size in texts:
        face = fit_font(draw, font, size, line, width)
        if top + face.size > height:
            raise ValueError("文字超出画布，请调整 text_x/text_y 或行数")
        draw.text((left, top), line, font=face, fill=variant.get("foreground", "#ffffff"),
                  stroke_width=2 if mode == "photo" else 0, stroke_fill=variant.get("outline", "#18231f"), anchor="lt")
        top += face.size + (18 if size == 36 else 22)
    if mode == "panel":
        origin = top + 28
        if origin >= height:
            raise ValueError("文字区占满画面")
        crop = ImageOps.fit(photo, (900, height - origin), Image.Resampling.LANCZOS, centering=(fx, fy))
        canvas.paste(crop, (0, origin))
    return canvas


def preview_page(variants):
    cards = []
    for idx, v in enumerate(variants, 1):
        title = escape(" ".join(v["headline"]))
        name = f"cover-{idx}"
        cards.append(f'<section><h2>{title}</h2><p>{escape(v.get("motive", ""))}</p>'
                     f'<a href="{name}.png">完整封面</a><div><img src="{name}-180x240.jpg" alt="三比四">'
                     f'<img src="{name}-thumb-1x1.jpg" alt="方形重排"><img src="{name}-thumb-9x16.jpg" alt="竖屏重排"></div></section>')
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>封面候选预览</title><style>body{font:16px/1.6 system-ui;margin:4vw auto;max-width:900px;padding:12px}'
            'img{width:180px;height:auto;align-self:start}div{display:flex;flex-wrap:wrap;gap:8px}</style>'
            '<h1>模拟列表预览</h1><p>按 180 像素宽比对。平台实际展示与界面遮挡须在对应版位核对。</p>'
            '<a href="cover-plan.json">可编辑方案</a>' + ''.join(cards) + '</html>')


def render(plan_file: Path, output: Path) -> None:
    plan_file = plan_file.resolve()
    spec = json.loads(plan_file.read_text(encoding="utf-8"))
    video = (plan_file.parent / spec["video"]).resolve()
    font = (plan_file.parent / spec["font"]).resolve()
    if output.exists() or not video.is_file() or not font.is_file():
        raise ValueError("需要可读视频与字体，以及一个新的输出目录")
    if len(spec["variants"]) < 2:
        raise ValueError("至少提供两种不同点击理由的候选")
    motives = {str(v.get("motive","")).strip() for v in spec["variants"]}
    if "" in motives or len(motives)<2:
        raise ValueError("须说明两个不同观看理由")
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
        images = set()
        for idx, variant in enumerate(spec["variants"], 1):
            name = f"cover-{idx}"
            frame = dest / (name + "-frame.png")
            source_frame(video, float(variant["seconds"]), frame)
            lines = variant["headline"]
            if not isinstance(lines, list) or not 0 <= len(lines) <= 3 or not all(isinstance(t, str) and t.strip() for t in lines):
                raise ValueError("标题最多三行非空文字。无字封面使用空数组和 photo 版式")
            if not lines and variant.get("layout") != "photo":
                raise ValueError("无字封面使用满版画面 photo")
            for ratio, height in (("3x4", 1200), ("1x1", 900), ("9x16", 1600)):
                canvas = draw_layout(frame, font, variant, lines, height)
                if height == 1200:
                    signature = hashlib.sha256(canvas.tobytes()).digest()
                    if signature in images:
                        raise ValueError("两案实际成图相同，请调整标题、取帧或构图")
                    images.add(signature)
                    canvas.save(dest / (name + ".png"))
                    previews(canvas, dest, name)
                else:
                    canvas.save(dest / f"{name}-layout-{ratio}.jpg", quality=94)
                    canvas.resize((180, height // 5), Image.Resampling.LANCZOS).save(dest / f"{name}-thumb-{ratio}.jpg", quality=93)
        (dest / "cover-plan.json").write_text(json.dumps(portable, ensure_ascii=False, indent=2), encoding="utf-8")
        (dest / "preview.html").write_text(preview_page(spec["variants"]), encoding="utf-8")
        dest.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.plan, args.output)
