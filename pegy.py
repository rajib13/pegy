from numpy import sort
import yfinance as yf
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PEGY Ratio Dashboard",
    layout="wide"
)

st.title("📊 PEGY Ratio Dashboard")
st.caption("PEGY = P/E ÷ (EPS Growth + Dividend Yield)")

# Sidebar
st.sidebar.header("Settings")
tickers_input = st.sidebar.text_area(
    "Enter stock tickers (comma separated)",
    value="MSFT"
)

refresh = st.sidebar.button("🔄 Refresh Data")

# Function to calculate PEGY
def calculate_pegy(tickers):
    data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract stock and S&P trend for 1Y
            analysis = stock.growth_estimates
            stock_trend = analysis.get("stockTrend")
            snp_trend= analysis.get("indexTrend")
            growth_1y = stock_trend.get("+1y", 0)
            snp_growth_1y = snp_trend.get("+1y", 0)

            forward_pe = info.get("forwardPE", 0)
            dividend = info.get("dividendYield", 0)

            # Convert decimals → %
            dividend_pct = dividend * 100 if dividend else 0
            growth_1y_pct = growth_1y * 100 if growth_1y else None
            snp_growth_1y_pct = snp_growth_1y * 100 if snp_growth_1y else None

            pegy_1y = (
                abs(forward_pe) / (growth_1y_pct + dividend)
                if forward_pe and growth_1y_pct
                else None
            )

            data.append({
                "Symbol": ticker,
                "Forward P/E": round(forward_pe, 2) if forward_pe else None,
                "Growth 1Y %": round(growth_1y_pct, 4) if growth_1y_pct else None,
                "Growth 1Y / S&P 500": round(growth_1y_pct / snp_growth_1y_pct, 4) if snp_growth_1y else None,
                "Dividend %": round(dividend_pct, 2) if dividend_pct else None,
                "PEGY-1Y": round(pegy_1y, 2) if pegy_1y else None,
            })

        except Exception as e:
            data.append({"Ticker": ticker, "Error": str(e)})

    return pd.DataFrame(data)

def calculate_and_display_pegy(tickers, category):
    # Load data
    with st.spinner("Fetching market data..."):
        df = calculate_pegy(tickers)

    # Format output
    numeric_cols = ["Forward P/E", "Growth 1Y %", "Growth 1Y / S&P 500", "Dividend %", "PEGY-1Y"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    # Prepare styled dataframe: round values and color `PEGY-1Y` by value.
    styled_df = df.round(2)
    if "PEGY-1Y" in styled_df.columns:
        def _hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        def _rgb_to_hex(rgb):
            return '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))

        def _lerp_color(a, b, t):
            ra, ga, ba = _hex_to_rgb(a)
            rb, gb, bb = _hex_to_rgb(b)
            return _rgb_to_hex((ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t))

        def _text_color_for_bg(hexcol):
            r, g, b = _hex_to_rgb(hexcol)
            # Perceived luminance
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            return 'color: black' if lum > 160 else 'color: white'

        # Define dark -> light for each region
        green_dark, green_light = '#0b6623', '#9ae6a4'
        amber_dark, amber_light = '#8a5a00', '#ffd27a'
        red_dark, red_light = '#7a1414', '#f4a6a6'

        def _color_pegy(val):
            if pd.isna(val):
                return ""
            try:
                v = float(val)
            except Exception:
                return ""

            # Region 1: 0 <= v < 1 (green gradient: darker near 0)
            if 0 <= v < 1:
                t = (v - 0) / 1.0
                bg = _lerp_color(green_dark, green_light, t)
                return f"background-color: {bg}; {_text_color_for_bg(bg)}"

            # Region 2: 1 <= v < 2 (amber gradient: darker near 1)
            if 1 <= v < 2:
                t = (v - 1) / 1.0
                bg = _lerp_color(amber_dark, amber_light, t)
                return f"background-color: {bg}; {_text_color_for_bg(bg)}"

            # Region 3: else (v < 0 or v >= 2). Use distance from boundary (0 for negatives, 2 for >2)
            if v < 0:
                dist = abs(v - 0)
                boundary = 0
            else:
                dist = abs(v - 2)
                boundary = 2
            # scale dist to [0,1] with a cap to avoid too-light colors; cap at 6 units
            cap = 6.0
            t = min(dist / cap, 1.0)
            bg = _lerp_color(red_dark, red_light, t)
            return f"background-color: {bg}; {_text_color_for_bg(bg)}"

        # Apply colors to the PEGY-1Y column
        styled_df = styled_df.style.map(_color_pegy, subset=["PEGY-1Y"])

        # Also color the `Symbol` cell based on the row's `PEGY-1Y` value
        if "Symbol" in df.columns and "PEGY-1Y" in df.columns:
            def _style_symbol_row(row):
                style = _color_pegy(row.get("PEGY-1Y"))
                return [style if col == "Symbol" else "" for col in row.index]

            styled_df = styled_df.apply(_style_symbol_row, axis=1)

    st.subheader(f"{category}")
    # Display styled dataframe if styling was applied; otherwise show rounded DataFrame
    if isinstance(styled_df, pd.io.formats.style.Styler):
        st.write(styled_df)
    else:
        st.dataframe(styled_df, use_container_width=True)

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

# Insights
st.subheader("🔍 Quick Interpretation")
st.markdown("""
- **PEGY < 1** → potentially undervalued vs growth + yield  
- **PEGY ≈ 1–2** → fairly valued  
- **PEGY > 3** → expensive relative to growth
""")

st.caption("Data source: Yahoo Finance (near-real-time)")