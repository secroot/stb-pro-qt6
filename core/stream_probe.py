"""
Stream-Probe Engine für STB Pro Qt6.
Ermittelt HTTP-Latenz, MPEG-TS PCR-Mux-Bitrate sowie Video-/Audio-Codecs und Auflösung via FFprobe.
"""
import os
import time
import json
import subprocess
import threading
import shutil
from typing import Optional, Dict
import requests

from core.models import StreamProbeResult


def find_ffprobe() -> str:
    which = shutil.which("ffprobe")
    if which:
        return which
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        candidate = os.path.join(local_app, "Microsoft", "WinGet", "Links", "ffprobe.exe")
        if os.path.exists(candidate):
            return candidate
    for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if pf:
            candidate = os.path.join(pf, "ffmpeg", "bin", "ffprobe.exe")
            if os.path.exists(candidate):
                return candidate
    return ""


FFPROBE_BIN = find_ffprobe()
_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def pcr_bitrate_kbps(data: bytes) -> float:
    """Echte Mux-Bitrate aus MPEG-TS-PCR."""
    n = len(data)
    start = -1
    for i in range(0, min(188, n - 376)):
        if data[i] == 0x47 and data[i + 188] == 0x47 and data[i + 376] == 0x47:
            start = i
            break
    if start < 0:
        return 0.0
    pid_ref = None
    first = last = None
    for o in range(start, n - 187, 188):
        if data[o] != 0x47:
            break
        if (data[o + 3] & 0x20) and data[o + 4] >= 7 and (data[o + 5] & 0x10):
            pid = ((data[o + 1] & 0x1F) << 8) | data[o + 2]
            if pid_ref is None:
                pid_ref = pid
            if pid != pid_ref:
                continue
            base = (data[o + 6] << 25) | (data[o + 7] << 17) | (data[o + 8] << 9) | (data[o + 9] << 1) | (data[o + 10] >> 7)
            t = (base * 300 + (((data[o + 10] & 1) << 8) | data[o + 11])) / 27_000_000.0
            if first is None:
                first = (o, t)
            last = (o, t)
    if first and last and last[1] - first[1] >= 0.3:
        return round((last[0] - first[0]) * 8 / (last[1] - first[1]) / 1000.0, 1)
    return 0.0


def format_codec_name(codec: str) -> str:
    c = str(codec or "").lower()
    if "h264" in c or "avc" in c:
        return "H.264 / AVC"
    elif "hevc" in c or "h265" in c:
        return "HEVC / H.265"
    elif "mpeg2" in c:
        return "MPEG-2"
    elif "eac3" in c:
        return "Dolby Digital+ (E-AC3)"
    elif "ac3" in c:
        return "Dolby Digital (AC3)"
    elif "aac" in c:
        return "AAC-LC"
    elif "mp3" in c:
        return "MP3 Audio"
    return codec.upper() if codec else "Unbekannt"


def format_resolution(width: int, height: int, fps: float) -> str:
    fps_suffix = f"p{int(round(fps))}" if fps > 0 else "p"
    if width >= 3800 or height >= 2100:
        return f"4K UHD ({width}x{height})"
    elif height >= 1300 or width >= 2400:
        return f"1440{fps_suffix} QHD"
    elif height >= 1050 or width >= 1900:
        return f"1080{fps_suffix} FHD"
    elif height >= 700 or width >= 1260:
        return f"720{fps_suffix} HD"
    elif height >= 560:
        return "576p SD"
    elif height >= 460:
        return "480p SD"
    elif height > 0:
        return f"{width}x{height}"
    return ""


