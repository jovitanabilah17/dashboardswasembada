import streamlit as st # Panggil bos besar Streamlit buat bikin UI webnya
import streamlit.components.v1 as components # Buat nyelipin elemen HTML/JS custom nih
import gspread # Modul andalan buat narik data dari Google Sheets
from google.oauth2.service_account import Credentials # Buat urusan login pake service account Google (Biar aman bro)
import pandas as pd # Swiss army knife buat ngolah data tabular (bikin dataframe)
from datetime import datetime, timedelta # Buat ngatur urusan waktu dan tanggal
import json # Buat parsing format JSON
import plotly.express as px # Library visualisasi data (bikin grafik gampang)
import plotly.graph_objects as go # Library grafik juga, tapi ngasih kontrol yang lebih detail/custom
import base64 # Buat ngubah file (kayak gambar) jadi teks biar bisa diselipin di HTML
from pathlib import Path # Buat ngatur path file/folder biar nggak pusing beda OS
import hmac # Buat ngecek keamanan password (nyocokin hash)
import sqlite3 # Database ringan bawaan Python, nggak ribet setup server
import hashlib # Buat ngenkripsi/nge-hash password biar aman
import os # Buat interaksi sama sistem operasi (misal bikin random byte buat salt password)
import time # Buat jeda waktu (delay), biasanya kepake pas mau retry koneksi

# Ngatur tampilan awal halaman web lo
st.set_page_config(
    page_title="Dashboard BRMP - Swasembada Pangan", # Judul tab di browser nih bos
    page_icon="🌾", # Pake emoji padi biar kerasa nuansa pertaniannya
    layout="wide", # Bikin kontennya melebar menuhin layar (nggak kotak di tengah doang)
    initial_sidebar_state="collapsed" # Sidebarnya disembunyiin dari awal biar lega
)

# Kamus default buat ngatur grafik mana aja yang mau ditampilin (default-nya nyala semua)
DEFAULT_CHART_CONFIG = {
    "chart_provinsi": "Bar Chart Jumlah Sasaran Berdasarkan Provinsi",
    "chart_materi": "Pie Chart Persentase Topik Materi",
    "chart_inovasi": "Bar Chart Komponen Inovasi Teknologi",
    "tabel_kabkota": "Tabel Jumlah Sasaran Tercapai Per Kab/Kota",
    "chart_instansi": "Bar Chart Asal Instansi Narasumber",
    "chart_narasumber_pie": "Pie Chart Persentase Asal Narasumber",
    "chart_1": "Line Chart Tren Kegiatan/Peserta",
    "chart_2": "Stacked Bar Komposisi Peserta Perwilayah",
    "chart_3": "Bar Chart Rata-Rata Peserta Per Kegiatan",
}

# Fungsi buat ngubah gambar lokal jadi string base64 biar bisa dimasukin ke tag <img> HTML
def get_base64_image(image_path):
    try: # Coba buka filenya
        with open(image_path, "rb") as img_file: # Buka dengan mode 'read binary'
            return base64.b64encode(img_file.read()).decode() # Ubah ke base64 terus decode ke string
    except: # Kalo gagal (misal file gak ada)
        return "" # Balikin string kosong aja daripada error nge-crash

# Bagian ini buat nyuntikin CSS kustom biar dashboard lo makin glowing & proper! ✨
st.markdown("""
<style>
    /* Ngilangin menu hamburger, tulisan footer, dan header bawaan Streamlit biar keliatan kayak web beneran */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Intinya blok CSS panjang ke bawah ini ngatur warna gradient ijo/oranye, efek bayangan (shadow), 
       nge-set tombol print, dan ngerapiin box-box metrik (KPI) biar enak dipandang mata. */
    .header-container { background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #388E3C 100%); padding: 20px; border-radius: 0px; margin: -60px -70px 30px -70px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); gap: 20px; }
    .header-left { display: flex; align-items: center; gap: 20px; }
    .header-logo { height: 80px; width: auto; margin-left: 20px; }
    .header-logo img { height: 100%; width: auto; object-fit: contain; }
    .header-title { color: white; font-size: 18px; font-weight: bold; text-transform: uppercase; margin: 0; line-height: 1.3; }
    .header-subtitle { color: white; font-size: 14px; margin: 0; }
    .print-button-header { background: rgba(255, 255, 255, 0.16); border: 1px solid rgba(255, 255, 255, 0.45); color: white; text-decoration: none; border-radius: 8px; padding: 10px 16px; font-size: 14px; font-weight: 700; white-space: nowrap; margin-right: 20px; transition: all 0.2s ease; }
    .print-button-header:hover { background: rgba(255, 255, 255, 0.3); border-color: rgba(255, 255, 255, 0.65); color: white; }
    .main-title { text-align: center; color: #2E7D32; font-size: 36px; font-weight: bold; margin: 30px 0 10px 0; text-transform: uppercase; }
    .sub-title { text-align: center; color: #333; font-size: 24px; font-weight: bold; margin: 0 0 30px 0; }
    .section-header { background-color: #A5D6A7; padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 18px; color: #1B5E20; margin: 30px 0 20px 0; text-transform: uppercase; }
    .metric-card-green { background: linear-gradient(135deg, #2E7D32 0%, #388E3C 100%); padding: 20px; border-radius: 8px; text-align: center; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 100%; }
    .metric-card-green .metric-label { font-size: 14px; margin-bottom: 10px; opacity: 0.95; }
    .metric-card-green .metric-value { font-size: 36px; font-weight: bold; line-height: 1; }
    .metric-card-orange { background: linear-gradient(135deg, #F57C00 0%, #FF9800 100%); padding: 20px; border-radius: 8px; text-align: center; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 100%; }
    .metric-card-orange .metric-label { font-size: 14px; margin-bottom: 10px; opacity: 0.95; }
    .metric-card-orange .metric-value { font-size: 36px; font-weight: bold; line-height: 1; }
    .metric-card-yellow { background: linear-gradient(135deg, #F9A825 0%, #FBC02D 100%); padding: 20px; border-radius: 8px; text-align: center; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 100%; }
    .metric-card-yellow .metric-label { font-size: 14px; margin-bottom: 10px; opacity: 0.95; }
    .metric-card-yellow .metric-value { font-size: 36px; font-weight: bold; line-height: 1; }
    .kpi-card { padding: 15px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.15); height: 100%; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s, box-shadow 0.2s; border: 2px solid transparent; }
    .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.2); }
    .kpi-card-green { background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%); border-color: #A5D6A7; }
    .kpi-card-yellow { background: linear-gradient(135deg, #F57F17 0%, #FBC02D 100%); border-color: #FFF59D; }
    .kpi-card-red { background: linear-gradient(135deg, #B71C1C 0%, #E53935 100%); border-color: #EF9A9A; }
    .kpi-title { font-size: 15px; font-weight: 700; margin-bottom: 8px; line-height: 1.2; text-transform: uppercase; opacity: 0.95; }
    .kpi-actual { font-size: 32px; font-weight: 800; margin: 5px 0; line-height: 1; }
    .kpi-target { font-size: 13px; opacity: 0.85; margin-bottom: 15px; font-weight: 500; }
    .kpi-score-box { background: rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 8px; margin-top: auto; display: flex; justify-content: center; align-items: center; gap: 8px; backdrop-filter: blur(5px); }
    .kpi-score-text { font-size: 22px; font-weight: bold; }
    .update-header { background: linear-gradient(135deg, #F57C00 0%, #FF9800 100%); padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 18px; color: white; margin: 30px 0 20px 0; text-transform: uppercase; text-align: center; }
    .akumulasi-header { background: linear-gradient(135deg, #F9A825 0%, #FBC02D 100%); padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 18px; color: white; margin: 30px 0 20px 0; text-transform: uppercase; text-align: center; }
    .divider { height: 3px; background: linear-gradient(90deg, transparent, #2E7D32, transparent); margin: 40px 0; }
    .profesi-header { background: linear-gradient(135deg, #F9A825 0%, #FBC02D 100%); padding: 15px 20px; border-radius: 5px; font-weight: bold; font-size: 20px; color: white; margin: 30px 0 30px 0; text-transform: uppercase; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .profesi-card { background: white; border: 3px solid #2E7D32; border-radius: 15px; padding: 20px; margin: 0 10px 20px 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); height: 100%; transition: transform 0.2s, box-shadow 0.2s; border: 2px solid transparent; }
    .profesi-card:hover { transform: translateY(-5px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .profesi-card .profesi-icon { font-size: 60px; margin-bottom: 10px; line-height: 1; display: block; font-family: "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", sans-serif; }
    .profesi-card .profesi-label { font-size: 14px; color: #2E7D32; font-weight: 600; margin: 10px 0; min-height: 40px; display: flex; align-items: center; justify-content: center; }
    .profesi-card .profesi-value { font-size: 36px; font-weight: bold; color: #2E7D32; margin-top: 5px; }
    .stDataFrame { font-size: 12px; }
    .footer-container { background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #388E3C 100%); padding: 20px; border-radius: 0px; margin: 40px -70px 0px -70px; text-align: center; color: white; font-size: 14px; position: relative; bottom: 0; }
    .table-header-orange { background: linear-gradient(135deg, #F57C00 0%, #FF9800 100%); padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 18px; color: white; margin: 30px 0 20px 0; text-transform: uppercase; text-align: center; }
    .chart-header-green { background: linear-gradient(135deg, #66BB6A 0%, #81C784 100%); padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 18px; color: white; margin: 30px 0 20px 0; text-transform: uppercase; text-align: center; }
</style>
""", unsafe_allow_html=True) # Tag ini ngizinin Streamlit nge-render HTML/CSS murni kita

