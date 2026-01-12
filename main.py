import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURÁCIÓ ÉS TITKOK ---
# A saját ID-d, ahová a bot a jelentkezéseket küldi
ADMIN_CHAT_ID = "8385947337" 
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
    # A jóváhagyott ID-k listája a Secrets-ből (Pl: ["8385947337", "12345"])
    APPROVED_IDS = st.secrets["APPROVED_IDS"]
except:
    # Alapértelmezett értékek, ha nincs beállítva Secrets
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"
    APPROVED_IDS = ["8385947337"]

# --- 2. SEGÉDFÜGGVÉNYEK ---

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

# --- 3. PIACI ADATOK (KATEGÓRIÁK) ---
MARKET_DATA = {
    "🇺🇸 Tech Óriások": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "NFLX"],
    "₿ Kriptovaluták": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "🇭🇺 Magyar Piac": ["OTP.BU", "MOL.BU", "RICHT.BU", "4IG.BU", "MTEL.BU"],
    "🚗 Ipar & EV": ["RIVN", "LCID", "NIO", "F", "GM"],
    "💰 Pénzügy": ["JPM", "BAC", "V", "MA", "COIN"]
}

# --- 4. STREAMLIT APP LOGIKA ---
st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["NVDA", "BTC-USD"]

# --- 5. BELÉPÉS ÉS REGISZTRÁCIÓ FELÜLET ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok VIP Klub")
    
    tab1, tab2 = st.tabs(["🔑 Belépés", "📝 Tagság igénylése"])
    
    with tab1:
        with st.form("login"):
            login_name = st.text_input("Felhasználónév")
            login_pw = st.text_input("Klub Jelszó", type="password")
            login_tg_id = st.text_input("Saját Telegram ID-d")
            if st.form_submit_button("Belépés"):
                if login_pw == KLUB_JELSZO and login_tg_id in APPROVED_IDS:
                    st.session_state.logged_in = True
                    st.session_state.user_name = login_name
                    st.session_state.user_id = login_tg_id
                    st.rerun()
                elif login_tg_id not in APPROVED_IDS and login_pw == KLUB_JELSZO:
                    st.warning("A regisztrációd még jóváhagyásra vár!")
                else:
                    st.error("Hibás adatok!")

    with tab2:
        st.subheader("Jelentkezés a VIP csoportba")
        with st.form("registration"):
            reg_name = st.text_input("Teljes neved")
            reg_tg_id = st.text_input("Telegram ID-d (ezen kapsz jelszót)")
            note = st.text_area("Üzenet az adminnak")
            if st.form_submit_button("Jelentkezés küldése"):
                if reg_name and reg_tg_id:
                    msg = f"🔔 ÚJ JELENTKEZŐ!\nNév: {reg_name}\nID: {reg_tg_id}\nMegjegyzés: {note}"
                    send_telegram_msg(ADMIN_CHAT_ID, msg)
                    st.success("Igénylés elküldve! Az admin hamarosan értesít Telegramon.")
                else:
                    st.error("Kérlek töltsd ki a kötelező mezőket!")

# --- 6. BELSŐ MONITOR FELÜLET ---
else:
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.divider()
        st.header("📂 Részvény hozzáadása")
        cat = st.selectbox("Válassz kategóriát:", list(MARKET_DATA.keys()))
        selected = st.selectbox("Válassz papírt:", MARKET_DATA[cat])
        
        if st.button("➕ Listára teszem"):
            if selected not in st.session_state.watchlist:
                st.session_state.watchlist.append(selected)
                st.rerun()
        
        st.divider()
        period = st.radio("Változás idötartama:", ["1D", "1W", "1M"])
        
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📊 Élő Piaci Monitor")
    
    # Ártáblázat generálása
    if st.session_state.watchlist:
        p_map = {"1D": "2d", "1W": "10d", "1M": "35d"}
        summary_data = []
        for t in st.session_state.watchlist:
            try:
                stock = yf.Ticker(t)
                hist = stock.history(period=p_map[period])
                if not hist.empty:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if period == "1D" else hist['Close'].iloc[0]
                    diff = ((curr - prev) / prev) * 100
                    summary_data.append({
                        "Ticker": t, 
                        "Ár (USD)": f"{curr:.2f}", 
                        f"Változás ({period})": f"{'🟢' if diff >= 0 else '🔴'} {diff:+.2f}%"
                    })
            except: pass
        st.table(pd.DataFrame(summary_data))

    st.divider()
    
    # Részletek és Hírek
    st.subheader("📰 Részletes elemzés és hírek")
    for t in st.session_state.watchlist:
        with st.expander(f"🔍 {t} Információk"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**Árfolyamgörbe (30 nap)**")
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