"""
howto.py - Der Anleitungsscreen.

QUELLEN
-------
Keine uebernommenen Codefragmente. Seitenaufbau, Tastenkappen-Darstellung
und alle Texte sind Eigenleistung.

KRITERIUM 2 DER WEGLEITUNG
--------------------------
Dieser Screen haelt alle notwendigen Informationen bereit. Weil das auf eine
Seite nicht lesbar passt, ist die Anleitung auf drei durchblaetterbare
Kapitel verteilt: Steuerung, Objekte und Spielmodi samt Punktevergabe.
"""

import pygame

from .. import config as cfg
from .. import pixelfont as pf
from .. import sprites
from ..ui import Button, draw_panel
from .base import MenuScene


class HowToScene(MenuScene):
    """Blaetterbare Spielanleitung."""

    back_action = "menu"

    def __init__(self, app):
        super().__init__(app)
        self.page = 0
        self.pages = ("STEUERUNG", "AUF DER STRECKE", "MODI & PUNKTE")

        self.buttons.append(Button((30, 232, 96, 20), "< ZURUECK", "prev",
                                   cfg.C_NEON_CYAN, scale=1))
        self.buttons.append(Button((cfg.VIRTUAL_W // 2 - 48, 232, 96, 20),
                                   "HAUPTMENUE", "menu", cfg.C_GREY, scale=1))
        self.buttons.append(Button((cfg.VIRTUAL_W - 126, 232, 96, 20),
                                   "WEITER >", "next", cfg.C_NEON_CYAN,
                                   scale=1))

    def on_enter(self, **kwargs):
        self.page = 0
        self.selected = 2
        self._sync_buttons()

    def _sync_buttons(self):
        """Schaltet die Blaetter-Buttons an den Raendern ab."""
        self.buttons[0].enabled = self.page > 0
        self.buttons[2].enabled = self.page < len(self.pages) - 1
        for index, button in enumerate(self.buttons):
            button.hovered = (index == self.selected and button.enabled)

    def handle_event(self, event):
        """Ergaenzt die Standardnavigation um das Blaettern per Pfeiltaste."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.on_action("prev")
                return
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.on_action("next")
                return
            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w,
                             pygame.K_s):
                self.move_selection(1 if event.key in (pygame.K_DOWN,
                                                       pygame.K_s) else -1)
                return
        super().handle_event(event)

    def on_action(self, action):
        """Blaettert vor und zurueck."""
        if action == "prev" and self.page > 0:
            self.page -= 1
            self.app.audio.play("click")
        elif action == "next" and self.page < len(self.pages) - 1:
            self.page += 1
            self.app.audio.play("click")
        self._sync_buttons()

    # -- Bausteine ---------------------------------------------------------
    def _key_cap(self, surface, pos, label, color=cfg.C_NEON_CYAN):
        """Zeichnet eine Taste als kleine Kappe.

        EIGENLEISTUNG: Die Tasten werden als gezeichnete Kappen dargestellt
        statt als blosser Text. So ist auf einen Blick klar, dass es sich um
        eine Taste handelt.
        """
        width = max(16, pf.text_size(label, 1)[0] + 8)
        rect = pygame.Rect(pos[0], pos[1], width, 13)
        draw_panel(surface, rect, fill=cfg.C_BG_NEAR, border=color, alpha=235,
                   corner=2)
        pf.draw(surface, label, (rect.centerx, rect.y + 3), 1, color,
                align="center")
        return rect

    def _row(self, surface, y, keys, text, color=cfg.C_NEON_CYAN):
        """Zeichnet eine Zeile aus Tastenkappen und Erklaerung."""
        x = 44
        for key in keys:
            rect = self._key_cap(surface, (x, y), key, color)
            x = rect.right + 4
        pf.draw(surface, text, (x + 6, y + 3), 1, cfg.C_LIGHT)

    def _page_controls(self, surface):
        """Kapitel 1: Steuerung."""
        y = 62
        self._row(surface, y, ["LINKS", "RECHTS"], "SPUR WECHSELN")
        self._row(surface, y + 19, ["HOCH", "LEER"], "SPRINGEN",
                  cfg.C_NEON_LIME)
        self._row(surface, y + 38, ["RUNTER"], "RUTSCHEN", cfg.C_NEON_LIME)
        self._row(surface, y + 57, ["P"], "PAUSE", cfg.C_NEON_AMBER)
        self._row(surface, y + 76, ["M"], "TON AN UND AUS", cfg.C_NEON_VIOLET)
        self._row(surface, y + 95, ["F11"], "VOLLBILD", cfg.C_NEON_VIOLET)
        self._row(surface, y + 114, ["ESC"], "SPIEL SOFORT BEENDEN",
                  cfg.C_NEON_PINK)
        self._row(surface, y + 133, ["ENTER"], "AUSWAHL BESTAETIGEN",
                  cfg.C_GREY)

    def _page_objects(self, surface):
        """Kapitel 2: Was auf der Strecke liegt."""
        items = [
            ("barrier", "HUERDE", "SPRINGEN", cfg.C_NEON_LIME, 1.3),
            ("lowbar", "BALKEN", "RUTSCHEN", cfg.C_NEON_AMBER, 1.3),
            ("train", "ZUG", "SPUR WECHSELN", cfg.C_NEON_PINK, 1.0),
            ("coin", "MUENZE", "EINSAMMELN", cfg.C_NEON_AMBER, 2.0),
            ("magnet", "MAGNET", "ZIEHT MUENZEN AN", cfg.C_NEON_PINK, 2.0),
            ("shield", "SCHILD", "FAENGT EINEN TREFFER", cfg.C_NEON_LIME, 2.0),
            ("double", "DOPPELT", "MUENZEN ZAEHLEN ZWEIFACH",
             cfg.C_NEON_AMBER, 2.0),
        ]
        y = 62
        for name, title, effect, color, scale in items:
            sprite = sprites.scaled(name, scale)
            surface.blit(sprite, sprite.get_rect(center=(56, y + 8)))
            pf.draw(surface, title, (78, y + 1), 1, color)
            pf.draw(surface, effect, (78, y + 11), 1, cfg.C_LIGHT)
            y += 22

    def _page_modes(self, surface):
        """Kapitel 3: Die beiden Modi und die Punktevergabe."""
        left = pygame.Rect(24, 56, 212, 150)
        right = pygame.Rect(244, 56, 212, 150)

        draw_panel(surface, left, border=cfg.C_NEON_CYAN, alpha=220)
        pf.draw(surface, "ENDLESS RUN", (left.centerx, left.y + 8), 2,
                cfg.C_NEON_CYAN, align="center")
        for i, line in enumerate([
            "Der klassische Lauf.",
            "",
            "Ein Treffer beendet",
            "den Durchgang sofort.",
            "",
            "Muenzen sind freiwillig",
            "und bringen Punkte.",
            "",
            "PUNKTE = STRECKE",
            "     + MUENZEN x 10",
        ]):
            pf.draw(surface, line, (left.x + 12, left.y + 30 + i * 11), 1,
                    cfg.C_NEON_CYAN if line.startswith("PUNKTE") or
                    line.startswith("     +") else cfg.C_LIGHT)

        draw_panel(surface, right, border=cfg.C_NEON_VIOLET, alpha=220)
        pf.draw(surface, "BLACKOUT", (right.centerx, right.y + 8), 2,
                cfg.C_NEON_VIOLET, align="center")
        for i, line in enumerate([
            "Die Strecke ist dunkel.",
            "",
            "Dein Licht laeuft auf",
            "einem Akku, der leerer",
            "wird - und mit ihm",
            "schrumpft die Sicht.",
            "",
            "Muenzen laden den Akku.",
            "Leer = 3 Sekunden blind,",
            "dann ist Schluss.",
        ]):
            pf.draw(surface, line, (right.x + 12, right.y + 30 + i * 11), 1,
                    cfg.C_LIGHT)

        pf.draw(surface, "IM BLACKOUT SIND MUENZEN KEINE PUNKTE, "
                         "SONDERN DEIN UEBERLEBEN.",
                (cfg.VIRTUAL_W // 2, 210), 1, cfg.C_NEON_AMBER, align="center")

    def draw(self, surface):
        self.draw_background(surface)
        self.draw_title(surface, "ANLEITUNG", y=8)

        # Ruhige Flaeche hinter dem Text - die Anleitung besteht aus vielen
        # kleinen Zeilen und braucht den gleichmaessigsten Untergrund.
        self.draw_content_panel(surface, pygame.Rect(16, 38, 448, 182),
                                border=cfg.C_NEON_CYAN, alpha=205)

        pf.draw(surface, self.pages[self.page], (cfg.VIRTUAL_W // 2, 44), 2,
                cfg.C_NEON_AMBER, align="center")

        (self._page_controls, self._page_objects,
         self._page_modes)[self.page](surface)

        # Seitenanzeige als Punktreihe
        for i in range(len(self.pages)):
            x = cfg.VIRTUAL_W // 2 - (len(self.pages) - 1) * 5 + i * 10
            color = cfg.C_NEON_CYAN if i == self.page else cfg.C_GREY
            surface.fill(color, (x - 2, 224, 4, 4))

        for button in self.buttons:
            button.draw(surface)
        surface.blit(self.vignette, (0, 0))
