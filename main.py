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

def get_yahoo_suggestions(query):
    if not query or len(query) < 2: return []
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        return [f"{res['symbol']} ({res.get('shortname', 'Ismeretlen')})" for res in data.get('quotes', []) if 'symbol' in res]
    except: return []

def get_finnhub_news(ticker):
    """Hírek lekérése az elmúlt 7 napból"""
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        return []
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
            else: st.error("Hibás!")
else:
    # --- OLDALSÁV ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.divider()
        st.header("🔍 Yahoo Kereső")
        search_query = st.text_input("Kezdd el írni (pl. Apple):")
        suggestions = get_yahoo_suggestions(search_query)
        
        if suggestions:
            selected_full = st.selectbox("Találatok:", suggestions)
            if st.button("➕ Hozzáadás"):
                new_ticker = selected_full.split(" ")[0]
                if new_ticker not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_ticker)
                    st.rerun()
        
        st.divider()
        period = st.radio("Változás mutató:", ["1D", "1W", "1M"])
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    # --- FŐOLDAL ---
    st.title("📊 Portfólió Monitor")
    
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
    
    # --- RÉSZLETEK ÉS HÍREK ---
    st.subheader("📰 Legfrissebb hírek és elemzések")
    for t in st.session_state.watchlist:
        with st.expander(f"🔍 {t} részletes adatok és hírek"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write(f"**{t} Grafikon (30 nap)**")
                st.line_chart(yf.Ticker(t).history(period="1mo")['Close'])
                if st.button(f"🗑️ Törlés: {t}", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()
            
            with c2:
                st.write("**Finnhub Hírcsatorna**")
                news = get_finnhub_news(t)
                if isinstance(news, list) and len(news) > 0:
                    for n in news[:5]: # Most már újra az első 5 hírt mutatjuk
                        headline = n.get('headline', 'Nincs cím')
                        url = n.get('url', '#')
                        source = n.get('source', 'Ismeretlen')
                        summary = n.get('summary', '')
                        dt = datetime.fromtimestamp(n.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')
                        
                        st.markdown(f"**[{headline}]({url})**")
                        st.caption(f"📅 {dt} | Forrás: {source}")
                        if summary:
                            st.write(f"_{summary[:200]}_...")
                        st.divider()
                else:
                    st.info("Ehhez a részvényhez most nincsenek friss hírek.")