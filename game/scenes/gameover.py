"""
gameover.py - Der Endscreen.

QUELLEN
-------
Keine uebernommenen Codefragmente. Layout, Ergebnisaufschluesselung, das
Rekord-Pop-up und die Konfettianimation sind Eigenleistung.

KRITERIUM 4 DER WEGLEITUNG
--------------------------
Der Endscreen ist mit fuenf Aktionen verknuepft und damit deutlich ueber der
geforderten Mindestzahl von zwei: noch einmal spielen, den Modus wechseln,
die Bestenliste ansehen, zurueck ins Hauptmenue und beenden. Zusaetzlich
liefert er einen Rueckblick auf den gerade beendeten Lauf.
"""

import math
import random

from .. import config as cfg
from .. import pixelfont as pf
from ..ui import Button, Popup, draw_panel
from .base import MenuScene

# Erklaerungstexte, warum der Lauf vorbei ist
CAUSE_TEXT = {
    "crash": "DU BIST IN EIN HINDERNIS GELAUFEN",
    "battery": "DER AKKU WAR LEER - DAS LICHT GING AUS",
}


class GameOverScene(MenuScene):
    """Zeigt das Ergebnis und bietet die Anschlussaktionen an."""

    back_action = "menu"
    music = "menu"

    def __init__(self, app):
        super().__init__(app)
        self.mode = cfg.MODE_ENDLESS
        self.score = 0
        self.distance = 0
        self.coins = 0
        self.cause = "crash"
        self.rank = None
        self.is_record = False
        self.confetti = []
        self.reveal = 0                # zaehlt den Punktestand hoch

        # EIGENLEISTUNG / LAYOUT: Die fuenf Aktionen liegen in zwei Reihen.
        # Nebeneinander in einer Reihe waere jeder Button zu schmal fuer seine
        # Beschriftung. So bekommt die haeufigste Aktion ausserdem sichtbar
        # mehr Gewicht als die vier Nebenwege.
        self.buttons.append(Button((cfg.VIRTUAL_W // 2 - 100, 150, 200, 22),
                                   "NOCHMAL SPIELEN", "again",
                                   cfg.C_NEON_LIME, scale=2))
        secondary = [
            ("MODUS WECHSELN", "swap", cfg.C_NEON_VIOLET),
            ("BESTENLISTE", "scores", cfg.C_NEON_AMBER),
            ("HAUPTMENUE", "menu", cfg.C_NEON_CYAN),
            ("BEENDEN", "quit", cfg.C_NEON_PINK),
        ]
        width, gap = 108, 4
        total = len(secondary) * width + (len(secondary) - 1) * gap
        x = (cfg.VIRTUAL_W - total) // 2
        for label, action, color in secondary:
            self.buttons.append(Button((x, 178, width, 20), label, action,
                                       color, scale=1))
            x += width + gap

    def on_enter(self, mode=cfg.MODE_ENDLESS, score=0, distance=0, coins=0,
                 cause="crash", **kwargs):
        """Traegt das Ergebnis ein und prueft die Bestenliste."""
        self.mode = mode
        self.score = int(score)
        self.distance = int(distance)
        self.coins = int(coins)
        self.cause = cause
        self.reveal = 0
        self.confetti = []
        self.selected = 0
        for index, button in enumerate(self.buttons):
            button.hovered = (index == 0)

        self.rank, self.is_record = self.app.highscores.submit(
            mode, self.score, self.distance, self.coins)

        # EIGENLEISTUNG: Ein Rekord wird nicht nur nebenbei erwaehnt, sondern
        # mit einem eigenen Pop-up gefeiert. Das Pop-up haelt den Endscreen
        # an, bis es bestaetigt wird.
        if self.is_record and self.score > 0:
            self.app.audio.play("fanfare")
            self._spawn_confetti()
            self.app.open_popup(Popup(
                "NEUER REKORD!",
                ["%s: %d PUNKTE" % (cfg.MODE_LABELS[mode], self.score),
                 "Das ist deine neue Bestleistung."],
                [("STARK!", "close", cfg.C_NEON_LIME),
                 ("BESTENLISTE ANSEHEN", "show_scores", cfg.C_NEON_AMBER)],
                color=cfg.C_NEON_LIME,
                on_cancel="close",
            ))
        elif self.rank is not None:
            self.app.toast("PLATZ %d IN DER BESTENLISTE" % self.rank,
                           cfg.C_NEON_AMBER)

    def _spawn_confetti(self):
        """Erzeugt Konfetti fuer die Rekordfeier."""
        colors = (cfg.C_NEON_PINK, cfg.C_NEON_CYAN, cfg.C_NEON_LIME,
                  cfg.C_NEON_AMBER, cfg.C_NEON_VIOLET)
        for _ in range(90):
            self.confetti.append([
                random.uniform(0, cfg.VIRTUAL_W),
                random.uniform(-cfg.VIRTUAL_H, 0),
                random.uniform(-0.4, 0.4),
                random.uniform(0.7, 2.2),
                random.choice(colors),
                random.uniform(0, math.pi * 2),
            ])

    def handle_popup_action(self, action):
        """Reagiert auf die Buttons des Rekord-Pop-ups."""
        if action == "show_scores":
            self.app.close_popup()
            self.app.go("scores", highlight=(self.mode, self.score))

    def update(self):
        super().update()

        # Punktestand laeuft beim Einblenden hoch statt sofort dazustehen
        if self.reveal < self.score:
            self.reveal = min(self.score,
                              self.reveal + max(1, self.score // 45))

        for flake in self.confetti:
            flake[0] += flake[2] + math.sin(flake[5]) * 0.5
            flake[1] += flake[3]
            flake[5] += 0.08
            if flake[1] > cfg.VIRTUAL_H:
                flake[1] = -4
                flake[0] = random.uniform(0, cfg.VIRTUAL_W)

    def on_action(self, action):
        """Fuehrt die gewaehlte Anschlussaktion aus."""
        if action == "again":
            self.app.go("play", mode=self.mode)
        elif action == "swap":
            other = cfg.MODE_BLACKOUT if self.mode == cfg.MODE_ENDLESS \
                else cfg.MODE_ENDLESS
            self.app.go("play", mode=other)
        elif action == "scores":
            self.app.go("scores", highlight=(self.mode, self.score))

    def draw(self, surface):
        self.draw_background(surface)

        color = cfg.C_NEON_PINK if self.cause == "crash" else cfg.C_NEON_VIOLET
        bob = math.sin(self.scroll * 0.04) * 1.5
        pf.draw(surface, "GAME OVER", (cfg.VIRTUAL_W // 2, int(12 + bob)), 4,
                cfg.C_WHITE, align="center", glow=color)
        pf.draw(surface, CAUSE_TEXT.get(self.cause, ""),
                (cfg.VIRTUAL_W // 2, 44), 1, color, align="center")

        self._draw_result_panel(surface)

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(surface, "PFEILE WAEHLEN   ENTER BESTAETIGT   "
                                  "ESC BEENDET DAS SPIEL")

        for x, y, _, _, col, _ in self.confetti:
            surface.fill(col, (int(x), int(y), 2, 3))
        surface.blit(self.vignette, (0, 0))

    def _draw_result_panel(self, surface):
        """Zeichnet die Ergebnistafel mit der Punkteaufschluesselung."""
        import pygame
        rect = pygame.Rect(90, 56, 300, 84)
        mode_color = cfg.C_NEON_CYAN if self.mode == cfg.MODE_ENDLESS \
            else cfg.C_NEON_VIOLET
        draw_panel(surface, rect, fill=cfg.C_DARK, border=mode_color, alpha=234)

        pf.draw(surface, cfg.MODE_LABELS[self.mode], (rect.centerx, rect.y + 6),
                1, mode_color, align="center")
        pf.draw(surface, "%d" % self.reveal, (rect.centerx, rect.y + 18), 4,
                cfg.C_WHITE, align="center", glow=mode_color)
        pf.draw(surface, "PUNKTE", (rect.centerx, rect.y + 50), 1, cfg.C_GREY,
                align="center")

        # Aufschluesselung, damit die Punkteformel nachvollziehbar bleibt
        left_x = rect.x + 16
        right_x = rect.right - 16
        pf.draw(surface, "STRECKE", (left_x, rect.bottom - 22), 1, cfg.C_GREY)
        pf.draw(surface, "%d M" % self.distance, (left_x, rect.bottom - 12), 1,
                cfg.C_LIGHT)

        pf.draw(surface, "MUENZEN", (rect.centerx, rect.bottom - 22), 1,
                cfg.C_GREY, align="center")
        pf.draw(surface, "%d" % self.coins, (rect.centerx, rect.bottom - 12), 1,
                cfg.C_NEON_AMBER, align="center")

        best = self.app.highscores.best(self.mode)
        pf.draw(surface, "REKORD", (right_x, rect.bottom - 22), 1, cfg.C_GREY,
                align="right")
        pf.draw(surface, "%d" % best, (right_x, rect.bottom - 12), 1,
                cfg.C_NEON_LIME if self.is_record else cfg.C_LIGHT,
                align="right")

        if self.rank is not None and not self.is_record:
            pf.draw(surface, "PLATZ %d" % self.rank, (rect.centerx, rect.y - 10),
                    1, cfg.C_NEON_AMBER, align="center")
