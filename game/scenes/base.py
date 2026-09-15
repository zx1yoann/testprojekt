"""
base.py - Gemeinsame Grundlage aller Menue-Screens.

QUELLEN
-------
Keine uebernommenen Codefragmente. Der animierte Menuehintergrund und die
gemeinsame Tastatur- und Maussteuerung sind Eigenleistung.

WARUM EINE BASISKLASSE?
-----------------------
Startscreen, Anleitung, Tonsteuerung, Bestenliste und Endscreen teilen sich
denselben Hintergrund und dieselbe Bedienlogik. Statt den Code fuenfmal zu
schreiben, steht er einmal hier.
"""

import math

import pygame

from .. import config as cfg
from .. import pixelfont as pf
from .. import sprites
from ..scene import Scene


class MenuScene(Scene):
    """Basis fuer alle Screens ausserhalb des eigentlichen Spiels."""

    music = "menu"
    #: Aktion, die ausgeloest wird, wenn die Ruecktaste gedrueckt wird
    back_action = None

    def __init__(self, app):
        super().__init__(app)
        self.scroll = 0.0
        self.sky = sprites.build_gradient(cfg.VIRTUAL_W, cfg.VIRTUAL_H,
                                          cfg.C_BG_DEEP, (38, 22, 66))
        self.stars = sprites.build_stars(cfg.VIRTUAL_W * 2, 140, seed=5,
                                         count=110)
        self.skyline_far = sprites.build_skyline(cfg.VIRTUAL_W * 2, 60, seed=17)
        self.skyline_near = sprites.build_skyline(cfg.VIRTUAL_W * 2, 42,
                                                  seed=23, near=True)
        self.vignette = sprites.build_vignette(cfg.VIRTUAL_W, cfg.VIRTUAL_H,
                                               strength=120)

    # -- Ablauf ------------------------------------------------------------
    def update(self):
        """Laesst den Hintergrund langsam weiterlaufen."""
        self.scroll += 0.35
        self.update_buttons(self.app.mouse_pos())

    def handle_event(self, event):
        """Standardnavigation: Pfeile, Enter, Ruecktaste, Maus."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT):
                self.move_selection(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT):
                self.move_selection(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                               pygame.K_SPACE):
                self.dispatch(self.activate_selection())
            elif event.key == pygame.K_BACKSPACE and self.back_action:
                self.app.audio.play("click")
                self.dispatch(self.back_action)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dispatch(self.click_buttons(self.app.mouse_pos()))

    def dispatch(self, action):
        """Behandelt die Aktionen, die jeder Menue-Screen kennt."""
        if action is None:
            return
        if action == "quit":
            self.app.confirm_quit()
        elif action == "menu":
            self.app.go("menu")
        else:
            self.on_action(action)

    def on_action(self, action):
        """Wird von den abgeleiteten Screens ueberschrieben."""

    # -- Zeichnen ----------------------------------------------------------
    def draw_background(self, surface):
        """Zeichnet den gemeinsamen Parallax-Hintergrund."""
        surface.blit(self.sky, (0, 0))
        for layer, factor, y in ((self.stars, 0.05, 0),
                                 (self.skyline_far, 0.16, 96),
                                 (self.skyline_near, 0.34, 132)):
            offset = int(self.scroll * factor) % cfg.VIRTUAL_W
            surface.blit(layer, (-offset, y))

        # Bodenflaeche mit laufenden Neon-Streifen als Bewegungsandeutung
        ground_y = 174
        surface.fill(cfg.C_BG_NEAR, (0, ground_y, cfg.VIRTUAL_W,
                                     cfg.VIRTUAL_H - ground_y))
        surface.fill(cfg.C_NEON_VIOLET, (0, ground_y - 1, cfg.VIRTUAL_W, 1))
        for i in range(-1, 14):
            x = int((i * 40 - self.scroll * 1.6) % (cfg.VIRTUAL_W + 40)) - 20
            pygame.draw.line(surface, cfg.C_TRACK_LINE,
                             (x, cfg.VIRTUAL_H), (x + 26, ground_y))

        # EIGENLEISTUNG / LESBARKEIT: Der Hintergrund ist bewusst detailreich,
        # macht Text aber schwer lesbar - besonders dort, wo helle Fenster der
        # Skyline hinter heller Schrift liegen. Dieser Schleier daempft ihn
        # so weit ab, dass er noch klar erkennbar bleibt, jede Schrift davor
        # aber sicher lesbar wird.
        veil = pygame.Surface((cfg.VIRTUAL_W, cfg.VIRTUAL_H), pygame.SRCALPHA)
        veil.fill((8, 5, 20, 120))
        surface.blit(veil, (0, 0))

    def draw_content_panel(self, surface, rect, border=None, alpha=200):
        """Legt eine ruhige Flaeche hinter einen Inhaltsbereich.

        Wird von den Screens genutzt, deren Inhalt aus vielen kleinen Zeilen
        besteht und die deshalb einen besonders ruhigen Untergrund brauchen.
        """
        from ..ui import draw_panel
        draw_panel(surface, rect, fill=cfg.C_BG_DEEP, border=border,
                   alpha=alpha)

    def draw_title(self, surface, text, subtitle=None, y=18):
        """Zeichnet eine Ueberschrift im Neon-Stil mit leichtem Schweben."""
        bob = math.sin(self.scroll * 0.03) * 1.5
        pf.draw(surface, text, (cfg.VIRTUAL_W // 2, int(y + bob)), 4,
                cfg.C_WHITE, align="center", glow=cfg.C_NEON_PINK)
        if subtitle:
            pf.draw(surface, subtitle, (cfg.VIRTUAL_W // 2, int(y + 34 + bob)),
                    1, cfg.C_NEON_CYAN, align="center")

    def draw_footer(self, surface, text):
        """Zeichnet die Hinweiszeile am unteren Bildrand."""
        pf.draw(surface, text, (cfg.VIRTUAL_W // 2, cfg.VIRTUAL_H - 12), 1,
                cfg.C_GREY, align="center")

    def draw(self, surface):
        """Standardaufbau: Hintergrund, Buttons, Vignette."""
        self.draw_background(surface)
        for button in self.buttons:
            button.draw(surface)
        surface.blit(self.vignette, (0, 0))
