import streamlit as st
import yfinance as yf

st.title("📈 Haveri Tőzsde Monitor")
user = st.sidebar.selectbox("Ki vagy?", ["Peti", "Gábor", "Laci", "Vendég"])
ticker = st.text_input("Részvény kód (pl. NVDA):", "NVDA").upper()

if ticker:
    stock = yf.Ticker(ticker)
    price = stock.fast_info['last_price']
    st.metric(label=f"{ticker} Árfolyam", value=f"{price:.2f} USD")
    st.line_chart(stock.history(period="7d")['Close'])
