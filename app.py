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
       nge-set tombol print, dan ngerapiin box-box metrik (KPI) biar enak dipandang mata. 
       Gue skip komen per barisnya ya bro, biar lo bisa fokus ke logika Python-nya! */
    .header-container { background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #388E3C 100%); padding: 20px; border-radius: 0px; margin: -60px -70px 30px -70px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); gap: 20px; }
    .header-left { display: flex; align-items: center; gap: 20px; }
    .header-logo { height: 80px; width: auto; margin-left: 20px; }
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
        secret_info = st.secrets["gcp_service_account"] # Ngambil kredensial dari Streamlit secrets
        
        # --- LOGIKA DEKODE BASE64 DENGAN PENAMBAL PADDING OTOMATIS ---
        if "base64_string" in secret_info:
            # 1. Bersihkan spasi tersembunyi atau baris baru di ujung teks
            b64_str = str(secret_info["base64_string"]).strip()
            
            # 2. Hilangkan karakter non-base64 jika ada yang terselip
            b64_str = ''.join(c for c in b64_str if c.isalnum() or c in '+/=')
            
            # 3. Rumus Sakti: Perbaiki padding matematika Base64 (wajib kelipatan 4)
            missing_padding = len(b64_str) % 4
            if missing_padding:
                b64_str += '=' * (4 - missing_padding)
            
            # 4. Ubah ke ASCII murni lalu dekode aman!
            clean_base64 = b64_str.encode('ascii', 'ignore')
            decoded_bytes = base64.b64decode(clean_base64)
            decoded_json = decoded_bytes.decode("utf-8")
            credentials_dict = json.loads(decoded_json)
            
        elif "json_string" in secret_info:
            clean_json = str(secret_info["json_string"]).strip().encode('ascii', 'ignore')
            credentials_dict = json.loads(clean_json.decode("utf-8"))
        else:
            credentials_dict = secret_info
        # -----------------------------------------------------------------
        
        scopes = [ # Tentu-in izin aksesnya (baca sheets & drive)
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        # Bikin token kredensial pake data tadi
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
    salt = os.urandom(16) # Bikin bumbu rahasia (salt) acak 16 byte
    # Enkripsi pake algoritma pbkdf2_hmac sha256 (diulang 200rb kali biar alot buat di-hack)
    digest = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, 200000)
    return f"{salt.hex()}${digest.hex()}" # Gabungin salt sama hasilnya pisahin pake dollar sign

# Fungsi buat nyocokin password user yang lagi login sama yang ada di DB
def verify_password(password, stored_hash):
    try: # Nyoba ekstrak
        salt_hex, digest_hex = str(stored_hash).split("$", 1) # Pisahin salt dan hash dari DB
        salt = bytes.fromhex(salt_hex) # Ubah ke bentuk byte
        expected = bytes.fromhex(digest_hex) # Target hash yang bener
        # Bikin hash baru pake password yang dimasukin user dicampur salt yang dari DB
        candidate = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, 200000)
        return hmac.compare_digest(candidate, expected) # Bandingin aman-aman pake hmac biar gak kena timing attack
    except Exception: # Kalo formatnya ngaco...
        return False # Tolak akses!

