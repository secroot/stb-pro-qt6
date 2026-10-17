import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from clients.stb_client import StbClient

client = StbClient(portal_url='http://iptv.darktv.eu:80/c/', mac='00:1A:79:73:1F:16')
client.handshake()
url = client.create_link('ffmpeg http://localhost/ch/182943_', media_type='itv', ch_id='182943')
print('URL:', url)

# Parameter aus url parsen
import urllib.parse
parsed = urllib.parse.urlparse(url)
qs = urllib.parse.parse_qs(parsed.query)
print("Query params:", qs)

# Tests mit verschiedenen Kombinationen
tests = [
    # 1. Andere Endpunkte
    ("Without play/", url.replace("/play/live.php", "/live.php")),
    # 2. Andere User-Agents
    ("User-Agent MAG250", url, {"User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3"}),
    ("User-Agent VLC", url, {"User-Agent": "VLC/3.0.20 LibVLC/3.0.20"}),
    ("User-Agent ffmpeg", url, {"User-Agent": "ffmpeg"}),
    ("User-Agent Lavf", url, {"User-Agent": "Lavf/58.76.100"}),
    ("User-Agent Kodi", url, {"User-Agent": "Kodi/20.0"}),
    # 3. Groß- / Kleinschreibung MAC
    ("Lowercase MAC", url.replace("00:1A:79:73:1F:16", "00:1a:79:73:1f:16")),
    # 4. Ohne extension=ts
    ("No extension", url.replace("&extension=ts", "")),
    # 5. Extension=m3u8
    ("Extension m3u8", url.replace("extension=ts", "extension=m3u8")),
    # 6. Ohne play_token
    ("No play_token", f"http://iptv.darktv.eu:80/play/live.php?mac=00:1A:79:73:1F:16&stream=182943&extension=ts"),
    # 7. Mit Referer & Origin
    ("With Origin & Referer", url, {"Referer": "http://iptv.darktv.eu:80/c/", "Origin": "http://iptv.darktv.eu:80"}),
    # 8. Mit stb_lang & timezone & token in Cookies
    ("With Stalker Cookies", url, {"Cookie": f"mac={client.mac}; token={client.token}; stb_lang=en; timezone=Europe%2FBerlin"}),
]

for item in tests:
    name = item[0]
    t_url = item[1]
    hdrs = item[2] if len(item) > 2 else {}
    try:
        r = requests.get(t_url, headers=hdrs, stream=True, timeout=3)
        print(f"[{name}] -> Status: {r.status_code}")
        if r.status_code == 200:
            chunk = next(r.iter_content(512), b"")
            print(f"   >>> BINGO! Read {len(chunk)} bytes: {chunk[:16]}")
        r.close()
    except Exception as e:
        print(f"[{name}] -> Error: {e}")
