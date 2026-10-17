import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from clients.stb_client import StbClient

client = StbClient(portal_url='http://iptv.darktv.eu:25461/c/', mac='00:1A:79:73:1F:16')
client.handshake()

epg = client.get_short_epg('4461')
print('EPG for 4461 count:', len(epg))
if epg:
    print('First EPG program:', epg[0].get('name'))
else:
    # Direkt raw abfragen
    res = client._request("get_short_epg", req_type="itv", extra_params={"ch_id": "4461", "size": "10"})
    print('Raw response from _request:', res)
