"""
utils.py - Hilfsfunktionen
===========================
Allgemeine Hilfsfunktionen, die von mehreren Modulen genutzt werden.
"""

from datetime import datetime
from typing import Optional


# Liste aller unterstützten Datumsformate in Prioritätsreihenfolge.
# Spezifischere Formate stehen vorne, um Fehlinterpretationen zu vermeiden.
SUPPORTED_DATE_FORMATS = [
    "%Y-%m-%d",      # ISO 8601:        2024-03-15
    "%d.%m.%Y",      # Deutsch:         15.03.2024
    "%d/%m/%Y",      # Europäisch:      15/03/2024
    "%m/%d/%Y",      # US-Format:       03/15/2024
    "%d-%m-%Y",      # Mit Bindestrich: 15-03-2024
    "%Y/%m/%d",      # Asiatisch:       2024/03/15
    "%d.%m.%y",      # Kurzes Deutsch:  15.03.24
    "%Y%m%d",        # Kompakt ISO:     20240315
]


def parse_date_flexible(value: str) -> Optional[datetime]:
    """
    Versucht einen Datums-String mit allen bekannten Formaten zu parsen.

    Probiert nacheinander alle Formate aus SUPPORTED_DATE_FORMATS durch.
    Gibt None zurück, wenn kein Format passt (statt eine Exception zu werfen).

    Args:
        value: Der zu parsende Datums-String.

    Returns:
        datetime-Objekt bei Erfolg, None bei unbekanntem Format.
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            # Plausibilitätsprüfung: Jahreszahlen zwischen 1900 und 2100
            if 1900 <= parsed.year <= 2100:
                return parsed
        except ValueError:
            continue  # Nächstes Format versuchen

    return None  # Kein Format hat gepasst


def format_filesize(size_bytes: int) -> str:
    """
    Formatiert eine Dateigröße in lesbare Einheiten (KB, MB).

    Args:
        size_bytes: Dateigröße in Bytes.

    Returns:
        Formatierter String, z. B. "12.4 KB" oder "2.1 MB".
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1024 ** 2:.1f} MB"


def truncate_path(path: str, max_length: int = 50) -> str:
    """
    Kürzt einen langen Dateipfad für die GUI-Anzeige.

    Args:
        path:       Vollständiger Dateipfad.
        max_length: Maximale Anzeigelänge (Standard: 50 Zeichen).

    Returns:
        Gekürzter Pfad mit '...' in der Mitte bei Überlänge.
    """
    if len(path) <= max_length:
        return path

    # Pfad in der Mitte kürzen (Anfang und Ende behalten)
    half = (max_length - 3) // 2
    return f"{path[:half]}...{path[-half:]}"
