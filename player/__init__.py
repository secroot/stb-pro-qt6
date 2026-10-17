"""
Player-Paket für STB Pro Qt6.
Enthält LibVLC-Controller, externen Player-Runner und das transparente Fullscreen-OSD.
"""
from player.vlc_controller import VLCPlayerController, VLC_AVAILABLE
from player.external_player import ExternalPlayerRunner
from player.osd_overlay import FullscreenOSDOverlay

__all__ = [
    "VLCPlayerController",
    "VLC_AVAILABLE",
    "ExternalPlayerRunner",
    "FullscreenOSDOverlay",
]
