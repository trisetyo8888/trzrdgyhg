import requests
import json
import random
import string
import time

# ==================== KONFIGURASI UTAMA ====================
PORTAL_URL = "http://foxbleu.pro/c" 
MAC_ADDRESS = "00:1A:79:86:82:B5"
# ===========================================================

def generate_hex(length):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

# Membuat identitas perangkat tiruan agar lolos dari deteksi bot
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

def fetch_free_proxies():
    print("[*] Mengambil daftar proxy publik gratis...")
    proxy_urls = [
        "https://proxyscrape.com",
        "https://githubusercontent.com"
    ]
    proxies = []
    for url in proxy_urls:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                # Memisahkan baris teks untuk mendapatkan list IP:Port
                found = [line.strip() for line in res.text.split("\n") if line.strip() and not line.startswith("{")]
                proxies.extend(found)
        except:
            continue
    # Acak daftar proxy agar tidak menggunakan IP yang sama terus-menerus
    random.shuffle(proxies)
    print(f"[+] Berhasil mengumpulkan {len(proxies)} kandidat proxy.")
    return proxies

def test_handshake_with_proxy(proxy_str):
    proxy_dict = {
        "http": f"http://{proxy_str}",
        "https": f"http://{proxy_str}"
    }
    params = {
        "type": "stb", "action": "handshake", "js": "1",
        "sn": serial_number, "stb_type": "MAG250", "image_version": "218",
        "device_id": device_id, "device_id2": device_id2, "signature": signature,
        "mac": MAC_ADDRESS
    }
    try:
        # Mencoba melakukan handshake ke server FoxBleu menggunakan proxy pilihan
        res = requests.get(PORTAL_URL, headers=headers, params=params, proxies=proxy_dict, timeout=7)
        data = res.json()
        token = data.get("js", {}).get("token")
        if token:
            return token, proxy_dict
    except:
        pass
    return None, None

def get_categories(token, proxies):
    params = {"type": "itv", "action": "get_genres", "token": token}
    categories = {}
    try:
        res = requests.get(PORTAL_URL, headers=headers, params=params, proxies=proxies, timeout=15).json()
        for item in res.get("js", []):
            categories[item["id"]] = item["title"]
    except:
        pass
    return categories

def main():
    proxy_list = fetch_free_proxies()
    token = None
    active_proxy = None
    
    print("[*] Memulai rotasi proxy untuk mencari koneksi yang lolos blokir...")
    # Mencoba maksimal 30 proxy teratas dari daftar acak
    for i, proxy in enumerate(proxy_list[:30]):
        print(f"    [{i+1}/30] Mencoba Proxy: {proxy} ...")
        token, active_proxy = test_handshake_with_proxy(proxy)
        if token:
            print(f"\n[+] BERHASIL TANDING TANGAN! Menggunakan Proxy: {proxy}")
            print(f"[+] Token Sesi Aktif Didapatkan: {token}\n")
            break
            
    if not token:
        print("\n[-] Semua proxy gagal menembus server. Server mendeteksi JSON bermasalah / IP diblokir.")
        print("[-] Disarankan jalankan secara LOKAL di laptop Anda tanpa GitHub Actions.")
        return
    
    # Ambil data kategori menggunakan proxy yang terbukti aktif
    categories = get_categories(token, active_proxy)
    
    params = {"type": "itv", "action": "get_all_channels", "token": token}
    try:
        print("[*] Mengunduh seluruh daftar siaran via proxy...")
        res = requests.get(PORTAL_URL, headers=headers, params=params, proxies=active_proxy, timeout=25).json()
        channels = res.get("js", {}).get("data", [])
    except Exception as e:
        print(f"[-] Gagal mengambil siaran: {e}")
        return

    if not channels:
        print("[-] Server tidak mengembalikan data siaran.")
        return

    print(f"[+] Sukses mengekstrak {len(channels)} siaran. Menyusun file M3U...")
    base_stream_url = PORTAL_URL.replace("/c/", "")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for ch in channels:
            name = ch.get("name", "").strip()
            if not name or name.startswith("-") or "★" in name or "●" in name:
                continue
                
            ch_cmd = ch.get("cmd", "")
            if not ch_cmd:
                continue

            clean_cmd = ch_cmd.replace("ffmpeg ", "").replace("ffrt ", "").replace("auto ", "")
            
            if clean_cmd.startswith("http"):
                stream_url = clean_cmd
            else:
                stream_url = f"{base_stream_url}/{clean_cmd}"

            # Menyisipkan token agar link bisa diputar di OTT Navigator
            if "?" in stream_url:
                stream_url += f"&token={token}"
            else:
                stream_url += f"?token={token}"

            genre_id = ch.get("tv_genre_id", "")
            group = categories.get(genre_id, "Lain-Lain")
            
            logo = ch.get("logo", "")
            logo_attr = f' tvg-logo="{logo}"' if logo else ""
            
            f.write(f'#EXTINF:-1{logo_attr} group-title="{group}",{name}\n')
            f.write(f'{stream_url}\n')
            
    print("[+] SELESAI! File 'playlist.m3u' berhasil dibuat dengan kategori dan logo.")

if __name__ == "__main__":
    main()
