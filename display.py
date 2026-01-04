import streamlit as st
import pandas as pd
import re
from ai import generate_company_summary, get_cached_summary


def format_display(df, category):
    # Ensure numeric types
    numeric_cols = ["Forward P/E", "Growth 1Y %", "Growth 1Y / S&P 500", "Dividend %", "PEGY-1Y"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Round numeric display values to 2 decimals
    disp = df.copy()
    for col in numeric_cols:
        if col in disp.columns:
            disp[col] = disp[col].round(2)

    # Color helpers (same as before)
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
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return 'black' if lum > 160 else 'white'

    green_dark, green_light = '#0b6623', '#9ae6a4'
    amber_dark, amber_light = '#8a5a00', '#ffd27a'
    red_dark, red_light = '#7a1414', '#f4a6a6'

    def _color_pegy_css(val):
        if pd.isna(val):
            return ""
        try:
            v = float(val)
        except Exception:
            return ""

        if 0 <= v < 1:
            t = (v - 0) / 1.0
            bg = _lerp_color(green_dark, green_light, t)
            text = _text_color_for_bg(bg)
            return f"background-color: {bg}; color: {text};"
        if 1 <= v < 2:
            t = (v - 1) / 1.0
            bg = _lerp_color(amber_light, amber_dark, t)
            text = _text_color_for_bg(bg)
            return f"background-color: {bg}; color: {text};"
        if v < 0:
            dist = abs(v - 0)
            cap = 6.0
            t = min(dist / cap, 1.0)
            bg = _lerp_color(red_dark, red_light, t)
            text = _text_color_for_bg(bg)
            return f"background-color: {bg}; color: {text};"
        dist = v - 2
        cap = 6.0
        t = min(dist / cap, 1.0)
        bg = _lerp_color(red_light, red_dark, t)
        text = _text_color_for_bg(bg)
        return f"background-color: {bg}; color: {text};"

    # Columns to display and column widths      
    display_cols = [
        "", # for serial number
        "Symbol",
        "Summary",
        "Forward P/E",
        "Growth 1Y %",
        "Growth 1Y / S&P 500",
        "Dividend %",
        "PEGY-1Y",
    ]
    widths = [0.5, 1.2, 2.0, 1, 1, 1, 1, 1]

    st.subheader(f"{category}")

    # Header
    header_cols = st.columns(widths)
    for i, col_name in enumerate(display_cols):
        header_cols[i].markdown(f"**{col_name}**")

    # Rows
    for serial, (idx, row) in enumerate(disp.iterrows()):
        cols = st.columns(widths)
        # Serial number column (0-based) — color it using the same PEGY-1Y coloring
        pegy_val = row.get("PEGY-1Y") if "PEGY-1Y" in disp.columns else None
        if pegy_val is not None and not pd.isna(pegy_val):
            try:
                style = _color_pegy_css(pegy_val)
                html_serial = f"<div style=\"{style} padding:6px; border-radius:4px; text-align:center\">{serial}</div>"
                cols[0].markdown(html_serial, unsafe_allow_html=True)
            except Exception:
                cols[0].markdown(f"**{serial}**")
        else:
            cols[0].markdown(f"**{serial}**")

        # Symbol (prefer 'Symbol' column, fall back to index)
        if "Symbol" in disp.columns:
            sym = row.get("Symbol", "")
        else:
            sym = idx

        safe_sym_html = str(sym).replace("\n", "<br />")
        cols[1].markdown(f"{safe_sym_html}", unsafe_allow_html=True)

        # Other columns (start at index 2 since 0=No., 1=Symbol)
        for i, col_name in enumerate(display_cols[2:], start=2):
            val = row.get(col_name, "")
            if col_name == "Summary":
                # Summary may be a dict (from AI) or a string; if missing, show checkbox in this cell
                if isinstance(val, dict):
                    for k, v in val.items():
                        cols[i].markdown(f"- **{k}**: {v}")
                elif pd.isna(val) or val is None or str(val).strip() == "":
                    # show checkbox to generate in-place
                    # Determine ticker-only identifier for label/key/cache
                    if "Ticker" in disp.columns and pd.notna(row.get("Ticker")):
                        ticker_only = str(row.get("Ticker")).strip()
                    else:
                        # fallback: try to parse ticker from Symbol like 'TICKER - Company Name'
                        sym_full = row.get("Symbol") if "Symbol" in disp.columns else ""
                        if isinstance(sym_full, str) and " - " in sym_full:
                            ticker_only = sym_full.split(" - ", 1)[0].strip()
                        elif sym_full:
                            ticker_only = str(sym_full).split()[0]
                        else:
                            ticker_only = f"row{idx}"

                    ai_symbol = ticker_only
                    safe_sym = re.sub(r"[^0-9A-Za-z_-]", "", ticker_only.replace(' ', '_'))
                    safe_cat = re.sub(r"[^0-9A-Za-z_-]", "", category.replace(' ', '_'))
                    key = f"summary_{safe_cat}_{safe_sym}_{idx}"
                    label = f"Generate AI summary for {ticker_only}"
                    checked = cols[i].checkbox(label, key=key)
                    if checked:
                        # Check cache first
                        cached = get_cached_summary(ai_symbol)
                        if cached:
                            for k, v in cached.items():
                                cols[i].markdown(f"- **{k}**: {v}")
                        else:
                            try:
                                with st.spinner("Generating summary..."):
                                    doc = generate_company_summary(ai_symbol)
                                for k, v in doc.items():
                                    cols[i].markdown(f"- **{k}**: {v}")
                            except Exception as e:
                                cols[i].error(str(e))
                else:
                    cols[i].write(val)
                continue

            if pd.isna(val):
                cols[i].write("")
            else:
                # Right align numeric values
                if isinstance(val, (int, float)):
                    if col_name == "PEGY-1Y":
                        style = _color_pegy_css(val)
                        html = f"<div style=\"{style} padding:6px; border-radius:4px; text-align:right\">{val:.2f}</div>"
                        cols[i].markdown(html, unsafe_allow_html=True)
                    else:
                        cols[i].write(f"{val:.2f}")
                else:
                    cols[i].write(val)