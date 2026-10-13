"""Fail closed when published media or its recorded source has drifted."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "docs/demo"


def run(*command: str) -> str:
    return subprocess.run(
        command, cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    capture = json.loads((DEMO / "capture.json").read_text())
    source = capture["recorded_source"]
    run("git", "merge-base", "--is-ancestor", source, "HEAD")
    for path, expected_blob in capture["source_blobs"].items():
        recorded_blob = run("git", "rev-parse", f"{source}:{path}")
        current_blob = run("git", "rev-parse", f"HEAD:{path}")
        if recorded_blob != expected_blob or current_blob != expected_blob:
            raise SystemExit(f"Source drift for {path}")

    media = capture["media"]
    for name, expected in media["artifacts"].items():
        path = DEMO / name
        if path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
            raise SystemExit(f"Artifact drift for {name}")

    for name in ("causal-machinelearning-demo.gif", "causal-machinelearning-demo.mp4"):
        path = DEMO / name
        probe = json.loads(
            run(
                "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,nb_read_frames", "-of", "json", str(path),
            )
        )["streams"][0]
        if int(probe["width"]) != media["width"] or int(probe["height"]) != media["height"]:
            raise SystemExit(f"Unexpected dimensions for {name}")
        if int(probe["nb_read_frames"]) != media["frames"]:
            raise SystemExit(f"Unexpected frame count for {name}")
        run("ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-")
    print("Demo source and media verified")


if __name__ == "__main__":
    main()
