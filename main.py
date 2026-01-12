import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURÁCIÓ ---
ADMIN_CHAT_ID = "8385947337" 
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

# A TE TÁBLÁZATOD LINKJE KÖZVETLENÜL BEÉPÍTVE
SHEET_URL = "https://docs.google.com/spreadsheets/d/1uEeTzFcyZyDFpNxzcxVa7tjQAraUUO-A510Z7yCpmm8/edit?usp=sharing"

try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
    APP_URL = st.secrets.get("APP_URL", "https://tozsdekiralyok.streamlit.app")
except:
    # Tartalék értékek, ha a Secrets nincs beállítva
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"
    APP_URL = "https://tozsdekiralyok.streamlit.app"

# Adatbázis kapcsolat inicializálása a beépített linkkel
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNKCIÓK ---

def get_users():
    """Lekéri a felhasználókat a megadott Google Táblázatból"""
    try:
        # Itt kényszerítjük a megadott link használatát
        return conn.read(spreadsheet=SHEET_URL, worksheet="Users", ttl=0)
    except Exception as e:
        st.error(f"Táblázat hiba: {e}")
        return pd.DataFrame(columns=["name", "telegram_id", "status"])

def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
        return True
    except: return False

def get_finnhub_news(ticker):
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. PIACI ADATOK ---
MARKET_DATA = {
    "🇺🇸 Tech Óriások": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "NFLX"],
    "₿ Kriptovaluták": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "🇭🇺 Magyar Piac": ["OTP.BU", "MOL.BU", "RICHT.BU", "4IG.BU", "MTEL.BU"]
}

# --- 4. APP LOGIKA ---
st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Felhasználók betöltése a táblázatból
users_df = get_users()

# --- 5. LOGIN & AUTOMATA REGISZTRÁCIÓ ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok VIP Klub")
    tab1, tab2 = st.tabs(["🔑 Belépés", "📝 Tagság igénylése"])
    
    with tab1:
        with st.form("login"):
            l_name = st.text_input("Név")
            l_id = st.text_input("Telegram ID")
            l_pw = st.text_input("Jelszó", type="password")
            if st.form_submit_button("Belépés"):
                # Ellenőrzés: admin vagy jóváhagyott tag?
                user_check = users_df[(users_df['telegram_id'].astype(str) == str(l_id)) & (users_df['status'] == 'Approved')]
                if l_pw == KLUB_JELSZO and (not user_check.empty or str(l_id) == ADMIN_CHAT_ID):
                    st.session_state.logged_in = True
                    st.session_state.user_name = l_name
                    st.session_state.user_id = str(l_id)
                    st.rerun()
                elif l_pw == KLUB_JELSZO:
                    st.warning("A regisztrációd még jóváhagyásra vár!")
                else: st.error("Hibás jelszó vagy ID!")

    with tab2:
        st.info("Mielőtt jelentkezel, indítsd el a botot Telegramon!")
        with st.form("reg"):
            r_name = st.text_input("Teljes neved")
            r_id = st.text_input("Telegram ID-d")
            if st.form_submit_button("Jelentkezés elküldése"):
                if r_name and r_id:
                    # Mentés a táblázatba (Pending státusszal)
                    new_member = pd.DataFrame([{"name": r_name, "telegram_id": str(r_id), "status": "Pending"}])
                    updated_df = pd.concat([users_df, new_member], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Users", data=updated_df)
                    
                    send_telegram_msg(ADMIN_CHAT_ID, f"🔔 ÚJ JELENTKEZŐ: {r_name}\nID: {r_id}\nJóváhagyhatod az appban!")
                    st.success("Sikeres jelentkezés! Az admin hamarosan értesít.")
                else: st.error("Töltsd ki az adatokat!")

# --- 6. BELSŐ FELÜLET & ADMIN PANEL ---
else:
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        
        # ADMIN PANEL (Csak neked)
        if st.session_state.user_id == ADMIN_CHAT_ID:
            st.divider()
            st.subheader("🛠️ Admin Jóváhagyás")
            pending_list = users_df[users_df['status'] == 'Pending']
            if not pending_list.empty:
                to_approve = st.selectbox("Várakozók:", pending_list['name'].tolist())
                if st.button("✅ Jóváhagyás"):
                    # Frissítés a táblázatban
                    users_df.loc[users_df['name'] == to_approve, 'status'] = 'Approved'
                    conn.update(spreadsheet=SHEET_URL, worksheet="Users", data=users_df)
                    
                    # Automata üzenet küldése
                    target_id = pending_list[pending_list['name'] == to_approve]['telegram_id'].values[0]
                    welcome = f"🎉 Szia {to_approve}!\n\nJóváhagytunk! ✅\n🔑 Jelszó: {KLUB_JELSZO}\n🌐 URL: {APP_URL}"
                    send_telegram_msg(target_id, welcome)
                    st.success(f"{to_approve} aktiválva!")
                    st.rerun()
            else:
                st.write("Nincs új jelentkező.")

        st.divider()
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    # --- MONITOR RÉSZ ---
    st.title("📊 VIP Portfólió Monitor")
    if 'watchlist' not in st.session_state: st.session_state.watchlist = ["NVDA", "BTC-USD"]
    
    # ... (A korábbi piaci adatok és hírek megjelenítése változatlanul folytatódik idelent)