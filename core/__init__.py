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
    is_valid_expire_date,
)
from core.signals import event_bus, worker_pool
from core.vpn_manager import vpn_manager, NordVpnManager
from core.scan_scheduler import ScanRotationMode, MultiPortalScanScheduler
from core.pattern_predictor import MacPatternPredictor, MacClusterPattern
from core.category_parser import (
    calculate_days_until_expire,
    detect_category_tags,
    calculate_hit_rate,
    format_hit_rate,
)

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
    "is_valid_expire_date",
    "event_bus",
    "worker_pool",
    "vpn_manager",
    "NordVpnManager",
    "ScanRotationMode",
    "MultiPortalScanScheduler",
    "MacPatternPredictor",
    "MacClusterPattern",
    "calculate_days_until_expire",
    "detect_category_tags",
    "calculate_hit_rate",
    "format_hit_rate",
]
