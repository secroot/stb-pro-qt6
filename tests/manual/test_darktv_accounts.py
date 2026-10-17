import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from core.scan_repository import ScanRepository
from clients.stb_client import StbClient

repo = ScanRepository()
host = repo.get_host("iptv.darktv.eu")
print(f"Total accounts for {host.host_name}: {len(host.accounts)}")

for idx, acc in enumerate(host.accounts[:5]):
    print(f"\n--- Testing Account {idx+1}: {acc.mac} (Expire: {acc.expire}) ---")
    try:
        c = StbClient(portal_url=acc.portal_url, mac=acc.mac)
        c.handshake()
        link = c.create_link("ffmpeg http://localhost/ch/375774_", media_type="itv", ch_id="375774")
        print(f"Link: {link}")
        r = requests.get(link, stream=True, timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f">>> THIS ACCOUNT WORKS! Got stream!")
            break
        r.close()
    except Exception as e:
        print(f"Error: {e}")
