
import argparse, csv, sys, os
from ugp_tools import ridge_full_table, export_survivors_csv, export_orders_csv

def cmd_scan(args):
    out_dir = args.out or "."
    os.makedirs(out_dir, exist_ok=True)
    surv = os.path.join(out_dir, "survivors.csv")
    ords = os.path.join(out_dir, "orders.csv")
    export_survivors_csv(surv, args.n_min, args.n_max)
    export_orders_csv(ords, args.n_min, args.n_max)
    print(f"Wrote {surv} and {ords}")

def cmd_table(args):
    n = args.n
    rows = ridge_full_table(n)
    writer = csv.writer(sys.stdout)
    writer.writerow(["n","b2","q2","b1","q1","c1","is_prime","reason"])
    for r in rows:
        writer.writerow(r)

def main():
    p = argparse.ArgumentParser(prog="ugp_cli.py", description="UGP tools CLI")
    sub = p.add_subparsers()

    s1 = sub.add_parser("scan", help="Export survivors.csv and orders.csv")
    s1.add_argument("--n-min", type=int, required=True)
    s1.add_argument("--n-max", type=int, required=True)
    s1.add_argument("--out", type=str, default=".")
    s1.set_defaults(func=cmd_scan)

    s2 = sub.add_parser("table", help="Print full ridge table for a given n (including composites)")
    s2.add_argument("-n", "--n", type=int, required=True)
    s2.set_defaults(func=cmd_table)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
