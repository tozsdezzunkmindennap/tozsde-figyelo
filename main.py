import streamlit as st
import yfinance as yf
import requests

# --- KONFIGURÁCIÓ ---
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

# Alapértelmezett jelszó, ha a Secrets-ben nincs felülírva
try:
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
except:
    KLUB_JELSZO = "Tozsdekiralyok2025"

def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": message})
        return response.status_code == 200
    except:
        return False

st.set_page_config(page_title="Zárt Tőzsde Klub", page_icon="📈")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- BEJELENTKEZŐ KERET ---
if not st.session_state.logged_in:
    st.title("🔐 Tőzsde Klub Belépés")
    
    with st.form("login_form"):
        # Megfordított sorrend és egyértelmű feliratok
        name_input = st.text_input("Válassz nevet / Hogy hívnak?")
        pass_input = st.text_input("KLUB JELSZÓ", type="password")
        tg_id_input = st.text_input("A te saját Telegram ID-d (szám)")
        
        submit = st.form_submit_button("Belépés a Klubba")
        
        if submit:
            if pass_input == KLUB_JELSZO and name_input and tg_id_input:
                st.session_state.logged_in = True
                st.session_state.user_name = name_input
                st.session_state.user_id = tg_id_input
                st.rerun()
            else:
                st.error("Helytelen KLUB JELSZÓ vagy hiányzó adatok!")

# --- BENTI FELÜLET ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    if st.sidebar.button("Kijelentkezés"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📈 Élő Monitor")
    
    ticker = st.text_input("Részvény kódja (pl: NVDA, TSLA):", "NVDA").upper()
    
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            price = stock.fast_info['last_price']
            st.metric(f"{ticker} Ár", f"{price:.2f} USD")
            
            target = st.number_input("Célár riasztáshoz:", value=float(price))
            
            if st.button("🚀 Riasztás kérése"):
                msg = f"Szia {st.session_state.user_name}! Figyelem a(z) {ticker}-t. Szólok {target} árnál!"
                if send_telegram_msg(st.session_state.user_id, msg):
                    st.success("Riasztás aktiválva! Nézd meg a Telegramod!")
                else:
                    st.error("Hiba! Jó az ID-d?")
            
            st.line_chart(stock.history(period="5d")['Close'])
        except:
            st.error("Hibás kód!")