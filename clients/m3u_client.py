"""
M3U / M3U8 Playlist Client für STB Pro Qt6.
"""
import os
import sys

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PARENT_DIR = os.path.dirname(_APP_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.append(_PARENT_DIR)

from m3u_client import M3UClient  # noqa: E402, F401

__all__ = ["M3UClient"]
