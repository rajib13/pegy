import streamlit as st
import pandas as pd


def format_display(df, category):
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
