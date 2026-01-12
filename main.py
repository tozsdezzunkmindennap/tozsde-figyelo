import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURÁCIÓ ---
ADMIN_CHAT_ID = "8385947337"
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

# A TE TÁBLÁZATOD FIX ADATAI
SHEET_ID = "1uEeTzFcyZyDFpNxzcxVa7tjQAraUUO-A510Z7yCpmm8"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Users"

try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
except:
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"

# --- 2. FUNKCIÓK ---

def get_users_direct():
    """Közvetlen CSV letöltés a Google Táblázatból"""
    try:
        # Tisztított beolvasás
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Adatbázis kapcsolódási hiba. Ellenőrizd a táblázat megosztását! Részletek: {e}")
        return pd.DataFrame(columns=["name", "telegram_id", "status"])

def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
        return True
    except:
        return False

def get_finnhub_news(ticker):
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []

# --- 3. STREAMLIT APP BEÁLLÍTÁSOK ---
st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["NVDA", "BTC-USD"]

# Felhasználók listájának frissítése
users_df = get_users_direct()

# --- 4. BELÉPÉS ÉS JELENTKEZÉS ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok VIP")
    t1, t2 = st.tabs(["🔑 Belépés", "📝 Jelentkezés"])
    
    with t1:
        with st.form("login_form"):
            l_id = st.text_input("Saját Telegram ID")
            l_pw = st.text_input("Jelszó", type="password")
            if st.form_submit_button("Belépés"):
                # ID és Státusz ellenőrzése a táblázatban
                is_approved = not users_df[(users_df['telegram_id'].astype(str) == str(l_id)) & 
                                           (users_df['status'].str.lower() == 'approved')].empty
                
                if l_pw == KLUB_JELSZO and (is_approved or str(l_id) == ADMIN_CHAT_ID):
                    st.session_state.logged_in = True
                    st.session_state.user_id = str(l_id)
                    st.rerun()
                elif l_pw == KLUB_JELSZO:
                    st.warning("A regisztrációd még jóváhagyásra vár!")
                else:
                    st.error("Hibás adatok!")

    with t2:
        with st.form("reg_form"):
            r_name = st.text_input("Teljes neved")
            r_id = st.text_input("Telegram ID-d")
            if st.form_submit_button("Jelentkezés küldése"):
                if r_name and r_id:
                    msg = f"🔔 ÚJ JELENTKEZŐ!\nNév: {r_name}\nID: {r_id}\n\nFrissítsd a táblázatot 'Approved'-ra a belépéshez!"
                    send_telegram_msg(ADMIN_CHAT_ID, msg)
                    st.success("Jelentkezés elküldve!")
                else:
                    st.error("Hiányzó adatok!")

# --- 5. BELSŐ FELÜLET ---
else:
    with st.sidebar:
        st.title(f"👤 VIP ID: {st.session_state.user_id}")
        
        # Csak neked: Admin nézet a táblázathoz
        if st.session_state.user_id == ADMIN_CHAT_ID:
            with st.expander("🛠️ Admin: Aktuális adatbázis"):
                st.dataframe(users_df)
                if st.button("🔄 Adatok frissítése"):
                    st.rerun()

        st.divider()
        st.header("📂 Portfólió")
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
        
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📊 VIP Élő Monitor")
    for t in st.session_state.watchlist:
        with st.expander(f"🔍 {t} Részletek", expanded=True):
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