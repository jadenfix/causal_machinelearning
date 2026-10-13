"""Execute the original simulation notebook and emit a verifiable receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

RESULT_NAMES = (
    "results_5",
    "results_6",
    "results_7",
    "results_8",
    "results_9",
    "results_p2_1",
    "results_p2_2",
    "results_p2_4",
    "results_p3_3",
    "results_p3_4",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_identity(root: Path) -> dict[str, Any]:
    """Return local source identity without making Git a runtime requirement."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"git_commit": commit, "tracked_source_dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"git_commit": None, "tracked_source_dirty": None}


def summarize_fit(fit: Any) -> dict[str, Any]:
    """Serialize the small, reviewable part of a statsmodels OLS result."""
    coefficients = {str(key): float(value) for key, value in fit.params.items()}
    standard_errors = {str(key): float(value) for key, value in fit.bse.items()}
    values = [*coefficients.values(), *standard_errors.values(), float(fit.rsquared)]
    if not all(math.isfinite(value) for value in values):
        raise RuntimeError("Regression receipt contains a non-finite value")
    return {
        "coefficients": coefficients,
        "standard_errors": standard_errors,
        "r_squared": float(fit.rsquared),
        "observations": int(fit.nobs),
    }


def build_result_receipt(namespace: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    missing = [name for name in RESULT_NAMES if name not in namespace]
    if missing:
        raise RuntimeError(f"Notebook did not produce expected fits: {', '.join(missing)}")

    fits = {name: summarize_fit(namespace[name]) for name in RESULT_NAMES}
    if fits["results_6"] != fits["results_8"]:
        raise RuntimeError("Step 8 is documented as the same specification as Step 6")

    sample_sizes = {
        "mincer": int(len(namespace["df_mincer"])),
        "dice_collider": int(len(namespace["df_p2"])),
        "dice_selection_full": int(len(namespace["df_p3"])),
        "dice_selection_selected": int(len(namespace["df_p3_reduced"])),
    }
    expected_observations = {
        "results_5": sample_sizes["mincer"],
        "results_6": sample_sizes["mincer"],
        "results_7": sample_sizes["mincer"],
        "results_8": sample_sizes["mincer"],
        "results_9": sample_sizes["mincer"],
        "results_p2_1": sample_sizes["dice_collider"],
        "results_p2_2": sample_sizes["dice_collider"],
        "results_p2_4": sample_sizes["dice_collider"],
        "results_p3_3": sample_sizes["dice_selection_full"],
        "results_p3_4": sample_sizes["dice_selection_selected"],
    }
    mismatches = {
        name: {"fit": fits[name]["observations"], "data": count}
        for name, count in expected_observations.items()
        if fits[name]["observations"] != count
    }
    if mismatches:
        raise RuntimeError(f"Regression/data row-count mismatch: {mismatches}")

    checks = {
        "all_reported_values_finite": True,
        "step_8_matches_step_6": True,
        "fit_observations_match_data": True,
        "expected_fit_count": len(fits),
    }
    return {"sample_sizes": sample_sizes, "fits": fits}, checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", choices=["Homework_2_Simulation_Code.ipynb"])
    parser.add_argument("--output", default="research-output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    notebook_path = root / args.notebook
    os.chdir(root)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    namespace: dict[str, Any] = {"__name__": "__main__"}
    import numpy as np

    np.random.seed(42)
    namespace["display"] = lambda *items: [print(item) for item in items]
    started = time.perf_counter()
    executed = []
    notebook = json.loads(notebook_path.read_text())
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code" or not "".join(cell["source"]).strip():
            continue
        source = "".join(cell["source"])
        if any(line.lstrip().startswith(("%", "!")) for line in source.splitlines()):
            raise RuntimeError(
                "Notebook magic requires interactive Jupyter; this lane must contain ordinary Python"
            )
        print(f"Executing {args.notebook}: cell {index}", flush=True)
        exec(compile(source, f"{args.notebook}:cell{index}", "exec"), namespace)
        executed.append(index)

    import matplotlib.pyplot as plt

    figures = []
    for figure_number in plt.get_fignums():
        figure_path = output / f"figure-{figure_number}.png"
        plt.figure(figure_number).savefig(figure_path, dpi=130, bbox_inches="tight")
        figures.append(
            {
                "path": figure_path.name,
                "sha256": sha256(figure_path),
                "bytes": figure_path.stat().st_size,
            }
        )

    results, checks = build_result_receipt(namespace)
    report = {
        "schema_version": 1,
        "status": "verified",
        "notebook": args.notebook,
        "executed_cells": executed,
        "elapsed_seconds": time.perf_counter() - started,
        "seed": 42,
        "sample_controls": {
            key: os.environ[key]
            for key in ["RESEARCH_N", "RESEARCH_MAX_ROWS"]
            if key in os.environ
        },
        "source": {
            **git_identity(root),
            "notebook_sha256": sha256(notebook_path),
            "runner_sha256": sha256(Path(__file__)),
        },
        "checks": checks,
        "results": results,
        "figures": figures,
        "scope": (
            "Offline synthetic coursework simulation. Coefficients describe only this seeded "
            "generated sample; they do not estimate an effect in an observed population. "
            "RESEARCH_N=10000 is a bounded smoke run, not reproduction of the default "
            "1,000,000-row estimates."
        ),
    }
    receipt_path = output / "execution.json"
    receipt_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
