# -*- coding: utf-8 -*-
"""
Personal Stock Suggestion Dashboard (Streamlit)
- Scans Nifty 100 for long-term ideas near 52-week low
- Scans Nifty 50 for simple intraday breakout conditions

Save this file as `my_dashboard.py` and run:
    streamlit run my_dashboard.py

Requires: streamlit, pandas, yfinance
Install:  pip3 install streamlit pandas yfinance
"""

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="Stock Suggestion Dashboard", layout="wide")

# --- Stock Lists (NSE Tickers) ---
NIFTY_50_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LICI.NS",
    "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "KOTAKBANK.NS", "LT.NS",
    "SUNPHARMA.NS", "AXISBANK.NS", "NTPC.NS", "ONGC.NS", "ADANIENT.NS",
    "TATAMOTORS.NS", "ASIANPAINT.NS", "WIPRO.NS", "DMART.NS",
    "ULTRACEMCO.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "ADANIPORTS.NS",
    "POWERGRID.NS", "NESTLEIND.NS", "GRASIM.NS", "SBILIFE.NS",
    "M&M.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "HDFCLIFE.NS",
    "INDUSINDBK.NS", "BRITANNIA.NS", "CIPLA.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "HINDALCO.NS", "HEROMOTOCO.NS", "BPCL.NS",
    "DIVISLAB.NS", "TECHM.NS", "APOLLOHOSP.NS", "TITAN.NS",
    "UPL.NS", "SHREECEM.NS"
]

NIFTY_100_STOCKS = NIFTY_50_STOCKS + [
    "ADANIGREEN.NS", "BAJAJ-AUTO.NS", "CHOLAFIN.NS", "GAIL.NS",
    "GODREJCP.NS", "HAVELLS.NS", "ICICIPRULI.NS", "IOC.NS",
    "PIDILITIND.NS", "SIEMENS.NS", "TATACONSUM.NS", "TVSMOTOR.NS",
    "VEDL.NS", "ZEEL.NS", "AMBUJACEM.NS", "BEL.NS", "BOSCHLTD.NS",
    "DLF.NS", "ICICIGI.NS", "INDIGO.NS", "MARICO.NS", "PGHH.NS",
    "PNB.NS", "SAIL.NS", "SRF.NS", "ZOMATO.NS", "BANKBARODA.NS",
    "BERGEPAINT.NS", "CANBK.NS", "DABUR.NS", "HAL.NS",
    "IDFCFIRSTB.NS", "INDUSTOWER.NS", "JINDALSTEL.NS", "LTIM.NS",
    "MOTHERSON.NS", "PETRONET.NS", "PIIND.NS", "SHRIRAMFIN.NS",
    "TATAPOWER.NS", "TORNTPOWER.NS", "TRENT.NS", "AUROPHARMA.NS",
    "COLPAL.NS", "HDFCAMC.NS", "HINDPETRO.NS", "IRCTC.NS"
]

# --- Helper: Streamlit progress safe update ---
def _update_progress(bar, i, total):
    try:
        bar.progress(min(1.0, (i + 1) / float(total)))
    except Exception:
        pass

# --- Functions for Analysis ---

def find_long_term_suggestions() -> pd.DataFrame:
    """
    Scan NSE 100 stocks to find those trading within 5% of their 52-week low.
    Returns a DataFrame with Stock, CMP, 52Wk Low/High, Upside Potential.
    """
    suggestions = []
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    for i, ticker in enumerate(NIFTY_100_STOCKS):
        try:
            status_text.text(f"Analyzing {ticker} ({i + 1}/{len(NIFTY_100_STOCKS)})…")
            stock_data = yf.download(ticker, period="1y", progress=False, auto_adjust=False)

            if not stock_data.empty:
                fifty_two_week_low = float(stock_data['Low'].min())
                fifty_two_week_high = float(stock_data['High'].max())
                current_price = float(stock_data['Close'].iloc[-1])

                # Within 5% of 52-week low
                if current_price <= (fifty_two_week_low * 1.05):
                    suggestions.append({
                        "Stock": ticker,
                        "CMP": f"₹{current_price:.2f}",
                        "52Wk Low": f"₹{fifty_two_week_low:.2f}",
                        "52Wk High": f"₹{fifty_two_week_high:.2f}",
                        "Upside Potential": f"{((fifty_two_week_high - current_price) / current_price) * 100:.2f}%",
                    })
        except Exception as e:
            st.warning(f"Could not analyze {ticker}. Error: {e}")
        finally:
            _update_progress(progress_bar, i, len(NIFTY_100_STOCKS))

    status_text.text("Analysis Complete!")
    return pd.DataFrame(suggestions)


