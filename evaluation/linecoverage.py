import os
import json
import subprocess as sp
import shutil

PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_PATH = os.path.join(PATH, "test")
COV_PATH = os.path.join(PATH, "test_cov")

def linecoverage(input: str, output: str):
    # copy input to backend/tests/input.json
    shutil.copy(input, os.path.join(PATH, "backend/tests/input.json"))
    # run pytest
    sp.run(["pytest", "--disable-warnings", "--cov=conduit", "--cov-branch", "--cov-report=json", "tests"], cwd=os.path.join(PATH, "backend"))
    # copy output to backend/tests/output.json
    shutil.copy(os.path.join(PATH, "backend/coverage.json"), output)

def linecoverage_all():
    stats = {
        "covered_lines": 0,
        "num_statements": 0,
        "missing_lines": 0,
        "excluded_lines": 0,
        "num_branches": 0,
        "num_partial_branches": 0,
        "covered_branches": 0,
        "missing_branches": 0
    }
    for file in os.listdir(TEST_PATH):
        if file.endswith(".json"):
            linecoverage(os.path.join(TEST_PATH, file), os.path.join(COV_PATH, file))
            with open(os.path.join(COV_PATH, file), "r") as f:
                data = json.load(f)
                for _, value in data["files"].items():
                    for k, _ in stats.items():
                        stats[k] += value["summary"][k]

    stats["line_coverage"] = stats["covered_lines"] / stats["num_statements"] * 100 if stats["num_statements"] > 0 else 0
    stats["branch_coverage"] = stats["covered_branches"] / stats["num_branches"] * 100 if stats["num_branches"] > 0 else 0

    with open(os.path.join(COV_PATH, "stats_summary.json"), "w") as f:
        json.dump(stats, f)


if __name__ == "__main__":
    linecoverage_all()
