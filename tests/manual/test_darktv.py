import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from clients.stb_client import StbClient

client = StbClient(portal_url='http://iptv.darktv.eu:25461/c/', mac='00:1A:79:73:1F:16')
client.handshake()
raw_link = client.create_link('ffmpeg http://localhost/ch/375774_', media_type='itv', ch_id='375774')
print('Raw link from server:', raw_link)

link_port25461 = raw_link.replace(':80/', ':25461/')
print('Testing with portal port 25461:', link_port25461)

r = requests.get(link_port25461, stream=True, timeout=5)
print('Response status on port 25461:', r.status_code)
print('Headers on port 25461:', dict(r.headers))
if r.status_code == 200:
    chunk = next(r.iter_content(512), b'')
    print(f'>>> BINGO! GOT STREAM BYTES: {len(chunk)} bytes!')
r.close()