def parse_sps_from_h264(sps_bytes: bytes) -> Optional[tuple[int, int]]:
    """Decodiert H.264 Sequence Parameter Set (SPS) direkt in (width, height) ohne externe Tools."""
    try:
        rb = bytearray()
        i = 0
        n = len(sps_bytes)
        while i < n:
            if i + 2 < n and sps_bytes[i] == 0 and sps_bytes[i+1] == 0 and sps_bytes[i+2] == 3:
                rb.append(0)
                rb.append(0)
                i += 3
            else:
                rb.append(sps_bytes[i])
                i += 1

        pos = 0
        bit = 0
        def read_bit() -> int:
            nonlocal pos, bit
            if pos >= len(rb):
                return 0
            v = (rb[pos] >> (7 - bit)) & 1
            bit += 1
            if bit == 8:
                bit = 0
                pos += 1
            return v

        def read_bits(count: int) -> int:
            v = 0
            for _ in range(count):
                v = (v << 1) | read_bit()
            return v

        def read_ue() -> int:
            zeros = 0
            while read_bit() == 0 and zeros < 32 and pos < len(rb):
                zeros += 1
            if zeros == 0:
                return 0
            return (1 << zeros) - 1 + read_bits(zeros)

        def read_se() -> int:
            v = read_ue()
            return (v + 1) // 2 if (v & 1) else -(v // 2)

        _nal = read_bits(8)
        profile_idc = read_bits(8)
        read_bits(8)  # constraints
        _level_idc = read_bits(8)
        read_ue()  # seq_parameter_set_id

        if profile_idc in (100, 110, 122, 244, 44, 83, 86, 118, 128):
            chroma_format_idc = read_ue()
            if chroma_format_idc == 3:
                read_bit()
            read_ue()  # bit_depth_luma
            read_ue()  # bit_depth_chroma
            read_bit()  # qpprime
            if read_bit():  # seq_scaling_matrix
                for k in range(12 if chroma_format_idc == 3 else 8):
                    if read_bit():
                        last_scale, next_scale = 8, 8
                        for _ in range(64 if k >= 6 else 16):
                            if next_scale != 0:
                                delta = read_se()
                                next_scale = (last_scale + delta + 256) % 256
                            last_scale = last_scale if next_scale == 0 else next_scale

        read_ue()  # log2_max_frame_num
        poc_type = read_ue()
        if poc_type == 0:
            read_ue()
        elif poc_type == 1:
            read_bit()
            read_se()
            read_se()
            num_ref = read_ue()
            for _ in range(num_ref):
                read_se()
        read_ue()  # max_num_ref_frames
        read_bit()  # gaps_in_frame_num
        pic_width_in_mbs = read_ue() + 1
        pic_height_in_map_units = read_ue() + 1
        frame_mbs_only = read_bit()
        if not frame_mbs_only:
            read_bit()
        read_bit()  # direct_8x8
        crop_l = crop_r = crop_t = crop_b = 0
        if read_bit():  # frame_cropping_flag
            crop_l = read_ue()
            crop_r = read_ue()
            crop_t = read_ue()
            crop_b = read_ue()

        w = (pic_width_in_mbs * 16) - (crop_l + crop_r) * 2
        h = ((2 - frame_mbs_only) * pic_height_in_map_units * 16) - (crop_t + crop_b) * 2
        if 160 <= w <= 7680 and 120 <= h <= 4320:
            return w, h
    except Exception:
        pass
    return None


def extract_video_info_from_ts(data: bytes) -> tuple[int, int, str]:
    """Scannt MPEG-TS Pakete nach H.264/H.265 SPS in Millisekunden."""
    n = len(data)
    if n < 188 * 4:
        return 0, 0, ""

    start = -1
    for i in range(0, min(188, n - 376)):
        if data[i] == 0x47 and data[i + 188] == 0x47 and data[i + 376] == 0x47:
            start = i
            break
    if start < 0:
        return 0, 0, ""

    pes_payloads: Dict[int, bytearray] = {}
    for o in range(start, n - 187, 188):
        if data[o] != 0x47:
            continue
        pid = ((data[o + 1] & 0x1F) << 8) | data[o + 2]
        if pid in (0x0000, 0x1FFF):
            continue
        afc = (data[o + 3] >> 4) & 0x03
        if afc in (0, 2):
            continue
        p_start = o + 4
        if afc == 3:
            af_len = data[o + 4]
            p_start = o + 5 + af_len
        if p_start >= o + 188:
            continue
        chunk = data[p_start : o + 188]
        pusi = bool(data[o + 1] & 0x40)

        buf = pes_payloads.setdefault(pid, bytearray())
        if pusi and len(buf) > 0:
            buf.clear()
        if len(buf) < 128 * 1024:
            buf.extend(chunk)

    for pid, stream_data in pes_payloads.items():
        if len(stream_data) < 32:
            continue
        sd = bytes(stream_data)
        idx = 0
        while True:
            pos = sd.find(b"\x00\x00\x01", idx)
            if pos < 0 or pos + 4 >= len(sd):
                break
            nal_byte = sd[pos + 3]
            nal_type_h264 = nal_byte & 0x1F
            if nal_type_h264 == 7:  # H.264 SPS
                next_pos = sd.find(b"\x00\x00\x01", pos + 3)
                sps_candidate = sd[pos + 3 : next_pos] if next_pos > 0 else sd[pos + 3 : pos + 128]
                res = parse_sps_from_h264(sps_candidate)
                if res:
                    return res[0], res[1], "H.264 / AVC"
            elif ((nal_byte >> 1) & 0x3F) == 33:
                return 0, 0, "HEVC / H.265"
            idx = pos + 3

    return 0, 0, ""


