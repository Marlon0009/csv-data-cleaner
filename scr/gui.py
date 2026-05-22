"""
gui.py - Tkinter-basierte Benutzeroberfläche
=============================================
Baut die komplette GUI für das CSV Data Cleaner Tool.
Verwendet ausschließlich die Standard-Bibliothek (tkinter + ttk),
um externe Abhängigkeiten zu minimieren.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path
from typing import Optional

from src.cleaner import CSVCleaner
from src.utils import truncate_path, format_filesize


# ── Farbpalette ─────────────────────────────────────────────────────────────
COLORS = {
    "bg":           "#0f1117",   # Hintergrund (fast Schwarz)
    "surface":      "#1a1d27",   # Kartenhintergrund
    "surface2":     "#22263a",   # Eingabefelder, Hover
    "border":       "#2e3347",   # Rahmen
    "accent":       "#4f8ef7",   # Primärfarbe (Blau)
    "accent_hover": "#3d7de8",   # Blau dunkler (Hover)
    "success":      "#3ecf8e",   # Grün
    "warning":      "#f5a623",   # Orange
    "danger":       "#e05252",   # Rot
    "text":         "#e8eaf0",   # Haupttext
    "text_muted":   "#6c7293",   # Gedämpfter Text
    "text_dim":     "#3a3f5c",   # Sehr gedämpft
}


class DataCleanerApp:
    """
    Hauptklasse der Anwendung.

    Verwaltet das Hauptfenster, alle Widgets und die Kommunikation
    mit der CSVCleaner-Kernlogik.
    """

    APP_TITLE = "CSV Data Cleaner"
    APP_VERSION = "v1.0.0"
    WINDOW_SIZE = "860x680"
    WINDOW_MIN_SIZE = (760, 580)

    def __init__(self) -> None:
        self.cleaner: Optional[CSVCleaner] = None
        self.input_path: Optional[str] = None
        self.output_path: Optional[str] = None

        self._build_window()
        self._apply_theme()
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  Fenster & Theme                                                     #
    # ------------------------------------------------------------------ #

    def _build_window(self) -> None:
        """Initialisiert das Hauptfenster mit Größe und Icon-Titel."""
        self.root = tk.Tk()
        self.root.title(f"{self.APP_TITLE}  {self.APP_VERSION}")
        self.root.geometry(self.WINDOW_SIZE)
        self.root.minsize(*self.WINDOW_MIN_SIZE)
        self.root.configure(bg=COLORS["bg"])

        # Fenster zentrieren
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 860) // 2
        y = (self.root.winfo_screenheight() - 680) // 2
        self.root.geometry(f"860x680+{x}+{y}")

    def _apply_theme(self) -> None:
        """Wendet ein dunkles TTK-Theme auf alle nativen Widgets an."""
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Scrollbar
        style.configure("Vertical.TScrollbar",
                         background=COLORS["surface2"],
                         troughcolor=COLORS["surface"],
                         bordercolor=COLORS["border"],
                         arrowcolor=COLORS["text_muted"],
                         relief="flat")

        # Checkbutton
        style.configure("Dark.TCheckbutton",
                         background=COLORS["surface"],
                         foreground=COLORS["text"],
                         font=("Consolas", 10))
        style.map("Dark.TCheckbutton",
                  background=[("active", COLORS["surface2"])])

        # Separator
        style.configure("TSeparator", background=COLORS["border"])

    # ------------------------------------------------------------------ #
    #  UI-Aufbau                                                           #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        """Baut die komplette UI-Hierarchie auf."""
        self._build_header()

        # Haupt-Scrollbereich
        main_frame = tk.Frame(self.root, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self._build_file_section(main_frame)
        self._build_options_section(main_frame)
        self._build_action_section(main_frame)
        self._build_log_section(main_frame)
        self._build_statusbar()

    def _build_header(self) -> None:
        """Erstellt die obere Titelleiste."""
        header = tk.Frame(self.root, bg=COLORS["surface"], height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Linke Seite: Icon + Titel
        left = tk.Frame(header, bg=COLORS["surface"])
        left.pack(side="left", padx=20, pady=12)

        tk.Label(left, text="⬡", font=("Segoe UI", 22),
                 fg=COLORS["accent"], bg=COLORS["surface"]).pack(side="left")

        title_block = tk.Frame(left, bg=COLORS["surface"])
        title_block.pack(side="left", padx=(10, 0))

        tk.Label(title_block, text="CSV Data Cleaner",
                 font=("Segoe UI Semibold", 14, "bold"),
                 fg=COLORS["text"], bg=COLORS["surface"]).pack(anchor="w")

        tk.Label(title_block, text="Daten bereinigen · validieren · exportieren",
                 font=("Segoe UI", 9),
                 fg=COLORS["text_muted"], bg=COLORS["surface"]).pack(anchor="w")

        # Rechte Seite: Versionsbadge
        badge = tk.Label(header, text=self.APP_VERSION,
                         font=("Consolas", 9),
                         fg=COLORS["accent"], bg=COLORS["surface2"],
                         padx=10, pady=4, relief="flat")
        badge.pack(side="right", padx=20, pady=18)

        # Trennlinie
        tk.Frame(self.root, bg=COLORS["border"], height=1).pack(fill="x")

    def _card(self, parent: tk.Widget, title: str) -> tk.Frame:
        """
        Erstellt eine wiederverwendbare Karten-Komponente mit Überschrift.

        Args:
            parent: Eltern-Widget.
            title:  Überschrift der Karte.

        Returns:
            Das innere Frame für den Karten-Inhalt.
        """
        wrapper = tk.Frame(parent, bg=COLORS["surface"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
        wrapper.pack(fill="x", pady=(0, 12))

        # Karten-Header
        header = tk.Frame(wrapper, bg=COLORS["surface"])
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(header, text=title.upper(),
                 font=("Consolas", 9, "bold"),
                 fg=COLORS["text_muted"], bg=COLORS["surface"]).pack(side="left")

        # Inhalt
        content = tk.Frame(wrapper, bg=COLORS["surface"])
        content.pack(fill="x", padx=16, pady=(0, 14))

        return content

    def _build_file_section(self, parent: tk.Widget) -> None:
        """Erstellt den Bereich zur Dateiauswahl (Eingabe & Ausgabe)."""
        content = self._card(parent, "📂  Dateien")

        # — Eingabedatei —
        tk.Label(content, text="Eingabedatei (CSV)",
                 font=("Segoe UI", 10),
                 fg=COLORS["text_muted"], bg=COLORS["surface"]).pack(anchor="w")

        input_row = tk.Frame(content, bg=COLORS["surface"])
        input_row.pack(fill="x", pady=(4, 10))

        self._input_label = tk.Label(
            input_row, text="Keine Datei ausgewählt",
            font=("Consolas", 10),
            fg=COLORS["text_dim"], bg=COLORS["surface2"],
            anchor="w", padx=12,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        self._input_label.pack(side="left", fill="x", expand=True, ipady=8)

        self._make_button(input_row, "Durchsuchen", self._select_input,
                          style="secondary").pack(side="right", padx=(8, 0))

        # — Ausgabedatei —
        tk.Label(content, text="Ausgabedatei (CSV)",
                 font=("Segoe UI", 10),
                 fg=COLORS["text_muted"], bg=COLORS["surface"]).pack(anchor="w")

        output_row = tk.Frame(content, bg=COLORS["surface"])
        output_row.pack(fill="x", pady=(4, 0))

        self._output_label = tk.Label(
            output_row, text="Keine Datei ausgewählt",
            font=("Consolas", 10),
            fg=COLORS["text_dim"], bg=COLORS["surface2"],
            anchor="w", padx=12,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        self._output_label.pack(side="left", fill="x", expand=True, ipady=8)

        self._make_button(output_row, "Speicherort", self._select_output,
                          style="secondary").pack(side="right", padx=(8, 0))

    def _build_options_section(self, parent: tk.Widget) -> None:
        """Erstellt die Bereinigungsoptionen als Checkboxen."""
        content = self._card(parent, "⚙  Bereinigungsoptionen")

        # Boolean-Variablen für die Checkboxen
        self._opt_duplicates = tk.BooleanVar(value=True)
        self._opt_missing    = tk.BooleanVar(value=True)
        self._opt_dates      = tk.BooleanVar(value=True)
        self._opt_emails     = tk.BooleanVar(value=True)

        options = [
            (self._opt_duplicates, "Duplikate entfernen",
             "Identische Zeilen werden erkannt und gelöscht"),
            (self._opt_missing,    "Fehlende Werte markieren",
             "Leere Felder werden mit MISSING gekennzeichnet"),
            (self._opt_dates,      "Datumsformate vereinheitlichen",
             "Verschiedene Datumsformate → YYYY-MM-DD"),
            (self._opt_emails,     "E-Mail-Adressen validieren",
             "Ungültige Adressen werden mit INVALID_EMAIL markiert"),
        ]

        grid = tk.Frame(content, bg=COLORS["surface"])
        grid.pack(fill="x")

        for i, (var, label, hint) in enumerate(options):
            row = i // 2
            col = i % 2

            cell = tk.Frame(grid, bg=COLORS["surface"])
            cell.grid(row=row, column=col, sticky="w", padx=(0, 30), pady=3)

            ttk.Checkbutton(cell, text=label, variable=var,
                            style="Dark.TCheckbutton").pack(anchor="w")

            tk.Label(cell, text=hint, font=("Segoe UI", 8),
                     fg=COLORS["text_dim"], bg=COLORS["surface"]).pack(anchor="w")

    def _build_action_section(self, parent: tk.Widget) -> None:
        """Erstellt den Aktionsbereich mit dem Starten-Button."""
        content = self._card(parent, "▶  Aktion")

        btn_row = tk.Frame(content, bg=COLORS["surface"])
        btn_row.pack(fill="x")

        self._run_btn = self._make_button(
            btn_row, "⬡  Bereinigung starten", self._run_cleaning,
            style="primary", font_size=11
        )
        self._run_btn.pack(side="left", ipadx=16, ipady=6)

        self._make_button(
            btn_row, "Zurücksetzen", self._reset,
            style="ghost"
        ).pack(side="left", padx=(10, 0), ipadx=12, ipady=6)

        # Fortschrittsbalken (initial unsichtbar)
        self._progress_frame = tk.Frame(content, bg=COLORS["surface"])
        self._progress_frame.pack(fill="x", pady=(10, 0))

        self._progress_var = tk.DoubleVar()
        self._progressbar = ttk.Progressbar(
            self._progress_frame,
            variable=self._progress_var,
            maximum=100,
            mode="indeterminate",
            length=400
        )

    def _build_log_section(self, parent: tk.Widget) -> None:
        """Erstellt das Protokoll-Textfeld."""
        content = self._card(parent, "📋  Protokoll")

        log_frame = tk.Frame(content, bg=COLORS["surface"])
        log_frame.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            log_frame,
            height=9,
            font=("Consolas", 9),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent"],
            relief="flat",
            state="disabled",
            wrap="word",
            padx=10, pady=8
        )
        self._log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical",
                                  command=self._log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self._log_text.configure(yscrollcommand=scrollbar.set)

        # Farbliche Tags für verschiedene Log-Level
        self._log_text.tag_config("info",    foreground=COLORS["text_muted"])
        self._log_text.tag_config("success", foreground=COLORS["success"])
        self._log_text.tag_config("warning", foreground=COLORS["warning"])
        self._log_text.tag_config("error",   foreground=COLORS["danger"])
        self._log_text.tag_config("header",  foreground=COLORS["accent"])

        self._log("CSV Data Cleaner gestartet.", "header")
        self._log("Bitte Eingabedatei auswählen und Bereinigung starten.", "info")

    def _build_statusbar(self) -> None:
        """Erstellt die untere Statusleiste."""
        bar = tk.Frame(self.root, bg=COLORS["surface"], height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Frame(self.root, bg=COLORS["border"], height=1).pack(
            fill="x", side="bottom")

        self._status_var = tk.StringVar(value="Bereit")
        tk.Label(bar, textvariable=self._status_var,
                 font=("Segoe UI", 9),
                 fg=COLORS["text_muted"], bg=COLORS["surface"],
                 anchor="w").pack(side="left", padx=16, pady=4)

        tk.Label(bar, text="Python · pandas · tkinter",
                 font=("Segoe UI", 9),
                 fg=COLORS["text_dim"], bg=COLORS["surface"]).pack(
            side="right", padx=16)

    # ------------------------------------------------------------------ #
    #  Button-Factory                                                      #
    # ------------------------------------------------------------------ #

    def _make_button(self, parent: tk.Widget, text: str,
                     command, style: str = "primary",
                     font_size: int = 10) -> tk.Label:
        """
        Erstellt einen einheitlich gestalteten Button als tk.Label.

        Args:
            parent:    Eltern-Widget.
            text:      Beschriftung des Buttons.
            command:   Callback-Funktion beim Klick.
            style:     'primary', 'secondary' oder 'ghost'.
            font_size: Schriftgröße.

        Returns:
            Das Label-Widget (verhält sich wie ein Button).
        """
        styles = {
            "primary":   (COLORS["accent"],   COLORS["accent_hover"],   COLORS["bg"]),
            "secondary": (COLORS["surface2"], COLORS["border"],          COLORS["text"]),
            "ghost":     (COLORS["surface"],  COLORS["surface2"],        COLORS["text_muted"]),
        }
        bg, hover_bg, fg = styles.get(style, styles["primary"])

        btn = tk.Label(parent, text=text,
                       font=("Segoe UI Semibold", font_size),
                       fg=fg, bg=bg,
                       padx=14, pady=7,
                       cursor="hand2",
                       relief="flat")

        # Hover-Effekte
        btn.bind("<Enter>", lambda _: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda _: btn.configure(bg=bg))
        btn.bind("<Button-1>", lambda _: command())

        return btn

    # ------------------------------------------------------------------ #
    #  Dateiauswahl                                                        #
    # ------------------------------------------------------------------ #

    def _select_input(self) -> None:
        """Öffnet einen Dateiauswahl-Dialog für die Eingabedatei."""
        path = filedialog.askopenfilename(
            title="CSV-Datei auswählen",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )
        if path:
            self.input_path = path
            size = format_filesize(os.path.getsize(path))
            display = truncate_path(path)
            self._input_label.configure(
                text=f"{display}  ({size})",
                fg=COLORS["text"]
            )

            # Standardpfad für Ausgabe vorschlagen (gleicher Ordner)
            if not self.output_path:
                stem = Path(path).stem
                default_out = str(Path(path).parent / f"{stem}_cleaned.csv")
                self.output_path = default_out
                self._output_label.configure(
                    text=truncate_path(default_out),
                    fg=COLORS["text_muted"]
                )

            self._log(f"Eingabedatei: {path}", "info")
            self._status("Datei geladen — bereit zur Bereinigung.")

    def _select_output(self) -> None:
        """Öffnet einen Speichern-Dialog für die Ausgabedatei."""
        initial = self.output_path or ""
        path = filedialog.asksaveasfilename(
            title="Bereinigte CSV speichern",
            defaultextension=".csv",
            initialfile=initial,
            filetypes=[("CSV-Dateien", "*.csv")]
        )
        if path:
            self.output_path = path
            self._output_label.configure(
                text=truncate_path(path),
                fg=COLORS["text"]
            )
            self._log(f"Ausgabedatei: {path}", "info")

    # ------------------------------------------------------------------ #
    #  Bereinigung                                                         #
    # ------------------------------------------------------------------ #

    def _run_cleaning(self) -> None:
        """Startet die Bereinigung in einem separaten Thread (UI bleibt reaktiv)."""
        if not self.input_path:
            messagebox.showwarning("Keine Datei",
                                   "Bitte eine CSV-Eingabedatei auswählen.")
            return

        if not self.output_path:
            messagebox.showwarning("Kein Speicherort",
                                   "Bitte einen Speicherort für die Ausgabe festlegen.")
            return

        # Prüfen ob mindestens eine Option aktiviert ist
        options = [self._opt_duplicates, self._opt_missing,
                   self._opt_dates, self._opt_emails]
        if not any(o.get() for o in options):
            messagebox.showwarning("Keine Optionen",
                                   "Bitte mindestens eine Bereinigungsoption aktivieren.")
            return

        # UI während der Verarbeitung deaktivieren
        self._set_ui_busy(True)

        # Bereinigung in eigenem Thread ausführen
        thread = threading.Thread(target=self._cleaning_worker, daemon=True)
        thread.start()

    def _cleaning_worker(self) -> None:
        """
        Führt die Bereinigungsschritte aus (läuft im Hintergrund-Thread).
        Kommuniziert mit der UI über thread-sichere after()-Aufrufe.
        """
        try:
            self._log("─" * 45, "info")
            self._log("Bereinigung gestartet...", "header")

            cleaner = CSVCleaner()

            # Schritt 1: Laden
            self._log("Lade CSV-Datei...", "info")
            cleaner.load_csv(self.input_path)
            self._log(
                f"  ✓ {cleaner.report.original_rows} Zeilen, "
                f"{len(cleaner.report.columns_processed)} Spalten geladen.", "success"
            )

            # Schritt 2: Ausgewählte Bereinigungsschritte anwenden
            if self._opt_duplicates.get():
                self._log("Suche nach Duplikaten...", "info")
                cleaner.remove_duplicates()
                self._log(f"  ✓ {cleaner.report.duplicates_removed} Duplikate entfernt.", "success")

            if self._opt_missing.get():
                self._log("Markiere fehlende Werte...", "info")
                cleaner.mark_missing_values()
                self._log(f"  ✓ {cleaner.report.missing_values_found} fehlende Werte markiert.", "success")

            if self._opt_dates.get():
                self._log("Normalisiere Datumsformate...", "info")
                cleaner.normalize_dates()
                self._log(f"  ✓ {cleaner.report.dates_normalized} Daten normalisiert.", "success")
                if cleaner.report.invalid_dates > 0:
                    self._log(
                        f"  ⚠ {cleaner.report.invalid_dates} ungültige Datumsangaben gefunden.",
                        "warning"
                    )

            if self._opt_emails.get():
                self._log("Validiere E-Mail-Adressen...", "info")
                cleaner.validate_emails()
                if cleaner.report.emails_invalid > 0:
                    self._log(
                        f"  ⚠ {cleaner.report.emails_invalid} ungültige E-Mails gefunden.",
                        "warning"
                    )
                else:
                    self._log("  ✓ Alle E-Mail-Adressen sind gültig.", "success")

            # Schritt 3: Export
            self._log("Exportiere bereinigte CSV...", "info")
            cleaner.export_csv(self.output_path)

            # Abschlussbericht
            self._log("─" * 45, "info")
            self._log("ABSCHLUSSBERICHT:", "header")
            for line in cleaner.report.summary().splitlines():
                self._log(line, "info")
            self._log("─" * 45, "info")
            self._log(f"✓ Datei gespeichert: {self.output_path}", "success")

            self._status(f"Bereinigung abgeschlossen — {cleaner.report.final_rows} Zeilen exportiert.")

            # Erfolgsmeldung in der UI
            self.root.after(0, lambda: messagebox.showinfo(
                "Fertig",
                f"Bereinigung abgeschlossen!\n\n"
                f"Originale Zeilen:   {cleaner.report.original_rows}\n"
                f"Bereinigte Zeilen:  {cleaner.report.final_rows}\n"
                f"Duplikate:          {cleaner.report.duplicates_removed}\n\n"
                f"Gespeichert unter:\n{self.output_path}"
            ))

        except FileNotFoundError as e:
            self._log(f"FEHLER: Datei nicht gefunden — {e}", "error")
            self.root.after(0, lambda: messagebox.showerror(
                "Datei nicht gefunden", str(e)))
        except ValueError as e:
            self._log(f"FEHLER: Ungültige Daten — {e}", "error")
            self.root.after(0, lambda: messagebox.showerror(
                "Ungültige Daten", str(e)))
        except PermissionError:
            self._log("FEHLER: Keine Schreibrechte für die Ausgabedatei.", "error")
            self.root.after(0, lambda: messagebox.showerror(
                "Berechtigungsfehler",
                "Die Ausgabedatei konnte nicht geschrieben werden.\n"
                "Bitte prüfen Sie die Schreibrechte."))
        except Exception as e:
            self._log(f"UNERWARTETER FEHLER: {e}", "error")
            self.root.after(0, lambda: messagebox.showerror(
                "Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n{e}"))
        finally:
            # UI immer wieder freigeben
            self.root.after(0, lambda: self._set_ui_busy(False))

    # ------------------------------------------------------------------ #
    #  UI-Hilfsmethoden                                                    #
    # ------------------------------------------------------------------ #

    def _set_ui_busy(self, busy: bool) -> None:
        """Aktiviert/deaktiviert den Fortschrittsbalken und den Start-Button."""
        if busy:
            self._progressbar.pack(fill="x", pady=(10, 0))
            self._progressbar.start(12)
            self._run_btn.configure(fg=COLORS["text_dim"],
                                    bg=COLORS["surface2"],
                                    cursor="")
        else:
            self._progressbar.stop()
            self._progressbar.pack_forget()
            self._run_btn.configure(fg=COLORS["bg"],
                                    bg=COLORS["accent"],
                                    cursor="hand2")

    def _log(self, message: str, level: str = "info") -> None:
        """
        Schreibt eine Nachricht in das Protokoll-Textfeld.

        Thread-sicher durch root.after()-Aufruf.

        Args:
            message: Die anzuzeigende Nachricht.
            level:   Log-Level ('info', 'success', 'warning', 'error', 'header').
        """
        def _write():
            self._log_text.configure(state="normal")
            self._log_text.insert("end", message + "\n", level)
            self._log_text.see("end")  # Automatisch nach unten scrollen
            self._log_text.configure(state="disabled")

        # Thread-sicherer Aufruf
        self.root.after(0, _write)

    def _status(self, message: str) -> None:
        """Aktualisiert die Statusleiste (thread-sicher)."""
        self.root.after(0, lambda: self._status_var.set(message))

    def _reset(self) -> None:
        """Setzt alle Eingaben und das Protokoll zurück."""
        self.input_path = None
        self.output_path = None

        self._input_label.configure(text="Keine Datei ausgewählt",
                                    fg=COLORS["text_dim"])
        self._output_label.configure(text="Keine Datei ausgewählt",
                                     fg=COLORS["text_dim"])

        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

        self._log("Zurückgesetzt. Bitte neue Datei auswählen.", "header")
        self._status("Bereit")

    # ------------------------------------------------------------------ #
    #  Start                                                               #
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """Startet die Tkinter-Hauptschleife."""
        self.root.mainloop()
