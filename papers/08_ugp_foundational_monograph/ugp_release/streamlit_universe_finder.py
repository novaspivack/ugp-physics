
import streamlit as st
import pandas as pd
import math

from ugp_tools import ridge_full_table, export_survivors_csv, export_orders_csv, fib

st.set_page_config(page_title="UGP Universe Finder", layout="wide")

st.title("UGP Universe Finder — Interactive Explorer")

with st.sidebar:
    st.header("Controls")
    n_min = st.number_input("n min", min_value=10, max_value=60, value=10, step=1)
    n_max = st.number_input("n max", min_value=n_min, max_value=60, value=18, step=1)
    run_scan = st.button("Scan now")

    st.markdown("---")
    st.subheader("Filters")
    show_only_survivors = st.checkbox("Show only prime-locked survivors", value=True)
    highlight_mirror = st.checkbox("Highlight mirror pairs", value=True)
    show_n10_full = st.checkbox("Show full n=10 ridge table", value=True)

    st.markdown("---")
    st.subheader("Downloads")
    if st.button("Generate CSVs (survivors.csv, orders.csv)"):
        export_survivors_csv("survivors.csv", n_min, n_max)
        export_orders_csv("orders.csv", n_min, n_max)
        st.success("CSV files written to working directory.")
        st.download_button("Download survivors.csv", data=open("survivors.csv","rb").read(), file_name="survivors.csv")
        st.download_button("Download orders.csv", data=open("orders.csv","rb").read(), file_name="orders.csv")

if run_scan:
    # Build survivors dataframe
    from ugp_tools import ridge_survivors
    rows = []
    for n in range(n_min, n_max+1):
        for (nn, b2, q2, b1, q1, c1, isp) in ridge_survivors(n):
            rows.append(dict(n=nn,b2=b2,q2=q2,b1=b1,q1=q1,c1=c1,is_prime=isp))
    if rows:
        df = pd.DataFrame(rows).sort_values(["n","b2"])
        st.subheader("Survivors (prime-locked)")
        st.dataframe(df, use_container_width=True)
        # Plot survivors n vs b2
        st.subheader("Scatter: n vs b₂")
        st.write("Each point is a survivor (prime-locked). Click a row to inspect invariants.")

        # Selection
        sel_idx = st.number_input("Select row index to inspect", min_value=0, max_value=len(df)-1, value=0, step=1)
        sel = df.iloc[int(sel_idx)]
        st.markdown(f"**Selected:** n={sel.n}, b2={sel.b2}, q2={sel.q2}, b1={sel.b1}, q1={sel.q1}, c1={sel.c1}")

        # Invariants + Fibonacci lift
        st.markdown("### Invariants & Even-step Fibonacci lift")
        qgap = int(sel.q2 - sel.q1)
        st.write(f"q₂ - q₁ = {qgap} → Fibonacci lift F_{qgap} = {fib(qgap)}")
        st.write(f"Even-step b₃ = b₂ + F_{qgap} = {sel.b2 + fib(qgap)}")

        # Mirror-pair panel (if a partner exists in df)
        if highlight_mirror:
            pair = df[(df['n']==sel.n) & (df['b2']==sel.q2)]
            if not pair.empty:
                st.info(f"Mirror partner detected at the same n with b₂={int(sel.q2)} (q₂={int(sel.b2)}). Shares b₁={int(sel.b1)}.")
            else:
                st.warning("No mirror partner among survivors for this selection.")

        # Orders by n
        from ugp_tools import orders_by_n
        ords = orders_by_n(n_min, n_max)
        odf = pd.DataFrame(ords, columns=["n","order"])
        st.subheader("Orders by n")
        st.bar_chart(odf.set_index("n"))

    else:
        st.warning("No survivors in the given range. Try widening n.")
else:
    st.info("Set your n-range and press 'Scan now' to populate the explorer.")

# Full n=10 ridge table (includes composites)
if show_n10_full:
    st.markdown("---")
    st.subheader("Full n=10 ridge table (diagnostic, includes composites)")
    full = ridge_full_table(10)
    if full:
        cols = ["n","b2","q2","b1","q1","c1","is_prime","reason"]
        fdf = pd.DataFrame(full, columns=cols).sort_values("b2")
        st.dataframe(fdf, use_container_width=True)
        # Quick mirror highlight tip
        st.caption("Tip: rows with (b₂,q₂)=(24,42) and (42,24) share b₁=73 and both have prime c₁ (order-2 mirror).")
