import requests
import json
import re

# --- KONFIGURASI PORTAL ---
# Ganti dengan URL Portal dan Alamat MAC Anda yang aktif
PORTAL_URL = "http://foxbleu.pro/c/" 
MAC_ADDRESS = "00:1A:79:86:82:B5"

headers = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp/2.1.4.r7 Profile/MIDP-2.0 Configuration/CLDC-1.1",
    "Cookie": f"mac={MAC_ADDRESS}"
}

def get_token():
    url = f"{PORTAL_URL}?type=stb&action=handshake"
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        return res.get("js", {}).get("token")
    except:
        return None

def get_categories(token):
    url = f"{PORTAL_URL}?type=itv&action=get_genres&token={token}"
    categories = {}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        for item in res.get("js", []):
            categories[item["id"]] = item["title"]
    except:
        pass
    return categories

def main():
    token = get_token()
    if not token:
        print("Gagal melakukan Handshake / Akses Ditolak")
        return
    
    # Ambil data kategori dahulu
    categories = get_categories(token)
    
    # Ambil data seluruh channel
    url = f"{PORTAL_URL}?type=itv&action=get_all_channels&token={token}"
    try:
        res = requests.get(url, headers=headers, timeout=15).json()
        channels = res.get("js", {}).get("data", [])
    except:
        print("Gagal mengambil data channel")
        return

    if not channels:
        print("Tidak ada channel ditemukan")
        return

    print(f"Sukses menarik {len(channels)} channel. Membuat file M3U...")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for ch in channels:
            name = ch.get("name", "Unknown Channel")
            
            # Lewati jika ini hanya baris pembatas kategori palsu (seperti contoh FR | TNT Anda)
            if name.startswith("-") or "--------" in name:
                continue
                
            ch_id = ch.get("cmd", "").replace("ffmpeg ", "")
            
            # Perbaikan URL agar mengarah ke server asli, bukan localhost
            stream_url = f"{PORTAL_URL.replace('/c/', '')}/{ch_id}"
            if "http" in ch_id:
                stream_url = ch_id
            
            # Ambil kategori asli berdasarkan ID genre
            genre_id = ch.get("tv_genre_id", "")
            group = categories.get(genre_id, "Lain-lain")
            
            # Ambil logo jika tersedia
            logo = ch.get("logo", "")
            logo_attr = f' tvg-logo="{logo}"' if logo else ""
            
            # Tulis dengan format Extended M3U yang benar
            f.write(f'#EXTINF:-1{logo_attr} group-title="{group}",{name}\n')
            f.write(f'{stream_url}\n')
            
    print("File playlist.m3u berhasil diperbarui dengan kategori dan logo!")

if __name__ == "__main__":
    main()