# Pake cache_resource biar koneksi ke GSheets ga di-restart terus tiap user nge-klik sesuatu
@st.cache_resource
def connect_to_gsheets():
    try: # Nyoba konek nih
        # Ambil salinan dict credential dari secrets agar bisa dimodifikasi di memori
        credentials_dict = dict(st.secrets["gserviceaccount"])
        
        # --- LOGIKA SAKTI SANITASI KUNCI PEM PRIVATE KEY ---
        raw_key = credentials_dict["private_key"]
        
        # 1. Bersihkan penulisan literal \n jika tidak sengaja ter-escape ganda di TOML
        raw_key = raw_key.replace("\\n", "\n")
        
        # 2. Pisahkan teks berdasarkan baris baru untuk mendeteksi isi kunci asli
        lines = [line.strip() for line in raw_key.split("\n") if line.strip()]
        
        # 3. Rekonstruksi struktur PEM: satukan bagian header, body kunci, dan footer secara bersih
        header = "-----BEGIN PRIVATE KEY-----"
        footer = "-----END PRIVATE KEY-----"
        
        # Ambil semua teks body di antara header dan footer
        body_lines = [l for l in lines if "-----" not in l]
        body_text = "".join(body_lines)
        
        # Atur ulang ke format string PEM lurus tunggal yang dimengerti library cryptography
        clean_key = f"{header}\n{body_text}\n{footer}\n"
        credentials_dict["private_key"] = clean_key
        # -----------------------------------------------------------------
        
        scopes = [ # Tentu-in izin aksesnya (baca sheets & drive)
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Bikin token kredensial pake data rapi tadi
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        client = gspread.authorize(credentials) # Log-in ke Gspread!
        return client # Kalo sukses, balikin objek client-nya
    except Exception as e: # Kalo gagal konek...
        st.error(f"Error connecting to Google Sheets: {str(e)}") # Munculin pesan error merah di web
        return None # Balikin kosongan

# Cache data biar ga ngabisin kuota API baca GSheets terus (di-refresh tiap 300 detik alias 5 menit)
@st.cache_data(ttl=300)
def load_data_from_sheets(_client, spreadsheet_url, sheet_name="Sheet1"):
    try: # Nyoba narik data
        sheet = _client.open_by_url(spreadsheet_url) # Buka file spreadsheet berdasarkan URL
        worksheet = sheet.worksheet(sheet_name) # Pilih sheet spesifik (misal 'Sheet1')
        data = worksheet.get_all_records() # Ambil semua datanya bentuk dictionary
        df = pd.DataFrame(data) # Ubah ke bentuk Dataframe Pandas biar asik diolah
        return df # Balikin si Dataframe
    except Exception as e: # Kalo gagal...
        st.error(f"Error loading data from sheet '{sheet_name}': {str(e)}") # Kasih tau errornya apa
        return pd.DataFrame() # Balikin Dataframe kosong biar kode lain ga ikut meledak

# Fungsi buat narik data dari beberapa sheet sekaligus, keren nih pake sistem retry
@st.cache_data(ttl=300)
def load_multiple_sheets(_client, spreadsheet_url, sheets_config):
    data_dict = {} # Siapin kamus kosong buat nampung data
    try:
        max_retries = 3 # Maksimal nyoba ngulang 3 kali kalo gagal
        retry_delay = 2 # Jeda 2 detik tiap mau nyoba lagi
        
        for attempt in range(max_retries): # Mulai nyoba looping
            try:
                sheet = _client.open_by_url(spreadsheet_url) # Buka URL
                break # Kalo sukses langsung tembus (break loop)
            except Exception as e: # Kalo gagal konek
                if attempt < max_retries - 1: # Kalo masih ada sisa nyawa (attempt)
                    st.warning(f"Mencoba kembali koneksi ke spreadsheet (percobaan {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay * (attempt + 1)) # Nunggu bentar, makin lama makin jedanya gede
                else:
                    raise e # Kalo udah abis nyawa, yaudah pass errornya ke luar
        
        unique_sheets = {} # Siapin kamus buat nyimpen sheet unik biar ga dobel download
        for key, sheet_name in sheets_config.items(): # Looping konfigurasinya
            try:
                if sheet_name not in unique_sheets: # Kalo sheet ini belum pernah di-download...
                    time.sleep(0.5) # Kasih jeda dikit biar API Google ga ngamuk (Rate Limit)
                    worksheet = sheet.worksheet(sheet_name) # Pilih sheetnya
                    try:
                        data = worksheet.get_all_records() # Ambil isinya
                        unique_sheets[sheet_name] = pd.DataFrame(data) # Masukin ke pandas
                    except Exception as record_error: # Kalo cara di atas gagal (mungkin header-nya berantakan)
                        all_values = worksheet.get_all_values() # Ambil semuanya mentah-mentah
                        if len(all_values) > 0: # Kalo ada isinya
                            headers = all_values[0] # Baris pertama dijadiin header
                            seen = {} # Buat nyatet header yang dobel
                            unique_headers = [] # Nampung header yang udah fix unik
                            for h in headers: # Looping header
                                if h in seen: # Kalo udah pernah ada namanya...
                                    seen[h] += 1 # Tambahin angka di belakangnya
                                    unique_headers.append(f"{h}_{seen[h]}" if h else f"Unnamed_{seen[h]}")
                                else:
                                    seen[h] = 0 # Kalo baru pertama kali liat
                                    unique_headers.append(h if h else "Unnamed_0") # Kalo kosong kasih nama Unnamed_0
                            # Bikin dataframe dari sisa baris (data), pake header yang udah dirapiin tadi
                            unique_sheets[sheet_name] = pd.DataFrame(all_values[1:], columns=unique_headers)
                        else:
                            unique_sheets[sheet_name] = pd.DataFrame() # Kalo beneran kosong plong
                
                data_dict[key] = unique_sheets[sheet_name].copy() # Masukin hasil akhirya ke kamus
                
            except Exception as e: # Kalo sheet tertentu aja yang gagal
                st.warning(f"Error loading sheet '{sheet_name}' for key '{key}': {str(e)}") # Kasih warning
                data_dict[key] = pd.DataFrame() # Kasih data kosong aja buat kunci itu
        
        return data_dict # Balikin semua data sheetnya
        
    except Exception as e: # Kalo gagal fatal dari awal
        st.error(f"Error connecting to spreadsheet: {str(e)}")
        return {key: pd.DataFrame() for key in sheets_config.keys()} # Balikin list kosongan biar app ga crash

# Fungsi bantalan buat bikin HTML card yang isinya angka gampang dibaca
def create_metric_card(label, value, card_type="green"):
    return f"""
    <div class="metric-card-{card_type}">
        <div class="metric-label">{label}</div> <div class="metric-value">{value:,}</div> </div>
    """

# Fungsi buat bikin box KPI (Key Performance Indicator) yang nunjukin actual vs target
def create_kpi_card(label, actual, target, suffix=""):
    score = (actual / target * 100) if target > 0 else 0 # Ngitung persenannya, dijagain biar ga dibagi 0 (error)
    
    if score >= 80: # Kalo pencapaian di atas 80% (Bagus!)
        card_class = "kpi-card-green" # Warnain Ijo
        status_icon = "✅" # Kasih centang
    elif score >= 60: # Kalo lumayan (60 - 79%)
        card_class = "kpi-card-yellow" # Warnain Kuning/Oranye
        status_icon = "⚠️" # Kasih warning 
    else: # Kalo jelek/kurang (di bawah 60%)
        card_class = "kpi-card-red" # Warnain Merah
        status_icon = "❌" # Silang dong
        
    # Kembalikan string HTML-nya yang udah dirakit pake data di atas
    return f"""
    <div class="kpi-card {card_class}">
        <div class="kpi-title">{label}</div>
        <div class="kpi-actual">{actual:,.0f} <span style="font-size: 14px; font-weight:normal;">{suffix}</span></div>
        <div class="kpi-target">Target: {target:,.0f} {suffix}</div>
        <div class="kpi-score-box">
            <span class="kpi-score-text">{score:.2f}%</span>
            <span style="font-size: 18px;">{status_icon}</span>
        </div>
    </div>
    """

# Seting letak database lokal SQLite, di folder yang sama sama file ini
DB_PATH = Path(__file__).parent / "dashboard.db"

# Fungsi buat ngebuka pintu koneksi ke database SQLite
def get_db_connection():
    conn = sqlite3.connect(DB_PATH) # Konek pake path tadi
    conn.row_factory = sqlite3.Row # Biar hasil query-nya bisa dipanggil pake nama kolom (kayak dictionary)
    return conn # Balikin kunci koneksinya

# Fungsi buat ngamanin password (hashing), jadi ga kelihatan wujud aslinya di DB
def hash_password(password):
    salt = os.urandom(16) # Bumbu rahasia (salt) acak 16 byte
    digest = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, 200000)
    return f"{salt.hex()}${digest.hex()}"

# Fungsi buat nyocokin password user yang lagi login sama yang ada di DB
def verify_password(password, stored_hash):
    try: # Nyoba ekstrak
        salt_hex, digest_hex = str(stored_hash).split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, 200000)
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False

