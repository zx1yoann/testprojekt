"""
play.py - Der Gamescreen. Enthaelt beide Spielmodi.

QUELLEN
-------
Keine uebernommenen Codefragmente. Die Pseudo-3D-Strasse, das HUD, die
Kollisionsauswertung, das Pause-System und insbesondere der komplette
Blackout-Modus mit der Akku-Mechanik sind Eigenleistung.
Spielprinzip inspiriert vom Endless-Runner-Genre (Subway Surfers), ohne
Code- oder Grafikuebernahme.

DIE BEIDEN SPIELMODI
--------------------
ENDLESS RUN
    Der klassische Modus. Ein Treffer beendet den Lauf. Muenzen sind reine
    Punkte, das Einsammeln ist also optional. Der Punktestand setzt sich aus
    Strecke und Muenzen zusammen.

BLACKOUT
    Der zweite Spielmodus, funktionell klar unterschieden. Die Strecke ist
    dunkel, nur ein Lichtkegel um die Figur ist sichtbar. Dieser Lichtkegel
    haengt an einem Akku, der stetig leerer wird und mit ihm schrumpft.
    Muenzen sind hier keine Punkte, sondern Akkuladung - und damit
    Pflichtprogramm statt Kuer. Ist der Akku leer, bleiben drei Sekunden
    Blindflug, dann ist der Lauf vorbei. Es gibt also eine zweite
    Verlustbedingung, die es im ersten Modus gar nicht gibt, und die
    Risikoabwaegung dreht sich um: Muenzen werden zum Ueberlebensmittel.
"""

import math
import random

import pygame

from .. import config as cfg
from .. import entities as ent
from .. import pixelfont as pf
from .. import sprites
from ..scene import Scene
from ..ui import Popup, draw_panel

# Ab dieser Tiefe hinter der Figur werden Objekte nicht mehr gezeichnet.
# Massgeblich ist das vordere Ende des Objekts: sobald das die Figur passiert
# hat, verschwindet es. Sonst bliebe vor allem der neun Einheiten lange Zug
# noch sekundenlang stehen und wuerde perspektivisch das halbe Bild fuellen,
# obwohl man laengst an ihm vorbei ist.
DRAW_Z_MIN = -1.5


