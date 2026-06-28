# Pake cache_resource biar koneksi ke GSheets ga di-restart terus tiap user nge-klik sesuatu
@st.cache_resource
def connect_to_gsheets():
    try: # Nyoba konek nih
        # Ambil salinan dict credential dari secrets agar bisa dimodifikasi di memori
        credentials_dict = dict(st.secrets["gserviceaccount"])
        
        # --- LOGIKA RADIKAL SANITASI KUNCI PEM PRIVATE KEY ---
        raw_key = str(credentials_dict["private_key"])
        
        # 1. Hapus penulisan teks literal \n jika ada yang terlepas
        raw_key = raw_key.replace("\\n", "")
        
        # 2. Bersihkan header dan footer bawaan agar tidak ikut tersaring
        raw_key = raw_key.replace("-----BEGIN PRIVATE KEY-----", "")
        raw_key = raw_key.replace("-----END PRIVATE KEY-----", "")
        
        # 3. BUANG SEMUA SPASI, ENTER, TAB, DAN BARIS BARU TERSEMBUNYI
        # Ini akan menyatukan seluruh isi kunci menjadi satu baris teks murni tanpa cela
        clean_body = "".join(raw_key.split())
        
        # 4. Bungkus ulang menjadi struktur PEM standar industri yang sah
        perfect_pem_key = f"-----BEGIN PRIVATE KEY-----\n{clean_body}\n-----END PRIVATE KEY-----\n"
        credentials_dict["private_key"] = perfect_pem_key
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
