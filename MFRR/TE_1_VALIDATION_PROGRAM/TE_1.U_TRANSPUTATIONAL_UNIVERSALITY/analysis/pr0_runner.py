#!/usr/bin/env python3
"""Generic PR-0 execution runner for TE1.U benchmarks.

Reads a command template from YAML, formats argument placeholders, and spawns
the PR-0 CLI process. Designed to work with `configs/pr0_job_template.yaml` or
per-benchmark variants.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import Dict

import yaml  # type: ignore
import csv
import numpy as np

CURRENT_FILE = Path(__file__).resolve()
PR0_PARENT = CURRENT_FILE.parents[5]  # ugp-physics repository root (see pr0_system/)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PR-0 benchmark job")
    parser.add_argument("--config", required=True, type=Path, help="YAML file describing the job")
    parser.add_argument("--dry-run", action="store_true", help="Print command and exit")
    return parser.parse_args()


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_command(command_cfg: Dict, exec_cfg: Dict) -> Dict[str, str]:
    fmt_kwargs = {
        "benchmark_config": exec_cfg.get("benchmark_config"),
        "output": exec_cfg.get("output_path"),
    }
    executable = command_cfg["executable"]
    args = [arg.format(**fmt_kwargs) for arg in command_cfg.get("arguments", [])]
    workdir = command_cfg.get("working_directory")
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", "")
    extra_path = str(PR0_PARENT)
    env["PYTHONPATH"] = (
        extra_path
        if not env["PYTHONPATH"]
        else os.pathsep.join([extra_path, env["PYTHONPATH"]])
    )
    env.update(command_cfg.get("env", {}))
    return {
        "executable": executable,
        "args": args,
        "cwd": workdir,
        "env": env,
    }


def write_logs(stdout_data: bytes, stderr_data: bytes, exec_cfg: Dict) -> None:
    stdout_path = Path(exec_cfg.get("log_path", "results/pr0_stdout.log"))
    stderr_path = Path(exec_cfg.get("stderr_path", "results/pr0_stderr.log"))
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_bytes(stdout_data)
    stderr_path.write_bytes(stderr_data)


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    command_cfg = cfg["command"]
    exec_cfg = cfg["execution"]

    build = build_command(command_cfg, exec_cfg)
    cmdline = [build["executable"], *build["args"]]
    if args.dry_run:
        print("Command:", " ".join(cmdline))
        print("cwd:", build.get("cwd"))
        return

    result = subprocess.run(
        cmdline,
        cwd=build.get("cwd"),
        env=build.get("env"),
        capture_output=True,
        check=False,
    )
    write_logs(result.stdout, result.stderr, exec_cfg)

    if result.returncode != 0:
        raise SystemExit(f"PR-0 command failed with code {result.returncode}")

    output_path = Path(exec_cfg.get("output_path"))
    if not output_path.exists():
        print("Warning: expected output was not created:", output_path)

    npy_target = exec_cfg.get("csv_to_npy")
    if npy_target and output_path.exists():
        with output_path.open("r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
        if rows:
            keys = reader.fieldnames or list(rows[0].keys())
            data = np.array([[float(row[key]) for key in keys] for row in rows], dtype=float)
            npy_path = Path(npy_target)
            npy_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(npy_path, data)
            print(f"Converted CSV to {npy_path}")

    print("PR-0 job completed successfully")


if __name__ == "__main__":
    main()