class PlayScene(Scene):
    """Die eigentliche Spielszene mit Welt, Physik und HUD."""

    music = "endless"

    def on_enter(self, mode=cfg.MODE_ENDLESS, **kwargs):
        """Startet einen frischen Lauf im gewaehlten Modus."""
        self.mode = mode
        self.blackout = (mode == cfg.MODE_BLACKOUT)
        self.music = "blackout" if self.blackout else "endless"
        self.app.audio.play_music(self.music)

        self.player = ent.Player()
        self.obstacles = []
        self.pickups = []
        self.particles = []
        self.generator = ent.LevelGenerator(blackout=self.blackout)

        self.speed = cfg.BASE_SPEED
        self.distance = 0.0
        self.coins = 0
        self.score = 0
        self.frames = 0
        self.world_scroll = 0.0
        self.shake = 0.0

        # Aktive Extras: Name -> verbleibende Frames
        self.effects = {}

        # Blackout-Zustand
        self.battery = cfg.BLACKOUT_BATTERY_MAX
        self.blind_timer = 0
        self.warned_low = False

        # Countdown zu Beginn: 3, 2, 1, LOS
        self.countdown = 170
        self.finished = False

        self._build_background()
        self._light_cache = {}

    # -- Hintergrund -------------------------------------------------------
    def _build_background(self):
        """Erzeugt die Parallax-Ebenen einmal pro Lauf."""
        width = cfg.VIRTUAL_W * 2      # doppelt breit fuer nahtloses Scrollen
        self.sky = sprites.build_gradient(cfg.VIRTUAL_W, cfg.HORIZON_Y + 20,
                                          cfg.C_BG_DEEP, (44, 24, 72))
        self.stars = sprites.build_stars(width, cfg.HORIZON_Y, seed=3)
        self.skyline_far = sprites.build_skyline(width, 46, seed=11)
        self.skyline_near = sprites.build_skyline(width, 34, seed=29, near=True)
        self.vignette = sprites.build_vignette(cfg.VIRTUAL_W, cfg.VIRTUAL_H)

    # -- Eingabe -----------------------------------------------------------
    def handle_event(self, event):
        """Verarbeitet Steuerung und Pause. ESC liegt bereits in der App."""
        if event.type != pygame.KEYDOWN:
            return
        if self.finished:
            return

        if event.key in (pygame.K_p, pygame.K_PAUSE):
            self._open_pause()
            return
        if self.countdown > 0 or self.player.state == ent.Player.CRASHED:
            return

        if event.key in (pygame.K_LEFT, pygame.K_a):
            if self.player.move(-1):
                self.app.audio.play("hover")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            if self.player.move(1):
                self.app.audio.play("hover")
        elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            if self.player.jump():
                self.app.audio.play("jump")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if self.player.slide():
                self.app.audio.play("slide")

    def _open_pause(self):
        """Oeffnet das Pause-Pop-up. Das friert die Szene automatisch ein."""
        self.app.open_popup(Popup(
            "PAUSE",
            ["Strecke: %d M" % int(self.distance),
             "Punkte: %d" % self._current_score()],
            [("WEITERSPIELEN", "resume", cfg.C_NEON_LIME),
             ("NEU STARTEN", "restart", cfg.C_NEON_AMBER),
             ("ZURUECK ZUM MENUE", "menu", cfg.C_NEON_CYAN)],
            color=cfg.C_NEON_LIME,
            on_cancel="resume",
        ))

    def handle_popup_action(self, action):
        """Reagiert auf die Buttons des Pause-Pop-ups."""
        if action == "resume":
            self.app.close_popup()
            self.countdown = max(self.countdown, 110)   # kurzer Wiedereinstieg
        elif action == "restart":
            self.app.close_popup()
            self.on_enter(mode=self.mode)
        elif action == "menu":
            self.app.close_popup()
            self.app.go("menu")

    # -- Punkte ------------------------------------------------------------
    def _current_score(self):
        """Berechnet den Punktestand nach den Regeln des jeweiligen Modus.

        EIGENLEISTUNG: Die Formeln unterscheiden sich bewusst. Im Endless-Modus
        zaehlen Muenzen kraeftig mit, im Blackout-Modus sind sie bereits
        Treibstoff - dort wird stattdessen das Ueberleben in der Dunkelheit
        belohnt.
        """
        if self.blackout:
            return int(self.distance * 2.5)
        return int(self.distance + self.coins * 10)

    # -- Logik -------------------------------------------------------------
    def update(self):
        """Rechnet einen Frame des Spiels weiter."""
        self.frames += 1

        if self.countdown > 0:
            self.countdown -= 1
            return

        if self.player.state == ent.Player.CRASHED:
            self._update_crash()
            return

        self._update_speed()
        self._update_player()
        self._update_world()
        self._update_effects()
        if self.blackout:
            self._update_battery()
        self._update_particles()
        self.score = self._current_score()

    def _update_speed(self):
        """Erhoeht das Tempo langsam und kontinuierlich."""
        self.speed = min(cfg.MAX_SPEED, self.speed + cfg.SPEED_RAMP)
        if self.blackout:
            # Im Dunkeln bleibt weniger Vorwarnzeit, deshalb ist das
            # Hoechsttempo hier spuerbar niedriger angesetzt.
            self.speed = min(self.speed, cfg.MAX_SPEED * 0.78)
        self.distance += self.speed
        self.world_scroll += self.speed

    def _update_player(self):
        """Aktualisiert die Figur und spielt das Landegeraeusch."""
        if self.player.update(self.speed) == "land":
            self.app.audio.play("land")

    def _update_world(self):
        """Bewegt alle Objekte, prueft Kollisionen und erzeugt Nachschub."""
        self.generator.spawn(self.distance, self.obstacles, self.pickups)

        for obstacle in self.obstacles:
            obstacle.advance(self.speed)
        for pickup in self.pickups:
            pickup.advance(self.speed)

        self._check_obstacles()
        self._check_pickups()

        self.obstacles = [o for o in self.obstacles if o.alive]
        self.pickups = [p for p in self.pickups if p.alive]

    def _check_obstacles(self):
        """Prueft, ob die Figur ein Hindernis beruehrt."""
        for obstacle in self.obstacles:
            if not obstacle.alive or not obstacle.in_hit_zone():
                continue
            if obstacle.lane != self.player.lane:
                continue
            if not obstacle.blocks(self.player):
                continue

            had_shield = self.player.shield
            fatal = self.player.crash()
            if fatal:
                self.app.audio.play("crash")
                self.shake = 9.0
                self._burst(cfg.C_NEON_PINK, 26)
            elif had_shield:
                self.app.audio.play("power")
                self.app.toast("SCHILD VERBRAUCHT", cfg.C_NEON_LIME)
                self.shake = 4.0
                self._burst(cfg.C_NEON_LIME, 14)
                obstacle.alive = False
            return

    def _check_pickups(self):
        """Sammelt Muenzen und Extras ein, inklusive Magnetwirkung."""
        magnet = "magnet" in self.effects
        for pickup in self.pickups:
            if not pickup.alive:
                continue

            # Magnet zieht Muenzen im Nahbereich auf die eigene Spur
            if magnet and isinstance(pickup, ent.Coin) and pickup.z < 26:
                pickup.attract(self.player.lane)

            if not pickup.in_hit_zone():
                continue

            # Muenzen brauchen keine punktgenaue Spur, das waere zu streng
            lane_ok = abs(pickup.lane - self.player.lane) < 0.55
            if not lane_ok:
                continue
            # Ein hoher Sprung hebt die Figur ueber tief liegende Muenzen
            # hinweg - die Greifweite ist grosszuegig, aber nicht unendlich.
            if abs(self.player.height - pickup.height) > cfg.PICKUP_REACH:
                continue

            pickup.alive = False
            if isinstance(pickup, ent.PowerUp):
                self._apply_powerup(pickup)
            else:
                self._collect_coin()

    def _collect_coin(self):
        """Verbucht eine eingesammelte Muenze je nach Modus."""
        gain = 2 if "double" in self.effects else 1
        self.coins += gain
        self.app.audio.play("coin")
        self._burst(cfg.C_NEON_AMBER, 5)

        if self.blackout:
            # EIGENLEISTUNG: Im Blackout-Modus laedt die Muenze den Akku.
            self.battery = min(cfg.BLACKOUT_BATTERY_MAX,
                               self.battery + cfg.BLACKOUT_COIN_GAIN * gain)
            if self.battery > 35:
                self.warned_low = False
            if self.blind_timer > 0:
                self.blind_timer = 0
                self.app.toast("LICHT WIEDER DA", cfg.C_NEON_LIME)

    def _apply_powerup(self, pickup):
        """Aktiviert ein eingesammeltes Extra."""
        kind = pickup.kind
        self.app.audio.play("power")
        self.app.toast(ent.PowerUp.LABELS[kind], ent.PowerUp.COLORS[kind])
        self._burst(ent.PowerUp.COLORS[kind], 16)

        if kind == "shield":
            self.player.shield = True
        else:
            self.effects[kind] = ent.PowerUp.DURATIONS[kind]

    def _update_effects(self):
        """Zaehlt die Laufzeit aktiver Extras herunter."""
        for kind in list(self.effects):
            self.effects[kind] -= 1
            if self.effects[kind] <= 0:
                del self.effects[kind]
                self.app.toast(ent.PowerUp.LABELS[kind] + " VORBEI", cfg.C_GREY)

    def _update_battery(self):
        """Die Akku-Mechanik des Blackout-Modus.

        EIGENLEISTUNG: Der Akku ist die zweite Verlustbedingung. Er sinkt
        konstant, wird durch Muenzen aufgeladen und bestimmt zugleich, wie
        weit die Figur ueberhaupt sehen kann. Faellt er auf null, laeuft eine
        Gnadenfrist von drei Sekunden - danach ist der Lauf vorbei.
        """
        drain = cfg.BLACKOUT_DRAIN * (1.0 + self.distance / 4200.0)
        self.battery = max(0.0, self.battery - drain)

        if 0 < self.battery <= 30 and not self.warned_low:
            self.warned_low = True
            self.app.audio.play("warn")
            self.app.toast("AKKU FAST LEER", cfg.C_NEON_PINK)

        if self.battery <= 0:
            self.blind_timer += 1
            if self.blind_timer % 40 == 1:
                self.app.audio.play("warn")
            if self.blind_timer >= cfg.BLACKOUT_GRACE_FRAMES:
                self.player.crash()
                self.app.audio.play("crash")
                self.shake = 9.0

    def _update_crash(self):
        """Laesst die Crash-Animation auslaufen und wechselt zum Endscreen."""
        self.player.update(self.speed)
        self.speed *= 0.90             # die Welt bremst sichtbar ab
        for obstacle in self.obstacles:
            obstacle.advance(self.speed)
        for pickup in self.pickups:
            pickup.advance(self.speed)
        self._update_particles()

        if self.player.crash_timer > 78 and not self.finished:
            self.finished = True
            self.app.go("gameover",
                        mode=self.mode,
                        score=self.score,
                        distance=int(self.distance),
                        coins=self.coins,
                        cause="battery" if (self.blackout and self.battery <= 0)
                              else "crash")

    # -- Partikel ----------------------------------------------------------
    def _burst(self, color, count):
        """Streut kurzlebige Funken an der Position der Figur.

        EIGENLEISTUNG: Ein leichtgewichtiges Partikelsystem ohne eigene
        Klasse - jedes Teilchen ist nur eine Liste aus Position, Tempo,
        Lebensdauer und Farbe. Das reicht voellig und kostet fast nichts.
        """
        x, y, _ = ent.project(0.0, self.player.lane_offset, self.player.height)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.6, 2.8)
            self.particles.append([
                x, y - 8,
                math.cos(angle) * speed,
                math.sin(angle) * speed - 0.9,
                random.randint(16, 40),
                color,
            ])

    def _update_particles(self):
        """Bewegt die Funken und entfernt erloschene."""
        for particle in self.particles:
            particle[0] += particle[2]
            particle[1] += particle[3]
            particle[3] += 0.13        # Schwerkraft
            particle[4] -= 1
        self.particles = [p for p in self.particles if p[4] > 0]

    # -- Zeichnen ----------------------------------------------------------
    def draw(self, surface):
        """Baut das Bild Ebene fuer Ebene auf."""
        # Bildschirmwackeln nach einem Treffer
        shake_x = shake_y = 0
        if self.shake > 0.3:
            shake_x = int(random.uniform(-self.shake, self.shake))
            shake_y = int(random.uniform(-self.shake, self.shake) * 0.5)
            self.shake *= 0.86

        frame = surface if (shake_x == shake_y == 0) else \
            pygame.Surface((cfg.VIRTUAL_W, cfg.VIRTUAL_H))

        self._draw_background(frame)
        self._draw_road(frame)
        self._draw_world(frame)
        self._draw_particles(frame)

        if self.blackout:
            self._draw_darkness(frame)
        else:
            frame.blit(self.vignette, (0, 0))

        if frame is not surface:
            surface.fill(cfg.C_BLACK)
            surface.blit(frame, (shake_x, shake_y))

        self._draw_hud(surface)
        if self.countdown > 0:
            self._draw_countdown(surface)

    def _draw_background(self, surface):
        """Zeichnet Himmel, Sterne und beide Skylines mit Parallax-Versatz."""
        surface.blit(self.sky, (0, 0))

        # Jede Ebene bewegt sich langsamer als die davor - das erzeugt Tiefe.
        for layer, factor, y in ((self.stars, 0.04, 0),
                                 (self.skyline_far, 0.13, cfg.HORIZON_Y - 46),
                                 (self.skyline_near, 0.30, cfg.HORIZON_Y - 30)):
            offset = int(self.world_scroll * factor) % cfg.VIRTUAL_W
            surface.blit(layer, (-offset, y))

        # Horizontlinie als Neon-Streifen
        surface.fill(cfg.C_NEON_VIOLET, (0, cfg.HORIZON_Y - 1, cfg.VIRTUAL_W, 1))

    def _draw_road(self, surface):
        """Zeichnet die Strasse zeilenweise in Perspektive.

        EIGENLEISTUNG: Statt die Strasse in Tiefenschritten aufzubauen, wird
        hier ueber die Bildschirmzeilen iteriert und zu jeder Zeile die
        passende Tiefe zurueckgerechnet. Der Vorteil: jedes Band ist exakt
        einen Pixel hoch, die Spurlinien bleiben dadurch lueckenlos und
        bilden keine Treppen. Der Aufwand ist konstant - eine Rechnung pro
        Bildzeile - unabhaengig davon, wie weit man sehen kann.

        Die Umkehrung der Projektion:
            y = HORIZON_Y + (GROUND_Y - HORIZON_Y) * d   =>  d aus y
            d = 1 / (1 + z * DEPTH_K)                    =>  z aus d
        """
        # Flaeche neben der Strasse (Tunnelboden) bis zum unteren Bildrand
        surface.fill(cfg.C_BG_NEAR, (0, cfg.HORIZON_Y,
                                     cfg.VIRTUAL_W, cfg.VIRTUAL_H - cfg.HORIZON_Y))

        span = cfg.GROUND_Y - cfg.HORIZON_Y
        bright = (cfg.C_TRACK[0] + 9, cfg.C_TRACK[1] + 7, cfg.C_TRACK[2] + 16)

        for y in range(cfg.HORIZON_Y + 1, cfg.VIRTUAL_H):
            d = (y - cfg.HORIZON_Y) / span
            if d <= 0.0:
                continue
            z = (1.0 / d - 1.0) / ent.DEPTH_K

            width = cfg.ROAD_W_FAR + (cfg.ROAD_W_NEAR - cfg.ROAD_W_FAR) * d
            left = int(ent.CENTER_X - width / 2)
            span_w = int(width) + 1

            # Querstreifen: die Farbe haengt an der Weltposition, dadurch
            # wandern die Streifen auf den Betrachter zu.
            phase = int((z + self.world_scroll) / 4.0) % 2
            surface.fill(cfg.C_TRACK if phase else bright, (left, y, span_w, 1))

            line_w = max(1, int(d * 2.0))
            # Spurtrennlinien auf den Grenzen zwischen den drei Spuren
            for edge in (-0.5, 0.5):
                lx = int(ent.CENTER_X + edge * width * 0.66) - line_w // 2
                surface.fill(cfg.C_TRACK_LINE, (lx, y, line_w, 1))
            # Aussenkanten als leuchtende Schienen
            for edge in (-1, 1):
                lx = int(ent.CENTER_X + edge * width * 0.5) - line_w // 2
                surface.fill(cfg.C_RAIL, (lx, y, line_w, 1))

    def _draw_world(self, surface):
        """Zeichnet alle Objekte von hinten nach vorne."""
        drawables = [o for o in self.obstacles if o.alive]
        drawables += [p for p in self.pickups if p.alive]
        # Weit entfernte Objekte zuerst, damit nahe sie ueberdecken
        drawables.sort(key=lambda o: o.z, reverse=True)
        for obj in drawables:
            # Zu weit vorne: noch nicht sichtbar.
            # Hinter der Figur: wuerde perspektivisch riesig werden und das
            # halbe Bild verdecken, obwohl das Objekt bereits passiert ist.
            if obj.z > cfg.SPAWN_DISTANCE or obj.z < DRAW_Z_MIN:
                continue
            obj.draw(surface)
        self.player.draw(surface)

    def _draw_particles(self, surface):
        """Zeichnet die Funken als einzelne Pixelquadrate."""
        for x, y, _, _, life, color in self.particles:
            size = 2 if life > 22 else 1
            if 0 <= x < cfg.VIRTUAL_W and 0 <= y < cfg.VIRTUAL_H:
                surface.fill(color, (int(x), int(y), size, size))

    def _light_mask(self, radius):
        """Erzeugt die Dunkelheitsmaske mit weichem Lichtkegel.

        EIGENLEISTUNG: Die Maske entsteht aus einer vollflaechig schwarzen
        Surface, in die ein radialer Verlauf mit BLEND_RGBA_MIN eingestanzt
        wird. Weil der Radius sich staendig aendert, werden die Masken auf
        Vierer-Schritte gerundet und zwischengespeichert - sonst muesste in
        jedem Frame eine neue Maske berechnet werden.
        """
        key = max(8, int(radius) // 4 * 4)
        cached = self._light_cache.get(key)
        if cached is not None:
            return cached

        hole = pygame.Surface((key * 2, key * 2), pygame.SRCALPHA)
        hole.fill((0, 0, 0, 255))
        # Von aussen nach innen immer durchsichtigere Kreise
        rings = 22
        for i in range(rings):
            t = i / (rings - 1)
            r = int(key * (1.0 - t * 0.98))
            alpha = int(248 * (t ** 1.9))
            pygame.draw.circle(hole, (0, 0, 0, 255 - alpha), (key, key), r)

        self._light_cache[key] = hole
        return hole

    def _draw_darkness(self, surface):
        """Legt die Dunkelheit ueber die Szene (nur im Blackout-Modus)."""
        ratio = self.battery / cfg.BLACKOUT_BATTERY_MAX
        radius = cfg.LIGHT_RADIUS_EMPTY + \
            (cfg.LIGHT_RADIUS_FULL - cfg.LIGHT_RADIUS_EMPTY) * ratio

        # Bei leerem Akku flackert das Restlicht und erlischt dann ganz
        if self.battery <= 0:
            flicker = max(0.0, 1.0 - self.blind_timer / cfg.BLACKOUT_GRACE_FRAMES)
            radius = cfg.LIGHT_RADIUS_EMPTY * flicker * \
                (0.75 + 0.25 * math.sin(self.frames * 0.7))
        elif ratio < 0.3:
            radius *= 0.92 + 0.08 * math.sin(self.frames * 0.35)

        dark = pygame.Surface((cfg.VIRTUAL_W, cfg.VIRTUAL_H), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 249))

        if radius >= 8:
            hole = self._light_mask(radius)
            # Der Lichtkegel folgt dem Sprung nur gedaempft, sonst wuerde er
            # bei jedem Sprung unruhig durchs Bild schiessen.
            px, py, _ = ent.project(0.0, self.player.lane_offset,
                                    self.player.height * 0.45)
            # Die Kegelmitte liegt bewusst ein Stueck VOR der Figur, nicht
            # auf ihr. Dadurch leuchtet mehr Strecke aus, auf die man
            # zulaeuft, statt Boden, den man bereits hinter sich hat.
            dark.blit(hole, (int(px) - hole.get_width() // 2,
                             int(py) - cfg.LIGHT_LOOK_AHEAD
                             - hole.get_height() // 2),
                      special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(dark, (0, 0))

    # -- HUD ---------------------------------------------------------------
    def _draw_hud(self, surface):
        """Zeichnet Punktestand, Strecke, Muenzen, Extras und Akku."""
        pf.draw(surface, "%07d" % self.score, (8, 7), 2, cfg.C_WHITE,
                glow=cfg.C_NEON_CYAN)
        pf.draw(surface, "%d M" % int(self.distance), (8, 24), 1, cfg.C_LIGHT)

        # Muenzzaehler rechts oben. Die Zahl waechst nach LINKS, sonst wuerde
        # sie bei fuenfstelligen Werten aus dem Bild laufen.
        coin_text = "%d" % self.coins
        coin_rect = pf.draw(surface, coin_text, (cfg.VIRTUAL_W - 8, 8), 2,
                            cfg.C_NEON_AMBER, align="right")
        coin_icon = sprites.scaled("coin", 1.0)
        surface.blit(coin_icon, (coin_rect.x - 12, 7))

        # Modusname dezent rechts
        pf.draw(surface, cfg.MODE_LABELS[self.mode],
                (cfg.VIRTUAL_W - 8, 24), 1, cfg.C_GREY, align="right")

        self._draw_effect_bars(surface)
        if self.blackout:
            self._draw_battery(surface)

        pf.draw(surface, "P = PAUSE", (8, cfg.VIRTUAL_H - 11), 1, cfg.C_GREY)

    def _draw_effect_bars(self, surface):
        """Zeigt laufende Extras als schrumpfende Balken."""
        y = 38
        if self.player.shield:
            pf.draw(surface, "SCHILD", (8, y), 1, cfg.C_NEON_LIME)
            y += 11
        for kind, remaining in self.effects.items():
            color = ent.PowerUp.COLORS[kind]
            total = ent.PowerUp.DURATIONS[kind] or 1
            pf.draw(surface, ent.PowerUp.LABELS[kind], (8, y), 1, color)
            bar_w = int(46 * remaining / total)
            surface.fill(cfg.C_BG_NEAR, (8, y + 9, 46, 3))
            surface.fill(color, (8, y + 9, bar_w, 3))
            y += 16

    def _draw_battery(self, surface):
        """Zeichnet die Akkuanzeige des Blackout-Modus."""
        ratio = self.battery / cfg.BLACKOUT_BATTERY_MAX
        rect = pygame.Rect(cfg.VIRTUAL_W // 2 - 44, cfg.VIRTUAL_H - 22, 88, 9)
        draw_panel(surface, rect.inflate(6, 6), fill=cfg.C_DARK,
                   border=cfg.C_GREY, alpha=190, corner=2)

        if ratio > 0.5:
            color = cfg.C_NEON_LIME
        elif ratio > 0.25:
            color = cfg.C_NEON_AMBER
        else:
            color = cfg.C_NEON_PINK

        # Segmentierte Balkenanzeige statt durchgehendem Balken
        segments = 16
        filled = int(segments * ratio + 0.5)
        for i in range(segments):
            sx = rect.x + 3 + i * 5
            seg_color = color if i < filled else cfg.C_BG_NEAR
            if i < filled and ratio <= 0.25 and (self.frames // 12) % 2 == 0:
                seg_color = cfg.C_DARK      # blinkt bei kritischem Stand
            surface.fill(seg_color, (sx, rect.y + 2, 4, rect.h - 4))

        pf.draw(surface, "AKKU", (rect.centerx, rect.y - 12), 1, color,
                align="center")

        if self.battery <= 0:
            left = (cfg.BLACKOUT_GRACE_FRAMES - self.blind_timer) / 60.0
            pf.draw(surface, "BLIND! %.1f S" % max(0.0, left),
                    (cfg.VIRTUAL_W // 2, cfg.VIRTUAL_H - 40), 2,
                    cfg.C_NEON_PINK, align="center", glow=cfg.C_NEON_PINK)

    def _draw_countdown(self, surface):
        """Zeigt den Startcountdown gross in der Bildmitte."""
        shade = pygame.Surface((cfg.VIRTUAL_W, cfg.VIRTUAL_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 100))
        surface.blit(shade, (0, 0))

        seconds_left = self.countdown // 40
        text = ("LOS", "1", "2", "3", "3")[min(4, seconds_left)]
        # Die Zahl schrumpft innerhalb ihrer Sekunde leicht zusammen
        phase = (self.countdown % 40) / 40.0
        scale = 5 + int(phase * 3)
        color = cfg.C_NEON_LIME if text == "LOS" else cfg.C_NEON_CYAN
        pf.draw(surface, text, (cfg.VIRTUAL_W // 2, cfg.VIRTUAL_H // 2 - 20),
                scale, color, align="center", glow=color)

        if self.frames < 200:
            pf.draw(surface, "PFEILE = SPUR   HOCH = SPRUNG   RUNTER = RUTSCHEN",
                    (cfg.VIRTUAL_W // 2, cfg.VIRTUAL_H - 50), 1, cfg.C_LIGHT,
                    align="center")
