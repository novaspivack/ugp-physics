import subprocess
import sys

def run(cmd):
    r = subprocess.run(cmd, shell=True)
    if r.returncode != 0:
        sys.exit(r.returncode)

def main():
    run("python -m src.rcp.run_l1")
    run("python -m src.rcp.run_l2")
    run("python -m src.rcp.run_l3")
    run("python -m src.rcp.run_rg")
    run("python -m src.rcp.run_pc")

if __name__ == "__main__":
    main()

