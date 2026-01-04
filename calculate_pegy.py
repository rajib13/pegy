import yfinance as yf
import pandas as pd

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
