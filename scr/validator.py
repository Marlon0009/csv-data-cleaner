"""
validator.py - Validierungslogik für verschiedene Datentypen
=============================================================
Kapselt Validierungsregeln, sodass sie unabhängig
getestet und wiederverwendet werden können.
"""

import re


class EmailValidator:
    """
    Validiert E-Mail-Adressen anhand eines RFC-5322-kompatiblen Musters.

    Prüft auf:
    - Vorhandensein eines @-Zeichens
    - Gültigen lokalen Teil (vor dem @)
    - Gültige Domain mit mindestens einer Punkt-Trennung
    - Gültige Top-Level-Domain (mind. 2 Zeichen)
    """

    # Regex-Muster für eine strukturell gültige E-Mail-Adresse.
    # Bewusst pragmatisch gehalten — RFC 5322 vollständig wäre zu komplex
    # für den praktischen Einsatz in einem Datenbereinigungs-Tool.
    _PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    )

    def is_valid(self, email: str) -> bool:
        """
        Prüft, ob eine E-Mail-Adresse syntaktisch gültig ist.

        Args:
            email: Die zu prüfende E-Mail-Adresse.

        Returns:
            True wenn die Adresse gültig ist, sonst False.
        """
        if not email or not isinstance(email, str):
            return False

        # Leerzeichen entfernen und Länge prüfen (RFC-Limit: 254 Zeichen)
        email = email.strip()
        if len(email) > 254:
            return False

        return bool(self._PATTERN.match(email))

    def get_invalid_reason(self, email: str) -> str:
        """
        Gibt eine Begründung zurück, warum eine E-Mail-Adresse ungültig ist.

        Args:
            email: Die zu prüfende E-Mail-Adresse.

        Returns:
            Fehlergrund als String oder 'valid' wenn die Adresse gültig ist.
        """
        if not email:
            return "Leer"
        if "@" not in email:
            return "Kein @-Zeichen"
        if email.count("@") > 1:
            return "Mehrere @-Zeichen"
        local, _, domain = email.partition("@")
        if not local:
            return "Lokaler Teil fehlt"
        if "." not in domain:
            return "Domain ohne Punkt"
        if not self._PATTERN.match(email):
            return "Ungültiges Format"
        return "valid"
