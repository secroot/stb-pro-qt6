import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from core.scan_repository import ScanRepository
from clients.stb_client import StbClient

repo = ScanRepository()
host = repo.get_host("iptv.darktv.eu")
print(f"Scanning through accounts of {host.host_name}...")

working = []
statuses = {}

for idx, acc in enumerate(host.accounts[:25]):
    try:
        c = StbClient(portal_url=acc.portal_url, mac=acc.mac, timeout=4)
        c.handshake()
        link = c.create_link("ffmpeg http://localhost/ch/375774_", media_type="itv", ch_id="375774")
        r = requests.get(link, stream=True, timeout=3)
        code = r.status_code
        statuses[code] = statuses.get(code, 0) + 1
        if code == 200:
            print(f">>> HIT! Account {acc.mac} works! (200 OK)")
            working.append(acc.mac)
        else:
            print(f"[{idx+1}/25] {acc.mac} -> Status {code}")
        r.close()
    except Exception as e:
        print(f"[{idx+1}/25] {acc.mac} -> Exception: {e}")

print("\nSummary of status codes:", statuses)
print("Working accounts:", working)
