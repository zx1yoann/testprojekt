"""
menu.py - Der Startscreen.

QUELLEN
-------
Keine uebernommenen Codefragmente. Aufbau, Titelanimation und die laufende
Figur im Hintergrund sind Eigenleistung.

KRITERIUM 1 DER WEGLEITUNG
--------------------------
Von hier aus wird das Spiel gestartet, und ueber weitere Buttons sind alle
uebrigen Screens erreichbar: Modusauswahl, Anleitung, Tonsteuerung und
Bestenliste.
"""

import math

from .. import config as cfg
from .. import pixelfont as pf
from .. import sprites
from ..ui import Button
from .base import MenuScene


class MenuScene_(MenuScene):
    """Der Startscreen mit dem Hauptmenue."""

    def __init__(self, app):
        super().__init__(app)
        self.anim = 0.0

        # Die Buttons werden einmal aufgebaut und danach nur noch gezeichnet.
        labels = [
            ("SPIELEN", "play", cfg.C_NEON_LIME),
            ("ANLEITUNG", "howto", cfg.C_NEON_CYAN),
            ("MUSIK UND TON", "audio", cfg.C_NEON_VIOLET),
            ("BESTENLISTE", "scores", cfg.C_NEON_AMBER),
            ("BEENDEN", "quit", cfg.C_NEON_PINK),
        ]
        y = 112
        for label, action, color in labels:
            self.buttons.append(Button((cfg.VIRTUAL_W // 2 - 86, y, 172, 22),
                                       label, action, color, scale=2))
            y += 27
        self.buttons[0].hovered = True

    def on_enter(self, **kwargs):
        """Setzt die Auswahl beim Betreten auf den ersten Eintrag."""
        self.selected = 0
        for index, button in enumerate(self.buttons):
            button.hovered = (index == 0)

    def update(self):
        super().update()
        self.anim = (self.anim + 0.18) % 4.0

    def on_action(self, action):
        """Leitet auf den jeweiligen Screen weiter."""
        if action == "play":
            self.app.go("modes")
        elif action == "howto":
            self.app.go("howto")
        elif action == "audio":
            self.app.go("audio")
        elif action == "scores":
            self.app.go("scores")

    def draw(self, surface):
        """Zeichnet Titel, laufende Figur, Menue und Statuszeile."""
        self.draw_background(surface)

        # EIGENLEISTUNG: Eine kleine laufende Figur zieht ueber den
        # Hintergrund und macht den Startscreen lebendig, ohne abzulenken.
        runner_x = int((self.scroll * 1.1) % (cfg.VIRTUAL_W + 60)) - 30
        runner = sprites.scaled("run", 1.6, int(self.anim))
        surface.blit(runner, runner.get_rect(midbottom=(runner_x, 196)))

        self.draw_title(surface, cfg.TITLE, "EIN PIXEL ENDLESS RUNNER", y=26)

        # Untertitel mit pulsierender Trennlinie
        pulse = int(60 + math.sin(self.scroll * 0.06) * 30)
        surface.fill((pulse, 30, pulse + 40),
                     (cfg.VIRTUAL_W // 2 - 60, 74, 120, 1))

        for button in self.buttons:
            button.draw(surface)

        # Bester Punktestand direkt im Hauptmenue sichtbar
        best = max(self.app.highscores.best(cfg.MODE_ENDLESS),
                   self.app.highscores.best(cfg.MODE_BLACKOUT))
        if best:
            pf.draw(surface, "BESTWERT %d" % best, (cfg.VIRTUAL_W // 2, 96), 1,
                    cfg.C_NEON_AMBER, align="center")

        # Statuszeile unten links - oben wuerde sie dem Titel-Leuchten
        # in die Quere kommen.
        muted = self.app.settings.get("muted", False)
        pf.draw(surface, "TON: AUS" if muted else "TON: AN",
                (8, cfg.VIRTUAL_H - 24), 1,
                cfg.C_NEON_PINK if muted else cfg.C_NEON_LIME)
        pf.draw(surface, "M = STUMM   F11 = VOLLBILD",
                (cfg.VIRTUAL_W - 8, cfg.VIRTUAL_H - 24), 1, cfg.C_GREY,
                align="right")

        self.draw_footer(surface, "PFEILE WAEHLEN   ENTER BESTAETIGT   "
                                  "ESC BEENDET DAS SPIEL")
        surface.blit(self.vignette, (0, 0))
