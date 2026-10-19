import requests
import json
import random
import string

# --- KONFIGURASI PORTAL ---
PORTAL_URL = "https://foxbleu.pro/c/" # Jalur portal (pastikan ada /c/ di akhir)
MAC_ADDRESS = "00:1A:79:86:82:B5"                   # Alamat MAC Anda

# Membuat Serial Number & Device ID tiruan agar lolos blokir server
def generate_random_hex(length):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

serial_number = "MAG" + generate_random_hex(10).upper()
device_id = generate_random_hex(40).upper()
device_id2 = generate_random_hex(40).upper()
signature = generate_random_hex(40).upper()

headers = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp/2.1.4.r7 Profile/MIDP-2.0 Configuration/CLDC-1.1",
    "X-User-Agent": "model=MAG250; link=mac",
    "Referer": f"{PORTAL_URL}index.html",
    "Cookie": f"mac={MAC_ADDRESS}; stb_lang=en; timezone=GMT",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

def get_token():
    # Menyertakan parameter handshake yang lengkap seperti OTT Navigator/STB asli
    params = {
        "type": "stb",
        "action": "handshake",
        "js": "1",
        "token": "",
        "sn": serial_number,
        "stb_type": "MAG250",
        "image_version": "218",
        "video_out": "hdmi",
        "device_id": device_id,
        "device_id2": device_id2,
        "signature": signature,
        "mac": MAC_ADDRESS
    }
    
    url = f"{PORTAL_URL}"
    try:
        res = requests.get(url, headers=headers, params=params, timeout=12)
        print(f"Status HTTP Handshake: {res.status_code}")
        data = res.json()
        
        # Mengambil token dinamis dari respon server
        token = data.get("js", {}).get("token")
        if token:
            return token
        else:
            print("Server merespon tetapi tidak memberikan token otentikasi.")
            return None
    except Exception as e:
        print(f"Koneksi gagal atau format salah: {e}")
        return None

def get_categories(token):
    params = {"type": "itv", "action": "get_genres", "token": token}
    categories = {}
    try:
        res = requests.get(PORTAL_URL, headers=headers, params=params, timeout=10).json()
        for item in res.get("js", []):
            categories[item["id"]] = item["title"]
    except:
        pass
    return categories

def main():
    token = get_token()
    if not token:
        print("Gagal melakukan Handshake / Akses Ditolak.")
        return
    
    print(f"Handshake Berhasil! Token aktif didapatkan.")
    categories = get_categories(token)
    
    params = {"type": "itv", "action": "get_all_channels", "token": token}
    try:
        res = requests.get(PORTAL_URL, headers=headers, params=params, timeout=15).json()
        channels = res.get("js", {}).get("data", [])
    except:
        print("Gagal mengambil daftar channel.")
        return

    if not channels:
        print("Tidak ada channel yang ditemukan di server.")
        return

    print(f"Sukses menarik {len(channels)} channel. Membuat file M3U...")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for ch in channels:
            name = ch.get("name", "Unknown Channel")
            
            # Abaikan baris kosong atau baris judul kategori palsu
            if not name or name.startswith("-") or "--------" in name:
                continue
                
            ch_id = ch.get("cmd", "").replace("ffmpeg ", "").replace("ffrt ", "")
            
            # Membuat link streaming ke server asli, bukan localhost
            base_url = PORTAL_URL.split("/c/")[0]
            stream_url = f"{base_url}/{ch_id}"
            if "http" in ch_id:
                stream_url = ch_id
            
            genre_id = ch.get("tv_genre_id", "")
            group = categories.get(genre_id, "Lain-lain")
            
            logo = ch.get("logo", "")
            logo_attr = f' tvg-logo="{logo}"' if logo else ""
            
            f.write(f'#EXTINF:-1{logo_attr} group-title="{group}",{name}\n')
            f.write(f'{stream_url}\n')
            
    print("Selesai! File playlist.m3u berhasil diperbarui dengan kategori dan logo.")

if __name__ == "__main__":
    main()