# Fungsi pas pertama kali setup database
def init_sqlite_database():
    default_username = st.secrets.get("admin_username", "admin")
    default_password = st.secrets.get("admin_password", "admin123")

    with get_db_connection() as conn:
        cur = conn.cursor()

        # Bikin tabel 'admin_users' kalo belum ada
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # Bikin tabel 'chart_config' buat nyimpen settingan mau nampilin chart yang mana aja
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chart_config (
                chart_key TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )
            """
        )

        cur.execute("SELECT COUNT(*) AS total FROM admin_users")
        total_admin = cur.fetchone()["total"]
        if total_admin == 0:
            cur.execute(
                "INSERT INTO admin_users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (str(default_username), hash_password(default_password), datetime.now().isoformat()),
            )

        for chart_key, label in DEFAULT_CHART_CONFIG.items():
            cur.execute(
                """
                INSERT OR IGNORE INTO chart_config (chart_key, label, enabled, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (chart_key, label, 1, datetime.now().isoformat()),
            )
        conn.commit()

# Fungsi buat narik settingan chart dari DB
def load_chart_config_from_db():
    chart_config = {}
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT chart_key, label, enabled FROM chart_config ORDER BY chart_key")
        rows = cur.fetchall()

    for row in rows:
        chart_config[row["chart_key"]] = {
            "enabled": bool(row["enabled"]),
            "label": row["label"],
        }
    return chart_config

# Fungsi buat nge-save kalo admin ngubah-ngubah settingan chart
def save_chart_config_to_db(chart_config):
    with get_db_connection() as conn:
        cur = conn.cursor()
        for chart_key, cfg in chart_config.items():
            cur.execute(
                """
                UPDATE chart_config
                SET enabled = ?, label = ?, updated_at = ?
                WHERE chart_key = ?
                """,
                (
                    1 if cfg.get("enabled", True) else 0,
                    str(cfg.get("label", chart_key)),
                    datetime.now().isoformat(),
                    chart_key,
                ),
            )
        conn.commit()

# Fungsi ngecek kredensial pas admin mau login
def authenticate_admin(username, password):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT username, password_hash FROM admin_users WHERE username = ?", (str(username),))
        row = cur.fetchone()

    if not row:
        return False
    return verify_password(password, row["password_hash"])

# Ambil list siapa aja yang jadi admin
def list_admin_users():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, created_at FROM admin_users ORDER BY created_at ASC")
        rows = cur.fetchall()
    return [dict(row) for row in rows]

