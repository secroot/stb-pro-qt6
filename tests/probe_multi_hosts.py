import sys
import os
import glob
import re
import requests

sys.path.insert(0, os.path.abspath("."))
from clients.stb_client import StbClient
from core.stream_probe import probe_stream, diagnose_iptv_status

scan_files = glob.glob("mac_scans/*.txt")
print(f"Gefundene Scan-Dateien: {len(scan_files)}\n", flush=True)

results = []

for sfile in sorted(scan_files):
    fname = os.path.basename(sfile)
    host_match = re.match(r"([^_]+)", fname)
    host_name = host_match.group(1) if host_match else fname
    
    content = open(sfile, encoding="utf-8", errors="ignore").read()
    blocks = content.split("---------------------------------------------")
    
    candidates = []
    for b in blocks:
        portal_m = re.search(r"Portal:\s*(\S+)", b)
        mac_m = re.search(r"Mac:\s*([0-9A-Fa-f:]+)", b)
        exp_m = re.search(r"Expire:\s*(.+)", b)
        chan_m = re.search(r"Channels:\s*(\d+)", b)
        if portal_m and mac_m and exp_m and chan_m:
            p_val = portal_m.group(1).strip()
            m_val = mac_m.group(1).strip()
            e_val = exp_m.group(1).strip()
            c_val = int(chan_m.group(1).strip())
            # Skip 0000, 1970, or inactive
            if "0000" in e_val or "1970" in e_val or c_val <= 0:
                continue
            candidates.append({"portal": p_val, "mac": m_val, "expire": e_val, "channels": c_val})
            
    # Sort candidates: moderate channels first (between 200 and 10000)
    candidates.sort(key=lambda x: (x["channels"] > 12000, x["channels"]))
    
    print(f"=== Host: {host_name} (Gueltige Accounts: {len(candidates)}) ===", flush=True)
    tested = False
    
    for cand in candidates[:3]:
        mac = cand["mac"]
        portal_url = cand["portal"]
        expire = cand["expire"]
        ch_count = cand["channels"]
        print(f"  Test Account: MAC={mac} | Expire={expire} | Chans={ch_count} | Portal={portal_url}", flush=True)
        
        try:
            client = StbClient(portal_url, mac, timeout=3.5)
            hs = client.handshake()
            if not client.token:
                print(f"    -> Handshake fehlgeschlagen (kein Token)", flush=True)
                continue
            
            # Fetch channels
            chans = client.get_ordered_list(genre="*", page=1)
            if not chans:
                print(f"    -> Handshake OK (Token={client.token[:8]}...), aber keine Kanalliste", flush=True)
                continue
            
            ch = chans[0]
            ch_name = ch.get("name", "Unbekannt").encode("ascii", "replace").decode("ascii")
            ch_id = str(ch.get("id", ""))
            cmd = ch.get("cmd", "")
            
            link = client.create_link(cmd, ch_id=ch_id)
            print(f"    -> Kanal: '{ch_name}' (ID: {ch_id})", flush=True)
            print(f"    -> Link: {link[:95]}...", flush=True)
            
            # Standard probe
            probe_res = probe_stream(
                link,
                user_agent="Lavf/58.29.100",
                cookies={"mac": mac, "token": client.token, "stb_lang": "en", "timezone": "Europe/Berlin"},
                timeout=4.0,
                sample_duration=0.5,
            )
            
            diag = probe_res.error_msg or ("OK" if probe_res.is_alive else diagnose_iptv_status(probe_res.status_code))
            print(f"    -> Probe Result: alive={probe_res.is_alive}, HTTP={probe_res.status_code}, Res={probe_res.resolution or '—'}, Bitrate={probe_res.bitrate_kbps} kbps, Diag={diag}", flush=True)
            
            # If blocked (456, 407, 403), test alternative headers (VLC UA, X-Forwarded-For)
            alt_info = ""
            if not probe_res.is_alive and probe_res.status_code in (403, 407, 456, 511):
                try:
                    alt_headers = {
                        "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
                        "X-Forwarded-For": "84.115.12.34", # Simulated residential
                        "Accept": "*/*",
                        "Range": "bytes=0-",
                        "Icy-MetaData": "1",
                        "Referer": portal_url,
                        "Cookie": f"mac={mac}; token={client.token}; stb_lang=en; timezone=Europe/Berlin"
                    }
                    r_alt = requests.get(link, headers=alt_headers, timeout=3.0, stream=True)
                    alt_info = f" [Alt UA/X-Forwarded: HTTP {r_alt.status_code}]"
                    print(f"    -> Header-Test:{alt_info}", flush=True)
                except Exception as e_alt:
                    alt_info = f" [Alt Test: {str(e_alt)[:30]}]"
            
            results.append({
                "host": host_name,
                "portal": portal_url,
                "mac": mac,
                "expire": expire,
                "channels": ch_count,
                "channel_sample": ch_name,
                "alive": probe_res.is_alive,
                "status": probe_res.status_code,
                "resolution": probe_res.resolution,
                "bitrate": probe_res.bitrate_kbps,
                "diag": diag + alt_info
            })
            tested = True
            break
        except Exception as e:
            err_s = str(e).encode("ascii", "replace").decode("ascii")
            print(f"    -> Fehler beim Test: {err_s[:80]}", flush=True)
            
    if not tested:
        print(f"  [!] Kein valider Account konnte für {host_name} erfolgreich verbunden werden.\n", flush=True)

print("\n" + "=" * 80, flush=True)
print("GESAMTÜBERSICHT MULTI-HOST STREAM & PROBE CHECK (Aktuelle US VPN IP)", flush=True)
print("=" * 80, flush=True)
for r in results:
    status_str = "🟢 LIVE & STREAMING" if r["alive"] else f"⚠️ HTTP {r['status']}"
    detail = f"{r['resolution']} @ {r['bitrate']} kbps" if r["alive"] else r["diag"]
    print(f"• {r['host']:<26} | MAC: {r['mac']} | {status_str:<22} | {detail}", flush=True)
