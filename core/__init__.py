"""
Core-Paket für STB Pro Qt6.
Enthält Datenmodelle, Event-Bus, Persistenz, Stream-Puffer, Probing und Recording.
"""
from core.models import (
    Channel,
    EPGProgram,
    Profile,
    StreamProbeResult,
    ScanResult,
    HttpLogEntry,
    AppState,
    quality_from_dimensions,
    detect_quality_tag,
)
from core.signals import event_bus, worker_pool

__all__ = [
    "Channel",
    "EPGProgram",
    "Profile",
    "StreamProbeResult",
    "ScanResult",
    "HttpLogEntry",
    "AppState",
    "quality_from_dimensions",
    "detect_quality_tag",
    "event_bus",
    "worker_pool",
]
