import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from clients.stb_client import StbClient

client = StbClient(portal_url='http://iptv.darktv.eu:25461/c/', mac='00:1A:79:73:1F:16')
client.handshake()
chans = client.get_all_channels()

c_4461 = next((c for c in chans if str(c.get("id")) == "4461" or str(c.get("ch_id")) == "4461"), None)
c_375774 = next((c for c in chans if str(c.get("id")) == "375774" or str(c.get("ch_id")) == "375774"), None)

print("=== CHANNEL 4461 ===")
print(json.dumps(c_4461, indent=2, ensure_ascii=False) if c_4461 else "NOT FOUND")

print("\n=== CHANNEL 375774 ===")
print(json.dumps(c_375774, indent=2, ensure_ascii=False) if c_375774 else "NOT FOUND")
