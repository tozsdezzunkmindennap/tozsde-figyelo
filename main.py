import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURÁCIÓ ---
# A te saját Telegram ID-d, amit megadtál (8385947337)
ADMIN_CHAT_ID = "8385947337" 
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"

try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
    # A jóváhagyott ID-k listája (ezt a Streamlit Secrets-ben kell szerkesztened)
    APPROVED_IDS = st.secrets["APPROVED_IDS"]
except:
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"
    APPROVED_IDS = ["8385947337"]

# --- 2. FUNKCIÓK ---

def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
        return r.status_code == 200
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

# Automatikus üdvözlő üzenet az új tagnak
def send_welcome_pack(user_id, user_name):
    welcome_text = (
        f"🎉 Szia {user_name}!\n\n"
        f"Örömmel értesítelek, hogy a tagságidat jóváhagytuk a TőzsdeKirályok VIP Klubban! ✅\n\n"
        f"Itt vannak a belépési adatok:\n"
        f"🔑 Jelszó: {KLUB_JELSZO}\n"
        f"🌐 App URL: {st.secrets.get('APP_URL', 'Kérd az admintól!')}\n\n"
        f"Most már be tudsz lépni a saját Telegram ID-ddal!"
    )
    return send_telegram_msg(user_id, welcome_text)

# --- 3. PIACI KATEGÓRIÁK ---
MARKET_DATA = {
    "🇺🇸 Tech Óriások": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "NFLX"],
    "₿ Kriptovaluták": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "🇭🇺 Magyar Piac": ["OTP.BU", "MOL.BU", "RICHT.BU", "4IG.BU", "MTEL.BU"],
    "💰 Pénzügy": ["JPM", "BAC", "V", "MA", "COIN"]
}

# --- 4. STREAMLIT APP LOGIKA ---
st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["NVDA", "BTC-USD"]

# --- 5. BELÉPÉS ÉS REGISZTRÁCIÓ ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok VIP Klub")
    
    tab1, tab2 = st.tabs(["🔑 Belépés", "📝 Tagság igénylése"])
    
    with tab1:
        with st.form("login"):
            login_name = st.text_input("Név")
            login_tg_id = st.text_input("Saját Telegram ID-d")
            login_pw = st.text_input("Klub Jelszó", type="password")
            if st.form_submit_button("Belépés"):
                if login_pw == KLUB_JELSZO and login_tg_id in APPROVED_IDS:
                    st.session_state.logged_in = True
                    st.session_state.user_name = login_name
                    st.session_state.user_id = login_tg_id
                    st.rerun()
                elif login_pw == KLUB_JELSZO and login_tg_id not in APPROVED_IDS:
                    st.warning("A regisztrációd még jóváhagyásra vár!")
                else:
                    st.error("Hibás jelszó vagy ID!")

    with tab2:
        st.subheader("Jelentkezés a csoportba")
        st.info("⚠️ Fontos: Mielőtt elküldöd, indítsd el a botot Telegramon, hogy tudjunk üzenni neked!")
        with st.form("registration"):
            reg_name = st.text_input("Hogy hívnak?")
            reg_tg_id = st.text_input("Telegram ID-d")
            if st.form_submit_button("Jelentkezés küldése"):
                if reg_name and reg_tg_id:
                    admin_msg = f"🔔 ÚJ TAGJELÖLT!\n\nNév: {reg_name}\nID: {reg_tg_id}\n\nHa jóváhagytad a Secrets-ben, használd az Admin Panelt az értesítéshez!"
                    send_telegram_msg(ADMIN_CHAT_ID, admin_msg)
                    st.success("Jelentkezés elküldve! Az admin értesítést kapott.")
                else:
                    st.error("Minden mezőt tölts ki!")

# --- 6. BELSŐ FELÜLET ---
else:
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        
        # --- ADMIN PANEL (Csak neked látszik) ---
        if st.session_state.user_id == ADMIN_CHAT_ID:
            st.divider()
            st.subheader("🛠️ Admin Műveletek")
            new_id = st.text_input("Jóváhagyott új ID:")
            new_name = st.text_input("Új tag neve:")
            if st.button("✅ Üdvözlő csomag küldése"):
                if new_id and new_name:
                    if send_welcome_pack(new_id, new_name):
                        st.sidebar.success(f"Üzenet elküldve: {new_name}")
                    else:
                        st.sidebar.error("Hiba! A tag elindította a botot?")
        
        st.divider()
        st.header("📂 Figyelőlista")
        cat = st.selectbox("Kategória:", list(MARKET_DATA.keys()))
        selected = st.selectbox("Részvény:", MARKET_DATA[cat])
        if st.button("➕ Hozzáadás"):
            if selected not in st.session_state.watchlist:
                st.session_state.watchlist.append(selected)
                st.rerun()
        
        st.divider()
        period = st.radio("Változás:", ["1D", "1W", "1M"])
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📊 VIP Élő Monitor")
    
    # Adatok megjelenítése
    if st.session_state.watchlist:
        p_map = {"1D": "2d", "1W": "10d", "1M": "35d"}
        data = []
        for t in st.session_state.watchlist:
            try:
                h = yf.Ticker(t).history(period=p_map[period])
                curr = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2] if period == "1D" else h['Close'].iloc[0]
                diff = ((curr - prev) / prev) * 100
                data.append({"Ticker": t, "Ár": f"{curr:.2f}", f"Változás ({period})": f"{'🟢' if diff >= 0 else '🔴'} {diff:+.2f}%"})
            except: pass
        st.table(pd.DataFrame(data))

    st.divider()
    
    for t in st.session_state.watchlist:
        with st.expander(f"🔍 {t} Információk"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.line_chart(yf.Ticker(t).history(period="1mo")['Close'])
                if st.button(f"🗑️ Törlés: {t}", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()
            with c2:
                news = get_finnhub_news(t)
                for n in news[:3]:
                    st.markdown(f"**[{n.get('headline','')}]({n.get('url','#')})**")
                    st.caption(f"{n.get('source','')} | {datetime.fromtimestamp(n.get('datetime', 0)).strftime('%Y-%m-%d')}")
                    st.divider()