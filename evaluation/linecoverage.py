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
    set_of_files = dict()
    for i, file in enumerate(os.listdir(TEST_PATH)):
        if file.endswith(".json"):
            linecoverage(os.path.join(TEST_PATH, file), os.path.join(COV_PATH, file))
            with open(os.path.join(COV_PATH, file), "r") as f:
                data = json.load(f)
                for key, value in data["files"].items():
                    if key not in set_of_files:
                        set_of_files[key] = {
                            "executed_lines": set(),
                            "missing_lines": set(),
                            "excluded_lines": set(),
                            "executed_branches": set(),
                            "missing_branches": set(),
                        }
                    for k, v in set_of_files[key].items():
                        if "branches" in k:
                            v = v | set(tuple(t) for t in value[k])
                        else:
                            v = v | set(value[k])
                        set_of_files[key][k] = v
            
            if i % 1000 == 0:
                for key, value in set_of_files.items():
                    value["missing_lines"] = value["missing_lines"] - value["excluded_lines"] - value["executed_lines"]
                    value["missing_branches"] = value["missing_branches"] - value["executed_branches"]
                    value["excluded_lines"] = value["excluded_lines"] - value["executed_lines"]

                stats = {
                    "covered_lines": sum(len(value["executed_lines"]) for value in set_of_files.values()),
                    "num_statements": sum(len(value["executed_lines"]) + len(value["missing_lines"]) + len(value["excluded_lines"]) for value in set_of_files.values()),
                    "missing_lines": sum(len(value["missing_lines"]) for value in set_of_files.values()),
                    "excluded_lines": sum(len(value["excluded_lines"]) for value in set_of_files.values()),
                    "num_branches": sum(len(value["executed_branches"]) + len(value["missing_branches"]) for value in set_of_files.values()),
                    "covered_branches": sum(len(value["executed_branches"]) for value in set_of_files.values()),
                    "missing_branches": sum(len(value["missing_branches"]) for value in set_of_files.values())
                }
                stats["line_coverage"] = stats["covered_lines"] / stats["num_statements"] * 100 if stats["num_statements"] > 0 else 0
                stats["branch_coverage"] = stats["covered_branches"] / stats["num_branches"] * 100 if stats["num_branches"] > 0 else 0

                for key, value in set_of_files.items():
                    for k, v in value.items():
                        v = list(v)
                        v.sort()
                        value[k] = len(v)

                with open(os.path.join(COV_PATH, "stats_summary.json"), "w") as f:
                    json.dump(
                        {
                            "stats": stats,
                            "set_of_files": set_of_files
                        },
                        f, indent=4, sort_keys=True)

if __name__ == "__main__":
    linecoverage_all()
