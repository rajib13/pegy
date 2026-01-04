import streamlit as st

def add_header():
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
    return tickers_input, refresh