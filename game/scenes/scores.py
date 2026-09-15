"""
scores.py - Die Bestenliste.

QUELLEN
-------
Keine uebernommenen Codefragmente. Tabellenaufbau und Hervorhebung des
neuesten Eintrags sind Eigenleistung.

KRITERIUM 6 DER WEGLEITUNG
--------------------------
Der Highscore ist hier dauerhaft einsehbar, getrennt nach Spielmodus, weil
die beiden Modi nach unterschiedlichen Regeln punkten und ihre Werte daher
nicht vergleichbar waeren.
"""

import pygame

from .. import config as cfg
from .. import pixelfont as pf
from ..highscore import MAX_ENTRIES
from ..ui import Button, draw_panel
from .base import MenuScene


class ScoreScene(MenuScene):
    """Zeigt die Top-Ergebnisse beider Modi nebeneinander."""

    back_action = "menu"

    def __init__(self, app):
        super().__init__(app)
        self.highlight = None          # (modus, punkte) des letzten Laufs
        self.buttons.append(Button((cfg.VIRTUAL_W // 2 - 60, 226, 120, 20),
                                   "HAUPTMENUE", "menu", cfg.C_NEON_CYAN,
                                   scale=1))
        self.buttons[0].hovered = True

    def on_enter(self, highlight=None, **kwargs):
        """highlight hebt das gerade erzielte Ergebnis hervor."""
        self.highlight = highlight
        self.selected = 0
        self.buttons[0].hovered = True

    def _draw_table(self, surface, rect, mode, color):
        """Zeichnet die Bestenliste eines Modus als Tabelle."""
        draw_panel(surface, rect, fill=cfg.C_DARK, border=color, alpha=228)
        pf.draw(surface, cfg.MODE_LABELS[mode], (rect.centerx, rect.y + 7), 2,
                color, align="center", glow=color)

        # Kopfzeile
        head_y = rect.y + 26
        pf.draw(surface, "PL", (rect.x + 8, head_y), 1, cfg.C_GREY)
        pf.draw(surface, "PUNKTE", (rect.x + 30, head_y), 1, cfg.C_GREY)
        pf.draw(surface, "M", (rect.x + 96, head_y), 1, cfg.C_GREY)
        pf.draw(surface, "MZ", (rect.x + 130, head_y), 1, cfg.C_GREY)
        surface.fill(cfg.C_GREY, (rect.x + 8, head_y + 9, rect.w - 16, 1))

        entries = self.app.highscores.top(mode)
        y = head_y + 15
        for index in range(MAX_ENTRIES):
            if index < len(entries):
                entry = entries[index]
                is_new = (self.highlight is not None
                          and self.highlight[0] == mode
                          and self.highlight[1] == entry.get("score"))
                row_color = cfg.C_NEON_LIME if is_new else cfg.C_LIGHT

                if is_new:
                    surface.fill((*cfg.C_NEON_LIME[:3],),
                                 (rect.x + 6, y - 2, 2, 11))

                pf.draw(surface, "%d." % (index + 1), (rect.x + 8, y), 1,
                        cfg.C_NEON_AMBER if index == 0 else cfg.C_GREY)
                pf.draw(surface, "%d" % entry.get("score", 0),
                        (rect.x + 30, y), 1, row_color)
                pf.draw(surface, "%d" % entry.get("distance", 0),
                        (rect.x + 96, y), 1, cfg.C_GREY)
                pf.draw(surface, "%d" % entry.get("coins", 0),
                        (rect.x + 130, y), 1, cfg.C_GREY)
                pf.draw(surface, entry.get("date", ""), (rect.right - 8, y), 1,
                        cfg.C_BG_NEAR, align="right")
            else:
                pf.draw(surface, "%d." % (index + 1), (rect.x + 8, y), 1,
                        cfg.C_BG_NEAR)
                pf.draw(surface, "- - -", (rect.x + 30, y), 1, cfg.C_BG_NEAR)
            y += 13

    def draw(self, surface):
        self.draw_background(surface)
        self.draw_title(surface, "BESTENLISTE", y=8)

        self._draw_table(surface, pygame.Rect(24, 54, 204, 118),
                         cfg.MODE_ENDLESS, cfg.C_NEON_CYAN)
        self._draw_table(surface, pygame.Rect(252, 54, 204, 118),
                         cfg.MODE_BLACKOUT, cfg.C_NEON_VIOLET)

        pf.draw(surface, "M = GELAUFENE METER    MZ = MUENZEN",
                (cfg.VIRTUAL_W // 2, 180), 1, cfg.C_GREY, align="center")
        pf.draw(surface, "BEIDE MODI PUNKTEN NACH EIGENEN REGELN UND "
                         "WERDEN DESHALB GETRENNT GEFUEHRT.",
                (cfg.VIRTUAL_W // 2, 194), 1, cfg.C_BG_NEAR, align="center")

        for button in self.buttons:
            button.draw(surface)
        surface.blit(self.vignette, (0, 0))
