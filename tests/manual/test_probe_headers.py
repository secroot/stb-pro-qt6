import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from clients.stb_client import StbClient

client = StbClient(portal_url='http://iptv.darktv.eu:80/c/', mac='00:1A:79:73:1F:16')
client.handshake()
url = client.create_link('ffmpeg http://localhost/ch/4461_', media_type="itv", ch_id="4461")
print("Stream URL:", url)

tests = [
    ("No headers", {}),
    ("No Range", {"User-Agent": client.user_agent}),
    ("VLC User-Agent without Range", {"User-Agent": "VLC/3.0.20 LibVLC/3.0.20"}),
    ("FFmpeg User-Agent without Range", {"User-Agent": "Lavf/60.16.100"}),
    ("Default STB User-Agent with Cookies", {"User-Agent": client.user_agent, "Cookie": f"mac={client.mac}; token={client.token}"}),
    ("With Referer no Range", {"User-Agent": client.user_agent, "Referer": "http://iptv.darktv.eu:80/c/"}),
    ("Only Range", {"Range": "bytes=0-1024"}),
    ("Host header explicit", {"Host": "iptv.darktv.eu:80", "User-Agent": client.user_agent}),
]

for name, hdrs in tests:
    try:
        r = requests.get(url, headers=hdrs, stream=True, timeout=5)
        print(f"[{name}] -> Status: {r.status_code}, Content-Type: {r.headers.get('Content-Type')}")
        if r.status_code == 200:
            chunk = next(r.iter_content(512), b"")
            print(f"   SUCCESS! Read {len(chunk)} bytes: {chunk[:16]}")
        r.close()
    except Exception as e:
        print(f"[{name}] -> Exception: {e}")
