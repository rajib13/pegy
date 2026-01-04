from numpy import sort
import streamlit as st
from header import add_header 
from insights import add_insights
from calculate_pegy import calculate_pegy
from display import format_display

tickers_input, refresh = add_header()

def calculate_and_display_pegy(tickers, category):
    # Load data
    with st.spinner("Fetching market data..."):
        df = calculate_pegy(tickers)
    
    # Format and display
    format_display(df, category)


# Parse tickers
# 0. Watchlist tickers
watchlist_tickers = ["PLTR", "RDW", "AVGO", "COST", "INTC", "AMD", "WMT", "V", "DDOG", "SNOW", "COIN", "RDDT", "CRWV"]
calculate_and_display_pegy(sorted(watchlist_tickers), "📋 Watchlist")

# 1. User Defined Tickers
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
calculate_and_display_pegy(sorted(tickers), "📝 User Defined")

# 2. Magnificent 7 Tickers
mags_tickers = ["AAPL", "AMZN", "ASML", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "ORCL", "TSLA", "TSM"]
calculate_and_display_pegy(mags_tickers, "⭐ Magnificent 7")

# 3. YOLO - AI Enerry Tickers
yolo_ai_enery_tickers = ["CCO", "CEG", "OKLO"]
calculate_and_display_pegy(yolo_ai_enery_tickers, "⚡ YOLO - AI Energy")

# 4. YOLO - Quantum Computing Tickers
yolo_quantum_tickers = ["IONQ", "RGTI", "QBTS", "QUBT"]
calculate_and_display_pegy(yolo_quantum_tickers, "🧬 YOLO - Quantum Computing")

# 5. YOLO - Robotics Tickers
yolo_robotics_tickers = ["SYM", "ISRG"]
calculate_and_display_pegy(yolo_robotics_tickers, "🤖 YOLO - Robotics")

# 6. YOLO - Space Technology Tickers
yolo_space_tickers = ["ASTS", "LMT", "PL", "RKLB"]
calculate_and_display_pegy(yolo_space_tickers, "🚀 YOLO - Space Technology")

# Add insights footer
add_insights()