def extract_resolution_from_hls_text(text: str) -> tuple[int, int]:
    """Extrahiert RESOLUTION=WxH direkt aus HLS-Playlists."""
    import re
    matches = re.findall(r'RESOLUTION=(\d+)x(\d+)', text)
    if matches:
        # Nimm die höchste gefundene Auflösung
        best_w, best_h = 0, 0
        for ws, hs in matches:
            try:
                w, h = int(ws), int(hs)
                if w * h > best_w * best_h:
                    best_w, best_h = w, h
            except ValueError:
                pass
        return best_w, best_h
    return 0, 0


def diagnose_iptv_status(status_code: int) -> str:
    """Diagnostiziert proprietäre/spezifische HTTP-Statuscodes von IPTV- und Streaming-Clustern."""
    mapping = {
        456: "HTTP 456 (Geo-IP / ISP-Sperre oder Multi-Connection Limit erreicht)",
        407: "HTTP 407 (Geo-IP Sperre / Proxy im Land des Anbieters erforderlich)",
        459: "HTTP 459 (Stream-Leitung belegt / Account wird parallel genutzt)",
        458: "HTTP 458 (Account auf Stream-Server abgelaufen / deaktiviert)",
        511: "HTTP 511 (Device-Auth ungültig / sn2 & device_id2 erforderlich)",
        512: "HTTP 512 (Streamer-Knoten antwortet nicht / Kanal offline)",
        401: "HTTP 401 (Nicht autorisiert / Token abgelaufen)",
        403: "HTTP 403 (Zugriff verweigert / WAF- oder Cloudflare-Block)",
        404: "HTTP 404 (Stream-URL oder Kanal-ID auf Server nicht gefunden)",
        429: "HTTP 429 (Rate Limit / Zu viele Anfragen - Pause nötig)",
        500: "HTTP 500 (Interner Serverfehler auf Streaming-Cluster)",
        502: "HTTP 502 (Bad Gateway / Transcoder nicht erreichbar)",
        503: "HTTP 503 (Dienst nicht verfügbar / Server überlastet)",
        504: "HTTP 504 (Gateway-Timeout zu Transcoder)",
    }
    return mapping.get(status_code, f"HTTP {status_code} vom Stream-Server")


