"""
Intelligenter MAC-Muster-Prädiktor und Permutations-Generator für STB Pro Qt6.
Analysiert bekannte Treffer aus der MAC-Datenbank auf Präfix-Häufungen (z. B. B5-Reihe '00:1A:79:B5:XX:XX'),
erkennt dichte Adress-Cluster und generiert gezielte Permutationen für weitere Scans.
"""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class MacClusterPattern:
    """Repräsentiert ein identifiziertes MAC-Muster oder Cluster."""
    prefix: str                       # z.B. "00:1A:79:B5" (4 Oktette) oder "00:1A:79:B5:42" (5 Oktette)
    depth: int                        # 4 oder 5
    hit_count: int                    # Anzahl Treffer mit diesem Präfix
    sample_macs: List[str]            # Beispiel-Treffer
    density_score: float              # Dichtebewertung (0.0 bis 1.0)
    description: str = ""             # z.B. "B5-Reihe (Sehr hohe Trefferdichte)"
    suggested_candidates: int = 100   # Vorgeschlagene Anzahl Permutationen


def normalize_mac(mac: str) -> str:
    """Bereinigt und formatiert eine MAC-Adresse nach XX:XX:XX:XX:XX:XX."""
    cleaned = re.sub(r'[^0-9A-Fa-f]', '', mac or "").upper()
    if len(cleaned) == 12:
        return ":".join(cleaned[i:i+2] for i in range(0, 12, 2))
    return (mac or "").strip().upper()


def mac_to_int(mac: str) -> int:
    """Konvertiert eine MAC-Adresse in eine 48-Bit-Ganzzahl."""
    cleaned = re.sub(r'[^0-9A-Fa-f]', '', mac or "")
    if len(cleaned) == 12:
        return int(cleaned, 16)
    return 0


def int_to_mac(val: int) -> str:
    """Konvertiert eine 48-Bit-Ganzzahl in eine formatierte MAC-Adresse."""
    h = f"{val & 0xFFFFFFFFFFFF:012X}"
    return ":".join(h[i:i+2] for i in range(0, 12, 2))


class MacPatternPredictor:
    """
    Analysiert MAC-Treffer auf wiederkehrende Muster und generiert
    intelligente Permutationen basierend auf Cluster-Dichten.
    """

    @staticmethod
    def analyze(mac_list: List[str]) -> List[MacClusterPattern]:
        """
        Analysiert eine Liste von MAC-Adressen und ermittelt die heißesten Muster
        (4-Byte Serien und 5-Byte Sub-Cluster), absteigend sortiert nach Treffern.
        """
        clean_macs = [normalize_mac(m) for m in mac_list if normalize_mac(m)]
        total = len(clean_macs)
        if total == 0:
            return []

        counts_4 = collections.Counter()
        samples_4 = collections.defaultdict(list)

        counts_5 = collections.Counter()
        samples_5 = collections.defaultdict(list)

        for m in clean_macs:
            parts = m.split(":")
            if len(parts) == 6:
                p4 = ":".join(parts[:4])
                p5 = ":".join(parts[:5])

                counts_4[p4] += 1
                if len(samples_4[p4]) < 3:
                    samples_4[p4].append(m)

                counts_5[p5] += 1
                if len(samples_5[p5]) < 3:
                    samples_5[p5].append(m)

        patterns: List[MacClusterPattern] = []

        # 1. 5-Byte Sub-Cluster auswerten (dichteste Bereiche)
        for p5, cnt in counts_5.most_common():
            density = min(1.0, cnt / 10.0)
            desc = f"Sub-Block ({cnt} Treffer in 256er-Bereich)"
            patterns.append(
                MacClusterPattern(
                    prefix=p5,
                    depth=5,
                    hit_count=cnt,
                    sample_macs=samples_5[p5],
                    density_score=density,
                    description=desc,
                    suggested_candidates=min(256, max(30, cnt * 25)),
                )
            )

        # 2. 4-Byte Serien auswerten (z. B. "B5-Reihe")
        for p4, cnt in counts_4.most_common():
            parts = p4.split(":")
            series_name = f"{parts[3]}-Reihe" if len(parts) == 4 else p4
            density = min(1.0, cnt / max(1.0, total * 0.25))
            desc = f"{series_name} ({cnt} Treffer)"
            patterns.append(
                MacClusterPattern(
                    prefix=p4,
                    depth=4,
                    hit_count=cnt,
                    sample_macs=samples_4[p4],
                    density_score=density,
                    description=desc,
                    suggested_candidates=min(1000, max(50, cnt * 50)),
                )
            )

        # Sortiere nach Hit-Count absteigend und Tiefe (5 vor 4)
        patterns.sort(key=lambda x: (x.hit_count, x.depth), reverse=True)
        return patterns

    @classmethod
    def generate_permutations(
        cls,
        source_macs: List[str],
        selected_patterns: Optional[List[MacClusterPattern]] = None,
        max_total: int = 500,
        mode: str = "cluster_full",  # "cluster_full", "neighbor_sweep", "series_sample"
        existing_macs: Optional[Set[str]] = None,
    ) -> List[str]:
        """
        Generiert neue, noch nicht bekannte MAC-Kandidaten aus Mustern und Cluster-Nachbarschaften.
        """
        known = set(normalize_mac(m) for m in (existing_macs or set()))
        known.update(normalize_mac(m) for m in source_macs)

        candidates: List[str] = []
        seen_cand: Set[str] = set()

        def _add(m: str):
            clean = normalize_mac(m)
            if clean and clean not in known and clean not in seen_cand:
                seen_cand.add(clean)
                candidates.append(clean)

        patterns = selected_patterns if selected_patterns is not None else cls.analyze(source_macs)

        if mode == "neighbor_sweep":
            # ± N um jeden bekannten Treffer
            for m in source_macs:
                val = mac_to_int(m)
                if val <= 0:
                    continue
                # Untersuche Nahbereich ± 40
                for offset in range(-40, 41):
                    if offset != 0:
                        _add(int_to_mac(val + offset))
                        if len(candidates) >= max_total:
                            return candidates[:max_total]

        elif mode == "cluster_full":
            # Vollständige /24 Blöcke für die 5-Byte Cluster
            for pat in [p for p in patterns if p.depth == 5]:
                for last_byte in range(0, 256):
                    _add(f"{pat.prefix}:{last_byte:02X}")
                    if len(candidates) >= max_total:
                        return candidates[:max_total]

            # Falls noch Kapazität: Nahbereich um 4-Byte Serien
            for pat in [p for p in patterns if p.depth == 4]:
                for sample in pat.sample_macs:
                    s_val = mac_to_int(sample)
                    for offset in range(-50, 51):
                        if offset != 0:
                            _add(int_to_mac(s_val + offset))
                            if len(candidates) >= max_total:
                                return candidates[:max_total]

        else:  # "series_sample"
            for pat in patterns:
                if pat.depth == 4:
                    # Verteile über die 4-Byte Reihe
                    for b5 in range(0, 256, 4):
                        for b6 in range(0, 256, 8):
                            _add(f"{pat.prefix}:{b5:02X}:{b6:02X}")
                            if len(candidates) >= max_total:
                                return candidates[:max_total]
                elif pat.depth == 5:
                    for b6 in range(0, 256):
                        _add(f"{pat.prefix}:{b6:02X}")
                        if len(candidates) >= max_total:
                            return candidates[:max_total]

        return candidates[:max_total]
