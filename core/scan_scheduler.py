"""
Multi-Portal Scan Scheduler für STB Pro Qt6.
Bietet intelligente Verteilungsmodi für Multi-Portal MAC-Scans:
- HOT_SPOT: Hot-Spot Affinity (Fokus bei Hit: bei einem Treffer nachfolgende MACs auf diesem Portal prüfen)
- ROUND_ROBIN: Klassische zyklische Verteilung aller MACs über alle erreichbaren Portale
- ADAPTIVE: Dynamische Hit-Rate-Gewichtung (Multi-Armed Bandit / epsilon-greedy)
- FAILOVER: Primäres Portal aktiv; automatischer Wechsel zum nächsten Portal bei 3 aufeinanderfolgenden Fehlern
- SWEEP: Jede MAC gegen alle Portale prüfen (vollständige Matrix)
- SWEEP_EARLY_EXIT: Sweep mit Abbruch sobald eine MAC auf einem Portal erfolgreich verifiziert wurde
"""
from __future__ import annotations

import collections
import random
import threading
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class ScanRotationMode:
    """Konstanten für Multi-Portal Rotations- und Scan-Modi."""
    HOT_SPOT = "hot_spot"
    ROUND_ROBIN = "round_robin"
    ADAPTIVE = "adaptive"
    FAILOVER = "failover"
    SWEEP = "sweep"
    SWEEP_EARLY_EXIT = "sweep_early_exit"

    @classmethod
    def describe(cls, mode: str) -> str:
        descriptions = {
            cls.HOT_SPOT: "Hot-Spot Affinity (Fokus bei Hit)",
            cls.ROUND_ROBIN: "Round-Robin (Gleichmäßig verteilt)",
            cls.ADAPTIVE: "Smart Adaptive (Hit-Rate gewichtet)",
            cls.FAILOVER: "Failover (Auto-Switch bei Fehler)",
            cls.SWEEP: "Sweep (Alle Portale vollständig)",
            cls.SWEEP_EARLY_EXIT: "Sweep (Stopp bei erstem Hit)",
        }
        return descriptions.get(mode, mode)

    @classmethod
    def from_ui_label(cls, label: str) -> str:
        s = label or ""
        if "Hot-Spot" in s:
            return cls.HOT_SPOT
        if "Adaptive" in s:
            return cls.ADAPTIVE
        if "Failover" in s:
            return cls.FAILOVER
        if "Stopp bei erstem Hit" in s or "Early" in s:
            return cls.SWEEP_EARLY_EXIT
        if "Sweep" in s:
            return cls.SWEEP
        return cls.ROUND_ROBIN


