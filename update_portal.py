import requests
import json
import random
import string
import urllib.parse

# ==================== KONFIGURASI UTAMA ====================
PORTAL_URL = "http://foxbleu.pro" 
MAC_ADDRESS = "00:1A:79:86:82:B5"  # Sesuai log error Anda sebelumnya
# ===========================================================

def generate_hex(length):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

# Membuat identitas perangkat palsu tingkat lanjut
serial_number = "MAG" + generate_hex(10).upper()
device_id = generate_hex(40).upper()
device_id2 = generate_hex(40).upper()
signature = generate_hex(40).upper()

headers = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp/2.1.4.r7 Profile/MIDP-2.0 Configuration/CLDC-1.1",
    "X-User-Agent": "model=MAG250; link=mac",
    "Referer": f"{PORTAL_URL}index.html",
    "Cookie": f"mac={MAC_ADDRESS}; stb_lang=en; timezone=Asia/Jakarta",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

def get_token():
    params = {
        "type": "stb", "action": "handshake", "js": "1",
        "sn": serial_number, "stb_type": "MAG250", "image_version": "218",
        "device_id": device_id, "device_id2": device_id2, "signature": signature,
        "mac": MAC_ADDRESS
    }
    try:
        # Menggunakan HTTP biasa (port 80) sesuai domain foxbleu
        res = requests.get(PORTAL_URL, headers=headers, params=params, timeout=15)
        data = res.json()
        return data.get("js", {}).get("token")
    except Exception as e:
        print(f"[-] Gagal Handshake: {e}")
        return None

def get_categories(token):
    params = {"type": "itv", "action": "get_genres", "token": token}
    categories = {}
    try:
        res = requests.get(PORTAL_URL, headers=headers, params=params, timeout=15).json()
        for item in res.get("js", []):
            categories[item["id"]] = item["title"]
    except:
        pass
    return categories

def main():
    print("[*] Memulai proses bypass jabat tangan (Handshake)...")
    token = get_token()
    if not token:
        print("[-] Akses tetap ditolak oleh server. IP GitHub Anda kemungkinan diblokir.")
        return
    
    print(f"[+] Handshake Sukses! Token Sesi Aktif: {token}")
    categories = get_categories(token)
    
    params = {"type": "itv", "action": "get_all_channels", "token": token}
    try:
        res = requests.get(PORTAL_URL, headers=headers, params=params, timeout=20).json()
        channels = res.get("js", {}).get("data", [])
    except:
        print("[-] Gagal mengunduh daftar siaran.")
        return

    if not channels:
        print("[-] Tidak ada siaran ditemukan.")
        return

    print(f"[+] Berhasil memuat {len(channels)} siaran. Menyusun Playlist M3U...")

    # Membersihkan domain utama untuk link streaming
    base_stream_url = PORTAL_URL.replace("/c/", "")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for ch in channels:
            name = ch.get("name", "").strip()
            
            # Abaikan baris pembatas dekorasi palsu (seperti tanda bintang/garis)
            if not name or name.startswith("-") or "★" in name or "●" in name:
                continue
                
            ch_cmd = ch.get("cmd", "")
            if not ch_cmd:
                continue

            # Trik Inti: Bersihkan perintah internal STB (ffmpeg / ffrt)
            clean_cmd = ch_cmd.replace("ffmpeg ", "").replace("ffrt ", "").replace("auto ", "")
            
            # Trik Inti: Bangun URL Streaming agar menyertakan Token Resmi
            if clean_cmd.startswith("http"):
                stream_url = clean_cmd
            else:
                # Format URL standar Stalker Middleware untuk pemutaran eksternal
                stream_url = f"{base_stream_url}/{clean_cmd}"

            # Menyisipkan token ke dalam URL siaran jika server membutuhkannya
            if "?" in stream_url:
                stream_url += f"&token={token}"
            else:
                stream_url += f"?token={token}"

            # Ambil kategori asli
            genre_id = ch.get("tv_genre_id", "")
            group = categories.get(genre_id, "Lain-Lain")
            
            # Ambil logo stasiun TV asli dari server
            logo = ch.get("logo", "")
            logo_attr = f' tvg-logo="{logo}"' if logo else ""
            
            # Tulis data dengan struktur format Extended M3U terlengkap
            f.write(f'#EXTINF:-1{logo_attr} group-title="{group}",{name}\n')
            f.write(f'{stream_url}\n')
            
    print("[+] SELESAI! File 'playlist.m3u' kini memiliki kategori, logo, dan tautan bypass token.")

if __name__ == "__main__":
    main()