def find_intraday_opportunities() -> pd.DataFrame:
    """
    Scan Nifty 50 stocks for potential intraday breakout opportunities.
    Strategy (very simple): price positive on the day, near day high, volume spike.
    """
    suggestions = []
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    data = yf.download(tickers=NIFTY_50_STOCKS, period="2d", interval="5m", progress=False)

    for i, ticker in enumerate(NIFTY_50_STOCKS):
        try:
            status_text.text(f"Analyzing {ticker} ({i + 1}/{len(NIFTY_50_STOCKS)})…")

            ticker_frame = data.loc[:, (slice(None), ticker)]
            ticker_frame.columns = ticker_frame.columns.droplevel(1)

            if not ticker_frame.empty:
                today = datetime.today().date()
                today_data = ticker_frame[ticker_frame.index.date == today]

                if not today_data.empty:
                    last_price = float(today_data['Close'].iloc[-1])
                    day_high = float(today_data['High'].max())
                    day_open = float(today_data['Open'].iloc[0])

                    if last_price > day_open and last_price >= (day_high * 0.995):
                        if 'Volume' in today_data.columns:
                            recent_vol = today_data['Volume'].iloc[-10:-1]
                            if not recent_vol.empty:
                                avg_volume = float(recent_vol.mean())
                                last_volume = float(today_data['Volume'].iloc[-1])
                            else:
                                avg_volume = 0
                                last_volume = 0
                        else:
                            avg_volume = 0
                            last_volume = 0

                        if avg_volume == 0 or last_volume > avg_volume * 1.5:
                            entry_price = day_high + 0.05
                            stop_loss = day_open
                            risk = entry_price - stop_loss
                            target = entry_price + (risk * 1.5)

                            if risk > 0:
                                suggestions.append({
                                    "Stock": ticker,
                                    "CMP": f"₹{last_price:.2f}",
                                    "Condition": "Near Day High + Volume Spike",
                                    "Entry >": f"₹{entry_price:.2f}",
                                    "Target": f"₹{target:.2f}",
                                    "Stop Loss": f"₹{stop_loss:.2f}",
                                })
        except Exception:
            pass
        finally:
            _update_progress(progress_bar, i, len(NIFTY_50_STOCKS))

    status_text.text("Analysis Complete!")
    return pd.DataFrame(suggestions)


# --- Dashboard UI ---
st.title("📈 Personal Stock Suggestion Dashboard")
st.caption(
    f"Last Updated: {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p IST')}"
)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.header("🧭 Long-Term Strategy")
    st.info("Finds (Nifty 100) stocks trading within 5% of their 52-week low.")
    if st.button("Find Long-Term Investments"):
        with st.spinner("Analyzing NSE 100 stocks… This might take a minute."):
            long_term_results = find_long_term_suggestions()
        if not long_term_results.empty:
            st.success(f"Found {len(long_term_results)} potential long-term investment(s)!")
            st.dataframe(long_term_results, use_container_width=True)
        else:
            st.warning("No stocks currently meet the long-term investment criteria.")

with col2:
    st.header("⚡ Intraday Strategy")
    st.info("Scans high-liquidity (Nifty 50) stocks for potential intraday breakout opportunities.")
    if st.button("Find Intraday Opportunities"):
        with st.spinner("Analyzing Nifty 50 for intraday action…"):
            intraday_results = find_intraday_opportunities()
        if not intraday_results.empty:
            st.success(f"Found {len(intraday_results)} potential intraday opportunit(y/ies)!")
            st.dataframe(intraday_results, use_container_width=True)
        else:
            st.warning("No stocks currently meet the intraday breakout criteria.")

st.markdown("---")
st.warning(
    """
**Disclaimer:** This is an automated tool for educational purposes only and not financial advice.
Market data is provided by Yahoo Finance and may have delays. Always conduct your own research and
consult with a qualified financial advisor before making any investment decisions.
"""
)
