"""
ui.py - Wiederverwendbare Bedienelemente: Buttons, Schieberegler, Pop-ups.

QUELLEN
-------
Keine uebernommenen Codefragmente. Das Aussehen im Neon-Stil, die
Hover-Animation, das Pop-up-System und die Toast-Meldungen sind
Eigenleistung. Grundlage ist ausschliesslich die PyGame-Dokumentation zu
Rect und Surface (https://www.pygame.org/docs/ref/rect.html).
"""

import math

import pygame

from . import config as cfg
from . import pixelfont as pf


def draw_panel(surface, rect, fill=cfg.C_DARK, border=cfg.C_NEON_CYAN,
               alpha=235, corner=3):
    """Zeichnet eine halbtransparente Box mit abgeschraegten Ecken.

    Die Ecken werden nicht gerundet, sondern pixelig abgeschnitten - das
    passt zum Retro-Look und kommt ohne Anti-Aliasing aus.
    """
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill((*fill, alpha))

    # Ecken ausstanzen
    for i in range(corner):
        cut = corner - i
        panel.fill((0, 0, 0, 0), (0, i, cut, 1))
        panel.fill((0, 0, 0, 0), (rect.w - cut, i, cut, 1))
        panel.fill((0, 0, 0, 0), (0, rect.h - 1 - i, cut, 1))
        panel.fill((0, 0, 0, 0), (rect.w - cut, rect.h - 1 - i, cut, 1))
    surface.blit(panel, rect.topleft)

    if border is not None:
        # Rahmen als vier Linien, die die abgeschraegten Ecken aussparen
        pygame.draw.line(surface, border, (rect.x + corner, rect.y),
                         (rect.right - corner - 1, rect.y))
        pygame.draw.line(surface, border, (rect.x + corner, rect.bottom - 1),
                         (rect.right - corner - 1, rect.bottom - 1))
        pygame.draw.line(surface, border, (rect.x, rect.y + corner),
                         (rect.x, rect.bottom - corner - 1))
        pygame.draw.line(surface, border, (rect.right - 1, rect.y + corner),
                         (rect.right - 1, rect.bottom - corner - 1))
        for i in range(corner):
            surface.set_at((rect.x + corner - i - 1, rect.y + i), border)
            surface.set_at((rect.right - corner + i, rect.y + i), border)
            surface.set_at((rect.x + corner - i - 1, rect.bottom - 1 - i), border)
            surface.set_at((rect.right - corner + i, rect.bottom - 1 - i), border)


class Button:
    """Ein anklickbarer Menue-Button mit Hover- und Klick-Rueckmeldung."""

    def __init__(self, rect, label, action, color=cfg.C_NEON_CYAN,
                 scale=2, enabled=True, hint=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action          # Name der Aktion, nicht die Funktion
        self.color = color
        self.scale = scale
        self.enabled = enabled
        self.hint = hint              # kleiner Zusatztext unter dem Label
        self.hovered = False
        self._pulse = 0.0

    def update(self, mouse_pos):
        """Aktualisiert den Hover-Zustand. Gibt True bei neuem Hover zurueck."""
        was = self.hovered
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)
        self._pulse = (self._pulse + 0.08) % (math.pi * 2)
        return self.hovered and not was

    def handle_click(self, pos):
        """Gibt die Aktion zurueck, wenn der Klick den Button getroffen hat."""
        if self.enabled and self.rect.collidepoint(pos):
            return self.action
        return None

    def draw(self, surface):
        """Zeichnet den Button je nach Zustand."""
        if not self.enabled:
            border, text_color, fill = cfg.C_GREY, cfg.C_GREY, cfg.C_DARK
        elif self.hovered:
            border, text_color, fill = self.color, cfg.C_WHITE, (
                min(255, cfg.C_DARK[0] + 26),
                min(255, cfg.C_DARK[1] + 20),
                min(255, cfg.C_DARK[2] + 44),
            )
        else:
            border, text_color, fill = self.color, cfg.C_LIGHT, cfg.C_DARK

        rect = self.rect.copy()
        if self.hovered:
            rect.x += 2               # Button rutscht beim Hover leicht nach rechts

        draw_panel(surface, rect, fill=fill, border=border, alpha=225)

        # Leuchtbalken am linken Rand als Auswahlmarkierung
        if self.hovered:
            glow = int(2 + math.sin(self._pulse) * 1.2)
            surface.fill(self.color, (rect.x + 2, rect.y + 3, glow, rect.h - 6))

        text_y = rect.centery - pf.GLYPH_H * self.scale // 2
        if self.hint:
            text_y = rect.y + 6
        pf.draw(surface, self.label, (rect.centerx, text_y), self.scale,
                text_color, align="center",
                glow=self.color if self.hovered else None)
        if self.hint:
            pf.draw(surface, self.hint, (rect.centerx, rect.bottom - 11), 1,
                    cfg.C_GREY, align="center")


