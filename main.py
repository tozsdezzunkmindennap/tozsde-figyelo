import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURÁCIÓ ---
ADMIN_CHAT_ID = "8385947337"
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

# Adatok biztonságos betöltése
try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
    # Itt tároljuk a jóváhagyott ID-kat a Streamlit felületén
    APPROVED_IDS = [str(i) for i in st.secrets["APPROVED_IDS"]]
except Exception:
    # Tartalék adatok, ha még nem állítottad be a Secrets-et
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"
    APPROVED_IDS = ["8385947337"] 

# --- 2. SEGÉDFÜGGVÉNYEK ---
def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
    except:
        pass

def get_finnhub_news(ticker):
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []

# --- 3. MEGJELENÉS ---
st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["NVDA", "BTC-USD"]

# --- 4. LOGIN ÉS REGISZTRÁCIÓ ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok VIP Klub")
    tab1, tab2 = st.tabs(["🔑 Belépés", "📝 Jelentkezés"])
    
    with tab1:
        with st.form("login_form"):
            l_id = st.text_input("Saját Telegram ID")
            l_pw = st.text_input("Klub Jelszó", type="password")
            if st.form_submit_button("Belépés"):
                if l_pw == KLUB_JELSZO and str(l_id) in APPROVED_IDS:
                    st.session_state.logged_in = True
                    st.session_state.user_id = str(l_id)
                    st.rerun()
                else:
                    st.error("Nincs jogosultságod! Ha most jelentkeztél, várj az admin jóváhagyására.")

    with tab2:
        with st.form("reg_form"):
            r_name = st.text_input("Neved")
            r_id = st.text_input("Telegram ID-d")
            if st.form_submit_button("Jelentkezés beküldése"):
                if r_name and r_id:
                    msg = f"🔔 ÚJ JELENTKEZŐ!\nNév: {r_name}\nID: {r_id}\n\nAdd hozzá az ID-t a Streamlit Secrets-hez!"
                    send_telegram_msg(ADMIN_CHAT_ID, msg)
                    st.success("Jelentkezés elküldve! Az admin hamarosan jóváhagy.")

# --- 5. BELSŐ MONITOR ---
else:
    with st.sidebar:
        st.title("👤 VIP Tag")
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.divider()
        st.header("📂 Figyelőlista")
        MARKET_DATA = {
            "🇺🇸 Tech": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META"],
            "₿ Kripto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"],
            "🇭🇺 Magyar": ["OTP.BU", "MOL.BU", "RICHT.BU", "4IG.BU"]
        }
        cat = st.selectbox("Kategória:", list(MARKET_DATA.keys()))
        ticker = st.selectbox("Papír:", MARKET_DATA[cat])
        if st.button("➕ Hozzáadás"):
            if ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(ticker)
                st.rerun()

    st.title("📊 VIP Élő Monitor")
    for t in st.session_state.watchlist:
        with st.expander(f"🔍 {t} Információk", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.line_chart(yf.Ticker(t).history(period="1mo")['Close'])
                if st.button(f"🗑️ Törlés: {t}", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()
            with col2:
                st.write("**Hírek:**")
                news = get_finnhub_news(t)
                for n in news[:2]:
                    st.markdown(f"* **[{n.get('headline','')}]({n.get('url','#')})**")