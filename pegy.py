from numpy import sort
import re
import streamlit as st
from header import add_header
from insights import add_insights
from calculate_pegy import calculate_pegy
from display import format_display
from tickers.snp import symbols as snp_tickers

# AI summary generators
from ai import generate_company_summary, get_cached_summary


tickers_input, refresh = add_header()


def _safe_key(label: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]+", "_", label)


def calculate_and_display_pegy(tickers, category):
    """Lazy-load and display PEGY data for `category`.

    Data is computed only when the user clicks the per-tab Load button and is
    cached in `st.session_state` under `df_<safe_category>`.
    """
    key = f"df_{_safe_key(category)}"
    load_key = f"load_{_safe_key(category)}"

    # If data already computed for this category, display immediately
    if key in st.session_state and st.session_state.get(key) is not None:
        format_display(st.session_state[key], category)
        return

    # When this function runs, the tab is active — compute now and cache result.
    with st.spinner("Fetching market data..."):
        st.session_state[key] = calculate_pegy(tuple(tickers))
    
    # Sorting controls: allow selecting column and order (restore previous behavior)
    df = st.session_state[key]
    cols = list(df.columns) if hasattr(df, 'columns') else []
    sort_key = f"sortcol_{_safe_key(category)}"
    sort_dir_key = f"sortdir_{_safe_key(category)}"

    options = ["PEGY-1Y (abs)"] + cols
    sel = st.selectbox("Sort by", options, index=0, key=sort_key)
    order = st.radio("Order", ("Ascending", "Descending"), index=0, horizontal=True, key=sort_dir_key)

    # Apply sorting
    try:
        if sel == "PEGY-1Y (abs)" and "PEGY-1Y" in df.columns:
            df_sorted = df.copy()
            df_sorted["_abs_pegy"] = df_sorted["PEGY-1Y"].abs()
            df_sorted = df_sorted.sort_values(by=["_abs_pegy"], ascending=(order == "Ascending"), na_position="last").drop(columns=["_abs_pegy"]).reset_index(drop=True)
        elif sel in df.columns:
            df_sorted = df.sort_values(by=[sel], ascending=(order == "Ascending"), na_position="last").reset_index(drop=True)
        else:
            df_sorted = df
    except Exception:
        df_sorted = df

    format_display(df_sorted, category)

# Parse tickers and show UI controls
# 0. Watchlist tickers (displayed by default)
watchlist_tickers = ["ONDS", "OSCR", "PLTR", "RDW", "AVGO", "COST", "INTC", "AMD", "WMT", "V", "DDOG", "SNOW", "COIN", "RDDT", "CRWV"]

# Pre-defined groups
mags_tickers = ["AAPL", "AMZN", "ASML", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "ORCL", "TSLA", "TSM"]
yolo_ai_enery_tickers = ["CCJ", "CEG", "OKLO"]
yolo_quantum_tickers = ["IONQ", "RGTI", "QBTS", "QUBT"]
yolo_robotics_tickers = ["SYM", "ISRG"]
yolo_space_tickers = ["ASTS", "LMT", "PL", "RKLB"]

# User defined tickers
user_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# Tabs: default/first tab is Watchlist; other lists to the right. Portfolio aggregates all lists
tab_labels = [
    "📋 Watchlist",
    "📝 User Defined",
    "⭐ Magnificent 7",
    "⚡ YOLO - AI Energy",
    "🧬 YOLO - Quantum Computing",
    "🤖 YOLO - Robotics",
    "🚀 YOLO - Space Technology",
    "📈 S&P 500 Constituents",
    "Portfolio",
]

tabs = st.tabs(tab_labels)

for label, tab in zip(tab_labels, tabs):
    with tab:
        if label == "📋 Watchlist":
            calculate_and_display_pegy(sorted(watchlist_tickers), label)
        elif label == "📝 User Defined":
            if user_tickers:
                calculate_and_display_pegy(sorted(user_tickers), label)
            else:
                st.info("No user-defined tickers provided. Enter symbols in the sidebar and rerun.")
        elif label == "⭐ Magnificent 7":
            calculate_and_display_pegy(mags_tickers, label)
        elif label == "⚡ YOLO - AI Energy":
            calculate_and_display_pegy(yolo_ai_enery_tickers, label)
        elif label == "🧬 YOLO - Quantum Computing":
            calculate_and_display_pegy(yolo_quantum_tickers, label)
        elif label == "🤖 YOLO - Robotics":
            calculate_and_display_pegy(yolo_robotics_tickers, label)
        elif label == "🚀 YOLO - Space Technology":
            calculate_and_display_pegy(yolo_space_tickers, label)
        elif label == "📈 S&P 500 Constituents":
            calculate_and_display_pegy(snp_tickers, label)
        elif label == "Portfolio":
            # Portfolio contains all groups except watchlist and S&P 500
            portfolio = []
            portfolio.extend(mags_tickers)
            portfolio.extend(yolo_ai_enery_tickers)
            portfolio.extend(yolo_quantum_tickers)
            portfolio.extend(yolo_robotics_tickers)
            portfolio.extend(yolo_space_tickers)
            # remove duplicates and any watchlist / snp members
            if portfolio:
                calculate_and_display_pegy(portfolio, label)
            else:
                st.info("Portfolio is empty (no tickers outside watchlist/S&P).")

# Add insights footer
add_insights()