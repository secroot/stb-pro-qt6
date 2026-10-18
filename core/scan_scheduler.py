"""
Multi-Portal Scan Scheduler für STB Pro Qt6.
Bietet intelligente Verteilungsmodi für Multi-Portal MAC-Scans:
- HOT_SPOT: Hot-Spot Affinity mit Backfill (bei einem Treffer werden auch zuvor auf anderen Portalen abgewiesene MACs auf dem Hot-Portal nachgetestet)
- ROUND_ROBIN: Klassische zyklische Verteilung aller MACs über alle erreichbaren Portale
- ADAPTIVE: Dynamische Hit-Rate-Gewichtung mit Backfill (Multi-Armed Bandit / epsilon-greedy)
- FAILOVER: Primäres Portal aktiv; automatischer Wechsel zum nächsten Portal bei 3 aufeinanderfolgenden Fehlern
- SWEEP: Jede MAC gegen alle Portale prüfen (vollständige Matrix)
- SWEEP_EARLY_EXIT: Sweep mit Abbruch sobald eine MAC auf einem Portal erfolgreich verifiziert wurde
"""
from __future__ import annotations

import collections
import random
import threading
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from core.models import is_valid_expire_date


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
            cls.HOT_SPOT: "Hot-Spot Affinity (Fokus & Backfill bei Hit)",
            cls.ROUND_ROBIN: "Round-Robin (Gleichmäßig verteilt)",
            cls.ADAPTIVE: "Smart Adaptive (Hit-Rate gewichtet & Backfill)",
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
    Thread-sicherer Work-Scheduler für Multi-Portal MAC-Scans mit intelligenter
    Coverage- und Backfill-Logik.
    """

    def __init__(
        self,
        portals: List[str],
        macs: List[str],
        mode: str = ScanRotationMode.HOT_SPOT,
        hot_spot_burst: int = 20,
        failover_threshold: int = 3,
        on_log: Optional[Callable[[str], None]] = None,
    ):
        self._lock = threading.RLock()
        self._on_log = on_log

        # Deduplizierte Portale & MACs
        clean_portals: List[str] = []
        for p in portals or []:
            ps = (p or "").strip()
            if ps and ps not in clean_portals:
                clean_portals.append(ps)
        self.portals: List[str] = clean_portals or [""]

        clean_macs: List[str] = []
        seen_macs = set()
        for m in macs or []:
            mu = (m or "").strip().upper()
            if mu and mu not in seen_macs:
                seen_macs.add(mu)
                clean_macs.append(mu)
        self.macs: List[str] = clean_macs

        self.mode = mode or ScanRotationMode.HOT_SPOT
        self.hot_spot_burst = max(1, int(hot_spot_burst or 20))
        self.failover_threshold = max(1, int(failover_threshold or 3))

        # Zähler & Metriken
        self.completed_count: int = 0
        self.skipped_count: int = 0
        self.in_flight: int = 0

        # Mapping: MAC -> Menge an Portalen, auf denen sie bereits getestet wurde
        self.tested_map: Dict[str, Set[str]] = collections.defaultdict(set)
        # Menge an MACs, die einen Hot-Hit (>0 Kanäle) erzielt haben
        self.solved_macs: Set[str] = set()
        # Aktuell in Bearbeitung befindliche Paare: (mac, portal)
        self.in_flight_pairs: Set[Tuple[str, str]] = set()

        # Requeue-Schlange für temporäre Fehler
        self._retry_queue: collections.deque[Tuple[str, str]] = collections.deque()

        # Frische MACs, die noch nirgends getestet wurden
        self._fresh_macs: collections.deque[str] = collections.deque(self.macs)

        # Backfill-Schlangen pro Portal: MACs, die auf anderen Portalen abgewiesen wurden,
        # aber auf diesem Portal noch nie getestet wurden!
        self._backfill_per_portal: Dict[str, collections.deque[str]] = {
            p: collections.deque() for p in self.portals
        }
        self._backfill_set_per_portal: Dict[str, Set[str]] = {
            p: set() for p in self.portals
        }

        # Modus-spezifische Queues
        if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
            work_items: List[Tuple[str, str]] = []
            for m in self.macs:
                for p in self.portals:
                    work_items.append((m, p))
            self._sweep_queue: collections.deque[Tuple[str, str]] = collections.deque(work_items)
            self.total_checks: int = len(work_items)
        else:
            self._sweep_queue = collections.deque()
            self.total_checks: int = len(self.macs)

        # Hot-Spot Zustand
        self.active_hot_portal: Optional[str] = None
        self.hot_spot_remaining: int = 0
        self.hot_spot_consecutive_misses: int = 0
        self.hot_spot_max_misses: int = 10

        # Adaptive Zustand
        self.portal_weights: Dict[str, float] = {p: 1.0 for p in self.portals}
        self.portal_stats: Dict[str, Dict[str, int]] = {
            p: {"checks": 0, "hits": 0, "errors": 0} for p in self.portals
        }

        # Failover Zustand
        self.current_primary_index: int = 0
        self.consecutive_errors: Dict[str, int] = {p: 0 for p in self.portals}

        # Round-Robin Index
        self._rr_index: int = 0

    def _log(self, msg: str):
        if self._on_log:
            try:
                self._on_log(msg)
            except Exception:
                pass

    def get_next_work_item(self) -> Optional[Tuple[str, str]]:
        """
        Gibt das nächste (MAC, Portal)-Tupel thread-sicher zurück.
        """
        with self._lock:
            # 1. Sweep-Modi
            if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                while self._sweep_queue:
                    mac, portal = self._sweep_queue.popleft()
                    if self.mode == ScanRotationMode.SWEEP_EARLY_EXIT and mac in self.solved_macs:
                        self.skipped_count += 1
                        continue
                    if (mac, portal) in self.in_flight_pairs:
                        self.skipped_count += 1
                        continue
                    self.in_flight += 1
                    self.in_flight_pairs.add((mac, portal))
                    return mac, portal
                return None

            # 2. Priorität: Transiente Retries
            while self._retry_queue:
                mac, portal = self._retry_queue.popleft()
                if mac in self.solved_macs:
                    self.skipped_count += 1
                    continue
                if (mac, portal) in self.in_flight_pairs:
                    self.skipped_count += 1
                    continue
                self.in_flight += 1
                self.in_flight_pairs.add((mac, portal))
                return mac, portal

            # 3. Modus-spezifische Zuweisung
            if self.mode == ScanRotationMode.HOT_SPOT:
                return self._get_hot_spot_item()
            elif self.mode == ScanRotationMode.ADAPTIVE:
                return self._get_adaptive_item()
            elif self.mode == ScanRotationMode.FAILOVER:
                return self._get_failover_item()
            else:  # ROUND_ROBIN
                return self._get_round_robin_item()

    def _get_hot_spot_item(self) -> Optional[Tuple[str, str]]:
        # Wird innerhalb von self._lock aufgerufen
        # 1. Hot-Spot aktiv: Zuerst Backfill-Kandidaten, dann frische MACs auf das Hot-Portal lenken
        if self.active_hot_portal and self.hot_spot_remaining > 0:
            hp = self.active_hot_portal

            # A. Bevorzuge Backfill (MACs, die auf anderen Portalen abgewiesen wurden, aber auf hp noch nie liefen!)
            bf_queue = self._backfill_per_portal[hp]
            while bf_queue:
                mac = bf_queue.popleft()
                self._backfill_set_per_portal[hp].discard(mac)
                if mac in self.solved_macs or hp in self.tested_map[mac] or (mac, hp) in self.in_flight_pairs:
                    self.skipped_count += 1
                    continue
                self.hot_spot_remaining -= 1
                self.in_flight += 1
                self.in_flight_pairs.add((mac, hp))
                if self.hot_spot_remaining <= 0:
                    self._log(f"[🔄 Hot-Spot] Burst für '{hp}' beendet. Kehre zur Portal-Rotation zurück.")
                    self.active_hot_portal = None
                return mac, hp

            # B. Frische MACs auf hp testen
            while self._fresh_macs:
                mac = self._fresh_macs.popleft()
                if mac in self.solved_macs:
                    self.skipped_count += 1
                    continue
                if hp in self.tested_map[mac] or (mac, hp) in self.in_flight_pairs:
                    self.skipped_count += 1
                    continue
                self.hot_spot_remaining -= 1
                self.in_flight += 1
                self.in_flight_pairs.add((mac, hp))
                if self.hot_spot_remaining <= 0:
                    self._log(f"[🔄 Hot-Spot] Burst für '{hp}' beendet. Kehre zur Portal-Rotation zurück.")
                    self.active_hot_portal = None
                return mac, hp

            # Weder Backfill noch frische MACs für hp vorhanden
            self.active_hot_portal = None

        # 2. Reguläre Erkundung frischer MACs zyklisch über Portale
        while self._fresh_macs:
            mac = self._fresh_macs.popleft()
            if mac in self.solved_macs:
                self.skipped_count += 1
                continue
            portal = self.portals[self._rr_index % len(self.portals)]
            self._rr_index += 1
            if portal in self.tested_map[mac] or (mac, portal) in self.in_flight_pairs:
                alt_portals = [
                    p for p in self.portals
                    if p not in self.tested_map[mac] and (mac, p) not in self.in_flight_pairs
                ]
                if alt_portals:
                    portal = alt_portals[0]
                else:
                    self.skipped_count += 1
                    continue
            self.in_flight += 1
            self.in_flight_pairs.add((mac, portal))
            return mac, portal

        # 3. Draining aller verbleibenden Backfill-Kandidaten über alle Portale
        # (wenn keine frischen MACs mehr vorhanden sind)
        for p in self.portals:
            bf_q = self._backfill_per_portal[p]
            while bf_q:
                mac = bf_q.popleft()
                self._backfill_set_per_portal[p].discard(mac)
                if mac in self.solved_macs or p in self.tested_map[mac] or (mac, p) in self.in_flight_pairs:
                    self.skipped_count += 1
                    continue
                self.in_flight += 1
                self.in_flight_pairs.add((mac, p))
                return mac, p

        return None

    def _get_adaptive_item(self) -> Optional[Tuple[str, str]]:
        # Wird innerhalb von self._lock aufgerufen
        if random.random() < 0.15:
            portal = random.choice(self.portals)
        else:
            portal = self._weighted_portal_choice()

        # 1. Bevorzuge Backfill für gewähltes Portal
        bf_q = self._backfill_per_portal[portal]
        while bf_q:
            mac = bf_q.popleft()
            self._backfill_set_per_portal[portal].discard(mac)
            if mac in self.solved_macs or portal in self.tested_map[mac] or (mac, portal) in self.in_flight_pairs:
                self.skipped_count += 1
                continue
            self.in_flight += 1
            self.in_flight_pairs.add((mac, portal))
            return mac, portal

        # 2. Frische MACs
        while self._fresh_macs:
            mac = self._fresh_macs.popleft()
            if mac in self.solved_macs:
                self.skipped_count += 1
                continue
            target_portal = portal
            if target_portal in self.tested_map[mac] or (mac, target_portal) in self.in_flight_pairs:
                alt_portals = [
                    p for p in self.portals
                    if p not in self.tested_map[mac] and (mac, p) not in self.in_flight_pairs
                ]
                if alt_portals:
                    target_portal = random.choice(alt_portals)
                else:
                    self.skipped_count += 1
                    continue
            self.in_flight += 1
            self.in_flight_pairs.add((mac, target_portal))
            return mac, target_portal

        # 3. Fallback: Suche beliebiges Portal mit ausstehenden Backfill-Kandidaten
        for p in self.portals:
            p_bf = self._backfill_per_portal[p]
            while p_bf:
                mac = p_bf.popleft()
                self._backfill_set_per_portal[p].discard(mac)
                if mac in self.solved_macs or p in self.tested_map[mac] or (mac, p) in self.in_flight_pairs:
                    self.skipped_count += 1
                    continue
                self.in_flight += 1
                self.in_flight_pairs.add((mac, p))
                return mac, p

        return None

    def _get_failover_item(self) -> Optional[Tuple[str, str]]:
        portal = self.portals[self.current_primary_index % len(self.portals)]
        bf_q = self._backfill_per_portal[portal]
        while bf_q:
            mac = bf_q.popleft()
            self._backfill_set_per_portal[portal].discard(mac)
            if mac in self.solved_macs or portal in self.tested_map[mac] or (mac, portal) in self.in_flight_pairs:
                self.skipped_count += 1
                continue
            self.in_flight += 1
            self.in_flight_pairs.add((mac, portal))
            return mac, portal

        while self._fresh_macs:
            mac = self._fresh_macs.popleft()
            if mac in self.solved_macs:
                self.skipped_count += 1
                continue
            if portal in self.tested_map[mac] or (mac, portal) in self.in_flight_pairs:
                self.skipped_count += 1
                continue
            self.in_flight += 1
            self.in_flight_pairs.add((mac, portal))
            return mac, portal

        return None

    def _get_round_robin_item(self) -> Optional[Tuple[str, str]]:
        while self._fresh_macs:
            mac = self._fresh_macs.popleft()
            if mac in self.solved_macs:
                self.skipped_count += 1
                continue
            portal = self.portals[self._rr_index % len(self.portals)]
            self._rr_index += 1
            if portal in self.tested_map[mac] or (mac, portal) in self.in_flight_pairs:
                alt_portals = [
                    p for p in self.portals
                    if p not in self.tested_map[mac] and (mac, p) not in self.in_flight_pairs
                ]
                if alt_portals:
                    portal = alt_portals[0]
                else:
                    self.skipped_count += 1
                    continue
            self.in_flight += 1
            self.in_flight_pairs.add((mac, portal))
            return mac, portal
        return None

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

    def _activate_hot_spot(self, portal: str, ch_cnt: int):
        """Aktiviert Hot-Spot Modus und sammelt alle bisher auf anderen Portalen abgewiesenen MACs."""
        self.active_hot_portal = portal
        self.hot_spot_remaining = self.hot_spot_burst
        self.hot_spot_consecutive_misses = 0

        # Sammle alle bisher auf ANDEREN Portalen getesteten MACs, die auf diesem Portal noch NIE probiert wurden!
        backfill_candidates = []
        if len(self.portals) > 1:
            for m in self.macs:
                if m not in self.solved_macs and portal not in self.tested_map[m]:
                    if len(self.tested_map[m]) > 0 and (m, portal) not in self.in_flight_pairs:
                        if m not in self._backfill_set_per_portal[portal]:
                            self._backfill_per_portal[portal].append(m)
                            self._backfill_set_per_portal[portal].add(m)
                            backfill_candidates.append(m)

        bf_count = len(backfill_candidates)
        if bf_count > 0:
            self.total_checks += bf_count
            self._log(
                f"[🔥 Hot-Spot] HIT auf '{portal}' ({ch_cnt} Kanäle)! Backfill aktiviert: "
                f"{bf_count} zuvor auf anderen Portalen abgewiesene MACs werden nun hier nachgetestet!"
            )
        else:
            self._log(
                f"[🔥 Hot-Spot] HIT auf '{portal}' ({ch_cnt} Kanäle)! Starte Hot-Spot Fokus "
                f"(nächste {self.hot_spot_burst} MACs werden hier geprüft)."
            )

    def report_result(self, portal_url: str, mac: str, result: Dict[str, Any]):
        """
        Aktualisiert Metriken, Treffer, Burst-Quotas und Failover-Zustände thread-sicher.
        """
        with self._lock:
            self.completed_count += 1
            self.in_flight = max(0, self.in_flight - 1)
            self.in_flight_pairs.discard((mac, portal_url))
            self.tested_map[mac].add(portal_url)

            is_hot = bool(
                result.get("tag") == "hot"
                or (
                    result.get("tag") is None
                    and result.get("valid")
                    and int(result.get("channels") or 0) > 0
                    and is_valid_expire_date(result.get("expire"))
                )
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

            # Bei Treffer: MAC global als gelöst markieren
            if is_hot:
                self.solved_macs.add(mac)

            # --- SWEEP EARLY EXIT ---
            if self.mode == ScanRotationMode.SWEEP_EARLY_EXIT and is_hot:
                self._log(
                    f"[⚡ Early-Exit] MAC {mac} auf '{portal_url}' erfolgreich verifiziert ({ch_cnt} Kanäle)! Weitere Portale für diese MAC übersprungen."
                )

            # --- HOT-SPOT AFFINITY ---
            elif self.mode == ScanRotationMode.HOT_SPOT:
                if is_hot:
                    if self.active_hot_portal == portal_url:
                        self.hot_spot_remaining = min(60, self.hot_spot_remaining + 10)
                        self.hot_spot_consecutive_misses = 0
                        self._log(
                            f"[🔥 Hot-Spot] Neuer Hit auf '{portal_url}' ({ch_cnt} Kanäle)! Burst um +10 verlängert (Rest: {self.hot_spot_remaining})."
                        )
                    else:
                        self._activate_hot_spot(portal_url, ch_cnt)
                elif is_error:
                    # Wenn Fehler auf diesem Portal auftreten: immer verbleibenden Backfill dieses Portals bereinigen
                    dropped = len(self._backfill_per_portal.get(portal_url, []))
                    if dropped > 0:
                        self.total_checks = max(self.completed_count + self.skipped_count, self.total_checks - dropped)
                        self._backfill_per_portal[portal_url].clear()
                        self._backfill_set_per_portal[portal_url].clear()
                        self._log(
                            f"[⚠️ Hot-Spot] Serverfehler/Rate-Limit auf '{portal_url}' -> {dropped} Backfill-Checks verworfen."
                        )
                    if self.active_hot_portal == portal_url:
                        self._log(
                            f"[⚠️ Hot-Spot] Serverfehler auf aktivem Hot-Portal '{portal_url}' -> Hot-Spot abgebrochen, rotiere weiter."
                        )
                        self.active_hot_portal = None
                        self.hot_spot_remaining = 0
                        self.hot_spot_consecutive_misses = 0
                elif self.active_hot_portal == portal_url:
                    self.hot_spot_consecutive_misses += 1
                    if self.hot_spot_consecutive_misses >= self.hot_spot_max_misses:
                        self._log(
                            f"[🔄 Hot-Spot] {self.hot_spot_max_misses}x kein Treffer in Folge auf '{portal_url}' -> Beende Hot-Spot Fokus, kehre zur Rotation zurück."
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
                    # Sammle Backfill-Kandidaten für das erfolgreiche Portal
                    bf_count = 0
                    if len(self.portals) > 1:
                        for m in self.macs:
                            if m not in self.solved_macs and portal_url not in self.tested_map[m] and len(self.tested_map[m]) > 0:
                                if m not in self._backfill_set_per_portal[portal_url]:
                                    self._backfill_per_portal[portal_url].append(m)
                                    self._backfill_set_per_portal[portal_url].add(m)
                                    bf_count += 1
                    if bf_count > 0:
                        self.total_checks += bf_count
                        self._log(
                            f"[🧠 Adaptive] Backfill: {bf_count} zuvor abgewiesene MACs werden für das erfolgreiche Portal '{portal_url}' priorisiert."
                        )
                elif is_error:
                    stats["errors"] += 1
                    new_w = max(0.1, cur_w * 0.5)
                    self.portal_weights[portal_url] = new_w
                    dropped = len(self._backfill_per_portal.get(portal_url, []))
                    if dropped > 0:
                        self.total_checks = max(self.completed_count + self.skipped_count, self.total_checks - dropped)
                        self._backfill_per_portal[portal_url].clear()
                        self._backfill_set_per_portal[portal_url].clear()
                        self._log(
                            f"[⚠️ Adaptive] Serverfehler auf '{portal_url}' -> {dropped} Backfill-Checks verworfen."
                        )
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
                        fo_add = 0
                        for m in self.macs:
                            if m not in self.solved_macs and new_p not in self.tested_map[m]:
                                if m not in self._backfill_set_per_portal[new_p]:
                                    self._backfill_per_portal[new_p].append(m)
                                    self._backfill_set_per_portal[new_p].add(m)
                                    fo_add += 1
                        if fo_add > 0:
                            self.total_checks += fo_add
                else:
                    self.consecutive_errors[portal_url] = 0

    def requeue_item(self, portal_url: str, mac: str, reason: str = ""):
        """
        Stellt ein Work-Item bei transientem Fehler thread-sicher erneut an.
        """
        with self._lock:
            self.in_flight = max(0, self.in_flight - 1)
            self.in_flight_pairs.discard((mac, portal_url))
            if self.mode == ScanRotationMode.FAILOVER and len(self.portals) > 1:
                target_portal = self.portals[self.current_primary_index % len(self.portals)]
            else:
                target_portal = portal_url

            if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                self._sweep_queue.append((mac, target_portal))
            else:
                self._retry_queue.append((mac, target_portal))

    def release_in_flight(
        self,
        portal_url: Optional[str] = None,
        mac: Optional[str] = None,
        requeue: bool = False,
        count_as_skipped: bool = True,
    ):
        """Reduziert in_flight und bereinigt in_flight_pairs, falls ein Worker abbricht oder pausiert wird."""
        with self._lock:
            self.in_flight = max(0, self.in_flight - 1)
            if mac and portal_url:
                self.in_flight_pairs.discard((mac, portal_url))
                if requeue:
                    if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                        self._sweep_queue.append((mac, portal_url))
                    else:
                        self._retry_queue.append((mac, portal_url))
                    return
            if count_as_skipped:
                self.skipped_count += 1

    def _is_exhausted_locked(self) -> bool:
        if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
            return len(self._sweep_queue) == 0 and self.in_flight == 0
        has_retries = len(self._retry_queue) > 0
        has_fresh = len(self._fresh_macs) > 0
        has_backfill = any(len(q) > 0 for q in self._backfill_per_portal.values())
        return not (has_retries or has_fresh or has_backfill) and self.in_flight == 0

    def is_exhausted(self) -> bool:
        """Prüft, ob alle Items verarbeitet wurden und keine mehr in Bearbeitung sind."""
        with self._lock:
            return self._is_exhausted_locked()

    def get_progress(self) -> Tuple[int, int]:
        """Gibt (effektive_fertige_checks, gesamt_checks) zurück."""
        with self._lock:
            done = self.completed_count + self.skipped_count
            if self._is_exhausted_locked():
                self.total_checks = done
            return min(self.total_checks, done), self.total_checks

    def get_queue_size(self) -> int:
        """Gibt die Anzahl der noch wartenden Items zurück."""
        with self._lock:
            if self.mode in (ScanRotationMode.SWEEP, ScanRotationMode.SWEEP_EARLY_EXIT):
                return len(self._sweep_queue)
            bf_sum = sum(len(q) for q in self._backfill_per_portal.values())
            return len(self._fresh_macs) + len(self._retry_queue) + bf_sum

    def get_active_portal(self) -> str:
        """Gibt das aktuell bevorzugte Portal zurück (für Status-Anzeigen)."""
        with self._lock:
            if self.mode == ScanRotationMode.HOT_SPOT and self.active_hot_portal:
                return self.active_hot_portal
            if self.mode == ScanRotationMode.FAILOVER and self.portals:
                return self.portals[self.current_primary_index % len(self.portals)]
            return ""