class Slider:
    """Ein Schieberegler fuer Lautstaerkewerte von 0 bis 1."""

    def __init__(self, rect, label, key, color=cfg.C_NEON_CYAN):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.key = key                # Schluessel in den Einstellungen
        self.color = color
        self.dragging = False

    def _value_from_x(self, x):
        """Rechnet eine Mausposition in einen Wert zwischen 0 und 1 um."""
        rel = (x - self.rect.x) / max(1, self.rect.w)
        return round(max(0.0, min(1.0, rel)), 2)

    def handle_event(self, event, settings, mouse_pos):
        """Verarbeitet Maus- und Tastatureingaben. True = Wert geaendert."""
        grab = self.rect.inflate(6, 10)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if grab.collidepoint(mouse_pos):
                self.dragging = True
                settings[self.key] = self._value_from_x(mouse_pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            settings[self.key] = self._value_from_x(mouse_pos[0])
            return True
        return False

    def nudge(self, settings, delta):
        """Aendert den Wert in Schritten - fuer die Tastatursteuerung."""
        settings[self.key] = round(
            max(0.0, min(1.0, float(settings.get(self.key, 0.0)) + delta)), 2)

    def draw(self, surface, settings, active=False, muted=False):
        """Zeichnet Beschriftung, Rille, Fuellstand und Prozentwert."""
        color = cfg.C_GREY if muted else self.color
        pf.draw(surface, self.label, (self.rect.x, self.rect.y - 13), 1,
                cfg.C_WHITE if active else cfg.C_LIGHT)

        value = float(settings.get(self.key, 0.0))
        pf.draw(surface, "%d%%" % round(value * 100),
                (self.rect.right, self.rect.y - 13), 1, color, align="right")

        # Rille
        surface.fill(cfg.C_BG_NEAR, self.rect)
        pygame.draw.rect(surface, cfg.C_GREY if not active else color,
                         self.rect, 1)

        # Fuellstand als Segmentbalken, damit es pixelig wirkt
        fill_w = int((self.rect.w - 2) * value)
        for x in range(0, fill_w, 3):
            surface.fill(color, (self.rect.x + 1 + x, self.rect.y + 1, 2,
                                 self.rect.h - 2))

        # Griff
        knob_x = self.rect.x + fill_w
        knob = pygame.Rect(knob_x - 1, self.rect.y - 3, 4, self.rect.h + 6)
        surface.fill(cfg.C_WHITE if active else cfg.C_LIGHT, knob)


class Popup:
    """Ein modales Overlay, das die darunterliegende Szene anhaelt.

    EIGENLEISTUNG: Pop-ups sind kein eigener Screen, sondern legen sich
    ueber die laufende Szene. Solange ein Pop-up offen ist, friert das Spiel
    ein - dadurch funktioniert dasselbe Element als Pause-Menue, als
    Sicherheitsabfrage und als Highscore-Meldung.
    """

    def __init__(self, title, lines, buttons, color=cfg.C_NEON_CYAN,
                 width=230, on_cancel=None):
        self.title = title
        self.lines = lines
        self.color = color
        self.on_cancel = on_cancel    # Aktion bei ESC-artigem Abbruch
        self.selected = 0
        self._anim = 0.0              # Einblend-Fortschritt von 0 bis 1

        line_block = len(lines) * 11
        height = 34 + line_block + len(buttons) * 22 + 10
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (cfg.VIRTUAL_W // 2, cfg.VIRTUAL_H // 2)

        self.buttons = []
        y = self.rect.y + 28 + line_block
        for label, action, btn_color in buttons:
            self.buttons.append(Button(
                (self.rect.x + 16, y, width - 32, 18), label, action,
                btn_color, scale=1))
            y += 22

    def update(self, mouse_pos):
        """Blendet das Pop-up ein und aktualisiert die Buttons."""
        self._anim = min(1.0, self._anim + 0.18)
        for index, button in enumerate(self.buttons):
            if button.update(mouse_pos):
                self.selected = index

    def move_selection(self, delta):
        """Tastatursteuerung durch die Button-Liste."""
        if not self.buttons:
            return
        self.selected = (self.selected + delta) % len(self.buttons)
        for index, button in enumerate(self.buttons):
            button.hovered = (index == self.selected)

    def activate(self):
        """Gibt die Aktion des aktuell markierten Buttons zurueck."""
        if not self.buttons:
            return None
        return self.buttons[self.selected].action

    def handle_click(self, pos):
        """Prueft alle Buttons auf einen Treffer."""
        for button in self.buttons:
            action = button.handle_click(pos)
            if action:
                return action
        return None

    def draw(self, surface):
        """Verdunkelt den Hintergrund und zeichnet die Box."""
        shade = pygame.Surface((cfg.VIRTUAL_W, cfg.VIRTUAL_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, int(170 * self._anim)))
        surface.blit(shade, (0, 0))

        # Die Box waechst beim Einblenden von oben in die Endhoehe hinein
        rect = self.rect.copy()
        grow = self._anim
        rect.h = max(4, int(self.rect.h * grow))
        rect.centery = self.rect.centery
        draw_panel(surface, rect, fill=cfg.C_DARK, border=self.color, alpha=246)

        if grow < 0.85:
            return                    # Inhalt erst zeigen, wenn Platz da ist

        pf.draw(surface, self.title, (self.rect.centerx, self.rect.y + 10), 2,
                self.color, align="center", glow=self.color)

        y = self.rect.y + 28
        for line in self.lines:
            pf.draw(surface, line, (self.rect.centerx, y), 1, cfg.C_LIGHT,
                    align="center")
            y += 11

        for button in self.buttons:
            button.draw(surface)


class Toast:
    """Eine kurze Einblendung im Spiel, etwa bei einem Power-Up.

    EIGENLEISTUNG: Toasts halten das Spiel nicht an. Sie fahren von oben ein,
    bleiben kurz stehen und verschwinden wieder - so stoert die Rueckmeldung
    den Spielfluss nicht.
    """

    LIFETIME = 100                     # Frames

    def __init__(self, text, color=cfg.C_NEON_VIOLET, icon=None):
        self.text = text
        self.color = color
        self.icon = icon
        self.age = 0

    @property
    def alive(self):
        return self.age < self.LIFETIME

    def update(self):
        self.age += 1

    def draw(self, surface, slot=0):
        """slot verschiebt mehrere gleichzeitige Toasts untereinander."""
        progress = self.age / self.LIFETIME
        # Ein- und Ausfahren ueber die ersten und letzten 15 Prozent
        if progress < 0.15:
            offset = int((1 - progress / 0.15) * -24)
        elif progress > 0.85:
            offset = int((progress - 0.85) / 0.15 * -24)
        else:
            offset = 0

        width = pf.text_size(self.text, 1)[0] + 20
        rect = pygame.Rect(0, 0, width, 16)
        rect.centerx = cfg.VIRTUAL_W // 2
        rect.y = 40 + slot * 20 + offset

        draw_panel(surface, rect, fill=cfg.C_DARK, border=self.color, alpha=210,
                   corner=2)
        pf.draw(surface, self.text, (rect.centerx, rect.y + 5), 1, self.color,
                align="center")
