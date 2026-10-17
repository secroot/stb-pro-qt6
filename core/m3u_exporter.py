"""
M3U / M3U8 Playlist Exporter für STB Pro Qt6 (QoL Feature).
Exportiert beliebige Kanallisten (aktueller Filter, Kategorie, Favoriten oder Gesamtliste)
als standardkonforme .m3u8 Datei für VLC, Kodi, TiviMate oder externe Tools.
"""
from typing import List, Optional, Callable
from core.models import Channel


def build_m3u_playlist(
    channels: List[Channel],
    user_agent: str = "",
    resolve_url_fn: Optional[Callable[[Channel], str]] = None,
) -> str:
    lines = ["#EXTM3U"]
    for ch in channels:
        if ch.is_dead:
            continue
        url = resolve_url_fn(ch) if resolve_url_fn else ch.cmd
        if not url:
            url = ch.cmd
        # Bereinige ffmpeg-Präfixe aus Stalker-CMDs falls direkt exportiert
        if url.startswith("ffmpeg "):
            url = url[7:].strip()
        elif url.startswith("ffrt "):
            url = url[5:].strip()
        elif url.startswith("auto "):
            url = url[5:].strip()

        name_clean = (ch.name or "Sender").replace('"', "'")
        cat_clean = (ch.category or "Allgemein").replace('"', "'")
        logo_clean = (ch.logo or "").replace('"', "")
        num_clean = str(ch.number or "").replace('"', "")

        extinf = (
            f'#EXTINF:-1 tvg-id="{ch.id}" tvg-chno="{num_clean}" '
            f'tvg-name="{name_clean}" tvg-logo="{logo_clean}" '
            f'group-title="{cat_clean}",{name_clean}'
        )
        lines.append(extinf)
        if user_agent:
            lines.append(f"#EXTVLCOPT:http-user-agent={user_agent}")
        lines.append(url)
    return "\n".join(lines) + "\n"
