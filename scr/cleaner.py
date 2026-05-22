"""
cleaner.py - Kernlogik für die CSV-Datenbereinigung
=====================================================
Enthält alle Bereinigungsschritte als eigenständige Methoden,
die unabhängig getestet und kombiniert werden können.
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from src.validator import EmailValidator
from src.utils import parse_date_flexible


@dataclass
class CleaningReport:
    """Speichert alle Statistiken eines Bereinigungsdurchlaufs."""
    original_rows: int = 0
    final_rows: int = 0
    duplicates_removed: int = 0
    missing_values_found: int = 0
    dates_normalized: int = 0
    invalid_dates: int = 0
    emails_invalid: int = 0
    columns_processed: list = field(default_factory=list)

    def summary(self) -> str:
        """Gibt eine lesbare Zusammenfassung des Reports zurück."""
        lines = [
            f"  Originale Zeilen:       {self.original_rows}",
            f"  Bereinigte Zeilen:      {self.final_rows}",
            f"  Duplikate entfernt:     {self.duplicates_removed}",
            f"  Fehlende Werte:         {self.missing_values_found}",
            f"  Daten normalisiert:     {self.dates_normalized}",
            f"  Ungültige Datumsangaben:{self.invalid_dates}",
            f"  Ungültige E-Mails:      {self.emails_invalid}",
        ]
        return "\n".join(lines)


class CSVCleaner:
    """
    Haupt-Klasse für die stufenweise Bereinigung von CSV-Daten.

    Jeder Bereinigungsschritt ist eine eigene Methode und gibt
    das modifizierte DataFrame zurück, um Method-Chaining zu ermöglichen.
    """

    # Marker für fehlende Werte in der Ausgabe
    MISSING_MARKER = "MISSING"

    def __init__(self) -> None:
        self.df: Optional[pd.DataFrame] = None
        self.report = CleaningReport()
        self._email_validator = EmailValidator()

    # ------------------------------------------------------------------ #
    #  Laden & Exportieren                                                 #
    # ------------------------------------------------------------------ #

    def load_csv(self, filepath: str, encoding: str = "utf-8") -> "CSVCleaner":
        """
        Lädt eine CSV-Datei in einen pandas DataFrame.

        Args:
            filepath: Pfad zur CSV-Datei.
            encoding: Zeichensatz der Datei (Standard: utf-8).

        Raises:
            FileNotFoundError: Wenn die Datei nicht existiert.
            ValueError: Wenn die Datei leer ist oder kein valides CSV ist.
        """
        try:
            self.df = pd.read_csv(filepath, encoding=encoding, dtype=str)
        except UnicodeDecodeError:
            # Fallback auf latin-1 bei Encoding-Problemen (häufig bei deutschen Umlauten)
            self.df = pd.read_csv(filepath, encoding="latin-1", dtype=str)

        if self.df.empty:
            raise ValueError("Die CSV-Datei ist leer.")

        # Leerzeichen in Spaltennamen und Zellwerten trimmen
        self.df.columns = self.df.columns.str.strip()
        self.df = self.df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

        self.report.original_rows = len(self.df)
        self.report.columns_processed = list(self.df.columns)
        return self

    def export_csv(self, filepath: str, encoding: str = "utf-8-sig") -> None:
        """
        Exportiert den bereinigten DataFrame als CSV.

        utf-8-sig sorgt für korrektes Öffnen in Excel (BOM-Header).

        Args:
            filepath: Zielpfad für die bereinigte CSV.
            encoding: Zeichensatz der Ausgabedatei.

        Raises:
            RuntimeError: Wenn noch keine Daten geladen wurden.
        """
        if self.df is None:
            raise RuntimeError("Keine Daten geladen. Bitte zuerst load_csv() aufrufen.")

        self.report.final_rows = len(self.df)
        self.df.to_csv(filepath, index=False, encoding=encoding)

    # ------------------------------------------------------------------ #
    #  Bereinigungsschritte                                                #
    # ------------------------------------------------------------------ #

    def remove_duplicates(self, subset: Optional[list] = None) -> "CSVCleaner":
        """
        Entfernt doppelte Zeilen aus dem DataFrame.

        Args:
            subset: Liste von Spalten, die für den Duplikat-Vergleich
                    herangezogen werden. None = alle Spalten.

        Returns:
            self (für Method-Chaining)
        """
        if self.df is None:
            raise RuntimeError("Keine Daten geladen.")

        rows_before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep="first")
        self.df = self.df.reset_index(drop=True)

        self.report.duplicates_removed = rows_before - len(self.df)
        return self

    def mark_missing_values(self, additional_na_values: Optional[list] = None) -> "CSVCleaner":
        """
        Erkennt fehlende oder leere Werte und ersetzt sie mit dem MISSING-Marker.

        Behandelt dabei: None, NaN, leere Strings, 'nan', 'null', 'N/A' etc.

        Args:
            additional_na_values: Weitere benutzerdefinierte Platzhalter für
                                  fehlende Werte (z. B. ["-", "k.A."]).

        Returns:
            self (für Method-Chaining)
        """
        if self.df is None:
            raise RuntimeError("Keine Daten geladen.")

        # Standard-NA-Werte, die als "fehlend" gelten
        default_na = ["", "nan", "none", "null", "n/a", "na", "-", "k.a.", "keine"]
        if additional_na_values:
            default_na.extend([v.lower() for v in additional_na_values])

        count = 0
        for col in self.df.columns:
            # Werte normalisieren und mit NA-Liste abgleichen
            mask = self.df[col].isna() | self.df[col].str.lower().isin(default_na)
            count += mask.sum()
            self.df.loc[mask, col] = self.MISSING_MARKER

        self.report.missing_values_found = count
        return self

    def normalize_dates(self, date_columns: Optional[list] = None,
                        target_format: str = "%Y-%m-%d") -> "CSVCleaner":
        """
        Erkennt und vereinheitlicht Datumsangaben in den angegebenen Spalten.

        Unterstützte Eingangsformate:
        - DD.MM.YYYY (deutsch)
        - DD/MM/YYYY
        - YYYY-MM-DD (ISO)
        - MM-DD-YYYY (US)

        Args:
            date_columns: Spaltennamen, die Datumsangaben enthalten.
                          Wenn None, wird automatisch nach 'date', 'datum',
                          'geburtstag', 'birthday' gesucht.
            target_format: Ausgabeformat (Standard: ISO 8601 = YYYY-MM-DD).

        Returns:
            self (für Method-Chaining)
        """
        if self.df is None:
            raise RuntimeError("Keine Daten geladen.")

        # Automatische Spaltenerkennung anhand häufiger Datumsbezeichnungen
        if date_columns is None:
            keywords = ["date", "datum", "geburts", "birth", "created", "updated", "time"]
            date_columns = [
                col for col in self.df.columns
                if any(kw in col.lower() for kw in keywords)
            ]

        normalized = 0
        invalid = 0

        for col in date_columns:
            if col not in self.df.columns:
                continue

            for idx, value in self.df[col].items():
                # MISSING-Werte überspringen
                if value == self.MISSING_MARKER or pd.isna(value):
                    continue

                parsed = parse_date_flexible(str(value))
                if parsed is not None:
                    formatted = parsed.strftime(target_format)
                    # Nur zählen, wenn sich das Format tatsächlich geändert hat
                    if formatted != value:
                        normalized += 1
                    self.df.at[idx, col] = formatted
                else:
                    # Ungültiges Datum mit Marker kennzeichnen
                    self.df.at[idx, col] = f"INVALID_DATE({value})"
                    invalid += 1

        self.report.dates_normalized = normalized
        self.report.invalid_dates = invalid
        return self

    def validate_emails(self, email_columns: Optional[list] = None) -> "CSVCleaner":
        """
        Prüft E-Mail-Adressen in den angegebenen Spalten auf syntaktische Gültigkeit.

        Ungültige Adressen werden mit einem INVALID_EMAIL-Marker versehen,
        bleiben aber im Datensatz erhalten (zur manuellen Nachprüfung).

        Args:
            email_columns: Spaltennamen mit E-Mail-Adressen. Wenn None,
                           wird automatisch nach 'email', 'mail', 'e-mail' gesucht.

        Returns:
            self (für Method-Chaining)
        """
        if self.df is None:
            raise RuntimeError("Keine Daten geladen.")

        # Automatische Spaltenerkennung
        if email_columns is None:
            keywords = ["email", "mail", "e-mail"]
            email_columns = [
                col for col in self.df.columns
                if any(kw in col.lower() for kw in keywords)
            ]

        invalid_count = 0

        for col in email_columns:
            if col not in self.df.columns:
                continue

            for idx, value in self.df[col].items():
                if value == self.MISSING_MARKER or pd.isna(value):
                    continue

                if not self._email_validator.is_valid(str(value)):
                    self.df.at[idx, col] = f"INVALID_EMAIL({value})"
                    invalid_count += 1

        self.report.emails_invalid = invalid_count
        return self

    def run_all(self) -> "CSVCleaner":
        """
        Führt alle Bereinigungsschritte in der empfohlenen Reihenfolge aus.

        Reihenfolge:
        1. Duplikate entfernen
        2. Fehlende Werte markieren
        3. Datumsformate normalisieren
        4. E-Mail-Adressen validieren

        Returns:
            self (für Method-Chaining)
        """
        return (
            self
            .remove_duplicates()
            .mark_missing_values()
            .normalize_dates()
            .validate_emails()
        )