def probe_stream(
    url: str,
    user_agent: str = "",
    cookies: Optional[Dict[str, str]] = None,
    timeout: float = 3.0,
    sample_duration: float = 0.5,
    cancel: Optional[threading.Event] = None,
    skip_ffprobe: bool = False,
    proxy: str = "",
    extract_thumbnail: bool = True,
) -> StreamProbeResult:
    if not url:
        return StreamProbeResult(is_alive=False, latency_ms=-1, error_msg="Keine Stream-URL")

    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (QtEmbedded; U; Linux; C) MAG200 stbapp",
        "Accept": "*/*",
        "Connection": "close",
    }
    if cookies and "token" in cookies:
        headers["Authorization"] = f"Bearer {cookies['token']}"

    status_code = 0
    latency_ms = -1
    measured_kbps = 0.0
    content_type = ""
    sample_bytes = b""
    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        t0 = time.time()
        with requests.get(
            url,
            headers=headers,
            cookies=cookies,
            stream=True,
            timeout=timeout,
            proxies=proxies,
        ) as resp:
            latency_ms = int((time.time() - t0) * 1000)
            status_code = resp.status_code
            content_type = resp.headers.get("Content-Type", "")

            # Wenn Server mehr als 3.0 Sekunden für Antwort brauchte -> als Offline werten
            if latency_ms > int(timeout * 1000):
                return StreamProbeResult(
                    is_alive=False,
                    status_code=status_code,
                    latency_ms=-1,
                    error_msg=f"Timeout: Antwort erst nach {latency_ms}ms (> {int(timeout * 1000)}ms)",
                )

            if status_code in (200, 206):
                total_bytes = 0
                sample = bytearray()
                t_start = time.time()
                for chunk in resp.iter_content(chunk_size=32768):
                    if cancel is not None and cancel.is_set():
                        return StreamProbeResult(
                            is_alive=False,
                            status_code=status_code,
                            latency_ms=latency_ms,
                            error_msg="Abgebrochen",
                        )
                    total_bytes += len(chunk)
                    if len(sample) < 2 * 1024 * 1024:
                        sample.extend(chunk)
                    elapsed = max(0.001, time.time() - t_start)
                    target_bytes = 800 * 1024 if extract_thumbnail else 512 * 1024
                    if total_bytes >= target_bytes or (elapsed >= sample_duration and total_bytes >= 512 * 1024):
                        break
                measured_kbps = round((total_bytes * 8) / (elapsed * 1000), 1)
                sample_bytes = bytes(sample)
                pcr_kbps = pcr_bitrate_kbps(sample_bytes)
                if pcr_kbps > 0:
                    measured_kbps = pcr_kbps
            else:
                diag = diagnose_iptv_status(status_code)
                return StreamProbeResult(
                    is_alive=False,
                    status_code=status_code,
                    latency_ms=-1,
                    error_msg=diag,
                )
    except Exception as e:
        err = str(e)
        is_to = "timed out" in err.lower() or "timeout" in err.lower()
        return StreamProbeResult(
            is_alive=False,
            status_code=status_code,
            latency_ms=-1,
            error_msg=f"Timeout (> {timeout:.1f}s): Kanal antwortet nicht" if is_to else f"Verbindungsfehler: {err}",
        )

    v_codec = ""
    a_codec = ""
    width = 0
    height = 0
    fps = 0.0
    a_channels = 0
    a_rate = 0
    a_kbps = 0.0

    # 1. Prio 1: Schneller HLS Master-Playlist Check (reines Textparsing, 0.01ms)
    if b"#EXTM3U" in sample_bytes[:128]:
        try:
            hls_txt = sample_bytes.decode("utf-8", "replace")
            hw, hh = extract_resolution_from_hls_text(hls_txt)
            if hw > 0 and hh > 0:
                width, height = hw, hh
                v_codec = "H.264 / AVC"
        except Exception:
            pass

    # 2. Prio 2: MPEG-TS reiner Python SPS-Parser (0.1ms direkt auf Stream-Bytes)
    if not height and len(sample_bytes) >= 188 * 4:
        tw, th, tcodec = extract_video_info_from_ts(sample_bytes)
        if th > 0:
            width, height = tw, th
            v_codec = tcodec or "H.264 / AVC"
        elif tcodec:
            v_codec = tcodec

    # 3. Prio 3: FFprobe Pipe-Scan auf sample_bytes (nur wenn Python-Parser nicht reichte)
    if not height and FFPROBE_BIN and not skip_ffprobe:
        def _parse_json(parsed):
            nonlocal v_codec, a_codec, width, height, fps, a_channels, a_rate, a_kbps
            for st in parsed.get("streams", []):
                c_type = st.get("codec_type")
                if c_type == "video" and not v_codec and int(st.get("width") or 0) > 0:
                    v_codec = format_codec_name(st.get("codec_name", ""))
                    width = int(st.get("width") or 0)
                    height = int(st.get("height") or 0)
                    r_fps = st.get("avg_frame_rate") if st.get("avg_frame_rate", "0/0") not in ("0/0", "0/1") else st.get("r_frame_rate", "0/1")
                    if "/" in str(r_fps):
                        num, den = str(r_fps).split("/")
                        if float(den) > 0:
                            fps = round(float(num) / float(den), 1)
                elif c_type == "audio" and not a_codec:
                    a_codec = format_codec_name(st.get("codec_name", ""))
                    a_channels = int(st.get("channels") or 0)
                    a_rate = int(st.get("sample_rate") or 0)
                    if st.get("bit_rate"):
                        try:
                            a_kbps = round(float(st["bit_rate"]) / 1000, 1)
                        except Exception:
                            pass

        if len(sample_bytes) >= 188 * 20:
            try:
                res = subprocess.run(
                    [FFPROBE_BIN, "-v", "quiet", "-print_format", "json", "-show_streams",
                     "-probesize", "500000", "-analyzeduration", "1000000", "-i", "pipe:0"],
                    input=sample_bytes,
                    capture_output=True,
                    timeout=1.5,
                    creationflags=_NOWIN,
                )
                if res.stdout:
                    _parse_json(json.loads(res.stdout.decode("utf-8", "replace")))
            except Exception:
                pass

    res_str = format_resolution(width, height, fps)

    t_bytes = None
    if extract_thumbnail and sample_bytes and len(sample_bytes) >= 188 * 10:
        try:
            from core.preview_grabber import extract_thumbnail_from_ts
            t_bytes = extract_thumbnail_from_ts(sample_bytes, width=320)
        except Exception:
            pass

    return StreamProbeResult(
        is_alive=True,
        status_code=status_code,
        latency_ms=latency_ms,
        content_type=content_type,
        video_codec=v_codec,
        resolution=res_str,
        width=width,
        height=height,
        fps=fps,
        bitrate_kbps=measured_kbps,
        audio_codec=a_codec,
        audio_channels=a_channels,
        audio_rate=a_rate,
        audio_bitrate_kbps=a_kbps,
        buffer_health="Ausgezeichnet" if measured_kbps > 6000 else "Gut" if measured_kbps > 2500 else "Schwach",
        thumb_bytes=t_bytes,
    )
