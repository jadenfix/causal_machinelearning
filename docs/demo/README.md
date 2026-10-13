# Verified workflow demo

The GIF and MP4 visualize an actual provider-free execution of
`Homework_2_Simulation_Code.ipynb` with `RESEARCH_N=10000`. The run produced
ten finite OLS receipts, verified fit/data row counts, an exact duplicate check
for Steps 6 and 8, and the displayed figure.

`capture.json` records the exact source commit and Git blobs, artifact SHA-256
digests, dimensions, frame count, and the bounded fixture scope.

Regenerate from a clean checkout of the recorded source:

```bash
python scripts/generate_demo.py --source <recorded-source>
```

Verify the committed source and fully decode both media files:

```bash
python scripts/verify_demo.py
```

The coefficients describe only this seeded synthetic coursework sample. The
demo makes no observational causal-effect, policy, accuracy, deployment, or
performance claim.