# Fungsi pas pertama kali setup database
def init_sqlite_database():
    default_username = st.secrets.get("admin_username", "admin") # Ngambil username admin dari file rahasia Streamlit
    default_password = st.secrets.get("admin_password", "admin123") # Ngambil password admin juga

    with get_db_connection() as conn: # Buka koneksi...
        cur = conn.cursor() # Bikin cursor buat ngeksekusi perintah SQL

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

        cur.execute("SELECT COUNT(*) AS total FROM admin_users") # Cek ada berapa biji akun admin
        total_admin = cur.fetchone()["total"]
        if total_admin == 0: # Kalo masih kosong melompong (baru pertama di-run)
            # Masukin akun admin default
            cur.execute(
                "INSERT INTO admin_users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (str(default_username), hash_password(default_password), datetime.now().isoformat()),
            )

        # Looping chart default di atas tadi
        for chart_key, label in DEFAULT_CHART_CONFIG.items():
            # Masukin settingan chart default ke DB, IGNORE kalo emang udah ada biar ga numpuk
            cur.execute(
                """
                INSERT OR IGNORE INTO chart_config (chart_key, label, enabled, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (chart_key, label, 1, datetime.now().isoformat()),
            )

        conn.commit() # Simpan perubahan (Save)

# Fungsi buat narik settingan chart dari DB
def load_chart_config_from_db():
    chart_config = {} # Siapin kamus kosong
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT chart_key, label, enabled FROM chart_config ORDER BY chart_key") # Tarik semuanya
        rows = cur.fetchall()

    for row in rows: # Pindahin hasil query ke kamus Python
        chart_config[row["chart_key"]] = {
            "enabled": bool(row["enabled"]), # Ubah dari 1/0 ke True/False
            "label": row["label"],
        }

    return chart_config # Balikin settingannya

# Fungsi buat nge-save kalo admin ngubah-ngubah settingan chart
def save_chart_config_to_db(chart_config):
    with get_db_connection() as conn:
        cur = conn.cursor()
        for chart_key, cfg in chart_config.items(): # Looping kamus updatenya
            # Timpa data lama pake data baru
            cur.execute(
                """
                UPDATE chart_config
                SET enabled = ?, label = ?, updated_at = ?
                WHERE chart_key = ?
                """,
                (
                    1 if cfg.get("enabled", True) else 0, # Kalo true jadi 1, false jadi 0
                    str(cfg.get("label", chart_key)),
                    datetime.now().isoformat(),
                    chart_key,
                ),
            )
        conn.commit() # Simpan permanen ke DB!

# Fungsi ngecek kredensial pas admin mau login
def authenticate_admin(username, password):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT username, password_hash FROM admin_users WHERE username = ?", (str(username),)) # Cari user ini
        row = cur.fetchone()

    if not row: # Kalo ga ketemu usernya
        return False
    return verify_password(password, row["password_hash"]) # Kalo ketemu, cek passwordnya tembus ga

# Ambil list siapa aja yang jadi admin
def list_admin_users():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, created_at FROM admin_users ORDER BY created_at ASC")
        rows = cur.fetchall()
    return [dict(row) for row in rows] # Balikin daftarnya dalam bentuk list of dictionary

# Fungsi buat nambah admin baru
def add_admin_user(username, password):
    username = str(username).strip() # Bersihin spasi kiri-kanan
    password = str(password)

    if len(username) < 3: # Syarat: Username minimal 3 huruf
        return False, "Username minimal 3 karakter."
    if len(password) < 6: # Syarat: Password minimal 6 huruf
        return False, "Password minimal 6 karakter."

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM admin_users WHERE username = ?", (username,)) # Cek udah ada yang pake belom
        if cur.fetchone():
            return False, "Username sudah digunakan." # Kalo udah ada, tolak!

        # Kalo aman, simpen data admin baru (jangan lupa password di-hash ya)
        cur.execute(
            "INSERT INTO admin_users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), datetime.now().isoformat()),
        )
        conn.commit()

    return True, "Admin baru berhasil ditambahkan." # Sukses bro!

# Fungsi buat ngehapus/tendang akun admin
def delete_admin_user(target_username, current_username):
    if str(target_username) == str(current_username): # Cek, masa mau ngehapus diri sendiri pas lagi login wkwk
        return False, "Anda tidak bisa menghapus akun yang sedang digunakan untuk login."

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM admin_users") # Itung ada berapa admin total
        total_admin = cur.fetchone()["total"]

        cur.execute("SELECT 1 FROM admin_users WHERE username = ?", (str(target_username),)) # Cari mangsanya
        if not cur.fetchone():
            return False, "Admin tidak ditemukan." # Lho ga ada orangnya?

        if total_admin <= 1: # Ga boleh dihapus semua, sisa 1 buat dijadiin super admin
            return False, "Minimal harus ada 1 akun admin."

        cur.execute("DELETE FROM admin_users WHERE username = ?", (str(target_username),)) # Eksekusi pemusnahan!
        conn.commit()

    return True, "Admin berhasil dihapus."

# Fungsi buat nyiapin state/sesi di memori Streamlit biar dia inget siapa yang lagi buka app
def init_admin_state():
    init_sqlite_database() # Nyalain/cek DB dulu

    if "admin_logged_in" not in st.session_state: # Kalo belom ada variabel penanda login...
        st.session_state.admin_logged_in = False # Set defaultnya belum login

    if "current_admin_username" not in st.session_state: # Buat nyimpen nama adminnya...
        st.session_state.current_admin_username = None 

    if "admin_chart_config" not in st.session_state: # Tarik config chart dari DB simpen ke state memori
        st.session_state.admin_chart_config = load_chart_config_from_db()

    if "show_logout_confirm" not in st.session_state: # Penanda popup mau logout
        st.session_state.show_logout_confirm = False

# Halaman khusus admin nih (UI-nya)
def render_admin_page():
    st.markdown('<h2 class="sub-title" style="margin-top: 10px;">HALAMAN ADMIN</h2>', unsafe_allow_html=True) # Judul Halaman

    if not st.session_state.admin_logged_in: # Kalo belum login
        st.info("Silakan login terlebih dahulu untuk mengakses pengaturan admin.") # Disuruh login dulu

        with st.form("admin_login_form"): # Bikin form login rapi
            username = st.text_input("Username", placeholder="Masukkan username admin") # Kolom input user
            password = st.text_input("Password", type="password", placeholder="Masukkan password") # Kolom input pass (disensor titik-titik)
            submitted = st.form_submit_button("Login") # Tombol nge-submit

            if submitted: # Kalo tombol dipencet...
                if authenticate_admin(username, password): # Lempar ke fungsi cek password
                    st.session_state.admin_logged_in = True # Nandain sukses login!
                    st.session_state.current_admin_username = str(username).strip() # Nyatet namanya siapa
                    st.success("Login berhasil. Selamat datang di halaman admin.") # Muncul toast sukses
                    st.rerun() # Refresh halamannya dong biar UI berubah
                else:
                    st.error("Username atau password salah.") # Yaah gagal, disuruh ngulang
        return # Setop ngoding UI admin lebih lanjut (krn belom tembus)

    # ---------- MULAI DARI SINI UDAH LOGIN ----------
    col_title, col_action = st.columns([4, 1]) # Bagi grid layar jadi 2 kolom, satu gede satu kecil
    with col_title:
        st.success("Mode admin aktif. Anda bisa melakukan kustomisasi konfigurasi grafik.") # Pesan sambutan
    with col_action:
        if st.button("Logout", use_container_width=True): # Bikin tombol logout di pojokan
            st.session_state.show_logout_confirm = True # Nyalain trigger konfirmasi

    if st.session_state.get("show_logout_confirm", False): # Kalo triggernya nyala...
        st.warning("Yakin ingin logout dari halaman admin?") # Tanya balik (Popup ala-ala)
        col_yes, col_cancel = st.columns(2) # Bikin 2 tombol jejer
        with col_yes:
            if st.button("Iya, Logout", type="primary", use_container_width=True): # Kalo beneran mau cabut
                st.session_state.admin_logged_in = False # Matikan status login
                st.session_state.current_admin_username = None # Apus riwayat user
                st.session_state.show_logout_confirm = False # Matiin trigger popup
                st.success("Anda berhasil logout.") # Dadahh
                st.rerun() # Refresh halamannya
        with col_cancel:
            if st.button("Cancel", use_container_width=True): # Kalo gajadi (kepencet)
                st.session_state.show_logout_confirm = False # Matiin trigger aja
                st.rerun()

    st.markdown('<div class="section-header">KUSTOMISASI VISUALISASI</div>', unsafe_allow_html=True) # Header seksi
    st.caption("Kustomisasi untuk mengatur grafik ditampilkan atau tidak ditampilkan di dashboard.") # Penjelasan dikit

    updated_config = st.session_state.admin_chart_config.copy() # Bikin kembaran data config chart buat diotak-atik

    # Looping semua chart default buat dibuatin panel tombolnya
    for chart_key, default_label in DEFAULT_CHART_CONFIG.items():
        chart_cfg = st.session_state.admin_chart_config.get(chart_key, {}) # Ambil settingannya si chart ini
        current_label = chart_cfg.get("label", default_label) # Ambil namanya

        with st.expander(f"Pengaturan: {current_label}", expanded=False): # Bikin komponen bisa di-drop-down/expander
            enabled = st.checkbox(
                "Tampilkan grafik ini di dashboard",
                value=chart_cfg.get("enabled", True), # Nilai defaultnya ngambil dari config
                key=f"admin_enabled_{chart_key}", # Kunci unik (wajib ada di Streamlit tiap nambah form element)
            )

            updated_config[chart_key] = { # Masukin status barunya ke kamus sementara
                "enabled": enabled,
                "label": current_label,
            }

    if st.button("Simpan Konfigurasi Grafik", type="primary"): # Kalo tombol "Save Config" dipencet
        st.session_state.admin_chart_config = updated_config # Update ke state Streamlit
        save_chart_config_to_db(updated_config) # Lempar ke DB biar paten
        st.success("Konfigurasi berhasil disimpan di sesi aplikasi.") # Kasih notif seneng

    st.markdown('<div class="section-header">KELOLA AKSES ADMIN</div>', unsafe_allow_html=True) # Judul section kelola akun

    with st.form("add_admin_form"): # Form buat masukin data admin baru
        st.markdown("#### Tambah Admin Baru")
        new_username = st.text_input("Username admin baru", key="new_admin_username") 
        new_password = st.text_input("Password admin baru", type="password", key="new_admin_password")
        confirm_password = st.text_input("Konfirmasi password", type="password", key="confirm_admin_password") # Input ulang biar ga typo
        add_submitted = st.form_submit_button("Tambah Admin")

        if add_submitted: # Pas disubmit
            if new_password != confirm_password: # Cek cocok engga
                st.error("Konfirmasi password tidak cocok.")
            else:
                ok, message = add_admin_user(new_username, new_password) # Lempar ke fungsi tambah ke DB
                if ok:
                    st.success(message) # Kalo sip, mantap
                    st.rerun() # Refresh biar muncul
                else:
                    st.error(message) # Kalo ditolak DB

    st.markdown("#### Daftar Admin") # Judul subbagian tabel admin
    current_admin = st.session_state.get("current_admin_username")
    admins = list_admin_users() # Narik list orang dari DB

    if not admins:
        st.warning("Belum ada data admin di database.") # Harusnya ga mungkin sih kan udah di-init
    else:
        for admin in admins: # Tunjukin semuanya atu-atu pake row baris
            col_user, col_created, col_action = st.columns([2, 2, 1]) # Bagi jadi 3 kolom per baris
            with col_user:
                badge = " (Anda)" if admin["username"] == current_admin else "" # Nandain mana yang lo pake sekarang
                st.write(f"**{admin['username']}**{badge}") # Tunjukin namanya (di-bold)
            with col_created:
                st.write(admin.get("created_at", "-")) # Tunjukin kapan dibikin
            with col_action:
                can_delete = admin["username"] != current_admin # Ga boleh apus diri sendiri
                if st.button(
                    "Hapus",
                    key=f"delete_admin_{admin['id']}", # Kunci beda ditiap tombol hapus
                    disabled=not can_delete, # Kalo itu diri sendiri, tombolnya dikunci (disabled)
                    use_container_width=True,
                ):
                    ok, message = delete_admin_user(admin["username"], current_admin) # Lakukan pemecatan!
                    if ok:
                        st.success(message)
                        st.rerun() # Refresh coy
                    else:
                        st.error(message)

# Fungsi buat ngebaca dari URL lagi di halaman mana (Routing ala-ala pake Query Params)
def get_current_route():
    route = st.query_params.get("route", "dashboard") # Cek parameter '?route=x' di address bar, defaultnya 'dashboard'
    if isinstance(route, list):
        route = route[0] if route else "dashboard" # Kalo isinya list, ambil yang pertama

    route = str(route).strip().lower() # Dirapihin ke huruf kecil semua
    if route in ["admin", "/admin"]: # Kalo route-nya admin
        return "admin" # Fix pindah mode admin
    return "dashboard" # Selain itu ya balik ke dashboard

# Fungsi sakti pake JS buat munculin dialog Print browser otomatis 
def trigger_print_if_requested():
    print_value = st.query_params.get("print", "0") # Cek URL ada nulis `?print=1` gak
    if isinstance(print_value, list):
        print_value = print_value[0] if print_value else "0"

    if str(print_value).strip().lower() in ["1", "true", "yes"]: # Kalo beneran disuruh nge-print
        # Masukin kode javascript murni (Hacky way but works!)
        components.html(
            """
            <script>
                (function () { // Fungsi jalan otomatis
                    function doPrint() { // Logika manggil menu print OS
                        try {
                            window.parent.print(); // Ngeprint window utama Streamlitnya
                        } catch (e) {
                            window.print(); // Backup kalo ga nemu parentnya
                        }
                    }

                    function waitUntilChartsReady(maxAttempts, intervalMs) {
                        var attempts = 0;

                        var timer = setInterval(function () { // Nge-loop delay buat nunggu grafiknya selese dirender (kalo kcepetan keprint blank!)
                            attempts += 1;

                            var chartCount = 0;
                            try {
                                chartCount = window.parent.document.querySelectorAll('.js-plotly-plot').length; // Ngitung jumlah elemen grafik plotly
                            } catch (e) {
                                chartCount = 0;
                            }

                            if (chartCount > 0 || attempts >= maxAttempts) { // Kalo grafiknya udah nongol / nyerah kelamaan nunggu
                                clearInterval(timer); // Stop timernya
                                setTimeout(doPrint, 400); // Kasih nafas 0.4 detik trus PRINT!
                            }
                        }, intervalMs);
                    }

                    requestAnimationFrame(function () { // Panggil fungsinya biar nyari aman
                        waitUntilChartsReady(20, 250); // Maks nyari 20 kali, jeda 250 milidetik
                    });
                })();
            </script>
            """,
            height=0,
            width=0, # Bikin iframe-nya sekecil atom biar ga ngerusak layout wkwk
        )

        if "print" in st.query_params: # Hapus query paramnya biar ga nge-print terus-terusan di refresh
            del st.query_params["print"]

# FUNGSI RAJA: Render semua UI dashboard utama
def render_dashboard():
    admin_chart_cfg = st.session_state.get("admin_chart_config", {}) # Ambil perizinan chart mana yang boleh nongol
    
    # Kumpulkan status nyala/mati dari tiap grafik ke dalem variabel lokal
    show_chart_provinsi = admin_chart_cfg.get("chart_provinsi", {}).get("enabled", True)
    show_chart_materi = admin_chart_cfg.get("chart_materi", {}).get("enabled", True)
    show_chart_inovasi = admin_chart_cfg.get("chart_inovasi", {}).get("enabled", True)
    show_tabel_kabkota = admin_chart_cfg.get("tabel_kabkota", {}).get("enabled", True)
    show_chart_instansi = admin_chart_cfg.get("chart_instansi", {}).get("enabled", True)
    show_chart_narasumber_pie = admin_chart_cfg.get("chart_narasumber_pie", {}).get("enabled", True)
    show_chart_1 = admin_chart_cfg.get("chart_1", {}).get("enabled", True)
    show_chart_2 = admin_chart_cfg.get("chart_2", {}).get("enabled", True)
    show_chart_3 = admin_chart_cfg.get("chart_3", {}).get("enabled", True)

    # Nempelin Header gede pake HTML + CSS, nyelipin gambar logo hasil convert base64 (formatnya dikirim ke '{}' trus disuntik lewat format())
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
    
    # Bikin judul h1 & h2 keren + garisan pembatas (divider)
    st.markdown('<h1 class="main-title">REALISASI PELAKSANAAN PENDAMPINGAN SWASEMBADA PANGAN</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-title">LINGKUP BRMP PENERAPAN TA 2025</h2>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    client = connect_to_gsheets() # Buka pintu ke mbah gugel sheets nih bro!
    
    # Nyiapin keranjang (variabel awal) buat nyimpen angka-angka summary program 0 biar aman
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
    
    # Siapin variabel panda dataframe kosongan dulu
    df_provinsi = None
    df_materi = None
    df_inovasi = None
    df_profesi = None
    df_kabkota = None
    df_instansi = None
    df_narasumber_peserta = None
    df_form_responses = None
    
    try: # Tarik config-an detail spreadhseet dari secret (url sama nama sheets-nya)
        spreadsheet_url = st.secrets.get("spreadsheet_url", "")
        sheets_config = {}
        if "sheets" in st.secrets:
            sheets_config = dict(st.secrets["sheets"])
    except Exception as e: # Kalo secretsnya gak ada/error format
        spreadsheet_url = ""
        sheets_config = {}
        st.error(f"Error reading configuration: {str(e)}") # Lempar error
    
    data_sheets = {} # Nampung hasil donlotan sheets
    
    if client and spreadsheet_url and sheets_config: # Kalo 3 syarat lengkap!
        try:
            data_sheets = load_multiple_sheets(client, spreadsheet_url, sheets_config) # Panggil fungsi download borongan
            loaded_sheets = [key for key, df in data_sheets.items() if not df.empty] # Hitung brp sheet yg ga kosong isinya
            
            if loaded_sheets: # Kalo dapet datanya
                st.success(f"Data berhasil dimuat dari {len(loaded_sheets)} sheet(s): {', '.join(loaded_sheets)}") # Pamer bentar sukses load data
                
                # ------ OLAH DATA PROGRAM SWASEMBADA ------
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_program = data_sheets["form_responses"] # Tarik sheet utama
                    df_form_responses = data_sheets["form_responses"].copy() # Bikin kembarannya (backup utuh)
                    
                    if 'Program Swasembada' in df_program.columns: # Cek klomnya ada ga
                        all_programs = df_program['Program Swasembada'].dropna().astype(str) # Copot isi yg kosong, ubah format ke text (string)
                        program_list = []
                        for value in all_programs: # Karena bisa pilih >1 (dipisah koma), kita looping
                            programs = [p.strip() for p in value.split(',') if p.strip()] # Pecah per koma (,) trus buang spasi ujungnya
                            program_list.extend(programs) # Masukin ke list gede
                        
                        program_counts = pd.Series(program_list).value_counts() # Suruh pandas ngitung cepet masing-masing nama muncul berapa kali
                        # Masukin hasilnya ke keranjang yang dibikin di awal tadi
                        ltt_reguler = int(program_counts.get('LTT Reguler', 0))
                        opt_lahan_rawa = int(program_counts.get('Optimasi Lahan Rawa', 0))
                        opt_lahan_non_rawa = int(program_counts.get('Optimasi Lahan Non Rawa', 0))
                        cetak_sawah = int(program_counts.get('Cetak Sawah Rakyat', 0))
                        padi_gogo = int(program_counts.get('Padi Gogo', 0))
                        brigade_pangan = int(program_counts.get('Brigade Pangan', 0))
                    else: # Ya kalo gaada kolomnya protes dong
                        st.warning(f"Kolom 'Program Swasembada' tidak ditemukan. Kolom yang ada: {list(df_program.columns)}")
                else: # Ya kalo datanya kosong plong
                    st.warning("Data form_responses tidak ditemukan atau kosong")
                
                # ------ OLAH DATA UPDATE MINGGUAN (7 HARI TERAKHIR) ------
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_update = data_sheets["form_responses"].copy()
                    
                    if 'Tanggal Pelaksanaan Kegiatan' in df_update.columns:
                        # Ubah format tanggal (text dari Gsheet) jadi datetime Python biar bisa dihitung
                        df_update['Tanggal Pelaksanaan Kegiatan'] = pd.to_datetime(
                            df_update['Tanggal Pelaksanaan Kegiatan'],
                            errors='coerce' # Kalo format ngawur (misal "kemaren"), jadiin null aja (NaT)
                        )
                        
                        today = pd.Timestamp.now() # Ambil tanggal hari ini
                        seven_days_ago = today - timedelta(days=7) # Kurangin 7 hari (buat minggu lalu)
                        
                        # Filter dataframe cuma ambil yang kegiatannya dalam 7 hari trakir
                        df_weekly = df_update[df_update['Tanggal Pelaksanaan Kegiatan'] >= seven_days_ago]
                        update_kegiatan = len(df_weekly) # Jumlah baris = jumlah kegiatan mingguan!
                        
                        if 'Provinsi' in df_weekly.columns:
                            update_provinsi = df_weekly['Provinsi'].nunique() # Ngitung provinsi beda yg kekunjung seminggu ini
                        
                        if 'Kabupaten/Kota' in df_weekly.columns:
                            update_kab = df_weekly['Kabupaten/Kota'].nunique() # Ngitung kab/kota
                        
                        if 'Total Peserta (orang)' in df_weekly.columns:
                            # Bersihin kolom peserta trus di-sum total semua (yg error text jadi 0)
                            update_sasaran = int(pd.to_numeric(df_weekly['Total Peserta (orang)'], errors='coerce').fillna(0).sum())
                
                # ------ OLAH DATA TOTAL AKUMULASI (DARI AWAL ZAMAN) ------
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_akum = data_sheets["form_responses"] # Pake data mentah ga di-filter waktu
                    akum_kegiatan = len(df_akum) # Hitung baris kegiatan 
                    
                    if 'Provinsi' in df_akum.columns:
                        akum_provinsi = df_akum['Provinsi'].nunique() # Jumlah provinsi fix
                    
                    if 'Kabupaten/Kota' in df_akum.columns:
                        akum_kab = df_akum['Kabupaten/Kota'].nunique() # Jumlah kab/kota
                    
                    if 'Total Peserta (orang)' in df_akum.columns:
                        akum_sasaran = int(pd.to_numeric(df_akum['Total Peserta (orang)'], errors='coerce').fillna(0).sum()) # Jumlah manusia!
                
                # ------ OLAH DATA TOTAL SASARAN PROVINSI BUAT GRAFIK ------
                df_provinsi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_sasaran_prov = data_sheets["form_responses"].copy()
                    
                    if 'Provinsi' in df_sasaran_prov.columns and 'Total Peserta (orang)' in df_sasaran_prov.columns:
                        # Bersihin angka dulu
                        df_sasaran_prov['Total Peserta (orang)'] = pd.to_numeric(
                            df_sasaran_prov['Total Peserta (orang)'], 
                            errors='coerce'
                        ).fillna(0)
                        
                        # Buang yg provinsinya kosong
                        df_sasaran_prov = df_sasaran_prov[
                            (df_sasaran_prov['Provinsi'].notna()) & 
                            (df_sasaran_prov['Provinsi'] != '')
                        ]
                        
                        # Gabung-gabungin (Group By) berdasarkan nama Provinsi lalu di-Sum peserta-nya
                        df_provinsi = df_sasaran_prov.groupby('Provinsi', as_index=False)['Total Peserta (orang)'].sum()
                        df_provinsi.columns = ['Provinsi', 'Total Peserta'] # Namain ulang kolomnya
                        df_provinsi = df_provinsi.sort_values('Total Peserta', ascending=False) # Urutin dari yg paling jumbo (descending)
                
                # ------ OLAH DATA TOPIK MATERI (Bisa multiple choice pisah koma) ------
                df_materi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_topik = data_sheets["form_responses"].copy()
                    
                    if 'Topik Materi' in df_topik.columns:
                        all_materi = df_topik['Topik Materi'].dropna().astype(str)
                        materi_list = []
                        for value in all_materi: # Sama triknya kek program swasembada, pecah koma!
                            if value.strip():
                                topics = [t.strip() for t in value.split(',') if t.strip()]
                                materi_list.extend(topics)
                        
                        materi_counts = pd.Series(materi_list).value_counts().reset_index() # Hitung jumlah
                        materi_counts.columns = ['Materi', 'Jumlah']
                        
                        total = materi_counts['Jumlah'].sum()
                        materi_counts['Persentase'] = (materi_counts['Jumlah'] / total * 100).round(1) # Bikin persen
                        df_materi = materi_counts
                
                # ------ OLAH DATA INOVASI TEKNOLOGI (Multiple choice lagi cuy) ------
                df_inovasi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_produk = data_sheets["form_responses"].copy()
                    kolom_inovasi = 'Jika inovasi teknologi modernisasi pertanian, komponen apa saja (Jawaban boleh lebih dari 1 pilihan)'
                    
                    if kolom_inovasi in df_produk.columns:
                        all_komponen = df_produk[kolom_inovasi].dropna().astype(str)
                        komponen_list = []
                        for value in all_komponen: # Sama lagi trik pecah koma wkwk (Gforms style begini ngerjain programmer!)
                            if value.strip():
                                items = [k.strip() for k in value.split(',') if k.strip()]
                                komponen_list.extend(items)
                        
                        produk_counts = pd.Series(komponen_list).value_counts().reset_index()
                        produk_counts.columns = ['Produk', 'Total Kegiatan']
                        df_inovasi = produk_counts
                
                # ------ OLAH DATA TOTAL PER PROFESI ------
                df_profesi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_profesi_raw = data_sheets["form_responses"].copy()
                    
                    profesi_columns = { # Pemetaan kolom-kolom orang yang ada di gsheets
                        'Peserta Petani (orang)': 'Peserta Petani (orang)',
                        'Peserta Penyuluh Pertanian (orang)': 'Peserta Penyuluh Pertanian (orang)',
                        'Peserta  POPT (orang)': 'Peserta  POPT (orang)',
                        'Peserta  PBT (orang)': 'Peserta  PBT (orang)',
                        'Peserta Babinsa (orang)': 'Peserta Babinsa (orang)',
                        'Peserta Staf Dinas (orang)': 'Peserta Staf Dinas (orang)',
                        'Peserta lainnya (orang) sebutkan': 'Peserta lainnya (orang) sebutkan'
                    }
                    
                    profesi_data = []
                    for kategori, kolom in profesi_columns.items(): # Iterasi semua kolom
                        if kolom in df_profesi_raw.columns:
                            # Totalin ke bawah per masing-masing kolom profesi
                            total = int(pd.to_numeric(df_profesi_raw[kolom], errors='coerce').fillna(0).sum())
                            profesi_data.append({'Kategori': kategori, 'Total Peserta': total}) # Masukin data ke list of dictionary
                    
                    if profesi_data:
                        df_profesi = pd.DataFrame(profesi_data) # Bungkus jadi dataframe
                        df_profesi = df_profesi.sort_values('Total Peserta', ascending=False) # Urutin biar cakep dr yg paling banyak
                
                # ------ OLAH DATA DAFTAR KAB/KOTA BUAT TABEL ------
                df_kabkota = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_kk_raw = data_sheets["form_responses"].copy()
                    
                    if 'Provinsi' in df_kk_raw.columns and 'Kabupaten/Kota' in df_kk_raw.columns and 'Total Peserta (orang)' in df_kk_raw.columns:
                        # Hapus yang kosong2
                        df_filtered = df_kk_raw[
                            (df_kk_raw['Provinsi'].notna()) & 
                            (df_kk_raw['Kabupaten/Kota'].notna()) &
                            (df_kk_raw['Provinsi'] != '') &
                            (df_kk_raw['Kabupaten/Kota'] != '')
                        ].copy()
                        
                        df_filtered['Total Peserta (orang)'] = pd.to_numeric(
                            df_filtered['Total Peserta (orang)'], 
                            errors='coerce'
                        ).fillna(0)
                        
                        # Group by Prov DAN Kab/Kota sekaligus, trus sum pesertanya (jadi per daerah detail)
                        df_kabkota = df_filtered.groupby(['Provinsi', 'Kabupaten/Kota'], as_index=False)['Total Peserta (orang)'].sum()
                        df_kabkota.columns = ['Provinsi', 'Kabupaten/Kota', 'Total Peserta']
                        df_kabkota = df_kabkota.sort_values('Total Peserta', ascending=False) # Urutin
                
                # ------ OLAH DATA INSTANSI NARASUMBER ------
                df_instansi = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_inst_raw = data_sheets["form_responses"].copy()
                    
                    if 'Narasumber' in df_inst_raw.columns:
                        kategori_valid = ['Internal BRMP', 'Pemerintah Daerah', 'NGO'] # Yg diterima mentah2
                        
                        # Fungsi buat nyelipin / grouping yang namanya aneh-aneh jadi "Lainnya"
                        def kategorikan_narasumber(value):
                            if pd.isna(value) or str(value).strip() == '': return None
                            value_str = str(value).strip()
                            if value_str in kategori_valid: return value_str
                            else: return 'Lainnya'
                        
                        # Aplikasikan fungsi di atas ke dataframe narasumber (pake .apply biar mantap!)
                        df_inst_raw['Kategori Narasumber'] = df_inst_raw['Narasumber'].apply(kategorikan_narasumber)
                        df_inst_filtered = df_inst_raw[df_inst_raw['Kategori Narasumber'].notna()]
                        
                        # Hitung jumlh kemunculan per instansi
                        instansi_counts = df_inst_filtered['Kategori Narasumber'].value_counts().reset_index()
                        instansi_counts.columns = ['Instansi', 'Jumlah Kegiatan']
                        
                        urutan_kategori = ['Internal BRMP', 'Pemerintah Daerah', 'NGO', 'Lainnya']
                        # Bikin kolom tempel buat sorting custom dr list kita di atas
                        instansi_counts['sort_order'] = instansi_counts['Instansi'].apply(
                            lambda x: urutan_kategori.index(x) if x in urutan_kategori else 99
                        )
                        df_instansi = instansi_counts.sort_values('sort_order').drop('sort_order', axis=1) # Selesai di-sort lgsg hapus tempelannya
                
                # ------ OLAH DATA PIE CHART ASAL NARASUMBER (INTERNAL/EKSTERNAL) ------
                df_narasumber_peserta = None
                if "form_responses" in data_sheets and not data_sheets["form_responses"].empty:
                    df_narpest_raw = data_sheets["form_responses"]
                    
                    if 'Narasumber' in df_narpest_raw.columns and 'Total Peserta (orang)' in df_narpest_raw.columns:
                        # Fungsi kelompokin internal v eksternal
                        def kategorikan_asal_narasumber(value):
                            if pd.isna(value) or str(value).strip() == '': return None
                            value_str = str(value).strip()
                            if value_str == 'Internal BRMP': return 'Internal'
                            elif value_str in ['Pemerintah Daerah', 'NGO']: return 'Eksternal'
                            else: return 'Lainnya'
                        
                        df_narpest_raw = df_narpest_raw.copy()
                        df_narpest_raw['Kategori Asal'] = df_narpest_raw['Narasumber'].apply(kategorikan_asal_narasumber)
                        df_filtered = df_narpest_raw[df_narpest_raw['Kategori Asal'].notna()].copy()
                        
                        df_filtered['Total Peserta (orang)'] = pd.to_numeric(
                            df_filtered['Total Peserta (orang)'], 
                            errors='coerce'
                        ).fillna(0)
                        
                        df_narasumber_peserta = df_filtered.groupby('Kategori Asal', as_index=False)['Total Peserta (orang)'].sum()
                        df_narasumber_peserta.columns = ['Narasumber', 'Total Peserta']
                        
                        # Sorting custom lagi
                        urutan_asal = ['Internal', 'Eksternal', 'Lainnya']
                        df_narasumber_peserta['sort_order'] = df_narasumber_peserta['Narasumber'].apply(
                            lambda x: urutan_asal.index(x) if x in urutan_asal else 99
                        )
                        df_narasumber_peserta = df_narasumber_peserta.sort_values('sort_order').drop('sort_order', axis=1)
                
            else: # Kalo gak masuk ke load sheet mana-mana (kosong)
                st.warning("Tidak ada data yang berhasil dimuat dari Google Sheets. Menggunakan data default.")
                
        except Exception as e: # Kalo ambyar beneran...
            st.warning(f"Menggunakan data default. Error: {str(e)}") # Fallback ke dummy
    else: # Kalo credential gak diset, kasih tau user
        if not sheets_config:
            st.info("Konfigurasi [sheets] belum diatur di secrets.toml. Saat ini menampilkan data contoh.")
        else:
            st.info("Konfigurasi Google Sheets belum lengkap di backend. Saat ini menampilkan data contoh.")
    
    # ------------------ MULAI NAMPILIN UI UTAMA: KPI TARGET ------------------
    st.markdown('<div class="section-header">PENCAPAIAN KPI PROGRAM SWASEMBADA TA 2025</div>', unsafe_allow_html=True)
    
    # Target-target dewa (Hardcoded value dari atasan wkwk)
    TARGET_LTT = 17005193
    TARGET_OPTIMASI = 500000 
    TARGET_CETAK_SAWAH = 225000
    TARGET_PADI_GOGO = 503457
    TARGET_BRIGADE = 2444
    
    total_optimasi = opt_lahan_rawa + opt_lahan_non_rawa # Rawa sama non digabung ya
    
    col1, col2, col3, col4, col5 = st.columns(5) # Bikin 5 kolom jajar genjang! Eh sejajar maksudnya
    
    # Render masing-masing card pakai data actual vs target pake fungsi pembantu tadi
    with col1:
        st.markdown(create_kpi_card("LTT Reguler", ltt_reguler, TARGET_LTT), unsafe_allow_html=True)
    with col2:
        st.markdown(create_kpi_card("Optimasi Lahan<br>(Rawa & Non Rawa)", total_optimasi, TARGET_OPTIMASI, "ha"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_kpi_card("Cetak Sawah Rakyat", cetak_sawah, TARGET_CETAK_SAWAH, "ha"), unsafe_allow_html=True)
    with col4:
        st.markdown(create_kpi_card("Padi Gogo", padi_gogo, TARGET_PADI_GOGO), unsafe_allow_html=True)
    with col5:
        st.markdown(create_kpi_card("Brigade Pangan", brigade_pangan, TARGET_BRIGADE), unsafe_allow_html=True)
        
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True) # Batas Suci
    
    # ------------------ NAMPILIN PANEL SUMMARY METRIK (Mingguan Vs Akumulasi) ------------------
    col_update, col_akumulasi = st.columns(2) # Belah dua layar
    
    with col_update:
        st.markdown('<div class="update-header">UPDATE MINGGUAN</div>', unsafe_allow_html=True)
        col_u1, col_u2, col_u3, col_u4 = st.columns(4) # Dalemnya pecah 4
        with col_u1:
            st.markdown(create_metric_card("Jumlah Kegiatan", update_kegiatan, "orange"), unsafe_allow_html=True)
        with col_u2:
            st.markdown(create_metric_card("Provinsi", update_provinsi, "orange"), unsafe_allow_html=True)
        with col_u3:
            st.markdown(create_metric_card("Kab/Kota", update_kab, "orange"), unsafe_allow_html=True)
        with col_u4:
            st.markdown(create_metric_card("Sasaran", update_sasaran, "orange"), unsafe_allow_html=True)
    
    with col_akumulasi:
        st.markdown('<div class="akumulasi-header">DATA AKUMULASI</div>', unsafe_allow_html=True)
        col_a1, col_a2, col_a3, col_a4 = st.columns(4) # Dalemnya pecah 4 juga
        with col_a1:
            st.markdown(create_metric_card("Jumlah Kegiatan", akum_kegiatan, "yellow"), unsafe_allow_html=True)
        with col_a2:
            st.markdown(create_metric_card("Provinsi", akum_provinsi, "yellow"), unsafe_allow_html=True)
        with col_a3:
            st.markdown(create_metric_card("Kab/Kota", akum_kab, "yellow"), unsafe_allow_html=True)
        with col_a4:
            st.markdown(create_metric_card("Sasaran", akum_sasaran, "yellow"), unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True) # Garisan lagi cuy
    
    # ------------------ SEKSI GRAFIK/CHART BARIS 1 ------------------
    col_chart1, col_chart2 = st.columns([1, 1]) # Bagi dua kolom seimbang
    
    with col_chart1:
        if show_chart_provinsi: # Cek izin admin, ditampilin gak?
            st.markdown('<div class="section-header">JUMLAH SASARAN BERDASARKAN PROVINSI</div>', unsafe_allow_html=True)
            
            if df_provinsi is not None and not df_provinsi.empty: # Kalo data real-nya ada
                pass # Pake datanya dong
            else: # Kalo ga dapet data, pakai data ngarang wkwk (biar pas presentasi nggak kosong blong)
                provinsi_data = {
                    'Provinsi': ['D.I Yogyakarta', 'Sulawesi Tengah', 'Jawa Tengah', 'Banten', 'Lampung', 'Gorontalo', 'Jambi', 'Riau', 'Kalimantan Selatan', 'Aceh', 'Bengkulu', 'DKI Jakarta', 'Maluku Utara', 'Papua Barat', 'Sulawesi Tenggara', 'Nusa Tenggara Timur', 'Sumatera Utara', 'Jawa Barat', 'Sumatera Barat', 'Maluku', 'Bali', 'Papua', 'Kepulauan Riau', 'Sulawesi Utara', 'Bangka Belitung', 'Kalimantan Barat', 'Sumatera Selatan', 'Papua Pegunungan', 'Papua Barat Daya', 'Papua Tengah'],
                    'Total Peserta': [1391, 1265, 1265, 1207, 1190, 1155, 1030, 960, 852, 584, 583, 578, 555, 483, 441, 434, 356, 325, 322, 248, 241, 212, 185, 168, 146, 130, 102, 50, 45, 30]
                }
                df_provinsi = pd.DataFrame(provinsi_data)
            
            fig_provinsi = go.Figure() # Mulai kanvas grafik baru
            fig_provinsi.add_trace(go.Bar( # Nambahin chart bentuk Bar (batang)
                y=df_provinsi['Provinsi'], # Sumbu y nama provinsinya
                x=df_provinsi['Total Peserta'], # Sumbu x pesertanya (jadi mendatar bar-nya, soalnya orientation h)
                orientation='h', # Mendatar (horizontal)
                marker=dict(color='#2E7D32', line=dict(color='#1B5E20', width=1)), # Warna hijau botol cakep
                text=df_provinsi['Total Peserta'], # Kasih tulisan angka di ujung batangnya
                textposition='outside', # Taruh diluar bar angkanya
                hovertemplate='<b>%{y}</b><br>Total Peserta: %{x:,}<extra></extra>' # Pop-up pas kursor dilewatin (hover)
            ))
            
            # Setting kosmetik (Margin, grid putih, font, dll)
            fig_provinsi.update_layout(
                height=700, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='white', paper_bgcolor='white',
                xaxis=dict(showgrid=True, gridcolor='#E0E0E0', title='', tickformat=','),
                yaxis=dict(showgrid=False, title='', autorange='reversed'), # autorange='reversed' biar yg paling banyak nongol di atas
                font=dict(size=11), showlegend=False
            )
            st.plotly_chart(fig_provinsi, use_container_width=True) # Render di Streamlit!!
    
    with col_chart2:
        if show_chart_materi: # Kalo dapet izin admin
            st.markdown('<div class="section-header">PERSENTASE TOPIK MATERI</div>', unsafe_allow_html=True)
            
            if df_materi is not None and not df_materi.empty: # Kalo data real ada
                labels = df_materi['Materi'].tolist() # Convert ke List (Array) biasa
                values = df_materi['Jumlah'].tolist()
            else: # Data ngibul (dummy) buat jaga-jaga
                topik_data = {
                    'Topik': ['Kebijakan/Program Pembangunan', 'Inovasi Teknologi Modernisasi Pertanian', 'Standardisasi'],
                    'Persentase': [47.9, 42.2, 9.9]
                }
                df_topik_default = pd.DataFrame(topik_data)
                labels = df_topik_default['Topik'].tolist()
                values = df_topik_default['Persentase'].tolist()
            
            # Bikin grafik Pie (Donat/Kue)
            fig_pie = go.Figure()
            fig_pie.add_trace(go.Pie(
                labels=labels, values=values, hole=0, # hole=0 berarti bolong tengahnya ga ada, pure pie chart
                marker=dict(colors=['#2E7D32', '#FBC02D', '#D32F2F', '#1976D2', '#F57C00', '#7B1FA2'], line=dict(color='white', width=2)),
                textinfo='percent', textfont=dict(size=14, color='white'), # Info yg nongol itu persentase, bukan angka bulet
                hovertemplate='<b>%{label}</b><br>Jumlah: %{value}<br>%{percent}<extra></extra>' # Pop-up infonya pas kursor ditaruh
            ))
            
            fig_pie.update_layout(
                height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05, font=dict(size=10)), # Posisin legenda di kanan grafik
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_pie, use_container_width=True) # Render di Streamlit cuy
        
        if show_chart_inovasi: # Kalo dapet perizinan admin
            st.markdown('<div class="section-header" style="margin-top: 30px;">KOMPONEN INOVASI TEKNOLOGI YANG DIGUNAKAN</div>', unsafe_allow_html=True)
            
            if df_inovasi is not None and not df_inovasi.empty:
                labels = df_inovasi['Produk'].tolist()
                values = df_inovasi['Total Kegiatan'].tolist()
            else: # Balik pake the power of dummy data
                inovasi_data = {
                    'Komponen': ['Sistem tanam', 'VUB', 'Alsintan', 'Sistem pengairan', 'Pengelolaan Hama Penyakit Terpadu', 'Rekomendasi pemupukan', 'Pemanenan', 'Penanganan pascapanen'],
                    'Total Kegiatan': [212, 212, 149, 135, 112, 85, 76, 48]
                }
                df_inovasi_default = pd.DataFrame(inovasi_data)
                labels = df_inovasi_default['Komponen'].tolist()
                values = df_inovasi_default['Total Kegiatan'].tolist()
            
            fig_inovasi = go.Figure()
            fig_inovasi.add_trace(go.Bar( # Bikin bar chart horisontal kyk yg provinsi tadi
                y=labels, x=values, orientation='h',
                marker=dict(color='#2E7D32', line=dict(color='#1B5E20', width=1)),
                text=values, textposition='outside',
                hovertemplate='<b>%{y}</b><br>Total Kegiatan: %{x}<extra></extra>'
            ))
            
            fig_inovasi.update_layout(
                height=350, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='white', paper_bgcolor='white',
                xaxis=dict(showgrid=True, gridcolor='#E0E0E0', title='', range=[0, max(values) * 1.15] if values else [0, 250]), # Ngasih space ekstra di ujung bar 15% biar teks ga kepotong layar
                yaxis=dict(showgrid=False, title='', autorange='reversed'), # reversed biar urutan paling byk diatas
                font=dict(size=11), showlegend=False
            )
            st.plotly_chart(fig_inovasi, use_container_width=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True) # Pembatas sakti
    
    # ------------------ BAGIAN TOTAL PESERTA PROFESI (ICON CARDS) ------------------
    st.markdown('<div class="profesi-header">JUMLAH SASARAN BERDASARKAN PROFESI</div>', unsafe_allow_html=True)
    
    # Kamus nyocokin nama di kolom excel sama emoji-emojinya yang kece badaaii
    icon_mapping = {
        'Peserta Petani (orang)': '👨‍🌾',
        'Peserta Penyuluh Pertanian (orang)': '👨‍🏫',
        'Peserta  POPT (orang)': '🦗',
        'Peserta  PBT (orang)': '🌾',
        'Peserta Babinsa (orang)': '👨‍✈️',
        'Peserta Staf Dinas (orang)': '👨‍💻',
        'Peserta lainnya (orang) sebutkan': '👔'
    }
    
    # Biar output icon boxnya urut sesuai urutan di bawah ini aja
    profesi_order = ['Peserta Petani (orang)', 'Peserta Penyuluh Pertanian (orang)', 'Peserta  POPT (orang)', 'Peserta  PBT (orang)', 'Peserta Babinsa (orang)', 'Peserta Staf Dinas (orang)', 'Peserta lainnya (orang) sebutkan']
    
    # Translasi nama kolom jelek Gsheet ke tulisan yg cantik buat dibaca user
    label_mapping = {
        'Peserta Petani (orang)': 'Petani',
        'Peserta Penyuluh Pertanian (orang)': 'Penyuluh Pertanian',
        'Peserta  POPT (orang)': 'Petugas Pengendalian Organisme Pengganggu Tumbuhan',
        'Peserta  PBT (orang)': 'Pengawas Benih Tanaman',
        'Peserta Babinsa (orang)': 'Babinsa',
        'Peserta Staf Dinas (orang)': 'Staf Dinas',
        'Peserta lainnya (orang) sebutkan': 'Profesi Lainnya'
    }
    
    profesi_list = [] # List buat nampung objek yang mo dirender
    
    profesi_values = {}
    if df_profesi is not None and not df_profesi.empty: # Tarik data real yg udah diproses di atas tadi
        for _, row in df_profesi.iterrows():
            profesi_values[row['Kategori']] = int(row['Total Peserta'])
    
    # Ngerakit datanya
    for kategori in profesi_order:
        profesi_list.append({
            'icon': icon_mapping.get(kategori, '👨‍🏫'), # Kasih icon, kl gada ksh icon guru fallback
            'label': label_mapping.get(kategori, kategori), # Ambil label bersih
            'value': profesi_values.get(kategori, 0) # Kasih default angka 0 kalo datanya kosong melompong
        })
    
    col_p1, col_p2, col_p3, col_p4 = st.columns(4, gap="large") # Bikin grid 4 kotak atas
    
    # Tembak masukin kode HTML murni biar bentuk card nya sesuai CSS di awal
    with col_p1:
        st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[0]["icon"]}</div><div class="profesi-label">{profesi_list[0]["label"]}</div><div class="profesi-value">{profesi_list[0]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p2:
        st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[1]["icon"]}</div><div class="profesi-label">{profesi_list[1]["label"]}</div><div class="profesi-value">{profesi_list[1]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p3:
        st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[2]["icon"]}</div><div class="profesi-label">{profesi_list[2]["label"]}</div><div class="profesi-value">{profesi_list[2]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p4:
        st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[3]["icon"]}</div><div class="profesi-label">{profesi_list[3]["label"]}</div><div class="profesi-value">{profesi_list[3]["value"]:,}</div></div>', unsafe_allow_html=True)
    
    # Biar susunannya asik: atas 4 kotak, bawah 3 kotak tapi di tengah. Kita pake spacer column!
    col_spacer1, col_p5, col_p6, col_p7, col_spacer2 = st.columns([0.5, 1, 1, 1, 0.5], gap="large")
    
    with col_p5:
        st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[4]["icon"]}</div><div class="profesi-label">{profesi_list[4]["label"]}</div><div class="profesi-value">{profesi_list[4]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p6:
        st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[5]["icon"]}</div><div class="profesi-label">{profesi_list[5]["label"]}</div><div class="profesi-value">{profesi_list[5]["value"]:,}</div></div>', unsafe_allow_html=True)
    with col_p7:
        st.markdown(f'<div class="profesi-card"><div class="profesi-icon">{profesi_list[6]["icon"]}</div><div class="profesi-label">{profesi_list[6]["label"]}</div><div class="profesi-value">{profesi_list[6]["value"]:,}</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True) # Sekat pemisah lagi bro
    
    # ------------------ BAGIAN TABEL DAN CHART INSTANSI BAWAH ------------------
    col_table, col_charts = st.columns([1, 1]) # Bagi 2 layar seimbang
    
    with col_table:
        if show_tabel_kabkota: # Kalo admin setuju
            st.markdown('<div class="table-header-orange">JUMLAH SASARAN TERCAPAI PER KAB/KOTA</div>', unsafe_allow_html=True)
            
            if df_kabkota is not None and not df_kabkota.empty:
                df_display = df_kabkota.copy()
                df_display.insert(0, 'No', range(1, len(df_display) + 1)) # Disisipin kolom angka urutan 1,2,3... di paling kiri
                df_display['Total Peserta'] = df_display['Total Peserta'].apply(lambda x: f"{int(x):,}") # Format ribuan angka pesertanya biar pake koma
            else: # Siapin data bayangan buat pameran/demo
                kab_kota_data = {
                    'No': list(range(1, 101)),
                    'Provinsi': ['Sumatera Utara', 'Sumatera Selatan', 'Sumatera Selatan', 'Sumatera Barat', 'Sumatera Barat'] * 20, # Dikali 20 biar panjang!
                    'Kabupaten/Kota': ['Langkat', 'OGAN KOMERING ILIR', 'MUSI RAWAS UTARA', 'Solok Selatan', 'Kabupaten Dharmasraya'] * 20,
                    'Total Peserta': ['356', '30', '72', '20', '61'] * 20
                }
                df_display = pd.DataFrame(kab_kota_data)
            
            # Tampilin dataframe pandasnya jadi elemen interaktif Streamlit, hide_index=True ngebuang kolom index bawaan pandas (0,1,2..) yg ga dipake
            st.dataframe(df_display, use_container_width=True, hide_index=True, height=600) 
            st.caption(f"Total: {len(df_display)} entries") # Tulisan kcil di pojok bawah sbg info jumlah baris
    
    with col_charts:
        if show_chart_instansi:
            st.markdown('<div class="chart-header-green">ASAL INSTANSI NARASUMBER</div>', unsafe_allow_html=True)
            
            if df_instansi is not None and not df_instansi.empty:
                labels = df_instansi['Instansi'].tolist()
                values = df_instansi['Jumlah Kegiatan'].tolist()
            else: # Data bohongan part kesekian kalinya
                instansi_data = {'Instansi': ['Internal BRMP', 'Lainnya', 'Pemerintah Daerah', 'NGO', 'Tidak Ada'], 'Jumlah Kegiatan': [310, 100, 38, 2, 2]}
                df_instansi_default = pd.DataFrame(instansi_data)
                labels = df_instansi_default['Instansi'].tolist()
                values = df_instansi_default['Jumlah Kegiatan'].tolist()
            
            fig_instansi = go.Figure()
            fig_instansi.add_trace(go.Bar( # Bikin bar chart vertikal
                x=labels, y=values, marker=dict(color='#2E7D32', line=dict(color='#1B5E20', width=1)),
                text=values, textposition='outside', hovertemplate='<b>%{x}</b><br>Jumlah Kegiatan: %{y}<extra></extra>'
            ))
            
            fig_instansi.update_layout(
                height=300, margin=dict(l=20, r=20, t=20, b=60), plot_bgcolor='white', paper_bgcolor='white',
                xaxis=dict(showgrid=False, title='', tickangle=-15), # Teks miring -15 drajat biar ga numpuk kl panjang
                yaxis=dict(showgrid=True, gridcolor='#E0E0E0', title='', range=[0, 450]),
                font=dict(size=11), showlegend=False
            )
            st.plotly_chart(fig_instansi, use_container_width=True)
            
        if show_chart_narasumber_pie:
            st.markdown('<div class="chart-header-green" style="margin-top: 30px;">PERSENTASE ASAL NARASUMBER BERDASARKAN JUMLAH PESERTA</div>', unsafe_allow_html=True)
            
            if df_narasumber_peserta is not None and not df_narasumber_peserta.empty:
                labels = df_narasumber_peserta['Narasumber'].tolist()
                values = df_narasumber_peserta['Total Peserta'].tolist()
            else: # Yoi, dummy data pie narasumber
                narasumber_data = {'Asal': ['Internal', 'Lainnya', 'Eksternal'], 'Persentase': [52.6, 46.7, 0.7]}
                df_narasumber_default = pd.DataFrame(narasumber_data)
                labels = df_narasumber_default['Asal'].tolist()
                values = df_narasumber_default['Persentase'].tolist()
            
            fig_narasumber_pie = go.Figure()
            fig_narasumber_pie.add_trace(go.Pie(
                labels=labels, values=values, hole=0, # Bukan donat
                marker=dict(colors=['#2E7D32', '#FBC02D', '#FF9800', '#1976D2', '#D32F2F'], line=dict(color='white', width=2)),
                textinfo='percent', textfont=dict(size=14, color='white'), hovertemplate='<b>%{label}</b><br>Total: %{value:,}<br>%{percent}<extra></extra>'
            ))
            
            fig_narasumber_pie.update_layout(
                height=300, margin=dict(l=20, r=20, t=20, b=20), showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10)), # Pindah legend ke bagian bawah (h = horisontal)
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_narasumber_pie, use_container_width=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True) # Skat lagi

    # ------------------ GRAFIK EKSTRA BAWAH, TREN WAKTU DLL ------------------
    if show_chart_1:
        st.markdown('<div class="chart-header-green">LINE CHART TREN KEGIATAN/PESERTA</div>', unsafe_allow_html=True)

        trend_df = pd.DataFrame() # Bikin dataframe pandas kosong
        if df_form_responses is not None and not df_form_responses.empty:
            trend_df = df_form_responses.copy()
            if 'Tanggal Pelaksanaan Kegiatan' in trend_df.columns: # Kalau ada kolom tgl
                trend_df['Tanggal Pelaksanaan Kegiatan'] = pd.to_datetime(trend_df['Tanggal Pelaksanaan Kegiatan'], errors='coerce') # Jadiin format datetime
                trend_df = trend_df[trend_df['Tanggal Pelaksanaan Kegiatan'].notna()].copy() # Buang yg error

                if 'Total Peserta (orang)' in trend_df.columns:
                    trend_df['Total Peserta (orang)'] = pd.to_numeric(trend_df['Total Peserta (orang)'], errors='coerce').fillna(0) # Buat jaga-jaga kl teks disulap jd 0
                else:
                    trend_df['Total Peserta (orang)'] = 0

                if not trend_df.empty:
                    trend_df['Periode'] = trend_df['Tanggal Pelaksanaan Kegiatan'].dt.to_period('M').astype(str) # Ubah ke bentuk Tahun-Bulan doang (2025-01, dll)

                    trend_df = ( # Group dan hitung tren per bulannya
                        trend_df.groupby('Periode', as_index=False)
                        .agg(
                            Jumlah_Kegiatan=('Periode', 'count'), # Baris dihitung
                            Total_Peserta=('Total Peserta (orang)', 'sum') # Peserta di-sum
                        )
                        .sort_values('Periode') # Urut waktu jalan
                    )

        if trend_df.empty: # Fallback the king of dummy data
            trend_df = pd.DataFrame({'Periode': ['2025-01', '2025-02', '2025-03', '2025-04'], 'Jumlah_Kegiatan': [18, 24, 21, 26], 'Total_Peserta': [640, 910, 805, 980]})

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter( # Bikin garis buat ngitung jumlah kegiatan doang (Sumbu Y kiri)
            x=trend_df['Periode'], y=trend_df['Jumlah_Kegiatan'], mode='lines+markers', name='Jumlah Kegiatan', # ada titik bullet per bulannya 
            line=dict(color='#2E7D32', width=3), marker=dict(size=7), hovertemplate='<b>%{x}</b><br>Jumlah Kegiatan: %{y:,}<extra></extra>',
        ))
        fig_trend.add_trace(go.Scatter( # Bikin garis ke-2 buat total peserta, pake sumbu Y kanan krn skalanya jauh (puluhan vs ribuan)
            x=trend_df['Periode'], y=trend_df['Total_Peserta'], mode='lines+markers', name='Total Peserta',
            line=dict(color='#F57C00', width=3), marker=dict(size=7), yaxis='y2', # Ini ngeset biar nempel ke y-axis ke2 di kanan layar
            hovertemplate='<b>%{x}</b><br>Total Peserta: %{y:,}<extra></extra>',
        ))
        fig_trend.update_layout(
            height=430, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='white', paper_bgcolor='white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1), # Taro legenda di atas kanan
            xaxis=dict(showgrid=False, title=''), # Sumbu X
            yaxis=dict(showgrid=True, gridcolor='#E0E0E0', title='Jumlah Kegiatan'), # Sumbu Y kiri
            yaxis2=dict(title='Total Peserta', overlaying='y', side='right', showgrid=False), # Sumbu Y kanan (yaxis2)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    if show_chart_2:
        st.markdown('<div class="chart-header-green">STACKED BAR KOMPOSISI PESERTA PERWILAYAH</div>', unsafe_allow_html=True)

        stacked_df = pd.DataFrame()
        if df_form_responses is not None and not df_form_responses.empty:
            base_df = df_form_responses.copy()
            group_col = 'Provinsi' # Grouping berdasarkan apa nih

            profesi_columns = { # Daftar kolom sbg komponen stack-nya
                'Petani': 'Peserta Petani (orang)', 'Penyuluh': 'Peserta Penyuluh Pertanian (orang)',
                'POPT': 'Peserta  POPT (orang)', 'PBT': 'Peserta  PBT (orang)',
                'Babinsa': 'Peserta Babinsa (orang)', 'Staf Dinas': 'Peserta Staf Dinas (orang)',
                'Lainnya': 'Peserta lainnya (orang) sebutkan',
            }

            if group_col in base_df.columns:
                base_df = base_df[base_df[group_col].notna() & (base_df[group_col] != '')].copy() # Filter blank text
                for col in profesi_columns.values():
                    if col in base_df.columns:
                        base_df[col] = pd.to_numeric(base_df[col], errors='coerce').fillna(0) # Ubah ke angka sblm digabung 
                    else:
                        base_df[col] = 0

                agg_dict = {source_col: 'sum' for source_col in profesi_columns.values()} # Nyiapin instruksi Sum ke agg
                grouped = base_df.groupby(group_col, as_index=False).agg(agg_dict) # Execute group by + sum tiap kolom secara otomatis!
                grouped['Total'] = grouped[list(profesi_columns.values())].sum(axis=1) # Bikin kolom "Total" per baris buat sorting ntar 
                grouped = grouped.sort_values('Total', ascending=False).head(15) # Ngurutin & cuma ditampilin Top 15 aja biar gak kepenuhan 

                stacked_df = grouped.rename(columns={v: k for k, v in profesi_columns.items()}) # Rename kolom pakai label yg asik dibaca

        if stacked_df.empty: # Dummy data lagi~
            stacked_df = pd.DataFrame({
                'Wilayah': ['Wilayah A', 'Wilayah B', 'Wilayah C', 'Wilayah D'], 'Petani': [120, 95, 88, 72],
                'Penyuluh': [30, 25, 22, 20], 'POPT': [18, 14, 12, 10], 'PBT': [15, 11, 10, 8],
                'Babinsa': [22, 18, 16, 14], 'Staf Dinas': [25, 20, 19, 15], 'Lainnya': [12, 10, 9, 7],
            })
            x_col = 'Wilayah'
        else:
            x_col = 'Provinsi'

        fig_stacked = go.Figure()
        for profesi_name in ['Petani', 'Penyuluh', 'POPT', 'PBT', 'Babinsa', 'Staf Dinas', 'Lainnya']: # Nambahin layer chart bertumpuk baris per barisnya
            if profesi_name in stacked_df.columns:
                fig_stacked.add_trace(go.Bar(
                    x=stacked_df[x_col], y=stacked_df[profesi_name], name=profesi_name,
                    hovertemplate=f'<b>%{{x}}</b><br>{profesi_name}: %{{y:,}}<extra></extra>', # Popup pas disentuh kursor
                ))

        fig_stacked.update_layout(
            barmode='stack', # INI KUNCI BIAR NAMPAK BERTUMPUK JADI SATU BAR!
            height=450, margin=dict(l=20, r=20, t=20, b=80), plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(title='', tickangle=-30, showgrid=False), # Dimiringin teksnya biar gak tabrakan 
            yaxis=dict(title='Total Peserta', showgrid=True, gridcolor='#E0E0E0'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1), # Legenda nangkring di atas
        )
        st.plotly_chart(fig_stacked, use_container_width=True)

    if show_chart_3:
        st.markdown('<div class="chart-header-green">BAR CHART RATA-RATA PESERTA PER KEGIATAN</div>', unsafe_allow_html=True)

        avg_df = pd.DataFrame()
        if df_form_responses is not None and not df_form_responses.empty:
            src_df = df_form_responses.copy()
            if 'Program Swasembada' in src_df.columns and 'Total Peserta (orang)' in src_df.columns:
                src_df['Total Peserta (orang)'] = pd.to_numeric(src_df['Total Peserta (orang)'], errors='coerce').fillna(0) # Angkain
                src_df = src_df[src_df['Program Swasembada'].notna() & (src_df['Program Swasembada'] != '')] # Filter yg programnya ga isi

                rows = []
                for _, row in src_df.iterrows(): # Iterasi per baris karena nama programnya bisa nyampur dipisah koma (multiple choice)
                    programs = [p.strip() for p in str(row['Program Swasembada']).split(',') if p.strip()] # Pecah per program
                    for p in programs:
                        rows.append({'Program': p, 'Peserta': row['Total Peserta (orang)']}) # Tambahin record pecahannya

                if rows:
                    exploded_df = pd.DataFrame(rows) # Jadiin dataframe yg bener
                    avg_df = ( # Cek rata-rata pesertanya! (mean)
                        exploded_df.groupby('Program', as_index=False)
                        .agg(
                            Rata_rata_Peserta=('Peserta', 'mean'), # 'mean' = hitung rata-rata angka di list itu
                            Jumlah_Kegiatan=('Program', 'count')
                        )
                        .sort_values('Rata_rata_Peserta', ascending=False)
                    )

        if avg_df.empty: # Dummy bro 
            avg_df = pd.DataFrame({
                'Program': ['LTT Reguler', 'Optimasi Lahan Rawa', 'Cetak Sawah Rakyat', 'Brigade Pangan'],
                'Rata_rata_Peserta': [42.5, 38.2, 35.8, 30.3], 'Jumlah_Kegiatan': [40, 26, 22, 18],
            })

        fig_avg = go.Figure()
        fig_avg.add_trace(go.Bar(
            x=avg_df['Program'], y=avg_df['Rata_rata_Peserta'],
            marker=dict(color='#66BB6A', line=dict(color='#2E7D32', width=1)),
            text=avg_df['Rata_rata_Peserta'].round(1), # Pembulatan 1 angka belakang koma
            textposition='outside', hovertemplate='<b>%{x}</b><br>Rata-rata Peserta: %{y:.1f}<extra></extra>',
        ))
        fig_avg.update_layout(
            height=420, margin=dict(l=20, r=20, t=20, b=80), plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(title='', tickangle=-20, showgrid=False), yaxis=dict(title='Rata-rata Peserta per Kegiatan', showgrid=True, gridcolor='#E0E0E0'),
            showlegend=False,
        )
        st.plotly_chart(fig_avg, use_container_width=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True) # Last divider!
    
    # Cetak timestamp kpn dirender
    st.markdown(f"**Last updated:** {datetime.now().strftime('%d %B %Y, %H:%M:%S')}") 
    
    # Nempelin blok custom HTML paling bawah sbg footer
    st.markdown("""
    <div class="footer-container">
        <p style="margin: 10px 0; padding-bottom: 0;">© 2025 BRMP PENERAPAN KEMENTERIAN PERTANIAN</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Hack CSS murni buat Streamlit, ngerubah bottom padding di tag parentnya biar footernya kedorong poll ke bawah
    st.markdown('<style>div.block-container{padding-bottom: 0rem;}</style>', unsafe_allow_html=True)

    trigger_print_if_requested() # Panggil fungsi eksekutor auto-print PDF! (Kalo disuruh di URL tadi lho)

# INI MAIN ENTRY POINT PROGRAMNYA: (Dieksekusi pas filenya dijalanin)
if __name__ == "__main__":
    init_admin_state() # 1. Siapin otak state-nya

    current_route = get_current_route() # 2. Cek user lagi numpang baca di URL mana (dashboard/admin)
    if current_route == "admin":
        render_admin_page() # 3. Kalo /admin ya muat si halaman rahasia admin
    else:
        render_dashboard() # 4. Kalo ga, tampilin dashboard utamanya biar seru!
