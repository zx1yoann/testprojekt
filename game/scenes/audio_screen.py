"""
audio_screen.py - Der Screen fuer Musik und Toneinstellungen.

QUELLEN
-------
Keine uebernommenen Codefragmente. Layout, Schieberegler-Anbindung, die
Pegelanzeige und die Hoerproben sind Eigenleistung.

KRITERIUM 2 DER WEGLEITUNG
--------------------------
Dieser Screen erfuellt die geforderte Musiksteuerung inklusive
Mute-Funktion. Zusaetzlich lassen sich Musik und Effekte getrennt regeln,
der Musiktitel laesst sich wechseln und beide Einstellungen koennen direkt
angehoert werden. Alle Werte werden dauerhaft gespeichert.
"""

import math

import pygame

from .. import config as cfg
from .. import pixelfont as pf
from ..ui import Button, Slider, draw_panel
from .base import MenuScene


class AudioScene(MenuScene):
    """Lautstaerke, Stummschaltung und Titelauswahl."""

    back_action = "menu"
    music = None                       # laufende Musik nicht unterbrechen

    def __init__(self, app):
        super().__init__(app)
        self.sliders = [
            Slider((140, 84, 200, 6), "MUSIK", "music_volume",
                   cfg.C_NEON_VIOLET),
            Slider((140, 118, 200, 6), "EFFEKTE", "sfx_volume",
                   cfg.C_NEON_CYAN),
        ]
        self.active_slider = 0
        self.preview_track = "menu"

        self.buttons.append(Button((140, 140, 200, 22), "TON AUSSCHALTEN",
                                   "mute", cfg.C_NEON_PINK, scale=1))
        self.buttons.append(Button((140, 168, 96, 20), "HOERPROBE",
                                   "test", cfg.C_NEON_CYAN, scale=1))
        self.buttons.append(Button((244, 168, 96, 20), "TITEL WECHSELN",
                                   "track", cfg.C_NEON_AMBER, scale=1))
        self.buttons.append(Button((cfg.VIRTUAL_W // 2 - 60, 200, 120, 20),
                                   "HAUPTMENUE", "menu", cfg.C_GREY, scale=1))
        self.buttons[0].hovered = True

    def on_enter(self, **kwargs):
        self.selected = 0
        self.active_slider = 0
        self._sync_labels()

    def _sync_labels(self):
        """Haelt die Beschriftung des Mute-Buttons aktuell."""
        muted = self.app.settings.get("muted", False)
        self.buttons[0].label = "TON EINSCHALTEN" if muted else \
            "TON AUSSCHALTEN"
        self.buttons[0].color = cfg.C_NEON_LIME if muted else cfg.C_NEON_PINK
        for index, button in enumerate(self.buttons):
            button.hovered = (index == self.selected)

    def handle_event(self, event):
        """Regelt zusaetzlich die Schieberegler per Maus und Tastatur."""
        mouse = self.app.mouse_pos()

        for index, slider in enumerate(self.sliders):
            if slider.handle_event(event, self.app.settings, mouse):
                self.active_slider = index
                self.app.settings["muted"] = False   # Regeln hebt Stumm auf
                self.app.audio.apply_volumes()
                self._sync_labels()
                return

        if event.type == pygame.KEYDOWN:
            # Tab schaltet zwischen den beiden Reglern um
            if event.key == pygame.K_TAB:
                self.active_slider = (self.active_slider + 1) % len(self.sliders)
                self.app.audio.play("hover")
                return
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT,
                             pygame.K_d):
                step = 0.05 if event.key in (pygame.K_RIGHT, pygame.K_d) \
                    else -0.05
                self.sliders[self.active_slider].nudge(self.app.settings, step)
                self.app.settings["muted"] = False
                self.app.audio.apply_volumes()
                self.app.audio.play("hover")
                self._sync_labels()
                return

        super().handle_event(event)

    def on_action(self, action):
        """Behandelt Mute, Hoerprobe und Titelwechsel."""
        if action == "mute":
            muted = self.app.audio.toggle_mute()
            self.app.toast("TON AUS" if muted else "TON AN", cfg.C_NEON_AMBER)
            self._sync_labels()
        elif action == "test":
            # Hoerprobe: erst ein Effekt, die Musik laeuft ohnehin
            self.app.audio.play("coin")
            self.app.audio.play("power")
            self.app.toast("HOERPROBE", cfg.C_NEON_CYAN)
        elif action == "track":
            order = ["menu", "endless", "blackout"]
            current = self.app.audio.current_track or "menu"
            nxt = order[(order.index(current) + 1) % len(order)] \
                if current in order else "menu"
            self.app.audio.play_music(nxt)
            self.preview_track = nxt
            self.app.toast("TITEL: " + nxt.upper(), cfg.C_NEON_VIOLET)
        cfg.save_settings(self.app.settings)

    def _draw_level_meter(self, surface):
        """Zeichnet eine animierte Pegelanzeige.

        EIGENLEISTUNG: Die Anzeige ist rein dekorativ, macht aber sofort
        sichtbar, ob und wie laut gerade etwas laeuft - bei Stummschaltung
        faellt sie in sich zusammen.
        """
        muted = self.app.settings.get("muted", False)
        volume = 0.0 if muted else float(
            self.app.settings.get("music_volume", 0.6))

        rect = pygame.Rect(30, 84, 96, 104)
        draw_panel(surface, rect, fill=cfg.C_DARK, border=cfg.C_GREY, alpha=210)
        pf.draw(surface, "PEGEL", (rect.centerx, rect.y + 6), 1, cfg.C_GREY,
                align="center")

        bars = 9
        for i in range(bars):
            # Jeder Balken schwingt mit eigener Phase, gedaempft durch volume
            wave = (math.sin(self.scroll * 0.11 + i * 0.9) + 1) / 2
            # Die Balken enden oberhalb der Titelzeile, damit sie diese nicht
            # ueberdecken.
            height = int(wave * volume * 54) + (2 if volume > 0 else 1)
            bx = rect.x + 8 + i * 10
            by = rect.bottom - 20 - height
            if volume <= 0:
                color = cfg.C_GREY
            elif height > 44:
                color = cfg.C_NEON_PINK
            elif height > 26:
                color = cfg.C_NEON_AMBER
            else:
                color = cfg.C_NEON_LIME
            surface.fill(color, (bx, by, 6, height))

        surface.fill(cfg.C_BG_NEAR, (rect.x + 8, rect.bottom - 17,
                                     rect.w - 16, 1))
        track = self.app.audio.current_track or "-"
        pf.draw(surface, track.upper(), (rect.centerx, rect.bottom - 13), 1,
                cfg.C_NEON_VIOLET, align="center")

    def draw(self, surface):
        self.draw_background(surface)
        self.draw_title(surface, "MUSIK UND TON", y=10)

        muted = self.app.settings.get("muted", False)
        self._draw_level_meter(surface)

        for index, slider in enumerate(self.sliders):
            slider.draw(surface, self.app.settings,
                        active=(index == self.active_slider), muted=muted)

        if muted:
            pf.draw(surface, "ALLES STUMMGESCHALTET", (240, 62), 1,
                    cfg.C_NEON_PINK, align="center")
        elif not self.app.audio.available:
            # Ehrliche Rueckmeldung statt stiller Fehlfunktion
            pf.draw(surface, "KEINE SOUNDKARTE GEFUNDEN", (240, 62), 1,
                    cfg.C_NEON_AMBER, align="center")
        else:
            pf.draw(surface, "ALLE KLAENGE WERDEN IM SPIEL BERECHNET",
                    (240, 62), 1, cfg.C_GREY, align="center")

        for button in self.buttons:
            button.draw(surface)

        self.draw_footer(surface, "TAB WECHSELT DEN REGLER   "
                                  "LINKS RECHTS AENDERT   M SCHALTET STUMM")
        surface.blit(self.vignette, (0, 0))
