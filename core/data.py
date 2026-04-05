import streamlit as st
import yfinance as yf


@st.cache_data(show_spinner=False)
def load_prices(ticker, start="2020-01-01", end="2024-01-01"):
    df = yf.download(ticker, start=start, end=end, progress=False)
    return df["Close"].squeeze()

