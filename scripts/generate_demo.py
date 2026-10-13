"""Render a source-pinned demo from an actual bounded research execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FPS = 960, 540, 8
SOURCE_INPUTS = [
    "Homework_2_Simulation_Code.ipynb",
    "requirements.txt",
    "run_research.py",
    "scripts/generate_demo.py",
    "scripts/verify_demo.py",
    "tests/test_research.py",
]


def run(*command: str, capture: bool = False, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=capture,
        text=True,
    )
    return completed.stdout.strip() if capture else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None):
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=2)


def base_frame(scene: int, title: str, subtitle: str, progress: float) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#07111f")
    draw = ImageDraw.Draw(image)
    draw.ellipse((-120, -170, 370, 320), fill="#102b47")
    draw.ellipse((720, 330, 1100, 710), fill="#19284a")
    draw.text((48, 34), "CAUSAL MACHINE LEARNING", font=font(15, True), fill="#65d9c8")
    draw.text((48, 72), title, font=font(34, True), fill="#f5f8ff")
    draw.text((50, 119), subtitle, font=font(17), fill="#a9b9ca")
    draw.text((822, 36), f"0{scene + 1} / 05", font=font(14, True), fill="#7991aa")
    draw.rounded_rectangle((48, 509, 912, 516), radius=4, fill="#172b40")
    draw.rounded_rectangle((48, 509, 48 + int(864 * progress), 516), radius=4, fill="#65d9c8")
    return image


def draw_badge(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, color: str = "#65d9c8"):
    width = draw.textbbox((0, 0), label, font=font(13, True))[2] + 26
    draw.rounded_rectangle((x, y, x + width, y + 30), radius=15, fill="#12273b", outline=color)
    draw.text((x + 13, y + 7), label, font=font(13, True), fill=color)
    return x + width + 10


def make_scene(index: int, receipt: dict, chart: Image.Image, progress: float) -> Image.Image:
    if index == 0:
        image = base_frame(index, "A run you can inspect", "Original notebook → verified receipt", progress)
        draw = ImageDraw.Draw(image)
        rounded(draw, (48, 177, 912, 450), "#0d1c2b", "#244058")
        draw.text((82, 207), "10", font=font(74, True), fill="#65d9c8")
        draw.text((206, 224), "OLS fits captured", font=font(27, True), fill="#f5f8ff")
        draw.text((206, 263), "with coefficients, uncertainty, and row counts", font=font(17), fill="#9fb1c4")
        x = 82
        for label in ("SYNTHETIC", "OFFLINE", "SEED 42"):
            x = draw_badge(draw, x, 344, label)
        draw.text((82, 399), "No observed population • no policy or performance claim", font=font(15), fill="#71879e")
        return image

    if index == 1:
        image = base_frame(index, "The reproducible lane", "Bounded smoke run • 10,000 generated rows", progress)
        draw = ImageDraw.Draw(image)
        steps = [
            ("01", "Execute", "Original notebook cells"),
            ("02", "Validate", "Finite fits + row counts"),
            ("03", "Receipt", "Hashes + exact source"),
        ]
        for step, (number, label, detail) in enumerate(steps):
            x = 48 + step * 292
            rounded(draw, (x, 190, x + 260, 405), "#0d1c2b", "#244058")
            draw.text((x + 22, 211), number, font=font(18, True), fill="#65d9c8")
            draw.text((x + 22, 260), label, font=font(25, True), fill="#f5f8ff")
            draw.text((x + 22, 306), detail, font=font(14), fill="#9fb1c4")
            draw.text((x + 22, 357), "VERIFIED", font=font(13, True), fill="#75e09b")
        return image

    if index == 2:
        fit1 = receipt["results"]["fits"]["results_p2_1"]["coefficients"]["X"]
        fit2 = receipt["results"]["fits"]["results_p2_2"]["coefficients"]["X"]
        image = base_frame(index, "Collider conditioning changes association", "Seeded dice SCM • descriptive workflow evidence", progress)
        draw = ImageDraw.Draw(image)
        rounded(draw, (48, 178, 445, 424), "#0d1c2b", "#244058")
        rounded(draw, (465, 178, 912, 424), "#0d1c2b", "#244058")
        draw.text((76, 205), "MARGINAL", font=font(14, True), fill="#7991aa")
        draw.text((76, 249), f"X slope  {fit1:+.4f}", font=font(31, True), fill="#f5f8ff")
        draw.text((76, 314), "Y ~ X", font=font(18), fill="#9fb1c4")
        draw.text((493, 205), "CONDITION ON Z", font=font(14, True), fill="#7991aa")
        draw.text((493, 249), f"X slope  {fit2:+.4f}", font=font(31, True), fill="#ffb978")
        draw.text((493, 314), "Y ~ X + Z", font=font(18), fill="#9fb1c4")
        draw.text((76, 379), "Synthetic association—not an empirical effect estimate", font=font(14), fill="#71879e")
        return image

    if index == 3:
        image = base_frame(index, "Selection changes the fitted view", "Actual figure emitted by the tested notebook", progress)
        image.paste(chart, (48, 164))
        draw = ImageDraw.Draw(image)
        rounded(draw, (670, 181, 912, 415), "#0d1c2b", "#244058")
        full = receipt["results"]["fits"]["results_p3_3"]["coefficients"]["X"]
        selected = receipt["results"]["fits"]["results_p3_4"]["coefficients"]["X"]
        selected_n = receipt["results"]["sample_sizes"]["dice_selection_selected"]
        draw.text((694, 206), "FULL SAMPLE", font=font(13, True), fill="#7991aa")
        draw.text((694, 235), f"{full:.4f}", font=font(30, True), fill="#f5f8ff")
        draw.text((694, 295), "SELECTED Z=1", font=font(13, True), fill="#7991aa")
        draw.text((694, 324), f"{selected:.4f}", font=font(30, True), fill="#ffb978")
        draw.text((694, 376), f"{selected_n} / 200 rows", font=font(14), fill="#9fb1c4")
        return image

    image = base_frame(index, "Verified—and deliberately bounded", "A truthful receipt for an archived coursework simulation", progress)
    draw = ImageDraw.Draw(image)
    checks = [
        "10 expected fits present",
        "All reported values finite",
        "Fit rows match generated data",
        "Step 8 exactly matches Step 6",
        "Figure and source hashes recorded",
    ]
    rounded(draw, (48, 170, 912, 438), "#0d1c2b", "#244058")
    for row, label in enumerate(checks):
        y = 197 + row * 43
        draw.ellipse((78, y + 2, 96, y + 20), fill="#65d9c8")
        draw.line((83, y + 11, 88, y + 16, 94, y + 7), fill="#07111f", width=2)
        draw.text((112, y), label, font=font(17), fill="#e9f0f8")
    draw.text((610, 393), "python run_research.py …", font=font(13), fill="#71879e")
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Committed source SHA to record")
    parser.add_argument("--output", default="docs/demo")
    args = parser.parse_args()
    source = run("git", "rev-parse", args.source, capture=True)
    head = run("git", "rev-parse", "HEAD", capture=True)
    if source != head:
        raise SystemExit("--source must equal HEAD while recording")
    dirty_inputs = run("git", "status", "--porcelain", "--", *SOURCE_INPUTS, capture=True)
    if dirty_inputs:
        raise SystemExit(f"Refusing to record dirty source inputs:\n{dirty_inputs}")

    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        receipt_dir = Path(temporary) / "research"
        environment = os.environ.copy()
        environment["RESEARCH_N"] = "10000"
        run(
            str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else "python",
            "run_research.py",
            "Homework_2_Simulation_Code.ipynb",
            "--output",
            str(receipt_dir),
            env=environment,
        )
        receipt = json.loads((receipt_dir / "execution.json").read_text())
        chart = Image.open(receipt_dir / "figure-1.png").convert("RGB")
        chart.thumbnail((600, 285), Image.Resampling.LANCZOS)
        chart_canvas = Image.new("RGB", (600, 285), "#ffffff")
        chart_canvas.paste(chart, ((600 - chart.width) // 2, (285 - chart.height) // 2))

        frames_dir = Path(temporary) / "frames"
        frames_dir.mkdir()
        scene_seconds = [3.2, 3.4, 4.0, 4.0, 3.6]
        total_frames = int(sum(scene_seconds) * FPS)
        frame_number = 0
        poster = None
        for scene, seconds in enumerate(scene_seconds):
            count = int(seconds * FPS)
            for _ in range(count):
                progress = (frame_number + 1) / total_frames
                frame = make_scene(scene, receipt, chart_canvas, progress)
                frame.save(frames_dir / f"frame-{frame_number:04d}.png")
                if scene == 0 and poster is None:
                    poster = frame.copy()
                frame_number += 1

        assert poster is not None
        poster.save(output / "causal-machinelearning-poster.png")
        run(
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "frame-%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output / "causal-machinelearning-demo.mp4"),
        )
        run(
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "frame-%04d.png"),
            "-vf", "fps=8,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
            "-loop", "0", str(output / "causal-machinelearning-demo.gif"),
        )

    source_blobs = {}
    for path in SOURCE_INPUTS:
        entry = run("git", "ls-tree", source, "--", path, capture=True).split()
        source_blobs[path] = entry[2]
    artifacts = {}
    for name in (
        "causal-machinelearning-demo.gif",
        "causal-machinelearning-demo.mp4",
        "causal-machinelearning-poster.png",
    ):
        path = output / name
        artifacts[name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    capture = {
        "schema_version": 1,
        "recorded_source": source,
        "source_blobs": source_blobs,
        "command": "python scripts/generate_demo.py --source " + source,
        "workflow": {
            "notebook": "Homework_2_Simulation_Code.ipynb",
            "sample_mode": "RESEARCH_N=10000 bounded synthetic smoke run",
            "receipt_checks": receipt["checks"],
            "sample_sizes": receipt["results"]["sample_sizes"],
        },
        "media": {
            "width": WIDTH,
            "height": HEIGHT,
            "fps": FPS,
            "frames": frame_number,
            "scope": "Offline seeded synthetic coursework only; no population causal-effect, policy, accuracy, or performance claim.",
            "artifacts": artifacts,
        },
    }
    (output / "capture.json").write_text(json.dumps(capture, indent=2) + "\n")
    print(json.dumps(capture, indent=2))


if __name__ == "__main__":
    main()
