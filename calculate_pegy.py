import yfinance as yf
import pandas as pd
import streamlit as st

# optionally use AI summary generation
try:
    from ai import generate_company_summary, get_cached_summary
except Exception:
    generate_company_summary = None
    get_cached_summary = None


@st.cache_data(ttl=60 * 30)
def calculate_pegy(tickers, generate_summaries: bool = False):
    """Calculate PEGY table for given tickers.

    If `generate_summaries` is True and the `ai` package is available, this will
    attempt to populate a `Summary` column using cached summaries or by calling
    `generate_company_summary` (may be slow / costly). Default is False.
    """
    data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract stock and S&P trend for 1Y
            analysis = stock.growth_estimates
            stock_trend = analysis.get("stockTrend")
            snp_trend = analysis.get("indexTrend")
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

            # Symbol formatted as 'TICKER - Company Name' (compat with UI expectations)
            symbol_display = ticker + " - " + (info.get("shortName") or "")
            
            # Populate summary from cache if available (non-blocking)
            summary = ""
            if get_cached_summary is not None:
                try:
                    cached = get_cached_summary(ticker)
                    if cached:
                        summary = cached
                    elif generate_summaries and generate_company_summary is not None:
                        # generate and cache via ai client
                        try:
                            summary = generate_company_summary(ticker, info.get("shortName"))
                        except Exception:
                            summary = None
                except Exception:
                    # do not fail the whole run if AI fails
                    summary = None

            row = {
                "Symbol": symbol_display,
                "Summary": summary if summary else None,
                "Forward P/E": round(forward_pe, 2) if forward_pe else None,
                "Growth 1Y %": round(growth_1y_pct, 4) if growth_1y_pct else None,
                "Growth 1Y / S&P 500": round(growth_1y_pct / snp_growth_1y_pct, 4) if snp_growth_1y else None,
                "Dividend %": round(dividend_pct, 2) if dividend_pct else None,
                "PEGY-1Y": round(pegy_1y, 2) if pegy_1y else None,
            }

            data.append(row)

        except Exception as e:
            data.append({"Ticker": ticker, "Error": str(e)})

    return pd.DataFrame(data)
