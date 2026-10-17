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

r = requests.get(url, allow_redirects=False)
print('Status:', r.status_code)
print('Headers:', dict(r.headers))
print('Cookies:', dict(r.cookies))
print('Text:', repr(r.text))
