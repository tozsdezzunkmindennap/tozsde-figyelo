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

MARKET_DATA = {
    "🇺🇸 Tech Óriások": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "NFLX", "AMD", "PLTR"],
    "₿ Kriptovaluták": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "🇭🇺 Magyar Részvények": ["OTP.BU", "MOL.BU", "RICHT.BU", "4IG.BU", "MTEL.BU"],
    "🏎️ Autóipar & EV": ["RIVN", "LCID", "NIO", "F", "GM", "BYDDF"],
    "🏦 Bank & Pénzügy": ["JPM", "BAC", "V", "MA", "PYPL", "COIN"]
}

def get_finnhub_news(ticker):
    """Hírek lekérése csak akkor, ha szükség van rá"""
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            return "LIMIT" # Túl sok kérés hiba
        return []
    except:
        return []

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
            else: st.error("Hibás!")
else:
    # --- OLDALSÁV ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.divider()
        st.header("📂 Böngészés")
        cat = st.selectbox("Válassz kategóriát:", list(MARKET_DATA.keys()))
        selected_ticker = st.selectbox("Választható:", MARKET_DATA[cat])
        
        if st.button("➕ Hozzáadás"):
            if selected_ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(selected_ticker)
                st.rerun()

        st.divider()
        period = st.radio("Változás mutató:", ["1D", "1W", "1M"])
        
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    # --- FŐOLDAL ---
    st.title("📊 Személyes Monitor")
    
    # Gyors árak táblázat
    if st.session_state.watchlist:
        p_map = {"1D": "2d", "1W": "10d", "1M": "35d"}
        quick_list = []
        for t in st.session_state.watchlist:
            try:
                s = yf.Ticker(t)
                h = s.history(period=p_map[period])
                if not h.empty:
                    curr = h['Close'].iloc[-1]
                    prev = h['Close'].iloc[-2] if period == "1D" else h['Close'].iloc[0]
                    diff = ((curr - prev) / prev) * 100
                    quick_list.append({"Ticker": t, "Ár": f"{curr:.2f}", f"Változás ({period})": f"{'🟢' if diff >= 0 else '🔴'} {diff:+.2f}%"})
            except: pass
        st.table(pd.DataFrame(quick_list))

    st.divider()
    
    # --- RÉSZLETEK (Lusta betöltésű hírekkel) ---
    for t in st.session_state.watchlist:
        # Minden részvény egy külön lenyíló ablak
        with st.expander(f"🔍 {t} részletek és hírek"):
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.write(f"**{t} Grafikon**")
                # Csak akkor kér le adatot, ha az expander nyitva van
                st.line_chart(yf.Ticker(t).history(period="1mo")['Close'])
                if st.button(f"🗑️ Törlés: {t}", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()
            
            with c2:
                st.write("**Legfrissebb hírek**")
                # Hírek lekérése csak MOST történik meg
                news = get_finnhub_news(t)
                
                if news == "LIMIT":
                    st.warning("⚠️ Túl sok kérés! Várj egy percet a hírek frissítéséhez.")
                elif isinstance(news, list) and len(news) > 0:
                    for n in news[:3]:
                        st.markdown(f"**[{n.get('headline', '')}]({n.get('url', '#')})**")
                        st.caption(f"{n.get('source', 'Ismeretlen')} | {datetime.fromtimestamp(n.get('datetime', 0)).strftime('%Y-%m-%d')}")
                        st.divider()
                else:
                    st.info("Ehhez a tickerhez jelenleg nincsenek friss hírek.")