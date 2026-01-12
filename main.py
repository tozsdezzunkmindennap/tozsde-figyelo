import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURÁCIÓ ---
ADMIN_CHAT_ID = "8385947337" 
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

# Adatbázis kapcsolat (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
    APP_URL = st.secrets.get("APP_URL", "Kérd az admintól!")
except:
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"
    APP_URL = "https://your-app.streamlit.app"

# --- 2. FUNKCIÓK ---

def get_users():
    """Lekéri a felhasználókat a táblázatból"""
    try:
        return conn.read(worksheet="Users", ttl=0)
    except:
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
    "🇺🇸 Tech": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN"],
    "₿ Kripto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"],
    "🇭🇺 Magyar": ["OTP.BU", "MOL.BU", "RICHT.BU"]
}

# --- 4. APP LOGIKA ---
st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

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
                # Ellenőrzés a Google Táblázatban
                user_check = users_df[(users_df['telegram_id'] == str(l_id)) & (users_df['status'] == 'Approved')]
                if l_pw == KLUB_JELSZO and (not user_check.empty or str(l_id) == ADMIN_CHAT_ID):
                    st.session_state.logged_in = True
                    st.session_state.user_name = l_name
                    st.session_state.user_id = str(l_id)
                    st.rerun()
                elif l_pw == KLUB_JELSZO:
                    st.warning("Várj a jóváhagyásra!")
                else: st.error("Hibás adatok!")

    with tab2:
        with st.form("reg"):
            r_name = st.text_input("Név")
            r_id = st.text_input("Telegram ID")
            if st.form_submit_button("Jelentkezés"):
                if r_name and r_id:
                    # Mentés a táblázatba (Pending státusszal)
                    new_data = pd.DataFrame([{"name": r_name, "telegram_id": str(r_id), "status": "Pending"}])
                    updated_df = pd.concat([users_df, new_data], ignore_index=True)
                    conn.update(worksheet="Users", data=updated_df)
                    send_telegram_msg(ADMIN_CHAT_ID, f"🔔 ÚJ TAG: {r_name}\nID: {r_id}\nJóváhagyhatod az appban!")
                    st.success("Siker! Értesítettük az admint.")

# --- 6. BELSŐ FELÜLET & AUTOMATA JÓVÁHAGYÁS ---
else:
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        
        # ADMIN PANEL: Itt történik a varázslat
        if st.session_state.user_id == ADMIN_CHAT_ID:
            st.divider()
            st.subheader("🛠️ Admin Jóváhagyás")
            pending_users = users_df[users_df['status'] == 'Pending']
            if not pending_users.empty:
                user_to_approve = st.selectbox("Várólista:", pending_users['name'].tolist())
                if st.button("✅ Jóváhagyás és Üzenet küldése"):
                    # 1. Státusz frissítése a táblázatban
                    users_df.loc[users_df['name'] == user_to_approve, 'status'] = 'Approved'
                    conn.update(worksheet="Users", data=users_df)
                    
                    # 2. Automata üzenet küldése a tagnak
                    target_id = pending_users[pending_users['name'] == user_to_approve]['telegram_id'].values[0]
                    welcome = f"🎉 Szia {user_to_approve}!\n\nJóváhagytuk a tagságidat!\n🔑 Jelszó: {KLUB_JELSZO}\n🌐 URL: {APP_URL}"
                    send_telegram_msg(target_id, welcome)
                    st.success(f"{user_to_approve} jóváhagyva!")
                    st.rerun()
            else:
                st.write("Nincs várakozó.")

        st.divider()
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    # (A monitor és hírfolyam rész változatlan...)
    st.title("📊 VIP Monitor")
    st.write("Itt láthatod a kiválasztott részvényeidet...")