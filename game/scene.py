"""
scene.py - Szenenverwaltung, Fenster, Skalierung und Hauptschleife.

QUELLEN
-------
Keine uebernommenen Codefragmente. Das Szenenmodell, die Skalierung auf die
virtuelle Aufloesung samt Maus-Umrechnung und die Pop-up-Verwaltung sind
Eigenleistung.
Grundlagen: pygame.display, pygame.time.Clock
(https://www.pygame.org/docs/ref/display.html)
"""

import pygame

from . import config as cfg
from . import pixelfont as pf
from . import sprites
from .audio import AudioManager
from .highscore import HighscoreStore
from .ui import Popup


class Scene:
    """Basisklasse fuer jeden Screen des Spiels.

    Jede abgeleitete Szene bekommt eine Referenz auf die App und kann damit
    auf Audio, Einstellungen und Highscores zugreifen sowie die Szene
    wechseln.
    """

    #: Name des Musikstuecks, das in dieser Szene laufen soll
    music = "menu"

    def __init__(self, app):
        self.app = app
        self.buttons = []
        self.selected = 0

    def on_enter(self, **kwargs):
        """Wird bei jedem Betreten der Szene aufgerufen."""

    def on_exit(self):
        """Wird beim Verlassen der Szene aufgerufen."""

    def handle_event(self, event):
        """Verarbeitet ein einzelnes Eingabe-Ereignis."""

    def update(self):
        """Rechnet einen Frame weiter."""

    def draw(self, surface):
        """Zeichnet die Szene auf die virtuelle Surface."""

    def handle_popup_action(self, action):
        """Behandelt Pop-up-Aktionen, die nur diese Szene kennt.

        Die allgemeinen Aktionen (schliessen, beenden) erledigt bereits die
        App. Hier landet alles, was szenenspezifisch ist.
        """

    # -- Hilfen fuer menuelastige Szenen ----------------------------------
    def update_buttons(self, mouse_pos):
        """Aktualisiert Hover-Zustaende und spielt dabei den Hover-Klang."""
        for index, button in enumerate(self.buttons):
            if button.update(mouse_pos):
                self.selected = index
                self.app.audio.play("hover")

    def move_selection(self, delta):
        """Bewegt die Tastaturauswahl ueber die aktiven Buttons."""
        usable = [i for i, b in enumerate(self.buttons) if b.enabled]
        if not usable:
            return
        if self.selected in usable:
            position = usable.index(self.selected)
        else:
            position = 0
            delta = 0
        self.selected = usable[(position + delta) % len(usable)]
        for index, button in enumerate(self.buttons):
            button.hovered = (index == self.selected)
        self.app.audio.play("hover")

    def click_buttons(self, pos):
        """Gibt die Aktion des getroffenen Buttons zurueck."""
        for button in self.buttons:
            action = button.handle_click(pos)
            if action:
                self.app.audio.play("click")
                return action
        return None

    def activate_selection(self):
        """Loest den per Tastatur markierten Button aus."""
        if 0 <= self.selected < len(self.buttons):
            button = self.buttons[self.selected]
            if button.enabled:
                self.app.audio.play("click")
                return button.action
        return None


