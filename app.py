import streamlit as st
import streamlit.components.v1 as components
import json
import os
import random
from datetime import datetime, timedelta, timezone

# App Settings
st.set_page_config(page_title="Pritika's Pro Trading Tracker", page_icon="📈", layout="centered")

# ==========================================
# GLOBAL HARA-BHARA & COLOURFUL CSS STYLING
# ==========================================
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #F9FBF9 0%, #FFFDF7 100%); }
div[data-testid="stPopover"] > div > button {
    background: linear-gradient(90deg, #FFF8DC, #FFE4B5) !important;
    border: 2px solid #FF8C00 !important; border-radius: 12px !important;
    padding: 14px 20px !important; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.12) !important;
}
div[data-testid="stPopover"] > div > button p {
    font-size: 21px !important; font-weight: 800 !important; color: #8B0000 !important;
}
div[data-testid="stPopover"] > div > button:hover {
    background: linear-gradient(90deg, #FFD700, #FFA500) !important; border-color: #8B0000 !important;
}
div[data-testid="stLinkButton"] > a {
    background: linear-gradient(90deg, #008080, #20B2AA) !important;
    color: #FFFFFF !important; border: 2px solid #004D40 !important;
    border-radius: 12px !important; padding: 12px 18px !important; font-weight: 800 !important;
}
div[data-testid="stLinkButton"] > a p { color: #FFFFFF !important; font-size: 18px !important; font-weight: bold !important; }
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(90deg, #1B5E20, #2E7D32, #43A047) !important;
    color: white !important; border: 2px solid #FFD700 !important;
    border-radius: 12px !important; padding: 12px 24px !important; width: 100% !important;
}
div.stButton > button p, div[data-testid="stFormSubmitButton"] > button p {
    font-size: 20px !important; font-weight: 800 !important; color: #FFFFFF !important;
}
div[data-testid="stCheckbox"] {
    background: linear-gradient(90deg, #E8F5E9, #F1F8E9);
    padding: 12px 16px; border-radius: 10px; border-left: 6px solid #2E7D32;
    border-right: 1px solid #C8E6C9; margin-bottom: 10px;
}
div[data-testid="stCheckbox"] label p { font-size: 18px !important; font-weight: 700 !important; color: #1B5E20 !important; }
div[data-testid="stExpander"] {
    border: 2px solid #2E7D32 !important; border-radius: 14px !important; background-color: #FAFFFA !important;
}
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
    border: 2px solid #2E7D32; border-radius: 12px; padding: 15px; text-align: center;
}
div[data-testid="stForm"] {
    background: linear-gradient(135deg, #F3E5F5, #E8EAF6);
    border: 2px solid #6A1B9A; border-radius: 14px; padding: 18px;
}
</style>
""", unsafe_allow_html=True)

import hashlib
import time

# ==============================================================================
# 🔒 UPGRADED SECURITY, USER ID TRACKER, LIVE MEMBER COUNTER & SEBI COMPLIANCE
# ==============================================================================
DB_FILE = "tracker_access_db.json"
IST = timezone(timedelta(hours=5, minutes=30))

# Admin password ko Streamlit Secrets se uthayein (GitHub par password nahi dikhega)
# Streamlit Cloud -> App Settings -> Secrets mein dalein: ADMIN_PASSWORD = "aapka_strong_password"
ADMIN_SECRET = st.secrets.get("ADMIN_PASSWORD", "7777")

def hash_pin(pin_str):
    return hashlib.sha256(str(pin_str).strip().encode()).hexdigest()

@st.cache_resource
def get_memory_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"admin_hash": hash_pin(ADMIN_SECRET), "pins": {}}

@st.cache_resource
def get_active_sessions():
    # Live users track karne ke liye shared dictionary: {user_id: last_active_timestamp}
    return {}

def save_db(db):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(db, f)
    except Exception:
        pass

def update_and_count_live_users(user_id):
    sessions = get_active_sessions()
    now_ts = time.time()
    # 15 minute se zyada inactive users ko hata dein
    expired = [uid for uid, ts in sessions.items() if now_ts - ts > 900]
    for uid in expired:
        del sessions[uid]
    if user_id:
        sessions[user_id] = now_ts
    return len(sessions), list(sessions.keys())

db = get_memory_db()

# Brute-force lock state
if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0
if "lock_until" not in st.session_state:
    st.session_state.lock_until = 0
if "sebi_accepted" not in st.session_state:
    st.session_state.sebi_accepted = False
if "saved_pass" not in st.session_state:
    st.session_state.saved_pass = ""

def verify_pin(user_input):
    pin = str(user_input).strip()
    if not pin:
        return False, "", False, [], ""
    
    # 1. Admin Check (Hashed)
    if hash_pin(pin) == db.get("admin_hash", hash_pin(ADMIN_SECRET)) or pin == ADMIN_SECRET:
        return True, "👑 Admin Mode Active (All Stages Unlocked)", True, ["1", "1.5", "2", "3", "4", "5"], "ADMIN-PRITIKA"
    
    # 2. User PIN Check
    pins_data = db.get("pins", {})
    pin_h = hash_pin(pin)
    
    # Support both hashed & old plain PINs
    info = pins_data.get(pin_h) or pins_data.get(pin)
    if info:
        exp_time = datetime.strptime(info["expiry"], "%Y-%m-%d %H:%M")
        now_ist = datetime.now(IST).replace(tzinfo=None)
        if now_ist > exp_time:
            return False, "⏳ Aapka Access PIN Expire ho chuka hai! Renew karne ke liye Admin se sampark karein.", False, [], ""
        allowed = info["stages"]
        uid = info.get("user_id", f"USER-{pin[-4:]}")
        stages_text = ", ".join([f"Stage {s}" for s in allowed])
        return True, f"✅ Active ({stages_text}) | Valid Till: {exp_time.strftime('%d %b %Y, %I:%M %p')}", False, allowed, uid
        
    return False, "❌ Galat Password / PIN! Kripya sahi password dalein.", False, [], ""

is_valid, status_msg, is_admin, allowed_stages, current_user_id = verify_pin(st.session_state.saved_pass)

# --- LOGIN SCREEN WITH SEBI DISCLAIMER & BRUTE-FORCE LOCK ---
if not is_valid:
    st.markdown("""
    <div style="text-align: center; background: linear-gradient(90deg, #004D40, #1B5E20, #2E7D32); padding: 18px; border-radius: 15px; border: 3px solid #FFD700; margin-bottom: 18px;">
        <h1 style="color: #FFD700; font-size: 34px; font-weight: 900; margin: 0;">🔒 Pritika's Pro Trading Tracker</h1>
    </div>
    """, unsafe_allow_html=True)

    # SEBI Mandatory Disclaimer Box on Login
    st.markdown("""
    <div style="background: #FFF8E1; border: 2px solid #FF8F00; border-left: 8px solid #E65100; border-radius: 10px; padding: 14px; margin-bottom: 16px;">
        <h4 style="color: #BF360C; margin: 0 0 6px 0;">⚖️ SEBI COMPLIANCE & RISK DISCLOSURE</h4>
        <p style="color: #333; font-size: 13.5px; margin: 0; line-height: 1.5;">
            1. <b>Not a SEBI Registered Advisor:</b> Yeh terminal sirf <b>Educational, Trading Discipline aur Risk Management</b> ke liye banaya gaya hai. Yahan koi bhi Buy/Sell tips, calls, ya investment advice nahi di jati.<br>
            2. <b>SEBI Derivatives Risk Warning:</b> SEBI study ke anusar, 9 out of 10 individual traders in equity Futures & Options (F&O) segment incur net losses.<br>
            3. <b>User Responsibility:</b> Kisi bhi trade ka profit ya loss poori tarah user ki apni zimmedari hogi. Trade lene se pehle apne SEBI-registered Financial Advisor se salah lein.
        </p>
    </div>
    """, unsafe_allow_html=True)

    agree_sebi = st.checkbox("✅ Maine SEBI Risk Disclosure padh liya hai aur main samajhta/samajhti hoon ki yeh sirf ek Discipline & Educational Tool hai.")

    # Lockout check
    now_t = time.time()
    if now_t < st.session_state.lock_until:
        rem = int(st.session_state.lock_until - now_t)
        st.error(f"🚫 Bahut zyada galat attempts! Security ke liye login **{rem} seconds** ke liye lock hai.")
        st.stop()

    st.info("🔑 App kholne ke liye apna **Authorized Access PIN** dalein.")
    input_pass = st.text_input("Enter Access PIN / Password:", type="password", max_chars=20, placeholder="Apna PIN dalein...")

    if st.button("🔓 Unlock Terminal"):
        if not agree_sebi:
            st.warning("⚠️ Aage badhne ke liye upar SEBI Risk Disclosure box par tick karein.")
        else:
            ok, msg, adm, stg, uid = verify_pin(input_pass)
            if ok:
                st.session_state.failed_attempts = 0
                st.session_state.saved_pass = input_pass.strip()
                st.session_state.sebi_accepted = True
                st.rerun()
            else:
                st.session_state.failed_attempts += 1
                if st.session_state.failed_attempts >= 5:
                    st.session_state.lock_until = time.time() + 120  # 2-minute lock
                    st.error("🚫 5 baar galat PIN! Terminal 2 minute ke liye lock ho gaya hai.")
                else:
                    st.error(f"{msg} (Bache hue attempts: {5 - st.session_state.failed_attempts})")
    st.stop()

# --- LIVE USER TRACKING & TOTAL MEMBERS BAR ---
live_count, live_user_list = update_and_count_live_users(current_user_id)
total_registered = len(db.get("pins", {})) + 1  # +1 for Admin

st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
            background: linear-gradient(90deg, #1A237E, #283593); color: white; padding: 10px 16px;
            border-radius: 12px; border: 2px solid #FFD700; margin-bottom: 12px; font-family: sans-serif;">
    <div style="font-size: 15px; font-weight: 800;">
        🆔 ACTIVE TERMINAL ID: <span style="background: #FFD700; color: #000; padding: 3px 10px; border-radius: 6px;">{current_user_id}</span>
    </div>
    <div style="font-size: 14px; font-weight: 700;">
        🟢 Live Now: <span style="color: #69F0AE; font-size: 16px;">{live_count}</span> &nbsp;|&nbsp;
        👥 Total Members: <span style="color: #FFD700; font-size: 16px;">{total_registered}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- TOP ADMIN BAR ---
if is_admin:
    col_status, col_admin, col_logout = st.columns([5.5, 2.5, 2])
    with col_status:
        st.success(status_msg)
    with col_admin:
        admin_box = st.popover("👑 Admin", use_container_width=True) if hasattr(st, "popover") else st.expander("👑 Admin")
        with admin_box:
            st.markdown(f"**🟢 Currently Online ({live_count}):** `{', '.join(live_user_list)}`")
            st.markdown("---")
            st.markdown("### ⚡ Naya Member ID & PIN Banayein")
            member_id = st.text_input("1. Member Name / ID:", placeholder="Ex: TRADER-RAHUL-01")
            plan = st.radio("2. Plan Validity:", ["1 Day (24 Hours)", "1 Month (30 Days)", "1 Year (365 Days)"])
            st.markdown("**3. Stages Select Karein:**")
            st_s1 = st.checkbox("Stage 1: Pre-Market", value=True, key="adm_s1")
            st_s15 = st.checkbox("Stage 1.5: Master Power Summary", value=True, key="adm_s15")
            st_s2 = st.checkbox("Stage 2: Live Market Rules", value=True, key="adm_s2")
            st_s3 = st.checkbox("Stage 3: Target Calculator", value=True, key="adm_s3")
            st_s4 = st.checkbox("Stage 4: Trade Diary", value=True, key="adm_s4")
            st_s5 = st.checkbox("Stage 5: Screen Recorder", value=True, key="adm_s5")
            custom_pin = st.text_input("4. Custom 4-Digit PIN (Optional):", max_chars=4, placeholder="Ex: 4582")
            selected_stages = [s for s, val in [("1", st_s1), ("1.5", st_s15), ("2", st_s2), ("3", st_s3), ("4", st_s4), ("5", st_s5)] if val]

            if st.button("🔑 Create Member Access"):
                if not member_id.strip():
                    st.warning("Member ka Naam ya ID zaroor dalein!")
                elif not selected_stages:
                    st.warning("Kam se kam 1 Stage select karein!")
                elif custom_pin and (len(custom_pin) != 4 or not custom_pin.isdigit()):
                    st.warning("Sirf 4 digits ka number dalein!")
                else:
                    new_pin = custom_pin if custom_pin else str(random.randint(1000, 9999))
                    days_map = {"1 Day (24 Hours)": 1, "1 Month (30 Days)": 30, "1 Year (365 Days)": 365}
                    exp_dt = datetime.now(IST).replace(tzinfo=None) + timedelta(days=days_map[plan])
                    db["pins"][hash_pin(new_pin)] = {
                        "user_id": member_id.strip().upper(),
                        "expiry": exp_dt.strftime("%Y-%m-%d %H:%M"),
                        "stages": selected_stages,
                        "plan": plan
                    }
                    save_db(db)
                    stg_names = ", ".join([f"Stage {x}" for x in selected_stages])
                    st.success(f"✅ Member Created: **{member_id.strip().upper()}** | PIN: **{new_pin}**")
                    st.code(f"📊 Pritika's Pro Trading Tracker\n🆔 User ID: {member_id.strip().upper()}\n🔑 PIN: {new_pin}\n🔓 Access: {stg_names}\n⏳ Valid till {exp_dt.strftime('%d %b %Y, %I:%M %p')}", language="markdown")

            if db.get("pins"):
                st.markdown("---")
                if st.button("🗑️ Clear All User Passwords"):
                    db["pins"] = {}
                    save_db(db)
                    st.rerun()

            st.markdown("---")
            st.markdown("### ⚙️ Apna Admin Password Badlein")
            new_admin_p = st.text_input("Naya Strong Admin Password:", type="password", placeholder="Ex: Pritika@2026")
            if st.button("💾 Save New Admin Password"):
                if len(new_admin_p.strip()) >= 6:
                    db["admin_hash"] = hash_pin(new_admin_p.strip())
                    save_db(db)
                    st.session_state.saved_pass = new_admin_p.strip()
                    st.success("✅ Admin Password Securely Updated!")
                else:
                    st.warning("Security ke liye kam se kam 6 characters ka password rakhein.")
    with col_logout:
        if st.button("🚪 Logout"):
            sessions = get_active_sessions()
            sessions.pop(current_user_id, None)
            st.session_state.saved_pass = ""
            st.rerun()
else:
    col_status, col_logout = st.columns([8, 2])
    with col_status:
        st.info(status_msg)
    with col_logout:
        if st.button("🚪 Logout"):
            sessions = get_active_sessions()
            sessions.pop(current_user_id, None)
            st.session_state.saved_pass = ""
            st.rerun()
# ==============================================================================
# 🕒 LIVE IST CLOCK + CURRENT PHASE + NEXT PHASE COUNTDOWN ALERT (TOP BANNER)
# ==============================================================================
components.html("""
<div id="liveAlertBox" style="background: linear-gradient(90deg, #0D47A1, #1565C0); color: white; padding: 14px 18px; border-radius: 14px; border: 3px solid #FFD700; font-family: sans-serif; box-shadow: 0px 4px 14px rgba(0,0,0,0.25); margin-bottom: 6px;">
    
    <!-- Top Row: Live Clock -->
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 8px; margin-bottom: 10px;">
        <span style="font-size: 16px; font-weight: 900; color: #FFD700;">🕒 LIVE MARKET RADAR (IST)</span>
        <span id="istClock" style="font-size: 20px; font-weight: 900; background: #00000066; padding: 4px 12px; border-radius: 8px; color: #FFFFFF; letter-spacing: 1px;">--:--:--</span>
    </div>

    <!-- Current Phase -->
    <div style="background: rgba(0,0,0,0.25); padding: 10px 12px; border-radius: 10px; margin-bottom: 10px;">
        <div style="font-size: 12px; font-weight: 800; color: #FFD700; text-transform: uppercase; letter-spacing: 0.5px;">🔴 ABHI CHAL RAHA HAI (CURRENT PHASE):</div>
        <div id="currTitle" style="font-size: 17px; font-weight: 900; margin: 3px 0;">Loading...</div>
        <div id="currAction" style="font-size: 14px; font-weight: 600; line-height: 1.4; color: #F5F5F5;">Checking live market time...</div>
    </div>

    <!-- Next Phase + Countdown -->
    <div style="background: rgba(255,255,255,0.14); padding: 10px 12px; border-radius: 10px; border-left: 5px solid #FFD700;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; margin-bottom: 4px;">
            <span style="font-size: 12px; font-weight: 900; color: #FFEB3B;">⏭️ AGLA PHASE AANE WALA HAI:</span>
            <span id="nextCountdown" style="font-size: 15px; font-weight: 900; background: #FFD700; color: #000000; padding: 3px 10px; border-radius: 6px;">⏳ --:--</span>
        </div>
        <div id="nextTitle" style="font-size: 15px; font-weight: 800; color: #FFFFFF;">Loading next phase...</div>
        <div id="nextAction" style="font-size: 13px; font-weight: 600; color: #E0F7FA; margin-top: 2px;">...</div>
    </div>

</div>

<script>
const PHASES = [
    {
        start: 9*60, end: 9*60+15,
        bg: "linear-gradient(90deg, #E65100, #F57C00)",
        title: "🔔 9:07 AM — Pre-Open Setup",
        action: "👀 Market ka sentiment dekhein aur Gap-Up / Gap-Down note karein. Abhi koi order mat lagayein."
    },
    {
        start: 9*60+15, end: 9*60+45,
        bg: "linear-gradient(90deg, #B71C1C, #D32F2F)",
        title: "🚨 9:15 – 9:45 AM — High Volatility (Trap Zone)",
        action: "🛑 WARNING: Retailers ko trap kiya jata hai! Trading AVOID karein, sirf Intraday High/Low levels mark karein."
    },
    {
        start: 9*60+45, end: 10*60+30,
        bg: "linear-gradient(90deg, #1B5E20, #2E7D32)",
        title: "🚀 9:45 – 10:30 AM — Trend Initiation (Asli Move)",
        action: "✅ Confirmation ka wait karein aur Trend ki disha mein apne Zone par entry lein."
    },
    {
        start: 10*60+30, end: 11*60+30,
        bg: "linear-gradient(90deg, #00695C, #00897B)",
        title: "📈 10:30 – 11:30 AM — Trend Continuation",
        action: "🎯 Profit mein hain to SL trail karein. Naye trade ke liye sirf clean pullback ka wait karein."
    },
    {
        start: 11*60+30, end: 12*60+30,
        bg: "linear-gradient(90deg, #AD1457, #C2185B)",
        title: "⚠️ 11:30 AM – 12:30 PM — Sideways & Low Volume",
        action: "🛑 Overtrading AVOID karein! Partial profit book karein aur sirf market ko observe karein."
    },
    {
        start: 12*60+30, end: 12*60+45,
        bg: "linear-gradient(90deg, #FF6F00, #FFA000)",
        title: "⚡ 12:30 – 12:45 PM — Breakout Window",
        action: "👀 Consolidation se tez Breakout aa sakta hai! Chart aur Volume par poori nazar rakhein."
    },
    {
        start: 12*60+45, end: 13*60+15,
        bg: "linear-gradient(90deg, #37474F, #546E7A)",
        title: "⏳ 12:45 – 1:15 PM — Mid-Day Wait Zone",
        action: "📌 Breakout sustain ho raha hai ya fake hai check karein. Bina confirmation entry na lein."
    },
    {
        start: 13*60+15, end: 14*60,
        bg: "linear-gradient(90deg, #4A148C, #7B1FA2)",
        title: "🔄 1:15 – 2:00 PM — Reversal Phase",
        action: "💡 Subah ka trend palat sakta hai! Counter-trend ya Retracement trades ke liye yeh best time hai."
    },
    {
        start: 14*60, end: 14*60+30,
        bg: "linear-gradient(90deg, #1565C0, #1976D2)",
        title: "📊 2:00 – 2:30 PM — Pre-Closing Setup",
        action: "👀 Aakhri ghante ke bade move ke liye apne levels aur positions check kar lein."
    },
    {
        start: 14*60+30, end: 15*60+30,
        bg: "linear-gradient(90deg, #BF360C, #E64A19)",
        title: "🔥 2:30 – 3:30 PM — Volatile Close (FII/DII Moves)",
        action: "💰 Bade players active hain! SL tight trail karein aur apna Profit Book karke dukaan band karein."
    }
];

function formatCountdown(sec) {
    if (sec < 0) sec = 0;
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    if (h > 0) return `⏳ ${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s mein`;
    return `⏳ ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s mein`;
}

function updateMarketRadar() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const ist = new Date(utc + (3600000 * 5.5));

    const hh = ist.getHours(), mm = ist.getMinutes(), ss = ist.getSeconds();
    const nowMin = hh * 60 + mm;
    const nowSec = hh * 3600 + mm * 60 + ss;

    const ampm = hh >= 12 ? 'PM' : 'AM';
    document.getElementById('istClock').innerText =
        `${String(hh % 12 || 12).padStart(2,'0')}:${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')} ${ampm}`;

    const box = document.getElementById('liveAlertBox');
    let idx = PHASES.findIndex(p => nowMin >= p.start && nowMin < p.end);

    if (idx !== -1) {
        const curr = PHASES[idx];
        const next = (idx + 1 < PHASES.length) ? PHASES[idx + 1] : {
            title: "🌙 3:30 PM — Market Closed",
            action: "📚 Din ki trading khatam! Apni Trade Diary aur galtiyan review karein."
        };
        const remSec = (curr.end * 60) - nowSec;

        box.style.background = curr.bg;
        document.getElementById('currTitle').innerText = curr.title;
        document.getElementById('currAction').innerText = curr.action;
        document.getElementById('nextTitle').innerText = next.title;
        document.getElementById('nextAction').innerText = "Taiyari: " + next.action;
        document.getElementById('nextCountdown').innerText = formatCountdown(remSec);
    } else {
        box.style.background = "linear-gradient(90deg, #263238, #37474F)";
        document.getElementById('currTitle').innerText = "🌙 Market Closed — Homework & Revision Time";
        document.getElementById('currAction').innerText = "📚 Aaj ki diary review karein aur kal ke liye Stage 1 (Pre-Market) ki taiyari karein.";
        document.getElementById('nextTitle').innerText = PHASES[0].title;
        document.getElementById('nextAction').innerText = "Agli Taiyari: " + PHASES[0].action;

        let remSec = (nowMin < 9*60) ? (9*3600 - nowSec) : ((24*3600 - nowSec) + 9*3600);
        document.getElementById('nextCountdown').innerText = formatCountdown(remSec);
    }
}
updateMarketRadar();
setInterval(updateMarketRadar, 1000);
</script>
""", height=245)

# ==============================================================================
# 🌍 WORLD & INDIAN CAPITAL MARKET FLASH NEWS + IMPACT ANALYZER
# ==============================================================================
import urllib.request
import xml.etree.ElementTree as ET

@st.cache_data(ttl=300)
def fetch_live_market_news():
    feeds = [
        ("🇮🇳 INDIA", "https://news.google.com/rss/search?q=Nifty+OR+Sensex+OR+RBI+OR+SEBI+OR+FII+stock+market+India&hl=en-IN&gl=IN&ceid=IN:en"),
        ("🌍 WORLD", "https://news.google.com/rss/search?q=US+Fed+OR+Powell+OR+CPI+inflation+OR+Crude+Oil+OR+Wall+Street+OR+Gold+market&hl=en-IN&gl=IN&ceid=IN:en")
    ]
    news_list = []
    bearish_kw = ["crash", "fall", "drop", "war", "attack", "rate hike", "hike", "inflation", "recession", "selloff", "sell-off", "plunge", "tariff", "tension", "slump", "tumble", "fear", "crisis"]
    bullish_kw = ["rally", "surge", "jump", "rate cut", "cut", "record high", "boom", "gain", "soar", "easing", "bull", "positive", "stimulus", "deal"]
    volatile_kw = ["fed", "fomc", "rbi", "cpi", "gdp", "powell", "sebi", "budget", "crude", "oil", "policy", "trump", "yield", "dollar"]

    for tag, url in feeds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall("./channel/item")[:5]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    t_low = title.lower()

                    if any(k in t_low for k in bearish_kw):
                        impact = "🔴 BEARISH / DANGER"
                        effect = "Market mein girawat ya selling pressure aa sakta hai! Call (CE) mein jaldbaazi na karein aur SL tight rakhein."
                        color = "#B71C1C"
                        bg = "#FFEBEE"
                        priority = 1
                    elif any(k in t_low for k in bullish_kw):
                        impact = "🟢 BULLISH / POSITIVE"
                        effect = "Market mein tezi (buying) aa sakti hai! Put (PE) mein trap hone se bachein aur Trend ke sath chalein."
                        color = "#1B5E20"
                        bg = "#E8F5E9"
                        priority = 2
                    elif any(k in t_low for k in volatile_kw):
                        impact = "⚡ HIGH VOLATILITY EVENT"
                        effect = "Bada data/event hai! Dono taraf tez jhatke (SL Hunting) lag sakte hain — Half Quantity ya Wait karein."
                        color = "#E65100"
                        bg = "#FFF3E0"
                        priority = 1
                    else:
                        impact = "🔵 MARKET UPDATE"
                        effect = "Normal khabar hai — apne pre-marked levels aur Stage 2 rules par dhyan dein."
                        color = "#0D47A1"
                        bg = "#E3F2FD"
                        priority = 3

                    news_list.append({
                        "tag": tag, "title": title, "link": link, "pub": pub[:22],
                        "impact": impact, "effect": effect, "color": color, "bg": bg, "priority": priority
                    })
        except Exception:
            pass

    news_list.sort(key=lambda x: x["priority"])
    return news_list

live_news = fetch_live_market_news()

# --- TOP BREAKING FLASH BANNER (Sabse Badi Impact News Turant Flash Hogi) ---
if live_news:
    top_n = live_news[0]
    st.markdown(f"""
    <div style="background: {top_n['bg']}; border: 3px solid {top_n['color']}; border-left: 10px solid {top_n['color']}; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0px 4px 12px rgba(0,0,0,0.15);">
        <div style="font-size: 13px; font-weight: 900; color: {top_n['color']}; letter-spacing: 0.5px;">
            🚨 FLASH NEWS ALERT ({top_n['tag']}) — {top_n['impact']}
        </div>
        <div style="font-size: 16px; font-weight: 800; color: #111111; margin: 4px 0;">
            {top_n['title']}
        </div>
        <div style="font-size: 14px; font-weight: 700; color: {top_n['color']};">
            👉 Market Effect: {top_n['effect']}
        </div>
    </div>
    """, unsafe_allow_html=True)

with st.expander("🌍 LIVE WORLD & INDIAN MARKET NEWS RADAR (Click to View All + Forex Factory)", expanded=False):
    nc1, nc2 = st.columns(2)
    with nc1:
        if st.button("🔄 Refresh Live News"):
            fetch_live_market_news.clear()
            st.rerun()
    with nc2:
        st.link_button("📅 Open Forex Factory (Red Folder Data)", "https://www.forexfactory.com/calendar", use_container_width=True)

    if not live_news:
        st.warning("Abhi live news load nahi ho pa rahi hai. Thodi der baad Refresh karein.")
    else:
        for n in live_news[:8]:
            st.markdown(f"""
            <div style="background: {n['bg']}; border-left: 6px solid {n['color']}; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                <div style="font-size: 12px; font-weight: 900; color: {n['color']};">
                    {n['tag']} | {n['impact']} <span style="color:#555; font-weight:600;">({n['pub']})</span>
                </div>
                <div style="font-size: 15px; font-weight: 800; color: #111; margin: 3px 0;">
                    <a href="{n['link']}" target="_blank" style="color: #111; text-decoration: none;">{n['title']} ↗</a>
                </div>
                <div style="font-size: 13px; font-weight: 700; color: {n['color']};">
                    🎯 Effect: {n['effect']}
                </div>
            </div>
            """, unsafe_allow_html=True)
# ==========================================
# MAIN APP TITLE & GEETA MAHAMANTRAS
# ==========================================
st.markdown("""
<div style="text-align: center; background: linear-gradient(90deg, #004D40, #1B5E20, #2E7D32); padding: 18px; border-radius: 15px; border: 3px solid #FFD700; margin-bottom: 18px;">
    <h1 style="color: #FFD700; font-size: 38px; font-weight: 900; margin: 0;">📊 Pritika's Pro Trading Tracker</h1>
</div>
<div style="text-align: center; background: linear-gradient(90deg, #FFD700, #FF8C00); padding: 18px; border-radius: 15px; border: 3px solid #8B0000; margin-bottom: 20px;">
    <h1 style="color: #800000; font-size: 40px; font-weight: 900; margin: 0;">🕉️ गीता के ३ महामंत्र 🕉️</h1>
    <p style="color: #1a1a1a; font-size: 20px; font-weight: bold; margin: 5px 0 0 0;">(Trader's Mindset)</p>
</div>
""", unsafe_allow_html=True)

with st.popover("🏹 १. वीतरागभयक्रोधः (Na Lalach, Na Darr, Na Gussa)", use_container_width=True):
    st.markdown("**🎯 Trading Meaning:** Lalach, Darr aur Gussa trading ke sabse bade dushman hain. Inse mukt hokar apne pre-marked zones par strict discipline ke sath trade execute karein.")
with st.popover("⚖️ २. कर्मण्येवाधिकारस्ते (Mera kaam sirf Rule follow karna hai...)", use_container_width=True):
    st.markdown("**🎯 Trading Meaning:** Aapka control sirf rules follow karne aur risk management par hai. Profit market ka prasad hai, aap sirf apne process par dhyan dein.")
with st.popover("⚔️ ३. युद्धाय कृतनिश्चयः (Ek Yoddha ki tarah bina emotions ke...)", use_container_width=True):
    st.markdown("**🎯 Trading Meaning:** Market ek jang ka maidan hai. Profit aur loss dono ko barabar accept karte hue bina kisi emotional baggage ke apne setup ka wait karein.")

st.markdown("""
<div style="background: linear-gradient(90deg, #E8F5E9, #C8E6C9); padding: 16px 20px; border-radius: 12px; border: 2px solid #2E7D32; margin: 15px 0; text-align: center;">
    <p style="color: #1B5E20; font-size: 20px; font-weight: 800; margin: 0;">✨ "Main Pritika Veer, apne in trading rules ka 100% palan karungi. Capital ko bachana mera pehla dharam hai, aur profit banana doosra."</p>
</div>
""", unsafe_allow_html=True)

# QUICK LINKS
st.markdown("""
<div style="background: linear-gradient(90deg, #00695C, #00897B); padding: 12px 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 15px;">
    <h3 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0;">🔗 Pritika's Master Tools</h3>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.link_button("📰 Open Veer Market News", "https://veer-market-news.streamlit.app", use_container_width=True)
with col2:
    st.link_button("🔎 Open Veer Master Scanner", "https://trading-scanner--veer-crty7rxlsxven92q2buuiy.streamlit.app/", use_container_width=True)
    st.link_button("🌟 Open Market Breath Engine", "https://colab.research.google.com/drive/1ds5WtQaIqTkKUeqGPGXQSB9ZZLxmG_fk?usp=sharing", use_container_width=True)

pm1 = pm2 = pm3 = pm4 = False
lm1 = lm2 = lm3 = lm4 = False

# ==========================================
# STAGE 1: PRE-MARKET ROUTINE
# ==========================================
if "1" in allowed_stages:
    st.write("")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1565C0, #1E88E5); padding: 14px 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 15px;">
        <h3 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0;">🌙 STAGE 1: Pre-Market & Data Analysis</h3>
    </div>
    """, unsafe_allow_html=True)
    pm1 = st.checkbox("1. FII/DII Data & Option Chain: Maine Veer News App mein aaj ka data analyze kar liya hai.")
    if pm1:
        st.warning("📌 IMP NOTE: Dhyan rahe! Agar FII aur DII dono Futures bech rahe hain, toh Call (CE) lene mein jaldbaazi na karein. Trend ke sath chalein.")
    pm2 = st.checkbox("2. Zone Marking: 'Smart Structure & Liquidity' se zones mark kar liye hain.")
    if pm2:
        st.info("📌 IMP NOTE: Fibonacci 0.618 level aur Gann ratios ko chart par cross-verify zaroor karein. Zone ke bahar NO ENTRY.")
    pm3 = st.checkbox("3. Global Cues & Pre-Open: Gift Nifty aur 9:08 AM ka settlement dekh liya hai.")
    pm4 = st.checkbox("4. Tech Ready: Veer Master Scanner aur Dhan Power Scalper login karke ready hain.")

# ==========================================
# STAGE 1.5: MASTER POWER SUMMARY
# ==========================================
if "1.5" in allowed_stages:
    st.write("")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #6A1B9A, #8E24AA); padding: 14px 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.15);">
        <h3 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0;">
            🧠 STAGE 1.5: Master Power Summary
        </h3>
        <p style="color: #F3E5F5; font-size: 16px; margin: 4px 0 0 0;">
            Apne teeno tools ka result yahan dalein aur aaj ka 'Power Note' banayein:
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚡ Generate Today's Trading Power Note", expanded=True):
        s1, s2, s3 = st.columns(3)
        with s1:
            fii_data = st.selectbox("1. Veer News (FII/DII)", ["Select...", "Bullish (Dono Buy)", "Bearish (Dono Sell)", "Mixed (Takkar)"])
        with s2:
            scanner_data = st.selectbox("2. Master Scanner", ["Select...", "CE (Long Setup)", "PE (Short Setup)", "No Clear Setup"])
        with s3:
            breath_data = st.selectbox("3. Market Breath", ["Select...", "Positive (+)", "Negative (-)", "Neutral"])
        
        if st.button("🔥 Generate Power Note"):
            if fii_data == "Select..." or scanner_data == "Select..." or breath_data == "Select...":
                st.error("Kripya teeno tools ka result select karein!")
            elif fii_data == "Bullish (Dono Buy)" and scanner_data == "CE (Long Setup)" and breath_data == "Positive (+)":
                st.success("🚀 **POWER NOTE (HIGH CONVICTION):** Teeno tools ek hi disha (BULLISH) mein ishara kar rahe hain! Aaj apne Zone par aate hi NORMAL/FULL quantity ke sath Call (CE) ka trade lein. Trend aapka dost hai.")
            elif fii_data == "Bearish (Dono Sell)" and scanner_data == "PE (Short Setup)" and breath_data == "Negative (-)":
                st.error("📉 **POWER NOTE (HIGH CONVICTION):** Teeno tools (BEARISH) ishara kar rahe hain! Aaj bounce aane par apne Zone se NORMAL/FULL quantity ke sath Put (PE) ka trade lein. Market weak hai.")
            elif fii_data == "Mixed (Takkar)" or breath_data == "Neutral" or scanner_data == "No Clear Setup":
                st.warning("⚠️ **POWER NOTE (CAUTION):** Data aapas mein match nahi kar raha hai! Market confused hai aur Trapping (SL Hunting) ho sakti hai. Aaj ya toh TRADE NA LEIN, ya sirf HALF (Aadhi) Quantity mein trade karein.")
            else:
                st.info("⚖️ **POWER NOTE (WAIT & WATCH):** Tools ek dusre ke khilaf (opposite) bol rahe hain. Aise din option buyer ka paisa zero hota hai. Jab tak Data ek taraf na mude, apne haath baandh kar rakhein!")

# ==========================================
# STAGE 2: LIVE MARKET ROUTINE & SCORE
# ==========================================
if "2" in allowed_stages:
    st.write("")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #B71C1C, #D84315); padding: 14px 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 15px;">
        <h3 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0;">🎯 STAGE 2: Live Market Entry</h3>
    </div>
    """, unsafe_allow_html=True)
    lm1 = st.checkbox("Rule 1: Trade strictly mere pre-marked 'ZONE' ke andar aa gaya hai (No FOMO).")
    lm2 = st.checkbox("Rule 2: Entry lene se pehle maine fix Stop Loss (SL) aur Target soch liya hai.")
    lm3 = st.checkbox("Rule 3: Aaj ki Max 3 Trades ki limit abhi bachi hui hai.")
    lm4 = st.checkbox("Rule 4: Main bina kisi Revenge ke, bilkul shant dimaag se trade le rahi hoon.")

    tasks = [pm1, pm2, pm3, pm4, lm1, lm2, lm3, lm4] if "1" in allowed_stages else [lm1, lm2, lm3, lm4]
    percentage = int((sum(tasks) / len(tasks)) * 100)

    st.progress(percentage)
    if percentage == 100:
        st.success("🟢 100% APPROVED: Sab kuch perfect hai. Aap apna trade execute kar sakti hain!")
        st.balloons()
    else:
        st.error(f"🔴 DO NOT TRADE! Abhi {len(tasks) - sum(tasks)} rules check karna bache hain.")

# ==========================================
# STAGE 3: TARGET ENFORCER & TAX CALCULATOR
# ==========================================
if "3" in allowed_stages:
    st.write("")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #004D40, #00796B); padding: 14px 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 12px;">
        <h3 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0;">🛡️ STAGE 3: Target Enforcer & Position Sizing</h3>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("🧮 Calculate Safe Lots, Exact Taxes & Target", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            risk_amount = st.number_input("Max Loss (₹)", min_value=100, value=1000, step=100)
            sl_points = st.number_input("Stop Loss (Points)", min_value=1, value=20, step=1)
        with c2:
            lot_size = st.number_input("Current Lot Size", min_value=1, value=15, step=1)
            buy_price = st.number_input("Option Buy Price", min_value=1, value=300, step=1)
        if st.button("Calculate Exact Tax & Target"):
            ideal_qty = int(risk_amount / sl_points)
            safe_lots = ideal_qty // lot_size
            final_qty = safe_lots * lot_size
            if safe_lots > 0:
                target_points = sl_points * 2
                sell_price = buy_price + target_points
                total_turnover = (buy_price * final_qty) + (sell_price * final_qty)
                total_taxes = round(40 + (sell_price * final_qty * 0.001) + (total_turnover * 0.0003503) + ((40 + (total_turnover * 0.0003503)) * 0.18), 2)
                net_profit = round((target_points * final_qty) - total_taxes, 2)
                st.info(f"✅ Safe Limit: **{safe_lots} Lots** (**{final_qty} Qty**) | Max Loss: **₹{risk_amount}**")
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("Brokerage + Taxes", f"₹{total_taxes}")
                bc2.metric("Target (1:2)", f"₹{sell_price}")
                bc3.metric("Net Profit", f"₹{net_profit}")
            else:
                st.error("🚨 DO NOT TRADE! Stop Loss aapke Risk limit se bada hai.")

# ==========================================
# STAGE 4: MARKET MAUSAM & DIARY
# ==========================================
if "4" in allowed_stages:
    st.write("")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #0277BD, #00ACC1); padding: 14px 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 15px;">
        <h3 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0;">🌤️ STAGE 4: Market Mausam & Emotion Tracker</h3>
    </div>
    """, unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        weather = st.radio("Market Direction:", ["☀️ Clear (Strong Trend)", "🌫️ Foggy (Sideways)", "🌧️ Stormy (Volatile)"])
    with col4:
        with st.form("trade_journal"):
            trade_pnl = st.number_input("Trade ka PnL (₹)", value=0)
            reason = st.selectbox("Reason:", ["Rule Followed", "FOMO", "Revenge", "Boredom"])
            if st.form_submit_button("💾 Save Trade Record"):
                st.success(f"Saved! PnL: ₹{trade_pnl} ({reason})")

# ==========================================
# STAGE 5: LIVE TRADE SCREEN & VOICE RECORDER
# ==========================================
if "5" in allowed_stages:
    st.write("")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #880E4F, #C2185B); padding: 14px 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.15);">
        <h3 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0;">
            🎥 STAGE 5: Live Trade Screen & Voice Recorder
        </h3>
        <p style="color: #FCE4EC; font-size: 16px; margin: 4px 0 0 0;">
            Apni pasand ka Audio Mode chunein (Sirf Mic, Sirf Computer, ya Dono Ek Sath) aur Live Trade record karein:
        </p>
    </div>
    """, unsafe_allow_html=True)

    components.html("""
    <div style="background: linear-gradient(135deg, #E8F5E9, #FFF8E1); border: 2px solid #2E7D32; border-radius: 14px; padding: 18px; text-align: center; font-family: sans-serif; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">
        <div style="margin-bottom: 14px;">
            <div style="font-size: 17px; font-weight: 800; color: #1B5E20; margin-bottom: 8px;">
                🎧 Step 1: Aawaz (Audio) Ka Option Chunein:
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; max-width: 620px; margin: 0 auto;">
                <label style="background: #FFFFFF; border: 2px solid #2E7D32; border-radius: 10px; padding: 10px; cursor: pointer; font-weight: bold; color: #1B5E20; font-size: 15px; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <input type="radio" name="audioMode" value="both" checked style="transform: scale(1.2);">
                    🎙️+💻 Dono Ek Sath (Mic + PC)
                </label>
                <label style="background: #FFFFFF; border: 2px solid #1565C0; border-radius: 10px; padding: 10px; cursor: pointer; font-weight: bold; color: #0D47A1; font-size: 15px; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <input type="radio" name="audioMode" value="mic" style="transform: scale(1.2);">
                    🎙️ Sirf Meri Aawaz (Mic Only)
                </label>
                <label style="background: #FFFFFF; border: 2px solid #6A1B9A; border-radius: 10px; padding: 10px; cursor: pointer; font-weight: bold; color: #4A148C; font-size: 15px; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <input type="radio" name="audioMode" value="system" style="transform: scale(1.2);">
                    💻 Sirf Computer Ki Aawaz
                </label>
                <label style="background: #FFFFFF; border: 2px solid #757575; border-radius: 10px; padding: 10px; cursor: pointer; font-weight: bold; color: #424242; font-size: 15px; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <input type="radio" name="audioMode" value="none" style="transform: scale(1.2);">
                    🔇 Bina Aawaz (Only Video)
                </label>
            </div>
        </div>

        <div id="status" style="font-size: 16px; font-weight: bold; color: #1B5E20; background: #C8E6C9; padding: 8px 12px; border-radius: 8px; margin-bottom: 14px;">
            🟢 Ready to Record (Upar Aawaz chunein aur Start Recording dabayein)
        </div>
        
        <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 10px;">
            <button id="startBtn" onclick="startRecording()" style="background: linear-gradient(90deg, #1B5E20, #43A047); color: white; border: 2px solid #FFD700; border-radius: 10px; padding: 12px 22px; font-size: 17px; font-weight: bold; cursor: pointer; box-shadow: 0px 3px 6px rgba(0,0,0,0.2);">
                🔴 Start Recording
            </button>
            <button id="stopBtn" onclick="stopRecording()" style="background: linear-gradient(90deg, #B71C1C, #E53935); color: white; border: 2px solid #FFD700; border-radius: 10px; padding: 12px 22px; font-size: 17px; font-weight: bold; cursor: pointer; box-shadow: 0px 3px 6px rgba(0,0,0,0.2);">
                ⏹️ Stop Recording
            </button>
            <a id="downloadLink" style="display: none; background: linear-gradient(90deg, #0D47A1, #1976D2); color: white; border: 2px solid #FFD700; border-radius: 10px; padding: 12px 22px; font-size: 17px; font-weight: bold; text-decoration: none; box-shadow: 0px 3px 6px rgba(0,0,0,0.2);">
                💾 Download Trade Video
            </a>
        </div>

        <video id="preview" autoplay muted playsinline style="width: 100%; max-height: 200px; border-radius: 10px; border: 2px solid #1B5E20; display: none; background: #000; margin-top: 8px;"></video>
    </div>

    <script>
    const store = window.parent || window;

    function bindActiveRecording() {
        const statusEl = document.getElementById('status');
        const preview = document.getElementById('preview');
        if (store._pritikaRecorder) store._pritikaRecorder.onstop = function() { finalizeRecording(); };
        if (store._pritikaDisplayStream && store._pritikaDisplayStream.getVideoTracks().length > 0) {
            store._pritikaDisplayStream.getVideoTracks()[0].onended = function() { stopRecording(); };
        }
        if (store._pritikaRecorder && store._pritikaRecorder.state === 'recording') {
            statusEl.innerHTML = store._pritikaStatusText || '🔴 LIVE RECORDING CHALU HAI...';
            statusEl.style.color = '#B71C1C'; statusEl.style.background = '#FFCDD2';
            if (store._pritikaDisplayStream) { preview.srcObject = store._pritikaDisplayStream; preview.style.display = 'block'; }
        }
    }

    function finalizeRecording() {
        const statusEl = document.getElementById('status');
        const preview = document.getElementById('preview');
        const downloadLink = document.getElementById('downloadLink');
        if (store._pritikaChunks && store._pritikaChunks.length > 0) {
            const blob = new Blob(store._pritikaChunks, { type: 'video/webm' });
            const url = URL.createObjectURL(blob);
            const now = new Date().toISOString().slice(0,19).replace(/[:T]/g, "-");
            if (downloadLink) {
                downloadLink.href = url; downloadLink.download = `Pritika_Trade_Recording_${now}.webm`;
                downloadLink.style.display = 'inline-block'; downloadLink.click();
            }
            if (statusEl) {
                statusEl.innerHTML = '✅ Recording Complete & Video Downloaded!';
                statusEl.style.color = '#0D47A1'; statusEl.style.background = '#BBDEFB';
            }
        } else if (statusEl) {
            statusEl.innerHTML = '⏹️ Recording Ruk Gayi Hai.';
            statusEl.style.color = '#1B5E20'; statusEl.style.background = '#C8E6C9';
        }
        if (preview) preview.style.display = 'none';
    }

    async function startRecording() {
        const statusEl = document.getElementById('status');
        const modeEl = document.querySelector('input[name="audioMode"]:checked');
        const mode = modeEl ? modeEl.value : 'both';
        try {
            if (store._pritikaRecorder && store._pritikaRecorder.state === 'recording') stopRecording();
            const mediaDevices = (store.navigator && store.navigator.mediaDevices) ? store.navigator.mediaDevices : navigator.mediaDevices;
            let micStream = null;
            if (mode === 'mic' || mode === 'both') {
                try { micStream = await mediaDevices.getUserMedia({ audio: true, video: false }); }
                catch (micErr) { if (mode === 'mic') { statusEl.innerHTML = '⚠️ Mic Permission Denied!'; return; } }
            }
            const displayStream = await mediaDevices.getDisplayMedia({ video: { cursor: "always" }, audio: (mode === 'system' || mode === 'both') });
            const hasMic = micStream && micStream.getAudioTracks().length > 0;
            const hasSys = displayStream && displayStream.getAudioTracks().length > 0;
            const tracks = [...displayStream.getVideoTracks()];

            if (hasMic && hasSys) {
                const AudioCtx = store.AudioContext || store.webkitAudioContext || window.AudioContext;
                const audioCtx = new AudioCtx();
                if (audioCtx.state === 'suspended') await audioCtx.resume();
                const dest = audioCtx.createMediaStreamDestination();
                audioCtx.createMediaStreamSource(displayStream).connect(dest);
                audioCtx.createMediaStreamSource(micStream).connect(dest);
                tracks.push(...dest.stream.getAudioTracks());
                store._pritikaAudioCtx = audioCtx;
                store._pritikaStatusText = '🔴 LIVE RECORDING: 🎙️ Meri Aawaz + 💻 Computer Aawaz DONO ON Hain!';
            } else if (hasMic) {
                tracks.push(...micStream.getAudioTracks());
                store._pritikaStatusText = '🔴 LIVE RECORDING: 🎙️ Meri Aawaz ON Hai';
            } else if (hasSys) {
                tracks.push(...displayStream.getAudioTracks());
                store._pritikaStatusText = '🔴 LIVE RECORDING: 💻 Sirf Computer Ki Aawaz Record Ho Rahi Hai!';
            } else {
                store._pritikaStatusText = '🔴 LIVE RECORDING: 🔇 Bina Aawaz (Only Video) Record Ho Raha Hai!';
            }

            const combinedStream = new MediaStream(tracks);
            store._pritikaDisplayStream = displayStream; store._pritikaMicStream = micStream;
            store._pritikaStream = combinedStream; store._pritikaChunks = [];
            let options = { mimeType: 'video/webm;codecs=vp8,opus' };
            if (!MediaRecorder.isTypeSupported(options.mimeType)) options = { mimeType: 'video/webm' };
            const recorder = new MediaRecorder(combinedStream, options);
            store._pritikaRecorder = recorder;
            recorder.ondataavailable = function(e) { if (e.data && e.data.size > 0) store._pritikaChunks.push(e.data); };
            bindActiveRecording();
            recorder.start(1000);
            document.getElementById('downloadLink').style.display = 'none';
        } catch (err) {
            statusEl.innerHTML = '⚠️ Screen select karke Share dabayein!';
            statusEl.style.color = '#E65100'; statusEl.style.background = '#FFE0B2';
        }
    }

    function stopRecording() {
        try {
            if (store._pritikaRecorder) {
                store._pritikaRecorder.onstop = function() { finalizeRecording(); };
                if (store._pritikaRecorder.state !== 'inactive') store._pritikaRecorder.stop();
                else finalizeRecording();
            } else finalizeRecording();
            if (store._pritikaStream) store._pritikaStream.getTracks().forEach(t => t.stop());
            if (store._pritikaDisplayStream) store._pritikaDisplayStream.getTracks().forEach(t => t.stop());
            if (store._pritikaMicStream) store._pritikaMicStream.getTracks().forEach(t => t.stop());
            if (store._pritikaAudioCtx && store._pritikaAudioCtx.state !== 'closed') store._pritikaAudioCtx.close();
        } catch (e) { finalizeRecording(); }
    }

    bindActiveRecording();
    </script>
    """, height=430)

# ==============================================================================
# 🛡️ STAGE 6: ULTIMATE RETAILER SHIELD (AUTO-UNLOCKS ONLY AT 100% SCORE)
# ==============================================================================
import io
import csv

st.write("")
score_ready = (locals().get("percentage", 0) == 100)

if not score_ready:
    # LOCKED STATE (Jab tak upar ki sabhi conditions poori na hon)
    st.markdown("""
    <div style="background: #ECEFF1; padding: 16px 20px; border-radius: 12px; border: 2px dashed #78909C; text-align: center; margin-top: 10px;">
        <h3 style="color: #455A64; font-size: 23px; font-weight: 800; margin: 0;">
            🔒 STAGE 6: Ultimate Retailer Shield (LOCKED)
        </h3>
        <p style="color: #607D8B; font-size: 16px; font-weight: bold; margin: 6px 0 0 0;">
            ⚠️ Pehle upar ke sabhi Rules (Stage 1 & Stage 2) tick karke 100% Discipline Score poora karein — tabhi yeh Shield Highlight aur Unlock hoga!
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # UNLOCKED & HIGHLIGHTED STATE (100% Rules Verified!)
    st.markdown("""
    <div style="background: linear-gradient(90deg, #FF6F00, #FFA000, #FFD600); padding: 16px 20px; border-radius: 14px; border: 3px solid #1B5E20; box-shadow: 0px 0px 18px rgba(255, 160, 0, 0.65); margin-top: 10px; margin-bottom: 12px;">
        <h3 style="color: #1B5E20; font-size: 26px; font-weight: 900; margin: 0; text-align: center;">
            🌟🛡️ STAGE 6: RETAILER SHIELD UNLOCKED & ACTIVE! 🛡️🌟
        </h3>
        <p style="color: #3E2723; font-size: 16px; font-weight: 800; margin: 5px 0 0 0; text-align: center;">
            ✅ 100% Conditions Verified! Niche Dropdown kholkar Live Action Alert lein:
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚡ OPEN 4-IN-1 RETAILER SHIELD DROPDOWN (Live Alerts)", expanded=True):
        shield_mode = st.selectbox(
            "🔽 Apni Live Situation Chunein (Action Alert ke liye):",
            [
                "1. ⚠️ Option Trap & Live Time Alert (Entry se pehle)",
                "2. 🎯 Live Trailing SL Step-Guide (Trade chalne ke baad)",
                "3. 🧊 15-Min Cooling-Off Lock & Daily Kill-Switch (Loss hone par)",
                "4. 📊 Drawdown Recovery Meter & Trade Excel Download"
            ]
        )

        st.markdown("---")

        # --- FEATURE 1: OPTION TRAP & LIVE TIME ALERT ---
        if shield_mode.startswith("1."):
            now_ist = datetime.now(IST)
            curr_time = now_ist.strftime("%I:%M %p")
            st.info(f"🕒 Abhi ka Live Time (IST): **{curr_time}**")

            t_col1, t_col2 = st.columns(2)
            with t_col1:
                day_type = st.selectbox("Aaj ka Din:", ["Normal Day", "Expiry Day (Hero-Zero Trap)"])
            with t_col2:
                strike_type = st.selectbox("Aapka Strike:", ["ITM (In The Money)", "ATM (At The Money)", "OTM (Out of The Money - Sasta)"])

            # Time Trap Check
            hr, mn = now_ist.hour, now_ist.minute
            if (hr == 9 and mn < 30):
                st.warning("🚨 **TIME ALERT (9:15 - 9:30 AM):** Opening Volatility Trap! Pehle 15 minute market ko settle hone dein.")
            elif (hr == 11 and mn >= 30) or (hr == 12) or (hr == 13 and mn <= 30):
                st.error("🚨 **LUNCH TIME TRAP (11:30 AM - 1:30 PM):** Market sideways aur Theta Decay tez hota hai. Naya Option Buy AVOID karein!")
            else:
                st.success("✅ **TIME SAFE:** Market momentum window active hai.")

            # Strike & Expiry Check
            if day_type.startswith("Expiry") and strike_type.startswith("OTM"):
                st.error("🛑 **BIG TRAP ALERT:** Expiry Day par OTM Option 90% time ZERO ho jata hai! Turant cancel karein aur sirf **ITM ya ATM** chunein.")
            elif strike_type.startswith("OTM"):
                st.warning("⚠️ **CAUTION:** OTM mein Theta Decay zyada hota hai. Safe trading ke liye ATM/ITM best hai.")
            else:
                st.success("🟢 **GREEN SIGNAL:** Aapka Strike safe hai. Apne pre-marked Zone par strict SL ke sath trade lein!")

        # --- FEATURE 2: LIVE TRAILING SL STEP-GUIDE ---
        elif shield_mode.startswith("2."):
            st.markdown("**Trade mein ghusne ke baad Darr aur Lalach khatam karne ka Action Plan:**")
            tr1, tr2 = st.columns(2)
            with tr1:
                t_buy = st.number_input("Option Buy Price (₹):", min_value=1.0, value=200.0, step=5.0, key="tr_buy")
            with tr2:
                t_sl = st.number_input("Stop Loss Points:", min_value=1.0, value=20.0, step=1.0, key="tr_sl")

            sl_price = t_buy - t_sl
            step1_price = t_buy + t_sl          # 1:1
            step2_price = t_buy + (t_sl * 1.5)  # 1:1.5
            final_tgt = t_buy + (t_sl * 2.0)    # 1:2

            st.error(f"🛑 **Hard Stop Loss:** ₹{sl_price:.1f} (Iske niche 1 second bhi nahi rukna hai!)")
            st.info(f"🔹 **Step 1 (Price ₹{step1_price:.1f} aane par - 1:1):** Apna SL uthakar **Buy Price (₹{t_buy:.1f})** par le aayein. Ab aapka Loss ZERO!")
            st.warning(f"🔸 **Step 2 (Price ₹{step2_price:.1f} aane par - 1:1.5):** **50% Quantity Book** karein aur baki ka SL ₹{step1_price:.1f} par trail karein.")
            st.success(f"🏆 **Step 3 (Final Target ₹{final_tgt:.1f} - 1:2):** Poora Profit book karein aur screen se door hat jayein!")

        # --- FEATURE 3: 15-MIN COOLING-OFF LOCK & DAILY KILL-SWITCH ---
        elif shield_mode.startswith("3."):
            k1, k2 = st.columns(2)
            with k1:
                max_daily_loss = st.number_input("Aaj ki Max Loss Limit (₹):", min_value=500, value=2000, step=500)
                curr_loss = st.number_input("Abhi tak ka Total Loss (₹):", min_value=0, value=0, step=100)
            with k2:
                trades_done = st.number_input("Aaj kitne Trades ho chuke hain?", min_value=0, max_value=10, value=0, step=1)

            if curr_loss >= max_daily_loss or trades_done >= 3:
                st.error("🚨🛑 **DAILY KILL-SWITCH ACTIVATED! AAJ KI DUKAAN BAND!** 🛑🚨\n\nAapki aaj ki Loss Limit ya 3 Trades ki limit poori ho chuki hai. Broker terminal turant **LOGOUT** karein. Ab jo bhi trade lengi woh Revenge Trade hoga!")
            else:
                st.success(f"✅ Aap abhi safe limit mein hain (Bache huye trades: {3 - trades_done}).")

            st.markdown("**Agar abhi-abhi SL Hit hua hai, to Revenge se bachne ke liye 15-Min Lock on karein:**")
            components.html("""
            <div style="background:#FFEBEE; border:2px solid #C62828; border-radius:12px; padding:14px; text-align:center; font-family:sans-serif;">
                <div id="coolTimer" style="font-size:28px; font-weight:900; color:#B71C1C; margin-bottom:8px;">🧊 15:00</div>
                <button onclick="startCool()" style="background:#C62828; color:white; border:none; border-radius:8px; padding:10px 20px; font-size:16px; font-weight:bold; cursor:pointer;">
                    🚨 SL Hit Hua — Start 15-Min Cooling Lock
                </button>
                <p id="coolMsg" style="color:#880E4F; font-weight:bold; margin:8px 0 0 0; font-size:14px;">
                    Click karte hi 15 minute tak chart mat dekhein, paani piyen aur shant ho jayein.
                </p>
            </div>
            <script>
            let coolInt;
            function startCool() {
                clearInterval(coolInt);
                let sec = 900;
                document.getElementById('coolMsg').innerText = "🛑 LOCK ACTIVE! 15 minute tak koi naya order mat lagayein!";
                coolInt = setInterval(() => {
                    sec--;
                    let m = String(Math.floor(sec / 60)).padStart(2, '0');
                    let s = String(sec % 60).padStart(2, '0');
                    document.getElementById('coolTimer').innerText = "🧊 " + m + ":" + s;
                    if (sec <= 0) {
                        clearInterval(coolInt);
                        document.getElementById('coolTimer').innerText = "✅ 00:00 (Mind Calm!)";
                        document.getElementById('coolMsg').innerText = "Ab aap shant dimaag se naya setup dekh sakti hain.";
                    }
                }, 1000);
            }
            </script>
            """, height=155)

        # --- FEATURE 4: DRAWDOWN RECOVERY METER & EXCEL DOWNLOAD ---
        elif shield_mode.startswith("4."):
            st.markdown("**📉 Capital Recovery Math (Drawdown Meter):**")
            r1, r2 = st.columns(2)
            with r1:
                total_cap = st.number_input("Total Trading Capital (₹):", min_value=1000, value=50000, step=5000)
            with r2:
                lost_cap = st.number_input("Abhi tak ka Loss (₹):", min_value=0, value=5000, step=500)

            if lost_cap >= total_cap:
                st.error("🚨 Capital khatam ho chuka hai! Pehle paper trading se practice karein.")
            elif lost_cap > 0:
                rem_cap = total_cap - lost_cap
                loss_pct = (lost_cap / total_cap) * 100
                req_profit_pct = (lost_cap / rem_cap) * 100
                m1, m2, m3 = st.columns(3)
                m1.metric("Capital Loss %", f"{loss_pct:.1f}%")
                m2.metric("Recovery ke liye Profit %", f"{req_profit_pct:.1f}%")
                m3.metric("Bacha hua Capital", f"₹{rem_cap}")
                if loss_pct >= 20:
                    st.error("⚠️ **ALERT:** 20% se zyada Drawdown hai! Agle 5 trades mein apni **Quantity AADHI (50%)** kar dein.")
                else:
                    st.info("✅ Normal Drawdown hai. Apne fix Lot Size aur rules par tike rahein.")
            else:
                st.success("🌟 Zero Loss! Aapka poora capital safe hai.")

            st.markdown("---")
            st.markdown("**📥 Aaj ka Trade Report Excel (CSV) Download Karein:**")
            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf)
            writer.writerow(["Date", "Total Capital", "Loss", "Discipline Score", "Status"])
            writer.writerow([datetime.now(IST).strftime("%d-%m-%Y"), total_cap, lost_cap, "100%", "Rules Followed"])
            st.download_button(
                label="💾 Download Today's Shield Report (Excel/CSV)",
                data=csv_buf.getvalue(),
                file_name=f"Pritika_Shield_Report_{datetime.now(IST).strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
# ==============================================================================
# ⚖️ SEBI GUIDELINES & PERMANENT FOOTER DISCLAIMER
# ==============================================================================
st.markdown("---")
st.markdown("""
<div style="background: #F5F5F5; border-top: 3px solid #B71C1C; border-radius: 10px; padding: 14px 18px; font-size: 13px; color: #333; line-height: 1.6;">
    <b style="color: #B71C1C; font-size: 14px;">⚖️ SEBI MANDATORY DISCLAIMER & GUIDELINES:</b><br>
    • <b>Educational Purpose Only:</b> Pritika's Pro Trading Tracker ek personal trading journal, checklist aur risk-management utility hai. Hum SEBI-registered Research Analyst (RA) ya Investment Advisor (IA) nahi hain.<br>
    • <b>No Tips / No Guaranteed Returns:</b> Is app par dikhaya gaya koi bhi data, news radar, ya power note buy/sell recommendation nahi hai.<br>
    • <b>SEBI F&O Risk Disclosure:</b> Derivatives trading mein high risk hota hai. SEBI ki report ke anusar 90% se zyada retail F&O traders loss karte hain. Apne risk appetite ke hisab se hi trade karein.
</div>
""", unsafe_allow_html=True)