class MultiPortalScanScheduler:
    """
    Thread-sicherer Work-Scheduler für Multi-Portal MAC-Scans.
    Verteilt MAC-Adressen dynamisch nach der gewählten Strategie auf Portale.
    """

    def __init__(
        self,
        portals: List[str],
        macs: List[str],
        mode: str = ScanRotationMode.HOT_SPOT,
        hot_spot_burst: int = 15,
        failover_threshold: int = 3,
        on_log: Optional[Callable[[str], None]] = None,
    ):
        self._lock = threading.Lock()
        self._on_log = on_log

        # Deduplizierte und bereinigte Portale & MACs
        clean_portals: List[str] = []
        for p in portals or []:
            ps = (p or "").strip()
            if ps and ps not in clean_portals:
                clean_portals.append(ps)
        self.portals: List[str] = clean_portals or [""]

        # Deduplizierte MAC-Liste unter Beibehaltung der Reihenfolge
        clean_macs: List[str] = []
        seen_macs = set()
        for m in macs or []:
            mu = (m or "").strip().upper()
            if mu and mu not in seen_macs:
                seen_macs.add(mu)
                clean_macs.append(mu)
        self.macs: List[str] = clean_macs

        self.mode = mode or ScanRotationMode.HOT_SPOT
        self.hot_spot_burst = max(1, int(hot_spot_burst or 15))
        self.failover_threshold = max(1, int(failover_threshold or 3))

        # Zähler & Metriken
        self.completed_count: int = 0
        self.skipped_count: int = 0
        self.in_flight: int = 0

        # Warteschlangen je nach Modus
        if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
            work_items: List[Tuple[str, str]] = []
            for m in self.macs:
                for p in self.portals:
                    work_items.append((m, p))
            self._sweep_queue: collections.deque[Tuple[str, str]] = collections.deque(work_items)
            self._solved_macs: Set[str] = set()
            self.total_checks: int = len(work_items)
        else:
            self._pending_macs: collections.deque[str] = collections.deque(self.macs)
            self._retry_queue: collections.deque[Tuple[str, str]] = collections.deque()
            self.total_checks: int = len(self.macs)

        # Modus-spezifische Zustände
        self._rr_index: int = 0

        # Hot-Spot Zustand
        self.active_hot_portal: Optional[str] = None
        self.hot_spot_remaining: int = 0
        self.hot_spot_consecutive_misses: int = 0

        # Adaptive Zustand
        self.portal_weights: Dict[str, float] = {p: 1.0 for p in self.portals}
        self.portal_stats: Dict[str, Dict[str, int]] = {
            p: {"checks": 0, "hits": 0, "errors": 0} for p in self.portals
        }

        # Failover Zustand
        self.current_primary_index: int = 0
        self.consecutive_errors: Dict[str, int] = {p: 0 for p in self.portals}

    def _log(self, msg: str):
        if self._on_log:
            try:
                self._on_log(msg)
            except Exception:
                pass

    def get_next_work_item(self) -> Optional[Tuple[str, str]]:
        """
        Gibt das nächste (MAC, Portal)-Tupel thread-sicher zurück.
        Gibt None zurück, wenn aktuell keine Items verfügbar sind.
        """
        with self._lock:
            if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                while self._sweep_queue:
                    mac, portal = self._sweep_queue.popleft()
                    if self.mode == ScanRotationMode.SWEEP_EARLY_EXIT and mac in self._solved_macs:
                        self.skipped_count += 1
                        continue
                    self.in_flight += 1
                    return mac, portal
                return None

            # Priorität 1: Requeue-Items (Retries bei transienten Fehlern)
            if self._retry_queue:
                mac, portal = self._retry_queue.popleft()
                self.in_flight += 1
                return mac, portal

            # Priorität 2: Nächste MAC aus der Ausgangsliste
            if not self._pending_macs:
                return None

            mac = self._pending_macs.popleft()
            portal = self._select_portal_for_mac(mac)
            self.in_flight += 1
            return mac, portal

    def _select_portal_for_mac(self, mac: str) -> str:
        # Wird nur innerhalb von self._lock aufgerufen
        if not self.portals or self.portals == [""]:
            return ""
        if len(self.portals) == 1:
            return self.portals[0]

        if self.mode == ScanRotationMode.HOT_SPOT:
            if self.active_hot_portal and self.hot_spot_remaining > 0:
                p = self.active_hot_portal
                self.hot_spot_remaining -= 1
                if self.hot_spot_remaining <= 0:
                    self._log(
                        f"[🔄 Hot-Spot] Burst für '{p}' abgeschlossen. Kehre zur Portal-Rotation zurück."
                    )
                    self.active_hot_portal = None
                    self.hot_spot_consecutive_misses = 0
                return p
            else:
                p = self.portals[self._rr_index % len(self.portals)]
                self._rr_index += 1
                return p

        elif self.mode == ScanRotationMode.ADAPTIVE:
            # 15% Exploration, 85% Exploitation (roulette-wheel gewichtet)
            if random.random() < 0.15:
                return random.choice(self.portals)
            return self._weighted_portal_choice()

        elif self.mode == ScanRotationMode.FAILOVER:
            return self.portals[self.current_primary_index % len(self.portals)]

        else:  # ROUND_ROBIN
            p = self.portals[self._rr_index % len(self.portals)]
            self._rr_index += 1
            return p

    def _weighted_portal_choice(self) -> str:
        total = sum(self.portal_weights.get(p, 1.0) for p in self.portals)
        if total <= 0:
            return random.choice(self.portals)
        r = random.uniform(0.0, total)
        upto = 0.0
        for p in self.portals:
            w = self.portal_weights.get(p, 1.0)
            if upto + w >= r:
                return p
            upto += w
        return self.portals[-1]

    def report_result(self, portal_url: str, mac: str, result: Dict[str, Any]):
        """
        Aktualisiert Metriken, Treffer, Burst-Quotas und Failover-Zustände thread-sicher.
        """
        with self._lock:
            self.completed_count += 1
            self.in_flight = max(0, self.in_flight - 1)

            is_hot = bool(
                result.get("tag") == "hot"
                or (result.get("valid") and int(result.get("channels") or 0) > 0)
            )
            ch_cnt = int(result.get("channels") or 0)
            err_str = str(result.get("error") or "")
            stat_str = str(result.get("status") or "")
            is_error = bool(
                result.get("channel_error")
                or "429" in err_str or "429" in stat_str
                or "502" in err_str or "502" in stat_str
                or "503" in err_str or "503" in stat_str
                or "504" in err_str or "504" in stat_str
                or "timeout" in err_str.lower() or "timeout" in stat_str.lower()
                or "Verbindungsfehler" in stat_str
                or "ConnectionError" in err_str
                or "RemoteDisconnected" in err_str
                or "WAF" in stat_str or "WAF" in err_str
            )

            # --- SWEEP EARLY EXIT ---
            if self.mode == ScanRotationMode.SWEEP_EARLY_EXIT and is_hot:
                if mac not in self._solved_macs:
                    self._solved_macs.add(mac)
                    self._log(
                        f"[⚡ Early-Exit] MAC {mac} auf '{portal_url}' erfolgreich verifiziert ({ch_cnt} Kanäle)! Weitere Portale für diese MAC übersprungen."
                    )

            # --- HOT-SPOT AFFINITY ---
            elif self.mode == ScanRotationMode.HOT_SPOT:
                if is_hot:
                    if self.active_hot_portal == portal_url:
                        self.hot_spot_remaining = min(30, self.hot_spot_remaining + 10)
                        self.hot_spot_consecutive_misses = 0
                        self._log(
                            f"[🔥 Hot-Spot] Neuer Hit auf '{portal_url}' ({ch_cnt} Kanäle)! Burst um +10 MACs verlängert (Rest: {self.hot_spot_remaining})."
                        )
                    else:
                        self.active_hot_portal = portal_url
                        self.hot_spot_remaining = self.hot_spot_burst
                        self.hot_spot_consecutive_misses = 0
                        self._log(
                            f"[🔥 Hot-Spot] HIT auf '{portal_url}' ({ch_cnt} Kanäle)! Starte Hot-Spot Fokus (nächste {self.hot_spot_burst} MACs werden hier geprüft)."
                        )
                elif self.active_hot_portal == portal_url:
                    if is_error:
                        self._log(
                            f"[⚠️ Hot-Spot] Serverfehler/Rate-Limit auf '{portal_url}' -> Hot-Spot abgebrochen, rotiere zurück."
                        )
                        self.active_hot_portal = None
                        self.hot_spot_remaining = 0
                        self.hot_spot_consecutive_misses = 0
                    else:
                        self.hot_spot_consecutive_misses += 1
                        if self.hot_spot_consecutive_misses >= 8:
                            self._log(
                                f"[🔄 Hot-Spot] 8x kein Treffer in Folge auf '{portal_url}' -> Beende Hot-Spot Fokus, kehre zur Rotation zurück."
                            )
                            self.active_hot_portal = None
                            self.hot_spot_remaining = 0
                            self.hot_spot_consecutive_misses = 0

            # --- SMART ADAPTIVE ---
            elif self.mode == ScanRotationMode.ADAPTIVE:
                stats = self.portal_stats.setdefault(portal_url, {"checks": 0, "hits": 0, "errors": 0})
                stats["checks"] += 1
                cur_w = self.portal_weights.get(portal_url, 1.0)
                if is_hot:
                    stats["hits"] += 1
                    new_w = min(20.0, cur_w + 3.0)
                    self.portal_weights[portal_url] = new_w
                    self._log(
                        f"[🧠 Adaptive] HIT auf '{portal_url}' ({ch_cnt} Kanäle) -> Prioritäts-Score auf {new_w:.1f} erhöht."
                    )
                elif is_error:
                    stats["errors"] += 1
                    new_w = max(0.1, cur_w * 0.5)
                    self.portal_weights[portal_url] = new_w
                elif result.get("valid"):
                    new_w = min(20.0, cur_w + 0.3)
                    self.portal_weights[portal_url] = new_w
                else:
                    new_w = max(0.2, cur_w - 0.05)
                    self.portal_weights[portal_url] = new_w

            # --- FAILOVER ---
            elif self.mode == ScanRotationMode.FAILOVER:
                current_active = self.portals[self.current_primary_index % len(self.portals)]
                if is_error:
                    self.consecutive_errors[portal_url] = self.consecutive_errors.get(portal_url, 0) + 1
                    if (
                        self.consecutive_errors[portal_url] >= self.failover_threshold
                        and portal_url == current_active
                        and len(self.portals) > 1
                    ):
                        old_p = portal_url
                        self.current_primary_index = (self.current_primary_index + 1) % len(self.portals)
                        new_p = self.portals[self.current_primary_index % len(self.portals)]
                        self.consecutive_errors[portal_url] = 0
                        self._log(
                            f"[🔀 Failover] Server-Fehlerhäufung ({self.failover_threshold}x) auf '{old_p}' -> Automatischer Notfall-Wechsel zu '{new_p}'!"
                        )
                else:
                    self.consecutive_errors[portal_url] = 0

    def requeue_item(self, portal_url: str, mac: str, reason: str = ""):
        """
        Stellt ein Work-Item bei transientem Fehler thread-sicher erneut an.
        """
        with self._lock:
            self.in_flight = max(0, self.in_flight - 1)
            if self.mode == ScanRotationMode.FAILOVER and len(self.portals) > 1:
                target_portal = self.portals[self.current_primary_index % len(self.portals)]
            else:
                target_portal = portal_url

            if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                self._sweep_queue.append((mac, target_portal))
            else:
                self._retry_queue.append((mac, target_portal))

    def release_in_flight(self):
        """Reduziert in_flight falls ein Worker unerwartet abbricht."""
        with self._lock:
            self.in_flight = max(0, self.in_flight - 1)

    def is_exhausted(self) -> bool:
        """Prüft, ob alle Items verarbeitet wurden und keine mehr in Bearbeitung sind."""
        with self._lock:
            if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                return len(self._sweep_queue) == 0 and self.in_flight == 0
            return len(self._pending_macs) == 0 and len(self._retry_queue) == 0 and self.in_flight == 0

    def get_progress(self) -> Tuple[int, int]:
        """Gibt (effektive_fertige_checks, gesamt_checks) zurück."""
        with self._lock:
            done = self.completed_count + self.skipped_count
            return min(self.total_checks, done), self.total_checks

    def get_queue_size(self) -> int:
        """Gibt die Anzahl der noch wartenden Items zurück."""
        with self._lock:
            if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                return len(self._sweep_queue)
            return len(self._pending_macs) + len(self._retry_queue)

    def get_active_portal(self) -> str:
        """Gibt das aktuell bevorzugte Portal zurück (für Status-Anzeigen)."""
        with self._lock:
            if self.mode == ScanRotationMode.HOT_SPOT and self.active_hot_portal:
                return self.active_hot_portal
            if self.mode == ScanRotationMode.FAILOVER and self.portals:
                return self.portals[self.current_primary_index % len(self.portals)]
            return ""
