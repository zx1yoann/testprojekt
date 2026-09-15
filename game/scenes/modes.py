"""
modes.py - Auswahl zwischen den beiden Spielmodi.

QUELLEN
-------
Keine uebernommenen Codefragmente. Layout, Vorschaukacheln und Texte sind
Eigenleistung.

KRITERIUM 8 DER WEGLEITUNG
--------------------------
Dieser Screen macht sichtbar, dass es zwei funktionell verschiedene Modi
gibt, und erklaert den Unterschied, bevor gestartet wird.
"""

import math

import pygame

from .. import config as cfg
from .. import pixelfont as pf
from .. import sprites
from ..ui import Button, draw_panel
from .base import MenuScene

# Beschreibung beider Modi. Bewusst kurz gehalten, damit sie auf die Kachel
# passt - Details stehen auf dem Anleitungsscreen.
MODE_INFO = {
    cfg.MODE_ENDLESS: {
        "color": cfg.C_NEON_CYAN,
        "tag": "DER KLASSIKER",
        "lines": [
            "Laufe so weit du kannst.",
            "Ein Treffer beendet den Lauf.",
            "Muenzen bringen Extrapunkte.",
        ],
        "rule": "STRECKE + MUENZEN X 10",
    },
    cfg.MODE_BLACKOUT: {
        "color": cfg.C_NEON_VIOLET,
        "tag": "DIE HERAUSFORDERUNG",
        "lines": [
            "Die Strecke liegt im Dunkeln.",
            "Dein Licht haengt am Akku.",
            "Muenzen laden ihn wieder auf.",
        ],
        "rule": "AKKU LEER = 3 SEK BIS AUS",
    },
}


class ModeScene(MenuScene):
    """Screen zur Wahl des Spielmodus."""

    back_action = "menu"

    def __init__(self, app):
        super().__init__(app)
        self.pulse = 0.0

        self.buttons.append(Button((22, 202, 206, 22), "ENDLESS RUN",
                                   "start_endless", cfg.C_NEON_CYAN, scale=2))
        self.buttons.append(Button((252, 202, 206, 22), "BLACKOUT",
                                   "start_blackout", cfg.C_NEON_VIOLET,
                                   scale=2))
        self.buttons.append(Button((cfg.VIRTUAL_W // 2 - 60, 230, 120, 18),
                                   "ZURUECK", "menu", cfg.C_GREY, scale=1))
        self.buttons[0].hovered = True

    def on_enter(self, **kwargs):
        self.selected = 0
        for index, button in enumerate(self.buttons):
            button.hovered = (index == 0)

    def update(self):
        super().update()
        self.pulse = (self.pulse + 0.05) % (math.pi * 2)

    def on_action(self, action):
        """Startet den gewaehlten Modus."""
        if action == "start_endless":
            self.app.go("play", mode=cfg.MODE_ENDLESS)
        elif action == "start_blackout":
            self.app.go("play", mode=cfg.MODE_BLACKOUT)

    def _draw_card(self, surface, rect, mode, highlighted):
        """Zeichnet eine Vorschaukachel fuer einen Modus."""
        info = MODE_INFO[mode]
        color = info["color"]
        border = color if highlighted else cfg.C_GREY
        draw_panel(surface, rect, fill=cfg.C_DARK, border=border, alpha=225)

        if highlighted:
            glow = int(1 + (math.sin(self.pulse) + 1) * 1.5)
            pygame.draw.rect(surface, color, rect.inflate(glow * 2, glow * 2), 1)

        pf.draw(surface, cfg.MODE_LABELS[mode], (rect.centerx, rect.y + 8), 2,
                color, align="center", glow=color if highlighted else None)
        pf.draw(surface, info["tag"], (rect.centerx, rect.y + 24), 1,
                cfg.C_GREY, align="center")

        # Kleine Vorschau: heller Streifen fuer Endless, dunkler fuer Blackout
        preview = pygame.Rect(rect.x + 14, rect.y + 38, rect.w - 28, 40)
        surface.fill(cfg.C_TRACK, preview)
        pygame.draw.rect(surface, cfg.C_TRACK_LINE, preview, 1)
        for i in range(3):
            lx = preview.x + preview.w // 4 * (i + 1) - preview.w // 8
            surface.fill(cfg.C_RAIL, (lx, preview.y + 2, 1, preview.h - 4))

        if mode == cfg.MODE_BLACKOUT:
            # Der Vorschaubereich wird bis auf einen Lichtkegel abgedunkelt
            shade = pygame.Surface(preview.size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 236))
            for r in range(30, 0, -1):
                pygame.draw.circle(shade, (0, 0, 0, int(236 * (r / 30) ** 2.2)),
                                   (preview.w // 2, preview.h - 12), r)
            surface.blit(shade, preview.topleft)
            surface.blit(sprites.scaled("run", 1.3, 1),
                         (preview.centerx - 8, preview.bottom - 26))
        else:
            surface.blit(sprites.scaled("run", 1.3, 1),
                         (preview.centerx - 8, preview.bottom - 26))
            surface.blit(sprites.scaled("barrier", 0.9),
                         (preview.x + 14, preview.y + 10))
            surface.blit(sprites.scaled("coin", 1.0),
                         (preview.right - 26, preview.y + 12))

        # Beschreibungstext, dann die Punkteregel, dann der Rekord - mit
        # festen Abstaenden zum unteren Rand, damit nichts herauslaeuft.
        y = rect.y + 84
        for line in info["lines"]:
            pf.draw(surface, line, (rect.centerx, y), 1, cfg.C_LIGHT,
                    align="center")
            y += 11

        surface.fill(cfg.C_BG_NEAR, (rect.x + 14, rect.bottom - 30,
                                     rect.w - 28, 1))
        pf.draw(surface, info["rule"], (rect.centerx, rect.bottom - 26), 1,
                color, align="center")

        best = self.app.highscores.best(mode)
        pf.draw(surface, "REKORD: %d" % best, (rect.centerx, rect.bottom - 13),
                1, cfg.C_NEON_AMBER if best else cfg.C_GREY, align="center")

    def draw(self, surface):
        self.draw_background(surface)
        self.draw_title(surface, "MODUS WAEHLEN", y=12)

        self._draw_card(surface, pygame.Rect(22, 46, 206, 150),
                        cfg.MODE_ENDLESS, self.selected == 0)
        self._draw_card(surface, pygame.Rect(252, 46, 206, 150),
                        cfg.MODE_BLACKOUT, self.selected == 1)

        for button in self.buttons:
            button.draw(surface)
        self.draw_footer(surface, "LINKS UND RECHTS WAEHLEN   ENTER STARTET")
        surface.blit(self.vignette, (0, 0))
