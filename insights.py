import streamlit as st

def add_insights():
    # Insights
    st.subheader("🔍 Quick Interpretation")
    st.markdown("""
    - **PEGY < 1** → potentially undervalued vs growth + yield  
    - **PEGY ≈ 1–2** → fairly valued  
    - **PEGY > 3** → expensive relative to growth
    """)

    st.caption("Data source: Yahoo Finance (near-real-time)")