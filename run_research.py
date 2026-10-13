"""Execute original notebook code in order without requiring a notebook server."""
import argparse, json, os, time
from pathlib import Path
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
parser=argparse.ArgumentParser()
parser.add_argument("notebook", choices=['Homework_2_Simulation_Code.ipynb'])
parser.add_argument("--output", default="research-output")
args=parser.parse_args()
root=Path(__file__).resolve().parent
os.chdir(root)
out=Path(args.output); out.mkdir(parents=True, exist_ok=True)
namespace={"__name__":"__main__"}
import numpy as np
np.random.seed(42)
namespace["display"]=lambda *items: [print(item) for item in items]
started=time.perf_counter(); executed=[]
for i,cell in enumerate(json.loads((root/args.notebook).read_text())["cells"]):
    if cell["cell_type"]!="code" or not "".join(cell["source"]).strip(): continue
    source="".join(cell["source"])
    if any(line.lstrip().startswith(("%", "!")) for line in source.splitlines()):
        raise RuntimeError("Notebook magic requires interactive Jupyter; this lane must contain ordinary Python")
    print(f"Executing {args.notebook}: cell {i}", flush=True)
    exec(compile(source, f"{args.notebook}:cell{i}", "exec"), namespace)
    executed.append(i)
import matplotlib.pyplot as plt
for i in plt.get_fignums(): plt.figure(i).savefig(out/f"figure-{i}.png", dpi=130, bbox_inches="tight")
report={"notebook":args.notebook,"executed_cells":executed,"elapsed_seconds":time.perf_counter()-started,"seed":42,"sample_controls":{k:os.environ[k] for k in ["RESEARCH_N","RESEARCH_MAX_ROWS"] if k in os.environ},"scope":'The Mincer-model simulation runs offline. Its generated observations are synthetic by design; they are not the unavailable observational `hw1_small.csv` study. The default uses the original 1,000,000 observations; set `RESEARCH_N=10000` for a bounded smoke run, which is not reproduction of full-scale estimates.'}
if "results" in namespace and isinstance(namespace["results"],dict): report["model_results"]=namespace["results"]
(out/"execution.json").write_text(json.dumps(report, indent=2, default=str))
print(json.dumps(report, indent=2, default=str))