# Fungsi buat nambah admin baru
def add_admin_user(username, password):
    username = str(username).strip()
    password = str(password)

    if len(username) < 3:
        return False, "Username minimal 3 karakter."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM admin_users WHERE username = ?", (username,))
        if cur.fetchone():
            return False, "Username sudah digunakan."

        cur.execute(
            "INSERT INTO admin_users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), datetime.now().isoformat()),
        )
        conn.commit()
    return True, "Admin baru berhasil ditambahkan."

# Fungsi buat ngehapus/tendang akun admin
def delete_admin_user(target_username, current_username):
    if str(target_username) == str(current_username):
        return False, "Anda tidak bisa menghapus akun yang sedang digunakan untuk login."

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM admin_users")
        total_admin = cur.fetchone()["total"]

        cur.execute("SELECT 1 FROM admin_users WHERE username = ?", (str(target_username),))
        if not cur.fetchone():
            return False, "Admin tidak ditemukan."

        if total_admin <= 1:
            return False, "Minimal harus ada 1 akun admin."

        cur.execute("DELETE FROM admin_users WHERE username = ?", (str(target_username),))
        conn.commit()
    return True, "Admin berhasil dihapus."

# Fungsi buat nyiapin state/sesi di memori Streamlit biar dia inget siapa yang lagi buka app
def init_admin_state():
    init_sqlite_database()

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if "current_admin_username" not in st.session_state:
        st.session_state.current_admin_username = None 

    if "admin_chart_config" not in st.session_state:
        st.session_state.admin_chart_config = load_chart_config_from_db()

    if "show_logout_confirm" not in st.session_state:
        st.session_state.show_logout_confirm = False

