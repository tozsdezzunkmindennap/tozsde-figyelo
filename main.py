import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURÁCIÓ (A titkokat a Streamlit felületén add meg!) ---
ADMIN_CHAT_ID = "8385947337"
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
    # Itt olvassa a jóváhagyott ID-kat (pl. ["8385947337", "12345"])
    APPROVED_IDS = [str(i) for i in st.secrets["APPROVED_IDS"]]
except:
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"
    APPROVED_IDS = ["8385947337"]

# --- 2. SEGÉDFÜGGVÉNYEK ---
def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
    except: pass

def get_finnhub_news(ticker):
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. MEGJELENÉS ÉS OLDALSÁV ---
st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["NVDA", "BTC-USD"]

# --- 4. BELÉPÉSI FELÜLET ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok VIP Klub")
    tab1, tab2 = st.tabs(["🔑 Belépés", "📝 Tagság igénylése"])
    
    with tab1:
        with st.form("login"):
            l_id = st.text_input("Telegram ID-d")
            l_pw = st.text_input("Klub Jelszó", type="password")
            if st.form_submit_button("Belépés"):
                if l_pw == KLUB_JELSZO and str(l_id) in APPROVED_IDS:
                    st.session_state.logged_in = True
                    st.rerun()
                elif l_pw == KLUB_JELSZO:
                    st.warning("Várj a jóváhagyásra! (Az ID-d még nincs a Secrets listában)")
                else:
                    st.error("Hibás jelszó vagy ID!")

    with tab2:
        with st.form("registration"):
            r_name = st.text_input("Teljes neved")
            r_id = st.text_input("Telegram ID-d")
            if st.form_submit_button("Jelentkezés küldése"):
                if r_name and r_id:
                    msg = f"🔔 ÚJ JELENTKEZŐ!\nNév: {r_name}\nID: {r_id}\n\nAdd hozzá az ID-t a Streamlit Secrets-hez!"
                    send_telegram_msg(ADMIN_CHAT_ID, msg)
                    st.success("Igénylés elküldve! Az admin értesítést kapott.")

# --- 5. BELSŐ MONITOR ---
else:
    with st.sidebar:
        st.title("👤 VIP Tag")
        st.divider()
        
        st.header("📂 Figyelőlista")
        MARKET_DATA = {
            "🇺🇸 Tech": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META"],
            "₿ Kripto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"],
            "🇭🇺 Magyar": ["OTP.BU", "MOL.BU", "RICHT.BU", "4IG.BU"]
        }
        cat = st.selectbox("Válassz kategóriát:", list(MARKET_DATA.keys()))
        ticker = st.selectbox("Válassz papírt:", MARKET_DATA[cat])
        
        if st.button("➕ Hozzáadás"):
            if ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(ticker)
                st.rerun()
        
        st.divider()
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📊 Személyes Piaci Monitor")
    
    # Lista megjelenítése kártyákon
    for t in st.session_state.watchlist:
        with st.expander(f"🔍 {t} Információk", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**Árfolyam (30 nap)**")
                st.line_chart(yf.Ticker(t).history(period="1mo")['Close'])
                if st.button(f"🗑️ Eltávolítás: {t}", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()
            with col2:
                st.write("**Legfrissebb Hírek**")
                news_list = get_finnhub_news(t)
                if news_list:
                    for n in news_list[:3]:
                        st.markdown(f"**[{n.get('headline','')}]({n.get('url','#')})**")
                        st.caption(f"{n.get('source','')} | {datetime.fromtimestamp(n.get('datetime',0)).strftime('%Y-%m-%d')}")
                        st.divider()
                else:
                    st.info("Nincsenek elérhető hírek.")