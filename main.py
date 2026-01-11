import streamlit as st
import yfinance as yf
import requests
import json
import os

# --- KONFIGURÁCIÓ ---
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"
USER_DB = "users.json"
TREND_DB = "trends.json"

# --- ADATKEZELŐ FÜGGVÉNYEK ---
def load_data(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# Adatok betöltése
users = load_data(USER_DB, {})
trends = load_data(TREND_DB, [])

def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

st.set_page_config(page_title="Zárt Tőzsde Klub", layout="wide")

# --- BELÉPTETŐ ÉS REGISZTRÁCIÓS RENDSZER ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 Belépés", "📝 Regisztráció"])
    
    with tab1:
        st.subheader("Bejelentkezés")
        login_user = st.text_input("Felhasználónév (Belépés)")
        login_pw = st.text_input("Jelszó (Belépés)", type="password")
        if st.button("Belépés"):
            if login_user in users and users[login_user]["pw"] == login_pw:
                st.session_state.logged_in = True
                st.session_state.user = login_user
                st.rerun()
            else:
                st.error("Hibás név vagy jelszó!")
                
    with tab2:
        st.subheader("Új fiók létrehozása")
        reg_user = st.text_input("Válassz nevet")
        reg_pw = st.text_input("Válassz jelszót", type="password")
        reg_id = st.text_input("Telegram ID-d (8385947337)")
        
        if st.button("Regisztrálok"):
            if reg_user and reg_pw and reg_id:
                if reg_user not in users:
                    users[reg_user] = {"pw": reg_pw, "id": reg_id}
                    save_data(USER_DB, users)
                    st.success("Sikeres regisztráció! Most már beléphetsz.")
                else:
                    st.error("Ez a név már foglalt!")
            else:
                st.warning("Minden mezőt tölts ki!")

else:
    # --- HA BE VAN JELENTKEZVE ---
    current_user = st.session_state.user
    user_id = users[current_user]["id"]
    
    st.sidebar.title(f"👤 {current_user}")
    if st.sidebar.button("Kijelentkezés"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("Privát Tőzsde Monitor")

    col1, col2 = st.columns([2, 1])

    with col1:
        ticker = st.text_input("Figyelt részvény:", "NVDA").upper()
        if ticker:
            stock = yf.Ticker(ticker)
            price = stock.fast_info['last_price']
            st.metric(f"{ticker} Árfolyam", f"{price:.2f} USD")
            
            target = st.number_input("Riasztási szint (USD):", value=float(price))
            
            if st.button("Riasztás élesítése"):
                # Névtelen trend mentése
                if ticker not in trends:
                    trends.append(ticker)
                    save_data(TREND_DB, trends)
                
                send_telegram_msg(user_id, f"Szia {current_user}! Figyelem a {ticker}-t. Célár: {target}")
                st.success("Riasztás beállítva és elmentve!")

    with col2:
        st.subheader("🕵️ Névtelen Trendek")
        st.write("Ezt nézik a többiek:")
        for item in trends:
            st.info(f"Valaki ezt figyeli: **{item}**")

    st.divider()
    if ticker:
        st.line_chart(stock.history(period="5d")['Close'])