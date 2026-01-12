import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- KONFIGURÁCIÓ ---
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"
try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
except:
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"

# Népszerű Ticker-ek listája az autocomplete-hez
POPULAR_TICKERS = [
    "NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "NFLX", # Részvények
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD" # Kripto
]

def get_finnhub_news(ticker):
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else []
    except: return []

st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["NVDA", "BTC-USD"]

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok Belépés")
    with st.form("login"):
        name = st.text_input("Válassz nevet")
        pw = st.text_input("KLUB JELSZÓ", type="password")
        tg_id = st.text_input("Telegram ID")
        if st.form_submit_button("Belépés"):
            if pw == KLUB_JELSZO and name and tg_id:
                st.session_state.logged_in, st.session_state.user_name, st.session_state.user_id = True, name, tg_id
                st.rerun()
            else: st.error("Hiba!")
else:
    # --- OLDALSÁV (Beállítások Modul) ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.divider()
        
        st.header("⚙️ Portfólió Beállítása")
        
        # AUTOCOMPLETE KERESŐ
        # Engedjük a listából választást vagy új beírását
        selected_ticker = st.selectbox(
            "Keress részvényt vagy kriptót:",
            options=[""] + sorted(list(set(POPULAR_TICKERS + st.session_state.watchlist))),
            format_func=lambda x: "Írj be egy kódot..." if x == "" else x,
            help="Válassz a listából vagy írj be egy újat!"
        )
        
        # Ha olyat ír be, ami nincs a listában
        manual_ticker = st.text_input("Vagy írd be kézzel (ha nincs a listában):").upper()
        ticker_to_add = manual_ticker if manual_ticker else selected_ticker

        if st.button("➕ Hozzáadás a figyelőhöz") and ticker_to_add:
            if ticker_to_add not in st.session_state.watchlist:
                st.session_state.watchlist.append(ticker_to_add)
                st.success(f"{ticker_to_add} hozzáadva!")
                st.rerun()
        
        st.divider()
        period_choice = st.radio("Változás idötartama:", ["Napi (1D)", "Heti (1W)", "Havi (1M)"])
        
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    # --- FŐOLDAL ---
    st.title("📊 Személyes Monitor")

    if st.session_state.watchlist:
        # Táblázat összeállítása (ugyanaz a logika, mint az előbb)
        quick_data = []
        period_map = {"Napi (1D)": "2d", "Heti (1W)": "10d", "Havi (1M)": "35d"}
        
        for t in st.session_state.watchlist:
            try:
                stock = yf.Ticker(t)
                hist = stock.history(period=period_map[period_choice])
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if period_choice == "Napi (1D)" else hist['Close'].iloc[0]
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    color = "🟢" if change_pct >= 0 else "🔴"
                    quick_data.append({"Ticker": t, "Ár (USD)": f"{current_price:.2f}", f"Változás ({period_choice})": f"{color} {change_pct:+.2f}%"})
            except: pass
        
        if quick_data:
            st.table(pd.DataFrame(quick_data))

    # --- RÉSZLETEK MODUL ---
    st.divider()
    st.subheader("🔍 Részletes elemzés")
    
    for t in st.session_state.watchlist:
        with st.expander(f"{t} - Grafikon és Hírek"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**{t} Riasztás beállítása**")
                target = st.number_input(f"Célár ({t}):", key=f"target_{t}")
                if st.button(f"🔔 Riasztás", key=f"btn_{t}"):
                    st.toast(f"Riasztás rögzítve: {t} @ {target}")
                
                st.line_chart(yf.Ticker(t).history(period="1mo")['Close'])
                
                if st.button(f"🗑️ Törlés: {t}", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()

            with col2:
                news = get_finnhub_news(t)
                if isinstance(news, list) and len(news) > 0:
                    for n in news[:3]:
                        st.markdown(f"**[{n.get('headline', '')}]({n.get('url', '#')})**")
                        st.caption(f"{n.get('source', '')}")
                        st.divider()