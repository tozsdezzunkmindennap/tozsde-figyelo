import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- KONFIGURÁCIÓ ---
TELEGRAM_TOKEN = "8350650650:AAFQ24n1nKNn0wIbTfG-yPRuwFQPpZHmujY"
SAJAT_TELEGRAM_ID = "8385947337" # Te, mint Admin

try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
    KLUB_JELSZO = st.secrets["KLUB_JELSZO"]
except:
    FINNHUB_KEY = "d5i1j79r01qu7bqqnu4gd5i1j79r01qu7bqqnu50"
    KLUB_JELSZO = "Tozsdekiralyok2025"

MARKET_DATA = {
    "🇺🇸 Tech Óriások": ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "NFLX", "AMD", "PLTR"],
    "₿ Kriptovaluták": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "🇭🇺 Magyar Részvények": ["OTP.BU", "MOL.BU", "RICHT.BU", "4IG.BU", "MTEL.BU"],
    "🏎️ Autóipar & EV": ["RIVN", "LCID", "NIO", "F", "GM", "BYDDF"],
    "🏦 Bank & Pénzügy": ["JPM", "BAC", "V", "MA", "PYPL", "COIN"]
}

def send_telegram_msg(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": message})
        return r.status_code == 200
    except: return False

def get_finnhub_news(ticker):
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_KEY}"
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else []
    except: return []

st.set_page_config(page_title="TőzsdeKirályok VIP", page_icon="💰", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["NVDA", "BTC-USD"]

# --- LOGIN & REGISZTRÁCIÓ ---
if not st.session_state.logged_in:
    st.title("🔐 TőzsdeKirályok VIP Klub")
    
    tab1, tab2 = st.tabs(["Belépés", "Tagság igénylése"])
    
    with tab1:
        with st.form("login_form"):
            name = st.text_input("Név")
            pw = st.text_input("Jelszó", type="password")
            tg_id = st.text_input("Saját Telegram ID-d")
            if st.form_submit_button("Belépés"):
                if pw == KLUB_JELSZO and name and tg_id:
                    st.session_state.logged_in, st.session_state.user_name, st.session_state.user_id = True, name, tg_id
                    st.rerun()
                else: st.error("Hibás adatok!")

    with tab2:
        st.write("Szeretnél csatlakozni? Küldj egy kérést az adminnak!")
        with st.form("reg_form"):
            reg_name = st.text_input("Hogy hívnak?")
            reg_tg_id = st.text_input("Telegram ID-d (ezen kapod a jelszót)")
            msg = st.text_area("Üzenet az adminnak (opcionális)")
            
            if st.form_submit_button("Jelentkezés elküldése"):
                if reg_name and reg_tg_id:
                    admin_text = f"🔔 ÚJ TAGJELÖLT!\n\nNév: {reg_name}\nID: {reg_tg_id}\nÜzenet: {msg}"
                    if send_telegram_msg(SAJAT_TELEGRAM_ID, admin_text):
                        st.success("Jelentkezés elküldve! Az admin hamarosan keresni fog Telegramon.")
                    else: st.error("Hiba a küldés során.")
                else: st.warning("Töltsd ki a nevet és az ID-t!")

# --- BENTI FELÜLET ---
else:
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.divider()
        st.header("📂 Böngészés")
        cat = st.selectbox("Kategória:", list(MARKET_DATA.keys()))
        selected = st.selectbox("Részvény/Kripto:", MARKET_DATA[cat])
        if st.button("➕ Hozzáadás"):
            if selected not in st.session_state.watchlist:
                st.session_state.watchlist.append(selected)
                st.rerun()
        
        st.divider()
        period = st.radio("Változás:", ["1D", "1W", "1M"])
        if st.button("🚪 Kijelentkezés"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📊 Monitor")
    
    # Táblázat
    if st.session_state.watchlist:
        p_map = {"1D": "2d", "1W": "10d", "1M": "35d"}
        q_list = []
        for t in st.session_state.watchlist:
            try:
                h = yf.Ticker(t).history(period=p_map[period])
                curr = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2] if period == "1D" else h['Close'].iloc[0]
                diff = ((curr - prev) / prev) * 100
                q_list.append({"Ticker": t, "Ár": f"{curr:.2f}", f"Változás ({period})": f"{'🟢' if diff >= 0 else '🔴'} {diff:+.2f}%"})
            except: pass
        st.table(pd.DataFrame(q_list))

    st.divider()
    
    for t in st.session_state.watchlist:
        with st.expander(f"🔍 {t} részletek"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.line_chart(yf.Ticker(t).history(period="1mo")['Close'])
                if st.button(f"🗑️ Törlés: {t}", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()
            with c2:
                st.write("**Hírek**")
                news = get_finnhub_news(t)
                if isinstance(news, list) and len(news) > 0:
                    for n in news[:3]:
                        st.markdown(f"**[{n.get('headline','')}]({n.get('url','#')})**")
                        st.caption(f"{n.get('source','')} | {datetime.fromtimestamp(n.get('datetime', 0)).strftime('%Y-%m-%d')}")
                        st.divider()