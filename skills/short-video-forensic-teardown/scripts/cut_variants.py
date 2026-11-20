"""Export matched comparison cuts from an existing source and second-based edit lists."""
import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


def render(plan: Path, output: Path):
    spec = json.loads(plan.read_text(encoding="utf-8"))
    video = (plan.parent / spec["video"]).resolve()
    output = output.resolve()
    if output.exists():
        raise ValueError("需要新的输出目录")
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                                              "-of", "json", str(video)]))
    duration = float(info["format"]["duration"])
    audio = any(s["codec_type"] == "audio" for s in info["streams"])
    variants = spec["variants"]
    if not variants:
        raise ValueError("请提供至少一个剪辑版本")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temporary:
        work = Path(temporary)
        result = work / "results"
        result.mkdir()
        seen = set()
        for variant in variants:
            name = variant["name"]
            if not name or name in seen or any(ch in name for ch in '/\\<>:"|?*') or name in {".",".."}:
                raise ValueError("版本名需唯一并可作为文件名")
            seen.add(name)
            filters = []
            segments = variant["segments"]
            if not segments:
                raise ValueError("剪辑单缺少片段")
            tracks = [("v", segments)]
            if audio:
                tracks.append(("a", variant.get("audio_segments", segments)))
            elif "audio_segments" in variant:
                raise ValueError("无声素材无法指定独立音轨")
            length = sum(end - start for start, end in segments)
            for track, spans in tracks:
                if not spans or abs(sum(end - start for start, end in spans) - length) > 0.001:
                    raise ValueError("替换画面时，音轨与画面长度须一致")
                nodes = []
                for i, (start, end) in enumerate(spans):
                    if not all(math.isfinite(t) for t in (start, end)) or not 0 <= start < end <= duration:
                        raise ValueError(f"源时码超出范围：{start}–{end}")
                    node = f"[{track}{i}]"
                    op = "atrim" if track == "a" else "trim"
                    pts = "asetpts" if track == "a" else "setpts"
                    filters.append(f"[0:{track}]{op}=start={start}:end={end},{pts}=PTS-STARTPTS{node}")
                    nodes.append(node)
                filters.append("".join(nodes) + f"concat=n={len(nodes)}:v={int(track=='v')}:a={int(track=='a')}[{track}]")
            label = "[v]"
            if variant.get("ass"):
                shutil.copyfile(plan.parent / variant["ass"], work / "captions.ass")
                filters.append("[v]ass=captions.ass[captioned]")
                label = "[captioned]"
            destination = result / (name + ".mp4")
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(video), "-filter_complex", ";".join(filters), "-map", label]
            if audio:
                cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
            subprocess.run(cmd+["-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(destination)], cwd=work, check=True)
        result.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.plan, args.output)
