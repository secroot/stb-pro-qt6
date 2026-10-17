import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from core.scan_repository import ScanRepository
from clients.stb_client import StbClient

repo = ScanRepository()
for host in repo.get_hosts():
    print(f"\n==================== {host.host_name} ====================")
    acc = host.accounts[0]
    print(f"Portal: {acc.portal_url}, MAC: {acc.mac}")
    try:
        c = StbClient(portal_url=acc.portal_url, mac=acc.mac)
        c.handshake()
        print(f"Handshake OK, Token: {c.token}")
        # Schnelle Abfrage von Seite 1
        res = c._request("get_ordered_list", req_type="itv", extra_params={"p": "1", "genre": "*", "sortby": "number"})
        data = res.get("data", []) if isinstance(res, dict) else []
        print(f"Loaded {len(data)} channels from page 1")
        if data:
            target = data[0]
            print(f"Target: {target.get('id')} - {target.get('name')}")
            cmd = target.get('cmd')
            print(f"CMD: {cmd}")
            link = c.create_link(cmd, media_type="itv", ch_id=str(target.get('id')))
            print(f"Resolved Link: {link}")
            r = requests.get(link, stream=True, timeout=5)
            print(f"HTTP Status: {r.status_code}")
            if r.status_code == 200:
                chunk = next(r.iter_content(512), b"")
                print(f"   >>> STREAM PLAYS! Read {len(chunk)} bytes!")
            elif r.status_code == 456:
                print(f"   >>> GOT 456! Server rejected live.php with 456")
            else:
                print(f"   >>> OTHER CODE: {r.status_code}")
            r.close()
    except Exception as e:
        print(f"Error: {e}")