# Halaman khusus admin nih (UI-nya)
def render_admin_page():
    st.markdown('<h2 class="sub-title" style="margin-top: 10px;">HALAMAN ADMIN</h2>', unsafe_allow_html=True)

    if not st.session_state.admin_logged_in:
        st.info("Silakan login terlebih dahulu untuk mengakses pengaturan admin.")

        with st.form("admin_login_form"):
            username = st.text_input("Username", placeholder="Masukkan username admin")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if authenticate_admin(username, password):
                    st.session_state.admin_logged_in = True
                    st.session_state.current_admin_username = str(username).strip()
                    st.success("Login berhasil. Selamat datang di halaman admin.")
                    st.rerun()
                else:
                    st.error("Username atau password salah.")
        return

    # ---------- MULAI DARI SINI UDAH LOGIN ----------
    col_title, col_action = st.columns([4, 1])
    with col_title:
        st.success("Mode admin aktif. Anda bisa melakukan kustomisasi konfigurasi grafik.")
    with col_action:
        if st.button("Logout", use_container_width=True):
            st.session_state.show_logout_confirm = True

    if st.session_state.get("show_logout_confirm", False):
        st.warning("Yakin ingin logout dari halaman admin?")
        col_yes, col_cancel = st.columns(2)
        with col_yes:
            if st.button("Iya, Logout", type="primary", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.session_state.current_admin_username = None
                st.session_state.show_logout_confirm = False
                st.success("Anda berhasil logout.")
                st.rerun()
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_logout_confirm = False
                st.rerun()

    st.markdown('<div class="section-header">KUSTOMISASI VISUALISASI</div>', unsafe_allow_html=True)
    st.caption("Kustomisasi untuk mengatur grafik ditampilkan atau tidak ditampilkan di dashboard.")

    updated_config = st.session_state.admin_chart_config.copy()

    for chart_key, default_label in DEFAULT_CHART_CONFIG.items():
        chart_cfg = st.session_state.admin_chart_config.get(chart_key, {})
        current_label = chart_cfg.get("label", default_label)

        with st.expander(f"Pengaturan: {current_label}", expanded=False):
            enabled = st.checkbox(
                "Tampilkan grafik ini di dashboard",
                value=chart_cfg.get("enabled", True),
                key=f"admin_enabled_{chart_key}",
            )

            updated_config[chart_key] = {
                "enabled": enabled,
                "label": current_label,
            }

    if st.button("Simpan Konfigurasi Grafik", type="primary"):
        st.session_state.admin_chart_config = updated_config
        save_chart_config_to_db(updated_config)
        st.success("Konfigurasi berhasil disimpan di sesi aplikasi.")

    st.markdown('<div class="section-header">KELOLA AKSES ADMIN</div>', unsafe_allow_html=True)

    with st.form("add_admin_form"):
        st.markdown("#### Tambah Admin Baru")
        new_username = st.text_input("Username admin baru", key="new_admin_username") 
        new_password = st.text_input("Password admin baru", type="password", key="new_admin_password")
        confirm_password = st.text_input("Konfirmasi password", type="password", key="confirm_admin_password")
        add_submitted = st.form_submit_button("Tambah Admin")

        if add_submitted:
            if new_password != confirm_password:
                st.error("Konfirmasi password tidak cocok.")
            else:
                ok, message = add_admin_user(new_username, new_password)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("#### Daftar Admin")
    current_admin = st.session_state.get("current_admin_username")
    admins = list_admin_users()

    if not admins:
        st.warning("Belum ada data admin di database.")
    else:
        for admin in admins:
            col_user, col_created, col_action = st.columns([2, 2, 1])
            with col_user:
                badge = " (Anda)" if admin["username"] == current_admin else ""
                st.write(f"**{admin['username']}**{badge}")
            with col_created:
                st.write(admin.get("created_at", "-"))
            with col_action:
                can_delete = admin["username"] != current_admin
                if st.button(
                    "Hapus",
                    key=f"delete_admin_{admin['id']}",
                    disabled=not can_delete,
                    use_container_width=True,
                ):
                    ok, message = delete_admin_user(admin["username"], current_admin)
                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

# Fungsi buat ngebaca dari URL lagi di halaman mana (Routing ala-ala pake Query Params)
def get_current_route():
    route = st.query_params.get("route", "dashboard")
    if isinstance(route, list):
        route = route[0] if route else "dashboard"

    route = str(route).strip().lower()
    if route in ["admin", "/admin"]:
        return "admin"
    return "dashboard"

# Fungsi sakti pake JS buat munculin dialog Print browser otomatis 
def trigger_print_if_requested():
    print_value = st.query_params.get("print", "0")
    if isinstance(print_value, list):
        print_value = print_value[0] if print_value else "0"

    if str(print_value).strip().lower() in ["1", "true", "yes"]:
        components.html(
            """
            <script>
                (function () {
                    function doPrint() {
                        try {
                            window.parent.print();
                        } catch (e) {
                            window.print();
                        }
                    }

                    function waitUntilChartsReady(maxAttempts, intervalMs) {
                        var attempts = 0;
                        var timer = setInterval(function () {
                            attempts += 1;
                            var chartCount = 0;
                            try {
                                chartCount = window.parent.document.querySelectorAll('.js-plotly-plot').length;
                            } catch (e) {
                                chartCount = 0;
                            }
                            if (chartCount > 0 || attempts >= maxAttempts) {
                                clearInterval(timer);
                                setTimeout(doPrint, 400);
                            }
                        }, intervalMs);
                    }
                    requestAnimationFrame(function () {
                        waitUntilChartsReady(20, 250);
                    });
                })();
            </script>
            """,
            height=0,
            width=0,
        )
        if "print" in st.query_params:
            del st.query_params["print"]

# FUNGSI RAJA: Render semua UI dashboard utama
def render_dashboard():
    admin_chart_cfg = st.session_state.get("admin_chart_config", {})
    
    show_chart_provinsi = admin_chart_cfg.get("chart_provinsi", {}).get("enabled", True)
    show_chart_materi = admin_chart_cfg.get("chart_materi", {}).get("enabled", True)
    show_chart_inovasi = admin_chart_cfg.get("chart_inovasi", {}).get("enabled", True)
    show_tabel_kabkota = admin_chart_cfg.get("tabel_kabkota", {}).get("enabled", True)
    show_chart_instansi = admin_chart_cfg.get("chart_instansi", {}).get("enabled", True)
    show_chart_narasumber_pie = admin_chart_cfg.get("chart_narasumber_pie", {}).get("enabled", True)
    show_chart_1 = admin_chart_cfg.get("chart_1", {}).get("enabled", True)
    show_chart_2 = admin_chart_cfg.get("chart_2", {}).get("enabled", True)
    show_chart_3 = admin_chart_cfg.get("chart_3", {}).get("enabled", True)

    st.markdown("""
    <div class="header-container">
        <div class="header-left">
            <img src="data:image/png;base64,{}" class="header-logo" alt="Logo BRMP">
            <div>
                <div class="header-title">BALAI BESAR PENGEMBANGAN DAN</div>
                <div class="header-title">PENERAPAN MODERNISASI PERTANIAN</div>
                <div class="header-subtitle">BADAN PENYULUHAN DAN MODERNISASI PERTANIAN</div>
            </div>
        </div>
        <a class="print-button-header" href="/?print=1">Cetak / Simpan PDF</a> </div>
    """.format(get_base64_image("logo-brmp.png")), unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">REALISASI PELAKSANAAN PENDAMPINGAN SWASEMBADA PANGAN</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-title">LINGKUP BRMP PENERAPAN TA 2025</h2>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    client = connect_to_gsheets()
    
    ltt_reguler = 0
    opt_lahan_rawa = 0
    opt_lahan_non_rawa = 0
    cetak_sawah = 0
    padi_gogo = 0
    sub_brigade_pangan = 0
    brigade_pangan = 0
    
    update_kegiatan = 0
    update_provinsi = 0
    update_kab = 0
    update_sasaran = 0
    
    akum_kegiatan = 0
    akum_provinsi = 0
    akum_kab = 0
    akum_sasaran = 0
    
    df_provinsi = None
    df_materi = None
    df_inovasi = None
    df_profesi = None
    df_kabkota = None
    df_instansi = None
    df_narasumber_peserta = None
    df_form_responses = None
    
    try:
        # Mengambil data config langsung dari penamaan tabel sheets baru kita
        spreadsheet_url = st.secrets["sheets"]["public_url"]
        sheets_config = {"form_responses": "Sheet1"} 
    except Exception as e:
        spreadsheet_url = ""
        sheets_config = {}
        st.error(f"Error reading configuration: {str(e)}")
    
    data_sheets = {}
    
    if client and spreadsheet_url and sheets_config:
        try:
            data_sheets = load_multiple_sheets(client, spreadsheet_url, sheets_config)
            loaded_sheets = [key for key, df in data_sheets.items() if not df.empty]
            
            if loaded_sheets:
                st.success(f"Data berhasil dimuat secara real-time dari Google Sheets!")
                
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_program = data_sheets["form_responses"]
                    df_form_responses = data_sheets["form_responses"].copy()
                    
                    if 'Program Swasembada' in df_program.columns:
                        all_programs = df_program['Program Swasembada'].dropna().astype(str)
                        program_list = []
                        for value in all_programs:
                            programs = [p.strip() for p in value.split(',') if p.strip()]
                            program_list.extend(programs)
                        
                        program_counts = pd.Series(program_list).value_counts()
                        ltt_reguler = int(program_counts.get('LTT Reguler', 0))
                        opt_lahan_rawa = int(program_counts.get('Optimasi Lahan Rawa', 0))
                        opt_lahan_non_rawa = int(program_counts.get('Optimasi Lahan Non Rawa', 0))
                        cetak_sawah = int(program_counts.get('Cetak Sawah Rakyat', 0))
                        padi_gogo = int(program_counts.get('Padi Gogo', 0))
                        brigade_pangan = int(program_counts.get('Brigade Pangan', 0))
                    else:
                        st.warning(f"Kolom 'Program Swasembada' tidak ditemukan.")
                
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_update = data_sheets["form_responses"].copy()
                    if 'Tanggal Pelaksanaan Kegiatan' in df_update.columns:
                        df_update['Tanggal Pelaksanaan Kegiatan'] = pd.to_datetime(df_update['Tanggal Pelaksanaan Kegiatan'], errors='coerce')
                        today = pd.Timestamp.now()
                        seven_days_ago = today - timedelta(days=7)
                        
                        df_weekly = df_update[df_update['Tanggal Pelaksanaan Kegiatan'] >= seven_days_ago]
                        update_kegiatan = len(df_weekly)
                        if 'Provinsi' in df_weekly.columns:
                            update_provinsi = df_weekly['Provinsi'].nunique()
                        if 'Kabupaten/Kota' in df_weekly.columns:
                            update_kab = df_weekly['Kabupaten/Kota'].nunique()
                        if 'Total Peserta (orang)' in df_weekly.columns:
                            update_sasaran = int(pd.to_numeric(df_weekly['Total Peserta (orang)'], errors='coerce').fillna(0).sum())
                
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_akum = data_sheets["form_responses"]
                    akum_kegiatan = len(df_akum)
                    if 'Provinsi' in df_akum.columns:
                        akum_provinsi = df_akum['Provinsi'].nunique()
                    if 'Kabupaten/Kota' in df_akum.columns:
                        akum_kab = df_akum['Kabupaten/Kota'].nunique()
                    if 'Total Peserta (orang)' in df_akum.columns:
                        akum_sasaran = int(pd.to_numeric(df_akum['Total Peserta (orang)'], errors='coerce').fillna(0).sum())
                
                df_provinsi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_sasaran_prov = data_sheets["form_responses"].copy()
                    if 'Provinsi' in df_sasaran_prov.columns and 'Total Peserta (orang)' in df_sasaran_prov.columns:
                        df_sasaran_prov['Total Peserta (orang)'] = pd.to_numeric(df_sasaran_prov['Total Peserta (orang)'], errors='coerce').fillna(0)
                        df_sasaran_prov = df_sasaran_prov[(df_sasaran_prov['Provinsi'].notna()) & (df_sasaran_prov['Provinsi'] != '')]
                        df_provinsi = df_sasaran_prov.groupby('Provinsi', as_index=False)['Total Peserta (orang)'].sum()
                        df_provinsi.columns = ['Provinsi', 'Total Peserta']
                        df_provinsi = df_provinsi.sort_values('Total Peserta', ascending=False)
                
                df_materi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_topik = data_sheets["form_responses"].copy()
                    if 'Topik Materi' in df_topik.columns:
                        all_materi = df_topik['Topik Materi'].dropna().astype(str)
                        materi_list = []
                        for value in all_materi:
                            if value.strip():
                                topics = [t.strip() for t in value.split(',') if t.strip()]
                                materi_list.extend(topics)
                        materi_counts = pd.Series(materi_list).value_counts().reset_index()
                        materi_counts.columns = ['Materi', 'Jumlah']
                        total = materi_counts['Jumlah'].sum()
                        materi_counts['Persentase'] = (materi_counts['Jumlah'] / total * 100).round(1)
                        df_materi = materi_counts
                
                df_inovasi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_produk = data_sheets["form_responses"].copy()
                    kolom_inovasi = 'Jika inovasi teknologi modernisasi pertanian, komponen apa saja (Jawaban boleh lebih dari 1 pilihan)'
                    if kolom_inovasi in df_produk.columns:
                        all_komponen = df_produk[kolom_inovasi].dropna().astype(str)
                        komponen_list = []
                        for value in all_komponen:
                            if value.strip():
                                items = [k.strip() for k in value.split(',') if k.strip()]
                                komponen_list.extend(items)
                        produk_counts = pd.Series(komponen_list).value_counts().reset_index()
                        produk_counts.columns = ['Produk', 'Total Kegiatan']
                        df_inovasi = produk_counts
                
                df_profesi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_profesi_raw = data_sheets["form_responses"].copy()
                    profesi_columns = {
                        'Peserta Petani (orang)': 'Peserta Petani (orang)',
                        'Peserta Penyuluh Pertanian (orang)': 'Peserta Penyuluh Pertanian (orang)',
                        'Peserta  POPT (orang)': 'Peserta  POPT (orang)',
                        'Peserta  PBT (orang)': 'Peserta  PBT (orang)',
                        'Peserta Babinsa (orang)': 'Peserta Babinsa (orang)',
                        'Peserta Staf Dinas (orang)': 'Peserta Staf Dinas (orang)',
                        'Peserta lainnya (orang) sebutkan': 'Peserta lainnya (orang) sebutkan'
                    }
                    profesi_data = []
                    for kategori, kolom in profesi_columns.items():
                        if kolom in df_profesi_raw.columns:
                            total = int(pd.to_numeric(df_profesi_raw[kolom], errors='coerce').fillna(0).sum())
                            profesi_data.append({'Kategori': kategori, 'Total Peserta': total})
                    if profesi_data:
                        df_profesi = pd.DataFrame(profesi_data)
                        df_profesi = df_profesi.sort_values('Total Peserta', ascending=False)
                
                df_kabkota = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_kk_raw = data_sheets["form_responses"].copy()
                    if 'Provinsi' in df_kk_raw.columns and 'Kabupaten/Kota' in df_kk_raw.columns and 'Total Peserta (orang)' in df_kk_raw.columns:
                        df_filtered = df_kk_raw[(df_kk_raw['Provinsi'].notna()) & (df_kk_raw['Kabupaten/Kota'].notna()) & (df_kk_raw['Provinsi'] != '') & (df_kk_raw['Kabupaten/Kota'] != '')].copy()
                        df_filtered['Total Peserta (orang)'] = pd.to_numeric(df_filtered['Total Peserta (orang)'], errors='coerce').fillna(0)
                        df_kabkota = df_filtered.groupby(['Provinsi', 'Kabupaten/Kota'], as_index=False)['Total Peserta (orang)'].sum()
                        df_kabkota.columns = ['Provinsi', 'Kabupaten/Kota', 'Total Peserta']
                        df_kabkota = df_kabkota.sort_values('Total Peserta', ascending=False)
                
                df_instansi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_inst_raw = data_sheets["form_responses"].copy()
                    if 'Narasumber' in df_inst_raw.columns:
                        kategori_valid = ['Internal BRMP', 'Pemerintah Daerah', 'NGO']
                        def kategorikan_narasumber(value):
                            if pd.isna(value) or str(value).strip() == '': return None
                            value_str = str(value).strip()
                            if value_str in kategori_valid: return value_str
                            else: return 'Lainnya'
                        df_inst_raw['Kategori Narasumber'] = df_inst_raw['Narasumber'].apply(kategorikan_narasumber)
                        df_inst_filtered = df_inst_raw[df_inst_raw['Kategori Narasumber'].notna()]
                        instansi_counts = df_inst_filtered['Kategori Narasumber'].value_counts().reset_index()
                        instansi_counts.columns = ['Instansi', 'Jumlah Kegiatan']
                        urutan_kategori = ['Internal BRMP', 'Pemerintah Daerah', 'NGO', 'Lainnya']
                        instansi_counts['sort_order'] = instansi_counts['Instansi'].apply(lambda x: urutan_kategori.index(x) if x in urutan_kategori else 99)
                        df_instansi = instansi_counts.sort_values('sort_order').drop('sort_order', axis=1)
                
                df_narasumber_peserta = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_narpest_raw = data_sheets["form_responses"]
                    if 'Narasumber' in df_narpest_raw.columns and 'Total Peserta (orang)' in df_narpest_raw.columns:
                        def kategorikan_asal_narasumber(value):
                            if pd.isna(value) or str(value).strip() == '': return None
                            value_str = str(value).strip()
                            if value_str == 'Internal BRMP': return 'Internal'
                            elif value_str in ['Pemerintah Daerah', 'NGO']: return 'Eksternal'
                            else: return 'Lainnya'
                        df_narpest_raw = df_narpest_raw.copy()
                        df_narpest_raw['Kategori Asal'] = df_narpest_raw['Narasumber'].apply(kategorikan_asal_narasumber)
                        df_filtered = df_narpest_raw[df_narpest_raw['Kategori Asal'].notna()].copy()
                        df_filtered['Total Peserta (orang)'] = pd.to_numeric(df_filtered['Total Peserta (orang)'], errors='coerce').fillna(0)
                        df_narasumber_peserta = df_filtered.groupby('Kategori Asal', as_index=False)['Total Peserta (orang)'].sum()
                        df_narasumber_peserta.columns = ['Narasumber', 'Total Peserta']
                        urutan_asal = ['Internal', 'Eksternal', 'Lainnya']
                        df_narasumber_peserta['sort_order'] = df_narasumber_peserta['Narasumber'].apply(lambda x: urutan_asal.index(x) if x in urutan_asal else 99)
                        df_narasumber_peserta = df_narasumber_peserta.sort_values('sort_order').drop('sort_order', axis=1)
            else:
                st.warning("Menggunakan data fallback contoh.")
        except Exception as e:
            st.warning(f"Menggunakan data default contoh. Error: {str(e)}")
    
    # ------------------ SEKSI RENDER DASHBOARD LAYOUT ------------------
    st.markdown('<div class="section-header">PENCAPAIAN KPI PROGRAM SWASEMBADA TA 2025</div>', unsafe_allow_html=True)
    TARGET_LTT = 17005193
    TARGET_OPTIMASI = 500000 
    TARGET_CETAK_SAWAH = 225000
    TARGET_PADI_GOGO = 503457
    TARGET_BRIGADE = 2444
    total_optimasi = opt_lahan_rawa + opt_lahan_non_rawa
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.markdown(create_kpi_card("LTT Reguler", ltt_reguler, TARGET_LTT), unsafe_allow_html=True)
    with col2: st.markdown(create_kpi_card("Optimasi Lahan<br>(Rawa & Non Rawa)", total_optimasi, TARGET_OPTIMASI, "ha"), unsafe_allow_html=True)
    with col3: st.markdown(create_kpi_card("Cetak Sawah Rakyat", cetak_sawah, TARGET_CETAK_SAWAH, "ha"), unsafe_allow_html=True)
    with col4: st.markdown(create_kpi_card("Padi Gogo", padi_gogo, TARGET_PADI_GOGO), unsafe_allow_html=True)
    with col5: st.markdown(create_kpi_card("Brigade Pangan", brigade_pangan, TARGET_BRIGADE), unsafe_allow_html=True)
        
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    col_update, col_akumulasi = st.columns(2)
    with col_update:
        st.markdown('<div class="update-header">UPDATE MINGGUAN</div>', unsafe_allow_html=True)
        col_u1, col_u2, col_u3, col_u4 = st.columns(4)
        with col_u1: st.markdown(create_metric_card("Jumlah Kegiatan", update_kegiatan, "orange"), unsafe_allow_html=True)
        with col_u2: st.markdown(create_metric_card("Provinsi", update_provinsi, "orange"), unsafe_allow_html=True)
        with col_u3: st.markdown(create_metric_card("Kab/Kota", update_kab, "orange"), unsafe_allow_html=True)
        with col_u4: st.markdown(create_metric_card("Sasaran", update_sasaran, "orange"), unsafe_allow_html=True)
    
    with col_akumulasi:
        st.markdown('<div class="akumulasi-header">DATA AKUMULASI</div>', unsafe_allow_html=True)
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        with col_a1: st.markdown(create_metric_card("Jumlah Kegiatan", akum_kegiatan, "yellow"), unsafe_allow_html=True)
        with col_a2: st.markdown(create_metric_card("Provinsi", akum_provinsi, "yellow"), unsafe_allow_html=True)
        with col_a3: st.markdown(create_metric_card("Kab/Kota", akum_kab, "yellow"), unsafe_allow_html=True)
        with col_a4: st.markdown(create_metric_card("Sasaran", akum_sasaran, "yellow"), unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns([1, 1])
    with col_chart1:
        if show_chart_provinsi:
            st.markdown('<div class="section-header">JUMLAH SASARAN BERDASARKAN PROVINSI</div>', unsafe_allow_html=True)
            if df_provinsi is None or df_provinsi.empty:
                provinsi_data = {
                    'Provinsi': ['D.I Yogyakarta', 'Sulawesi Tengah', 'Jawa Tengah', 'Banten', 'Lampung', 'Gorontalo', 'Jambi', 'Riau', 'Kalimantan Selatan', 'Aceh'],
                    'Total Peserta': [1391, 1265, 1265, 1207, 1190, 1155, 1030, 960, 852, 584]
                }
                df_provinsi = pd.DataFrame(provinsi_data)
            fig_provinsi = go.Figure(go.Bar(y=df_provinsi['Provinsi'], x=df_provinsi['Total Peserta'], orientation='h', marker=dict(color='#2E7D32'), text=df_provinsi['Total Peserta'], textposition='outside'))
            fig_provinsi.update_layout(height=700, plot_bgcolor='white', yaxis=dict(autorange='reversed'))
            st.plotly_chart(fig_provinsi, use_container_width=True)
    
    with col_chart2:
        if show_chart_materi:
            st.markdown('<div class="section-header">PERSENTASE TOPIK MATERI</div>', unsafe_allow_html=True)
            if df_materi is None or df_materi.empty:
                df_materi = pd.DataFrame({'Materi': ['Kebijakan Pembangunan', 'Inovasi Teknologi', 'Standardisasi'], 'Jumlah': [47.9, 42.2, 9.9]})
            fig_pie = go.Figure(go.Pie(labels=df_materi['Materi'], values=df_materi['Jumlah']))
            fig_pie.update_layout(height=350)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        if show_chart_inovasi:
            st.markdown('<div class="section-header" style="margin-top: 30px;">KOMPONEN INOVASI TEKNOLOGI YANG DIGUNAKAN</div>', unsafe_allow_html=True)
            if df_inovasi is None or df_inovasi.empty:
                df_inovasi = pd.DataFrame({'Produk': ['Sistem tanam', 'VUB', 'Alsintan', 'Pengairan'], 'Total Kegiatan': [212, 212, 149, 135]})
            fig_inovasi = go.Figure(go.Bar(y=df_inovasi['Produk'], x=df_inovasi['Total Kegiatan'], orientation='h', marker=dict(color='#2E7D32'), text=df_inovasi['Total Kegiatan'], textposition='outside'))
            fig_inovasi.update_layout(height=350, plot_bgcolor='white', yaxis=dict(autorange='reversed'))
            st.plotly_chart(fig_inovasi, use_container_width=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="profesi-header">JUMLAH SASARAN BERDASARKAN PROFESI</div>', unsafe_allow_html=True)
    icon_mapping = {'Peserta Petani (orang)': '👨‍🌾', 'Peserta Penyuluh Pertanian (orang)': '👨‍🏫', 'Peserta  POPT (orang)': '🦗', 'Peserta  PBT (orang)': '🌾', 'Peserta Babinsa (orang)': '👨‍✈️', 'Peserta Staf Dinas (orang)': '👨‍💻', 'Peserta lainnya (orang) sebutkan': '👔'}
    profesi_order = ['Peserta Petani (orang)', 'Peserta Penyuluh Pertanian (orang)', 'Peserta  POPT (orang)', 'Peserta  PBT (orang)', 'Peserta Babinsa (orang)', 'Peserta Staf Dinas (orang)', 'Peserta lainnya (orang) sebutkan']
    label_mapping = {'Peserta Petani (orang)': 'Petani', 'Peserta Penyuluh Pertanian (orang)': 'Penyuluh Pertanian', 'Peserta  POPT (orang)': 'POPT', 'Peserta  PBT (orang)': 'PBT', 'Peserta Babinsa (orang)': 'Babinsa', 'Peserta Staf Dinas (orang)': 'Staf Dinas', 'Peserta lainnya (orang) sebutkan': 'Profesi Lainnya'}
    
    profesi_list = []
    profesi_values = {}
    if df_profesi is not None and not df_profesi.empty:
        for _, row in df_profesi.iterrows(): profesi_values[row['Kategori']] = int(row['Total Peserta'])
    for kategori in profesi_order:
        profesi_list.append({'icon': icon_mapping.get(kategori, '👨‍🏫'), 'label': label_mapping.get(kategori, kategori), 'value': profesi_values.get(kategori, 0)})
    
    col_p1, col_p2, col_p3, col_p4 = st.columns(4, gap="large")
    with col_p1: st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[0]["icon"]}</div><div class="profesi-label">{profesi_list[0]["label"]}</div><div class="profesi-value">{profesi_list[0]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p2: st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[1]["icon"]}</div><div class="profesi-label">{profesi_list[1]["label"]}</div><div class="profesi-value">{profesi_list[1]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p3: st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[2]["icon"]}</div><div class="profesi-label">{profesi_list[2]["label"]}</div><div class="profesi-value">{profesi_list[2]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p4: st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[3]["icon"]}</div><div class="profesi-label">{profesi_list[3]["label"]}</div><div class="profesi-value">{profesi_list[3]["value"]:,}</div></div>', unsafe_allow_html=True)
    
    col_spacer1, col_p5, col_p6, col_p7, col_spacer2 = st.columns([0.5, 1, 1, 1, 0.5], gap="large")
    with col_p5: st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[4]["icon"]}</div><div class="profesi-label">{profesi_list[4]["label"]}</div><div class="profesi-value">{profesi_list[4]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p6: st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[5]["icon"]}</div><div class="profesi-label">{profesi_list[5]["label"]}</div><div class="profesi-value">{profesi_list[5]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p7: st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[6]["icon"]}</div><div class="profesi-label">{profesi_list[6]["label"]}</div><div class="profesi-value">{profesi_list[6]["value"]:,}</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    col_table, col_charts = st.columns([1, 1])
    with col_table:
        if show_tabel_kabkota:
            st.markdown('<div class="table-header-orange">JUMLAH SASARAN TERCAPAI PER KAB/KOTA</div>', unsafe_allow_html=True)
            if df_kabkota is not None and not df_kabkota.empty:
                df_display = df_kabkota.copy()
                df_display.insert(0, 'No', range(1, len(df_display) + 1))
                df_display['Total Peserta'] = df_display['Total Peserta'].apply(lambda x: f"{int(x):,}")
            else:
                df_display = pd.DataFrame({'No': [1, 2], 'Provinsi': ['Sumatera Barat', 'Sumatera Utara'], 'Kabupaten/Kota': ['Solok Selatan', 'Langkat'], 'Total Peserta': ['20', '356']})
            st.dataframe(df_display, use_container_width=True, hide_index=True, height=600)
    
    with col_charts:
        if show_chart_instansi:
            st.markdown('<div class="chart-header-green">ASAL INSTANSI NARASUMBER</div>', unsafe_allow_html=True)
            if df_instansi is None or df_instansi.empty:
                df_instansi = pd.DataFrame({'Instansi': ['Internal BRMP', 'Pemda', 'NGO'], 'Jumlah Kegiatan': [310, 38, 2]})
            fig_instansi = go.Figure(go.Bar(x=df_instansi['Instansi'], y=df_instansi['Jumlah Kegiatan'], marker=dict(color='#2E7D32'), text=df_instansi['Jumlah Kegiatan'], textposition='outside'))
            fig_instansi.update_layout(height=300, plot_bgcolor='white')
            st.plotly_chart(fig_instansi, use_container_width=True)
            
        if show_chart_narasumber_pie:
            st.markdown('<div class="chart-header-green" style="margin-top: 30px;">PERSENTASE ASAL NARASUMBER</div>', unsafe_allow_html=True)
            if df_narasumber_peserta is None or df_narasumber_peserta.empty:
                df_narasumber_peserta = pd.DataFrame({'Narasumber': ['Internal', 'Eksternal'], 'Total Peserta': [52.6, 47.4]})
            fig_narasumber_pie = go.Figure(go.Pie(labels=df_narasumber_peserta['Narasumber'], values=df_narasumber_peserta['Total Peserta']))
            fig_narasumber_pie.update_layout(height=300)
            st.plotly_chart(fig_narasumber_pie, use_container_width=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if show_chart_1:
        st.markdown('<div class="chart-header-green">LINE CHART TREN KEGIATAN/PESERTA</div>', unsafe_allow_html=True)
        trend_df = pd.DataFrame({'Periode': ['2025-01', '2025-02', '2025-03', '2025-04'], 'Jumlah_Kegiatan': [18, 24, 21, 26], 'Total_Peserta': [640, 910, 805, 980]})
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=trend_df['Periode'], y=trend_df['Jumlah_Kegiatan'], mode='lines+markers', name='Jumlah Kegiatan', line=dict(color='#2E7D32')))
        fig_trend.add_trace(go.Scatter(x=trend_df['Periode'], y=trend_df['Total_Peserta'], mode='lines+markers', name='Total Peserta', yaxis='y2', line=dict(color='#F57C00')))
        fig_trend.update_layout(height=430, plot_bgcolor='white', yaxis2=dict(overlaying='y', side='right'))
        st.plotly_chart(fig_trend, use_container_width=True)

    if show_chart_2:
        st.markdown('<div class="chart-header-green">STACKED BAR KOMPOSISI PESERTA PERWILAYAH</div>', unsafe_allow_html=True)
        stacked_df = pd.DataFrame({'Wilayah': ['Wilayah A', 'Wilayah B'], 'Petani': [120, 95], 'Penyuluh': [30, 25]})
        fig_stacked = go.Figure()
        fig_stacked.add_trace(go.Bar(x=stacked_df['Wilayah'], y=stacked_df['Petani'], name='Petani'))
        fig_stacked.add_trace(go.Bar(x=stacked_df['Wilayah'], y=stacked_df['Penyuluh'], name='Penyuluh'))
        fig_stacked.update_layout(barmode='stack', height=450, plot_bgcolor='white')
        st.plotly_chart(fig_stacked, use_container_width=True)

    if show_chart_3:
        st.markdown('<div class="chart-header-green">BAR CHART RATA-RATA PESERTA PER KEGIATAN</div>', unsafe_allow_html=True)
        avg_df = pd.DataFrame({'Program': ['LTT Reguler', 'Optimasi Lahan'], 'Rata_rata_Peserta': [42.5, 38.2]})
        fig_avg = go.Figure(go.Bar(x=avg_df['Program'], y=avg_df['Rata_rata_Peserta'], marker=dict(color='#66BB6A'), text=avg_df['Rata_rata_Peserta'], textposition='outside'))
        fig_avg.update_layout(height=420, plot_bgcolor='white')
        st.plotly_chart(fig_avg, use_container_width=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f"**Last updated:** {datetime.now().strftime('%d %B %Y, %H:%M:%S')}") 
    st.markdown('<div class="footer-container"><p>© 2025 BRMP PENERAPAN KEMENTERIAN PERTANIAN</p></div>', unsafe_allow_html=True)
    st.markdown('<style>div.block-container{padding-bottom: 0rem;}</style>', unsafe_allow_html=True)
    trigger_print_if_requested()

# INI MAIN ENTRY POINT PROGRAMNYA: (Dieksekusi pas filenya dijalanin)
if __name__ == "__main__":
    init_admin_state() # 1. Siapin otak state-nya

    current_route = get_current_route() # 2. Cek user lagi numpang baca di URL mana (dashboard/admin)
    if current_route == "admin":
        render_admin_page() # 3. Kalo /admin ya muat si halaman rahasia admin
    else:
        render_dashboard() # 4. Kalo ga, tampilin dashboard utamanya biar seru!
