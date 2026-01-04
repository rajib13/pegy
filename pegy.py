from numpy import sort
import streamlit as st
from header import add_header
from insights import add_insights
from calculate_pegy import calculate_pegy
from display import format_display
from tickers.snp import symbols as snp_tickers

# AI summary generators
from ai import generate_company_summary, get_cached_summary

tickers_input, refresh = add_header()

def calculate_and_display_pegy(tickers, category):
    # Load data
    with st.spinner("Fetching market data..."):
        df = calculate_pegy(tickers)
    
    # Format and display
    format_display(df, category)


# Parse tickers and show UI controls
# 0. Watchlist tickers (displayed by default)
watchlist_tickers = ["PLTR", "RDW", "AVGO", "COST", "INTC", "AMD", "WMT", "V", "DDOG", "SNOW", "COIN", "RDDT", "CRWV"]

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