import re
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import os

# Membaca gambar logo secara aman
try:
    logo = Image.open("logo.jpg") # Sesuaikan dengan nama file gambar Anda di GitHub (misal: logo.jpg / logo.png)
except Exception as e:
    logo = None

# 1. MENYIAPAN MEMORI STATUS SIDEBAR
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

# 2. ATUR KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Tory Bot",
    page_icon=logo,
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.sidebar_open else "collapsed"
)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("⚠️ Environment variable GEMINI_API_KEY belum ditemukan di Advanced Settings.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ── Session state Chat ──────────────────────────────────────────
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None
if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 0

def new_chat():
    cid = st.session_state.chat_counter
    st.session_state.chat_counter += 1
    st.session_state.chats[cid] = {"title": f"Chat {cid + 1}", "messages": []}
    st.session_state.active_chat = cid

if st.session_state.active_chat is None:
    new_chat()


# ═══════════════════════════════════════════════════════════════
#  GREETING DETECTION
# ═══════════════════════════════════════════════════════════════

SAPAAN_KATA = {
    "halo", "hai", "hei", "hay",
    "hi", "hello", "hey", "howdy", "holla",
    "pagi", "siang", "sore", "malam",
    "permisi", "helo",
    "assalamualaikum", "assalamualikum",
    "wa'alaikumsalam", "waalaikumsalam",
}

SAPAAN_FRASA = [
    "selamat pagi", "selamat siang",
    "selamat sore", "selamat malam",
    "apa kabar", "apa kbr",
    "halo tory", "hai tory", "hi tory",
]

def cek_sapaan(teks: str) -> bool:
    t = teks.lower().strip()
    bersih = re.sub(r"[!?.,;:\-]+", " ", t).strip()
    kata_list = bersih.split()

    if len(kata_list) > 6:
        return False

    for kata in kata_list:
        if kata in SAPAAN_KATA:
            return True

    for frasa in SAPAAN_FRASA:
        if frasa in t:
            return True

    return False


def buat_prompt(user_input: str, kelas: str) -> str:
    if cek_sapaan(user_input):
        return f"""
Kamu adalah Tory Bot, asisten belajar yang super ramah dan menyenangkan.
Target pengguna: Siswa {kelas}.

Pengguna baru saja menyapamu dengan: "{user_input}"

Tugasmu:
1. Balas sapaannya dengan hangat dan antusias — jika ada kata waktu (pagi/siang/sore/malam), sesuaikan balasannya.
2. Perkenalkan dirimu sebagai **Tory Bot**, asisten belajar pintar khusus siswa {kelas}.
3. Sebutkan 2-3 contoh mata pelajaran atau topik yang bisa kamu bantu (misal: Matematika, IPA, IPS, Bahasa Indonesia, dll).
4. Tutup dengan kalimat ajakan yang hangat supaya mereka mau langsung bertanya.

Panduan gaya:
- Nada: ceria, hangat, bersemangat — seperti kakak yang baik hati
- Panjang: 4-5 kalimat saja, tidak bertele-tele
- Wajib pakai emoji yang relevan dan menarik 🎉📚✨
"""
    else:
        return (
            f"Kamu adalah Tory Bot, asisten belajar yang ramah dan menyenangkan.\n"
            f"Target pengguna: Siswa {kelas}\n"
            f"Gunakan bahasa yang sederhana, mudah dipahami, dan menarik.\n"
            f"Berikan penjelasan yang singkat namun jelas.\n\n"
            f"Pertanyaan: {user_input}"
        )

# ═══════════════════════════════════════════════════════════════

# 3. MENGHITUNG POSISI INPUT SECARA DINAMIS (Untuk PC)
posisi_kiri_input = "58%" if st.session_state.sidebar_open else "50%"

# ── CSS: Light clean theme + RESPONSIVE SCREEN ──────────────────
st.markdown(f"""
<style>

/* ─── Global ─────────────────────────────────────────── */
.stApp {{ background-color: #ffffff; }}
.main .block-container {{
    max-width: 860px;
    padding-top: 1.5rem;
    padding-bottom: 8rem;
    margin: 0 auto;
}}

/* ─── Sidebar ────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: #f0f2f6;
    border-right: 1px solid #e2e4e8;
}}
[data-testid="stSidebar"] * {{ color: #31333f !important; }}

/* ─── Hide Streamlit chrome ──────────────────────────── */
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background-color: transparent !important; }}

/* ─── Chat input fixed bottom (RESPONSIVE) ───────────── */
[data-testid="stChatInput"] {{
    position: fixed;
    bottom: 20px;
    z-index: 1000;
}}

/* Jika layar lebar (PC / Laptop) */
@media (min-width: 992px) {{
    [data-testid="stChatInput"] {{
        width: min(820px, 60%);
        left: {posisi_kiri_input}; 
        transform: translateX(-50%);
    }}
}}

/* Jika layar sedang (Tablet) */
@media (min-width: 768px) and (max-width: 991px) {{
    [data-testid="stChatInput"] {{
        width: 80%;
        left: 50%;
        transform: translateX(-50%);
    }}
}}

/* Jika layar kecil (HP) */
@media (max-width: 767px) {{
    [data-testid="stChatInput"] {{
        width: 90%;
        left: 50%;
        transform: translateX(-50%);
    }}
}}

[data-testid="stChatInput"] textarea {{
    background-color: #ffffff !important;
    color: #31333f !important;
    border: 1px solid #cccccc !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
    font-size: 15px !important;
}}

/* ─── Hide avatars ───────────────────────────────────── */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"],
[data-testid^="stChatMessageAvatar"] {{ display: none !important; }}

/* ─── User bubble ────────────────────────────────────── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
    background-color: #f0f2f6;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
}}

/* ─── Assistant bubble ───────────────────────────────── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
    background-color: #ffffff;
    padding: 14px 0;
    margin: 8px 0;
}}

/* ─── Buttons ────────────────────────────────────────── */
.stButton > button {{
    background-color: #ffffff;
    border: 1px solid #e0e2e6;
    color: #31333f !important;
    border-radius: 8px;
    font-size: 13.5px;
    text-align: left;
    transition: background 0.15s, border 0.15s;
}}
.stButton > button:hover {{
    background-color: #e6e8ef !important;
    border-color: #c4c6cc !important;
}}
button[kind="primary"] {{
    background-color: #e6e8ef !important;
    border: 1px solid #c4c6cc !important;
    font-weight: 600 !important;
    color: #1a1a2e !important;
}}

/* ─── Selectbox ──────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {{
    background-color: #ffffff !important;
    border: 1px solid #cccccc !important;
    border-radius: 8px !important;
    color: #31333f !important;
}}

/* ─── Divider ────────────────────────────────────────── */
hr {{ border-color: #e2e4e8 !important; }}

/* ─── Welcome screen ─────────────────────────────────── */
.tory-welcome {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: 10vh;
    gap: 2px;
}}
.tory-icon-wrap {{
    background-color: #ff6b35;
    border-radius: 20px;
    width: 72px;
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(255,107,53,0.25);
}}
.tory-title {{
    font-size: 40px;
    font-weight: 700;
    color: #1a1a2e;
    letter-spacing: -0.5px;
    margin: 0 0 8px 0;
}}
.tory-sub {{
    font-size: 16px;
    color: #888;
    margin: 0;
}}

/* ─── Markdown text ──────────────────────────────────── */
.stMarkdown p, .stMarkdown li,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    color: #31333f !important;
}}

</style>
""", unsafe_allow_html=True)


# ── SIDEBAR ────────────────────────────────────────────────────
with st.sidebar:
    col_img, col_name = st.columns([1, 3])
    with col_img:
        if logo:
            st.image(logo, width=44)
    with col_name:
        st.markdown(
            "<h3 style='margin:6px 0 0 0; color:#1a1a2e; font-size:20px;'>Tory Bot</h3>",
            unsafe_allow_html=True
        )

    st.caption("Apa yang ingin Anda pelajari hari ini?")
    st.divider()

    if st.button("➕  New Chat", use_container_width=True, key="new_chat_btn"):
        new_chat()
        st.rerun()

    st.selectbox("Jenjang", ["SD", "SMP"], key="kelas")

    st.divider()
    st.markdown(
        "<p style='font-size:12.5px; color:#888; margin:0 0 6px 2px;'>Riwayat Chat</p>",
        unsafe_allow_html=True
    )

    for cid in reversed(list(st.session_state.chats.keys())):
        cdata_s = st.session_state.chats[cid]
        is_active = (cid == st.session_state.active_chat)
        c1, c2 = st.columns([5, 1])
        with c1:
            if st.button(
                f"💬  {cdata_s['title']}",
                key=f"chat_btn_{cid}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.active_chat = cid
                st.rerun()
        with c2:
            if st.button("🗑", key=f"del_{cid}"):
                del st.session_state.chats[cid]
                remaining = list(st.session_state.chats.keys())
                st.session_state.active_chat = remaining[-1] if remaining else None
                if st.session_state.active_chat is None:
                    new_chat()
                st.rerun()


# ── MAIN AREA ──────────────────────────────────────────────────
active   = st.session_state.active_chat
cdata    = st.session_state.chats.get(active, {"title": "", "messages": []})
messages = cdata["messages"]

if not messages:
    st.markdown("""
    <div class="tory-welcome">
        <div class="tory-icon-wrap">💬</div>
        <p class="tory-title">Halo, saya Tory Bot 👋</p>
        <p class="tory-sub">🚀 Asisten belajar yang menyenangkan untuk siswa SD &amp; SMP</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ketik pesan untuk Tory Bot...")

if user_input:
    messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    if len(messages) == 1:
        st.session_state.chats[active]["title"] = (
            user_input[:30] + ("..." if len(user_input) > 30 else "")
        )

    with st.chat_message("assistant"):
        with st.spinner("Tory Bot sedang mengetik..."):

            prompt = buat_prompt(user_input, st.session_state.kelas)

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                answer = response.text
            except Exception as e:
                answer = f"⚠️ Maaf, terjadi kesalahan: {str(e)}"

        st.markdown(answer)

    messages.append({"role": "assistant", "content": answer})
    st.session_state.chats[active]["messages"] = messages
    st.rerun()
