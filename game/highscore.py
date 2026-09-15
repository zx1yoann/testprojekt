"""
highscore.py - Dauerhafte Bestenliste, getrennt nach Spielmodus.

QUELLEN
-------
Keine uebernommenen Codefragmente. Aufbau, Sortierung und die Trennung
nach Spielmodus sind Eigenleistung.
Genutztes Standardmodul: json (https://docs.python.org/3/library/json.html)

WARUM GETRENNTE LISTEN?
-----------------------
Die beiden Spielmodi punkten nach voellig unterschiedlichen Regeln. Ein
gemeinsames Ranking waere nicht aussagekraeftig, weil die Werte nicht
vergleichbar sind. Deshalb fuehrt jeder Modus seine eigene Top-5-Liste.
"""

import datetime
import json
import os

from . import config as cfg

MAX_ENTRIES = 5


class HighscoreStore:
    """Laedt, speichert und sortiert die Bestenlisten beider Modi."""

    def __init__(self, path=None):
        self.path = path or cfg.HIGHSCORE_FILE
        self.data = {cfg.MODE_ENDLESS: [], cfg.MODE_BLACKOUT: []}
        self.load()

    def load(self):
        """Liest die Bestenliste. Fehlt die Datei, startet sie leer."""
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                stored = json.load(fh)
        except (OSError, ValueError):
            return                     # Beschaedigte Datei wird ignoriert
        for mode in self.data:
            entries = stored.get(mode, [])
            if isinstance(entries, list):
                self.data[mode] = [e for e in entries if isinstance(e, dict)]
        self._sort_all()

    def save(self):
        """Schreibt die Bestenliste auf die Festplatte."""
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2)
        except OSError:
            pass                       # Kein Schreibrecht: Spiel laeuft weiter

    def _sort_all(self):
        """Sortiert beide Listen absteigend und kuerzt sie auf MAX_ENTRIES."""
        for mode in self.data:
            self.data[mode].sort(key=lambda e: e.get("score", 0), reverse=True)
            self.data[mode] = self.data[mode][:MAX_ENTRIES]

    def best(self, mode):
        """Gibt den hoechsten Punktestand eines Modus zurueck."""
        entries = self.data.get(mode, [])
        return entries[0]["score"] if entries else 0

    def top(self, mode):
        """Gibt die sortierte Bestenliste eines Modus zurueck."""
        return list(self.data.get(mode, []))

    def qualifies(self, mode, score):
        """Prueft, ob ein Ergebnis in die Bestenliste kommt."""
        entries = self.data.get(mode, [])
        if score <= 0:
            return False
        if len(entries) < MAX_ENTRIES:
            return True
        return score > entries[-1].get("score", 0)

    def submit(self, mode, score, distance, coins):
        """Traegt ein Ergebnis ein.

        Gibt (platz, ist_neuer_rekord) zurueck. Platz ist 1-basiert oder
        None, falls das Ergebnis nicht fuer die Liste gereicht hat.
        """
        previous_best = self.best(mode)
        if not self.qualifies(mode, score):
            return (None, False)

        self.data.setdefault(mode, []).append({
            "score": int(score),
            "distance": int(distance),
            "coins": int(coins),
            "date": datetime.date.today().isoformat(),
        })
        self._sort_all()
        self.save()

        # Platz des gerade eingetragenen Ergebnisses suchen
        rank = None
        for index, entry in enumerate(self.data[mode]):
            if entry["score"] == int(score):
                rank = index + 1
                break
        return (rank, int(score) > previous_best)
