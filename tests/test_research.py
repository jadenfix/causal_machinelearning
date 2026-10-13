import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ResearchReceiptTest(unittest.TestCase):
    def test_bounded_workflow_emits_verified_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            environment = os.environ.copy()
            environment["RESEARCH_N"] = "1000"
            completed = subprocess.run(
                [
                    sys.executable,
                    "run_research.py",
                    "Homework_2_Simulation_Code.ipynb",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            receipt = json.loads((output / "execution.json").read_text())

            self.assertEqual(receipt["status"], "verified")
            self.assertEqual(receipt["checks"]["expected_fit_count"], 10)
            self.assertTrue(receipt["checks"]["all_reported_values_finite"])
            self.assertTrue(receipt["checks"]["fit_observations_match_data"])
            self.assertEqual(receipt["results"]["sample_sizes"]["mincer"], 1000)
            self.assertEqual(
                receipt["results"]["fits"]["results_6"],
                receipt["results"]["fits"]["results_8"],
            )
            self.assertEqual(len(receipt["source"]["notebook_sha256"]), 64)
            self.assertEqual(len(receipt["source"]["runner_sha256"]), 64)
            self.assertGreater(receipt["figures"][0]["bytes"], 1000)
            self.assertTrue((output / receipt["figures"][0]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