class App:
    """Haelt Fenster, Szenen, Audio und die Hauptschleife zusammen."""

    def __init__(self):
        pygame.init()

        self.settings = cfg.load_settings()
        self.audio = AudioManager(self.settings)
        self.highscores = HighscoreStore()

        self.fullscreen = bool(self.settings.get("fullscreen", False))
        self.window = None
        self._apply_display_mode()
        pygame.display.set_caption(cfg.TITLE)

        # Alles wird zuerst hierauf gezeichnet und danach hochskaliert.
        self.canvas = pygame.Surface((cfg.VIRTUAL_W, cfg.VIRTUAL_H))

        sprites.build()
        self.clock = pygame.time.Clock()
        self.running = True

        self.scenes = {}
        self.scene = None
        self.popup = None
        self.toasts = []

        # Umrechnung Fenster -> virtuelle Surface
        self._scale = 1.0
        self._offset = (0, 0)
        self._recalc_viewport()

    # -- Fenster -----------------------------------------------------------
    def _apply_display_mode(self):
        """Erzeugt das Fenster im gewuenschten Modus."""
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(
                (cfg.WINDOW_W, cfg.WINDOW_H), pygame.RESIZABLE)
        self._recalc_viewport()

    def _recalc_viewport(self):
        """Berechnet Skalierungsfaktor und schwarze Balken (Letterbox).

        EIGENLEISTUNG: Damit das Seitenverhaeltnis 16:9 immer erhalten
        bleibt, wird der kleinere der beiden Skalierungsfaktoren genommen
        und das Bild mittig platziert. Deshalb sieht das Spiel im Fenster
        und im Fullscreen identisch aus.
        """
        if self.window is None:
            return
        win_w, win_h = self.window.get_size()
        self._scale = min(win_w / cfg.VIRTUAL_W, win_h / cfg.VIRTUAL_H)
        draw_w = int(cfg.VIRTUAL_W * self._scale)
        draw_h = int(cfg.VIRTUAL_H * self._scale)
        self._offset = ((win_w - draw_w) // 2, (win_h - draw_h) // 2)

    def toggle_fullscreen(self):
        """Schaltet zwischen Fenster und Vollbild um und merkt sich das."""
        self.fullscreen = not self.fullscreen
        self.settings["fullscreen"] = self.fullscreen
        cfg.save_settings(self.settings)
        self._apply_display_mode()

    def mouse_pos(self):
        """Liefert die Mausposition in virtuellen Pixeln."""
        mx, my = pygame.mouse.get_pos()
        x = (mx - self._offset[0]) / max(0.001, self._scale)
        y = (my - self._offset[1]) / max(0.001, self._scale)
        return (int(x), int(y))

    # -- Szenen ------------------------------------------------------------
    def register(self, name, scene):
        """Meldet eine Szene unter einem Namen an."""
        self.scenes[name] = scene

    def go(self, name, **kwargs):
        """Wechselt zu einer Szene und schliesst offene Pop-ups."""
        if self.scene is not None:
            self.scene.on_exit()
        self.popup = None
        self.toasts.clear()
        self.scene = self.scenes[name]
        self.scene.on_enter(**kwargs)
        if self.scene.music:
            self.audio.play_music(self.scene.music)

    # -- Pop-ups und Toasts ------------------------------------------------
    def open_popup(self, popup):
        """Oeffnet ein modales Pop-up ueber der laufenden Szene."""
        self.popup = popup
        self.audio.play("click")

    def close_popup(self):
        """Schliesst das aktuelle Pop-up."""
        self.popup = None

    def toast(self, text, color=cfg.C_NEON_VIOLET):
        """Zeigt eine kurze, nicht blockierende Meldung an."""
        from .ui import Toast
        self.toasts.append(Toast(text, color))
        if len(self.toasts) > 3:
            self.toasts.pop(0)

    def confirm_quit(self):
        """Oeffnet die Sicherheitsabfrage vor dem Beenden."""
        self.open_popup(Popup(
            "BEENDEN?",
            ["Das Spiel wird geschlossen.", "Highscores bleiben gespeichert."],
            [("JA, BEENDEN", "quit_yes", cfg.C_NEON_PINK),
             ("ABBRECHEN", "quit_no", cfg.C_NEON_CYAN)],
            color=cfg.C_NEON_PINK,
            on_cancel="quit_no",
        ))

    def quit(self):
        """Beendet die Hauptschleife und speichert die Einstellungen."""
        cfg.save_settings(self.settings)
        self.running = False

    # -- Hauptschleife -----------------------------------------------------
    def _dispatch_popup_action(self, action):
        """Behandelt die Aktionen, die jedes Pop-up kennt."""
        if action in (None, "quit_no", "close"):
            self.close_popup()
            return True
        if action == "quit_yes":
            self.quit()
            return True
        return False

    def _handle_events(self):
        """Verteilt alle anstehenden Ereignisse."""
        mouse = self.mouse_pos()
        for event in pygame.event.get():

            # KRITERIUM 5: Das Kreuz des Fensters schliesst immer sofort.
            if event.type == pygame.QUIT:
                self.quit()
                return

            if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self._recalc_viewport()
                continue

            if event.type == pygame.KEYDOWN:
                # KRITERIUM 5: ESCAPE schliesst das Spiel zu jedem Zeitpunkt,
                # auch mitten im Spiel oder bei offenem Pop-up.
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                    return
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue
                if event.key == pygame.K_m:
                    muted = self.audio.toggle_mute()
                    cfg.save_settings(self.settings)
                    self.toast("TON AUS" if muted else "TON AN",
                               cfg.C_NEON_AMBER)
                    continue

            # Ein offenes Pop-up bekommt alle restlichen Eingaben allein.
            if self.popup is not None:
                self._popup_event(event, mouse)
                continue

            self.scene.handle_event(event)

    def _popup_event(self, event, mouse):
        """Eingabebehandlung, solange ein Pop-up offen ist."""
        action = None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.popup.move_selection(-1)
                self.audio.play("hover")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.popup.move_selection(1)
                self.audio.play("hover")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                               pygame.K_SPACE):
                action = self.popup.activate()
                self.audio.play("click")
            elif event.key == pygame.K_BACKSPACE:
                action = self.popup.on_cancel or "close"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.popup.handle_click(mouse)
            if action:
                self.audio.play("click")

        if action is None:
            return
        if self._dispatch_popup_action(action):
            return
        # Alles andere entscheidet die Szene selbst.
        self.scene.handle_popup_action(action)

    def run(self):
        """Die Hauptschleife: Ereignisse, Logik, Zeichnen, Ausgabe."""
        while self.running:
            self._handle_events()
            if not self.running:
                break

            mouse = self.mouse_pos()
            if self.popup is not None:
                self.popup.update(mouse)   # Szene bleibt bewusst eingefroren
            else:
                self.scene.update()

            for toast in list(self.toasts):
                toast.update()
                if not toast.alive:
                    self.toasts.remove(toast)

            self.canvas.fill(cfg.C_BG_DEEP)
            self.scene.draw(self.canvas)
            for index, toast in enumerate(self.toasts):
                toast.draw(self.canvas, index)
            if self.popup is not None:
                self.popup.draw(self.canvas)

            self._present()
            self.clock.tick(cfg.FPS)

        pygame.quit()

    def _present(self):
        """Skaliert die virtuelle Surface auf das Fenster und zeigt sie an."""
        self.window.fill(cfg.C_BLACK)
        draw_w = int(cfg.VIRTUAL_W * self._scale)
        draw_h = int(cfg.VIRTUAL_H * self._scale)
        # scale statt smoothscale: harte Pixelkanten bleiben erhalten
        self.window.blit(
            pygame.transform.scale(self.canvas, (draw_w, draw_h)),
            self._offset)
        pygame.display.flip()

    def frame_to_surface(self):
        """Rendert einen Einzelframe - wird fuer automatische Tests genutzt."""
        self.canvas.fill(cfg.C_BG_DEEP)
        self.scene.draw(self.canvas)
        for index, toast in enumerate(self.toasts):
            toast.draw(self.canvas, index)
        if self.popup is not None:
            self.popup.draw(self.canvas)
        return self.canvas
