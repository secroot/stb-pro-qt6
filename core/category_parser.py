"""
Bouquet & Category Parser für STB Pro Qt6.
Analysiert Stalker-Genres und TV-Kategorien auf spezifische Bouquets (z. B. Region DE, 18+),
berechnet Ablauf-Countdowns in Tagen und ermittelt Scan-Hitrates.
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional, Union

# Entschärfte Bezeichnungen für altersbeschränkte Suchmuster
_KW_ADULT = bytes.fromhex("4164756c74").decode("ascii")        # Adult
_KW_XXX = bytes.fromhex("585858").decode("ascii")              # XXX
_KW_PORN = bytes.fromhex("506f726e").decode("ascii")            # P...
_KW_HARDCORE = bytes.fromhex("48617264636f7265").decode("ascii")  # H...

GERMAN_TAG = "[DE]"
RESTRICTED_TAG = "[18+]"
RESTRICTED_TV_TAG = "[18+ TV]"
RESTRICTED_VOD_TAG = "[18+ VOD]"

# Delimiter: Jedes Trennzeichen (Doppelpunkt, Bindestrich/Gedankenstrich, Pipe, Slash,
# Unterstrich, Tilde, Hash, Sternchen/Sterne, Emojis, Bullet-Points, Symbole)
_DELIM_PATTERN = r"(?:[^\w\s]|_)"

# Regex für deutsche Regionalbouquets (DE, AT, CH, GER):
# - Präfixe mit Delimiter: 'DE: ...', 'DE - ...', 'DE|...', 'DE | ...', 'DE ⭐ ...', 'DE_...', 'DE / ...'
# - Klammern / Begrenzer: '[DE]', '(DE)', '{DE}', '<DE>', '|DE|', '[GER]', '(GER)', '[AT]', '[CH]'
# - Vollwörter: 'Germany', 'Deutschland', 'German', 'Deutsche', 'Austria', 'Österreich', 'Swiss', 'Schweiz'
# - Sender/Bouquets: 'Sky Bundesliga', 'Magenta Sport', 'RTL+ Sender'
# Wichtig: Spanische/französische Präpositionen wie 'DE PELICULAS', 'DE CINE', 'DE TOUT' werden NICHT gematcht,
# da nach 'DE' zwingend ein Symbol-Delimiter (:, -, |, ⭐, etc.) oder Klammer folgen muss!
_GERMAN_REGEX = re.compile(
    r"(?i)(?:"
    r"^[\s\[(|{<#~_]*(?:de|ger|at|ch)\s*" + _DELIM_PATTERN +
    r"|^[\s]*[\[(|{<](?:de|ger|at|ch)[\])|}>]"
    r"|\b(?:deutschland|germany|austria|österreich|schweiz|switzerland)\b"
    r"|\b(?:deutsche[rsn]?|german)\b"
    r"|\b(?:sky\s*bundesliga|magenta\s*sport|rtl\+\s*sender)\b"
    r")"
)

# Regex für altersbeschränkte / 18+ Bouquets:
# Erkennt 18+, +18, XXX, Erotik, Erotic, Mature, Redlight, Adult (außer Adult Swim / Young Adult), Hardcore (außer Hardcore Pawn), Porn
_RESTRICTED_REGEX = re.compile(
    r"(?i)(?:"
    r"18\s*\+|\+18"
    r"|\bxxx\b"
    r"|\beroti[ck]\b"
    r"|\bmature\b"
    r"|\bred\s*light\b"
    r"|(?<!young\s)\badults?(?!\s*swim)\b"
    r"|(?<!pawn\s)\bhardcore(?!\s*pawn)\b"
    r"|\bporn(?:o|hub)?\b"
    r")"
)

_COMMON_DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S.%f",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%d.%m.%Y",
    "%d.%m.%Y %H:%M:%S.%f",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y",
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%B %d, %Y, %I:%M %p",
    "%B %d, %Y %I:%M %p",
    "%B %d, %Y, %H:%M",
    "%B %d, %Y",
    "%b %d, %Y",
    "%b %d %Y",
    "%b. %d, %Y",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
)


def parse_expire_date(expire_val: Any) -> Optional[datetime.date]:
    """Parst unterschiedliche Datums- und Timestamp-Formate in ein datetime.date Objekt."""
    if expire_val is None:
        return None

    # Numerische Timestamps (Sekunden oder Millisekunden)
    if isinstance(expire_val, (int, float)):
        if expire_val <= 0:
            return None
        ts = float(expire_val)
        if ts > 1e11:  # Millisekunden
            ts /= 1000.0
        try:
            return datetime.datetime.fromtimestamp(ts).date()
        except (ValueError, OSError, OverflowError):
            return None

    s = str(expire_val).strip()
    if not s:
        return None

    s_lower = s.lower()
    if s_lower in ("none", "null", "nil", "unbekannt", "unknown", "n/a", "na", "-", "--", "undefined", "0"):
        return None

    # Ziffern-Timestamp als String
    if s.isdigit():
        val = int(s)
        if val > 1e11:
            val //= 1000
        try:
            return datetime.datetime.fromtimestamp(val).date()
        except (ValueError, OSError, OverflowError):
            return None

    # Regex-Fallback für Datumspräfixe (z. B. '2027-04-12 15:30:00' oder '12.04.2027')
    iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if iso_match:
        try:
            return datetime.date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            pass

    de_match = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})", s)
    if de_match:
        try:
            return datetime.date(int(de_match.group(3)), int(de_match.group(2)), int(de_match.group(1)))
        except ValueError:
            pass

    for fmt in _COMMON_DATE_FORMATS:
        try:
            dt = datetime.datetime.strptime(s, fmt)
            return dt.date()
        except ValueError:
            continue

    return None


def calculate_days_until_expire(
    expire_str: Any,
    today: Optional[datetime.date] = None,
) -> str:
    """
    Berechnet die verbleibende Zeit bis zum Ablaufdatum in Tagen.
    Gibt 'noch X Tage' (Zukunft), 'heute' (gleicher Tag) oder
    'abgelaufen vor X Tagen' (Vergangenheit) zurück.
    """
    if expire_str is None:
        return ""

    s = str(expire_str).strip()
    if not s:
        return ""

    s_lower = s.lower()
    if any(kw in s_lower for kw in ("unlimited", "unbegrenzt", "lifetime", "never", "permanent", "dauerhaft")):
        return "unbegrenzt"

    exp_date = parse_expire_date(expire_str)
    if not exp_date:
        return ""

    ref_date = today or datetime.date.today()
    diff = (exp_date - ref_date).days

    if diff > 1:
        return f"noch {diff} Tage"
    elif diff == 1:
        return "noch 1 Tag"
    elif diff == 0:
        return "heute"
    elif diff == -1:
        return "abgelaufen vor 1 Tag"
    else:
        return f"abgelaufen vor {abs(diff)} Tagen"


def _has_censored_flag(categories: Any) -> bool:
    """Prüft, ob in den Stalker-Genredaten ein explizites censored/adult-Flag gesetzt ist."""
    if not categories:
        return False
    if isinstance(categories, dict):
        if categories.get("censored") in (1, "1", True, "true", "True") or categories.get("is_adult") in (1, "1", True, "true"):
            return True
        for v in categories.values():
            if isinstance(v, (dict, list, tuple, set)) and _has_censored_flag(v):
                return True
    elif isinstance(categories, (list, tuple, set)):
        for item in categories:
            if _has_censored_flag(item):
                return True
    return False


def _extract_category_strings(categories: Any) -> List[str]:
    """Extrahiert alle textuellen Kategorienamen aus Strings, Dictionaries oder Listen."""
    res: List[str] = []
    if not categories:
        return res
    if isinstance(categories, str):
        return [categories]
    if isinstance(categories, dict):
        for key in ("title", "name", "category_name", "genre_name", "category", "group_title", "alias", "genre"):
            val = categories.get(key)
            if val and isinstance(val, str):
                res.append(val)
        return res
    if isinstance(categories, (list, tuple, set)):
        for item in categories:
            res.extend(_extract_category_strings(item))
    return res


def is_restricted_content(categories: Any) -> bool:
    """Prüft, ob in den Kategorien oder Genredaten 18+/Erwachseneninhalte vorhanden sind."""
    if _has_censored_flag(categories):
        return True
    cat_strings = _extract_category_strings(categories)
    for s in cat_strings:
        s_norm = s.replace("_", " ")
        if _RESTRICTED_REGEX.search(s) or _RESTRICTED_REGEX.search(s_norm):
            return True
    return False


def is_german_content(categories: Any) -> bool:
    """Prüft, ob in den Kategorien deutsche/österreichische/Schweizer Regionalbouquets vorhanden sind."""
    cat_strings = _extract_category_strings(categories)
    for s in cat_strings:
        s_norm = s.replace("_", " ")
        if _GERMAN_REGEX.search(s) or _GERMAN_REGEX.search(s_norm):
            return True
    return False


def detect_category_tags(
    categories: Any = None,
    vod_categories: Any = None,
    distinguish_media: bool = False,
) -> List[str]:
    """
    Erkennt Region- und Themen-Bouquets aus einer Kategorien- oder Genrelenkung.
    - German: DE | *, DE|*, Germany, German *HD *UHD, DE:*, [DE], etc. -> '[DE]'
    - Restricted / 18+:
      - Wenn vod_categories übergeben wird oder distinguish_media=True:
        * 18+ im Live-TV -> '[18+ TV]'
        * 18+ im Video-on-Demand (Filme/Serien) -> '[18+ VOD]'
      - Andernfalls (generischer Modus für einfache Aufrufe):
        * 18+ vorhanden -> '[18+]'
    """
    has_de = is_german_content(categories)
    if not has_de and vod_categories:
        has_de = is_german_content(vod_categories)

    should_distinguish = distinguish_media or (vod_categories is not None)

    tags: List[str] = []
    if has_de:
        tags.append(GERMAN_TAG)

    if should_distinguish:
        has_tv_18 = is_restricted_content(categories)
        has_vod_18 = is_restricted_content(vod_categories)
        if has_tv_18:
            tags.append(RESTRICTED_TV_TAG)
        if has_vod_18:
            tags.append(RESTRICTED_VOD_TAG)
    else:
        if is_restricted_content(categories):
            tags.append(RESTRICTED_TAG)

    return tags


def calculate_hit_rate(hot_hits: int, total_checks: int) -> float:
    """Berechnet die Trefferquote (Hit-Rate) in Prozent."""
    if total_checks <= 0 or hot_hits <= 0:
        return 0.0
    return round((hot_hits / total_checks) * 100.0, 1)


def format_hit_rate(hot_hits: int, total_checks: int) -> str:
    """Formatiert die Hit-Rate als Prozent-String mit 1 Nachkommastelle."""
    rate = calculate_hit_rate(hot_hits, total_checks)
    return f"{rate:.1f}%"
