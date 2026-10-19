import os
import sys
import requests
import re
import json

m3u_content = "#EXTM3U\n"
total_all_channels = 0

if not os.path.exists('Portal.txt'):
    print("Error: File Portal.txt tidak ditemukan!")
    sys.exit(1)

with open('Portal.txt', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

if not lines:
    print("Error: File Portal.txt kosong!")
    sys.exit(1)

print(f"Membaca {len(lines)} akun MAC Portal dari file...")

for index, account in enumerate(lines, start=1):
    if '|' not in account:
        print(f"Skipping baris {index}: Format salah")
        continue
        
    PORTAL_URL, MAC_ADDRESS = account.split('|', 1)
    PORTAL_URL = PORTAL_URL.strip()
    MAC_ADDRESS = MAC_ADDRESS.strip()
    
    print(f"\n[{index}/{len(lines)}] Memproses: {PORTAL_URL}")
    
    if '/c/' in PORTAL_URL:
        base_url = PORTAL_URL.split('/c/')[0]
    else:
        base_url = PORTAL_URL.rstrip('/')
        
    api_url = f"{base_url}/server/load.php"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbid/000000000000000000000000000000000000',
        'Cookie': f'mac={MAC_ADDRESS}; stb_lang=en; timezone=Europe%2FParis;',
        'Referer': f"{base_url}/c/",
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }
    
    try:
        # Handshake Token
        handshake_url = f"{api_url}?type=stb&action=handshake&token="
        response = requests.get(handshake_url, headers=headers, timeout=12)
        if response.status_code == 200:
            try:
                token = response.json().get('js', {}).get('token', '')
                if token:
                    headers['Authorization'] = f"Bearer {token}"
                    print("-> Autentikasi Berhasil!")
            except:
                pass

        # Tarik data siaran
        channels_url = f"{api_url}?type=itv&action=get_all_channels"
        res = requests.get(channels_url, headers=headers, timeout=15)
        raw_text = res.text
        
        count = 0
        
        # METODE 1: Membaca secara JSON (Lebih Akurat untuk Logo)
        try:
            data = json.loads(raw_text)
            channels_list = data.get('js', [])
            if isinstance(channels_list, dict):
                channels_list = list(channels_list.values())
                
            if isinstance(channels_list, list) and len(channels_list) > 0:
                for ch in channels_list:
                    if isinstance(ch, dict):
                        name = ch.get('name', 'Unknown Channel')
                        cmd = ch.get('cmd', '')
                        ch_id = ch.get('id', '')
                        ch_group = ch.get('tv_genre_name', f'Portal_{index}')
                        logo = ch.get('logo', '')
                        
                        stream_url = ""
                        if cmd:
                            stream_url = str(cmd).replace('\\', '')
                            link_match = re.search(r'(http[s]?://\S+)', stream_url)
                            if link_match:
                                stream_url = link_match.group(1).replace('"', '').replace("'", "")
                            else:
                                if "localhost" in stream_url or "/" in stream_url:
                                    clean_cmd = stream_url.split('/')[-1]
                                    stream_url = f"{base_url}/play/live.php?mac={MAC_ADDRESS}&stream={clean_cmd}"
                        
                        if not stream_url:
                            stream_url = f"{base_url}/playlist/live/{ch_id}.ts"
                            
                        logo_url = ""
                        if logo:
                            logo_url = logo if str(logo).startswith('http') else f"{base_url}/misc/logos/320/{logo}"
                        
                        if logo_url:
                            m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo_url}" group-title="{ch_group}",{name}\n{stream_url}\n'
                        else:
                            m3u_content += f'#EXTINF:-1 tvg-id="{ch_id}" group-title="{ch_group}",{name}\n{stream_url}\n'
                        count += 1
        except:
            pass

        # METODE FALLBACK 2: Regular Expression (Jika JSON Gagal, dipastikan Channel Tetap Keluar)
        if count == 0:
            matches = re.findall(r'"name"\s*:\s*"([^"]+)"[^}]+?"cmd"\s*:\s*"([^"]+)"', raw_text)
            if matches:
                for name, cmd in matches:
                    stream_url = cmd.replace('\\', '')
                    link_match = re.search(r'(http[s]?://\S+)', stream_url)
                    if link_match:
                        stream_url = link_match.group(1).replace('"', '').replace("'", "")
                    else:
                        clean_cmd = stream_url.split('/')[-1]
                        stream_url = f"{base_url}/play/live.php?mac={MAC_ADDRESS}&stream={clean_cmd}"
                    
                    m3u_content += f'#EXTINF:-1 group-title="Portal_{index}",{name}\n{stream_url}\n'
                    count += 1
                
        print(f"-> Sukses mengekstrak {count} channel dari akun ini.")
        total_all_channels += count

    except Exception as e:
        print(f"-> Gagal memproses: {e}")
        continue

print(f"\nSelesai! Total keseluruhan: {total_all_channels} channel berhasil dikumpulkan.")
with open('mac_playlist.m3u', 'w', encoding='utf-8') as f:
    f.write(m3u_content)
