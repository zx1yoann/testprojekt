"""
entities.py - Spielfigur, Hindernisse, Muenzen, Power-Ups und die
Perspektiv-Projektion der Spielwelt.

QUELLEN
-------
Keine uebernommenen Codefragmente. Die Projektionsformel, das Lane-System,
die Sprungphysik, die Kollisionspruefung und der faire Hindernis-Generator
sind Eigenleistung.
Inspiration fuer das Spielprinzip (kein Code uebernommen): das Genre der
Endless Runner, bekannt durch Subway Surfers und Temple Run.

SO FUNKTIONIERT DIE WELT
------------------------
Die Spielwelt ist nicht wirklich dreidimensional. Jedes Objekt hat nur zwei
Werte: die Spur (0, 1 oder 2) und die Entfernung z. Bei z = 0 steht die
Spielfigur, grosse z-Werte liegen weit vorne am Horizont. Pro Frame wird z
kleiner, dadurch kommt alles auf die Figur zu. Erst beim Zeichnen wird aus
(spur, z) ein Bildschirmpunkt berechnet.
"""

import math
import random

import pygame

from . import config as cfg
from . import sprites

CENTER_X = cfg.VIRTUAL_W // 2

# Perspektivkonstante: bestimmt, wie schnell Objekte in der Ferne
# zusammenschrumpfen. Groesser = staerkere Tiefenwirkung.
DEPTH_K = 0.105
SPRITE_SCALE_NEAR = 2.0

# Groesster erlaubter Tiefenfaktor. Ohne diese Grenze wuerde der Faktor fuer
# z-Werte nahe -1/DEPTH_K gegen unendlich laufen und die Strasse zerreissen.
MAX_DEPTH = 2.6

# z-Fenster, in dem eine Kollision mit der Figur geprueft wird.
#
# EIGENLEISTUNG / BALANCE: Das Fenster ist bewusst schmal gehalten. Zusammen
# mit der Tiefe eines Hindernisses ergibt sich die Zeitspanne, waehrend der
# die Figur dem Hindernis ausweichen muss. Bei einer Huerde sind das rund
# 1.8 + 1.4 = 3.2 Welteinheiten, also nur etwa fuenf Frames beim Starttempo.
# Waere das Fenster breiter, muesste die Figur ueber den kompletten Sprung
# hinweg oberhalb der Huerde bleiben - und ein sauber getimter Sprung wuerde
# trotzdem am absteigenden Ast scheitern.
HIT_Z_MIN = -0.6
HIT_Z_MAX = 1.2

# Koerpermasse der Figur in Bildschirmpixeln, gemessen vom Boden aus
STANDING_HEAD_HEIGHT = 40.0            # Kopfhoehe im Stehen und im Sprung
SLIDE_HEAD_HEIGHT = 14.0               # Kopfhoehe beim Rutschen


def depth_factor(z):
    """Perspektivfaktor: 1.0 direkt bei der Figur, gegen 0 am Horizont.

    Negative z-Werte liegen hinter der Figur und ergeben Faktoren ueber 1.0.
    Das wird gebraucht, um die Strasse ueber den unteren Bildrand hinaus
    weiterzuzeichnen. Der Faktor wird nach oben begrenzt, damit die Formel
    nicht gegen unendlich laeuft.
    """
    return min(MAX_DEPTH, 1.0 / max(0.05, 1.0 + z * DEPTH_K))


def project(z, lane_offset=0.0, height=0.0):
    """Rechnet Entfernung und Spur in Bildschirmkoordinaten um.

    lane_offset ist -1 (links), 0 (mitte) oder +1 (rechts), darf aber auch
    ein Zwischenwert sein - so entsteht der weiche Spurwechsel.
    height hebt ein Objekt vom Boden ab und wird in Bildschirmpixeln
    angegeben, gemessen ganz vorne bei der Figur. In der Ferne schrumpft der
    Abstand automatisch mit, weil er mit dem Tiefenfaktor multipliziert wird.

    Gibt (x, y, faktor) zurueck.
    """
    d = depth_factor(z)
    y = cfg.HORIZON_Y + (cfg.GROUND_Y - cfg.HORIZON_Y) * d
    road_w = cfg.ROAD_W_FAR + (cfg.ROAD_W_NEAR - cfg.ROAD_W_FAR) * d
    x = CENTER_X + lane_offset * road_w * 0.33
    y -= height * d
    return (x, y, d)


class Player:
    """Die Spielfigur: Spurwechsel, Sprung, Rutschen und Animation."""

    RUNNING = "running"
    JUMPING = "jumping"
    SLIDING = "sliding"
    CRASHED = "crashed"

    def __init__(self):
        self.reset()

    def reset(self):
        """Setzt die Figur auf den Startzustand zurueck."""
        self.lane = 1                  # Mittelspur
        self.visual_lane = 1.0         # weich nachgezogene Position
        self.state = self.RUNNING
        self.height = 0.0              # Hoehe ueber dem Boden
        self.vy = 0.0
        self.slide_timer = 0
        self.anim = 0.0
        self.crash_timer = 0
        self.shield = False
        self.invincible = 0            # Frames Unverwundbarkeit nach Treffer

    # -- Steuerung ---------------------------------------------------------
    def move(self, direction):
        """Wechselt die Spur. Gibt True zurueck, wenn es geklappt hat."""
        if self.state == self.CRASHED:
            return False
        target = self.lane + direction
        if 0 <= target < cfg.LANE_COUNT:
            self.lane = target
            return True
        return False

    def jump(self):
        """Startet einen Sprung, sofern die Figur am Boden ist."""
        if self.state == self.RUNNING:
            self.state = self.JUMPING
            self.vy = cfg.JUMP_POWER
            return True
        return False

    def slide(self):
        """Startet eine Rutschbewegung.

        Ein Sprung wird dabei abgebrochen: die Figur wird nach unten
        gerissen. Das erlaubt das schnelle Reagieren aus der Luft heraus.
        """
        if self.state == self.RUNNING:
            self.state = self.SLIDING
            self.slide_timer = cfg.SLIDE_FRAMES
            return True
        if self.state == self.JUMPING:
            self.vy = -cfg.JUMP_POWER   # Schnellabstieg
            return True
        return False

    def crash(self):
        """Laesst die Figur verungluecken.

        Ein aktiver Schild faengt den Treffer ab und wird dabei verbraucht.
        Gibt True zurueck, wenn der Treffer toedlich war.
        """
        if self.invincible > 0:
            return False
        if self.shield:
            self.shield = False
            self.invincible = 70
            return False
        self.state = self.CRASHED
        self.crash_timer = 0
        return True

    # -- Physik ------------------------------------------------------------
    def update(self, speed):
        """Rechnet einen Frame der Figur weiter."""
        if self.invincible > 0:
            self.invincible -= 1

        if self.state == self.CRASHED:
            self.crash_timer += 1
            self.height = max(0.0, self.height - 0.4)
            return

        # Spurwechsel weich nachziehen statt hart umspringen
        target = float(self.lane)
        diff = target - self.visual_lane
        if abs(diff) < 0.02:
            self.visual_lane = target
        else:
            self.visual_lane += diff / cfg.LANE_SWITCH_FRAMES * 2.2

        if self.state == self.JUMPING:
            self.height += self.vy
            self.vy -= cfg.GRAVITY
            if self.height <= 0.0:
                self.height = 0.0
                self.vy = 0.0
                self.state = self.RUNNING
                return "land"
        elif self.state == self.SLIDING:
            self.slide_timer -= 1
            if self.slide_timer <= 0:
                self.state = self.RUNNING

        # Lauf-Animation laeuft schneller, je hoeher das Tempo
        self.anim = (self.anim + 0.22 * (speed / cfg.BASE_SPEED)) % 4.0
        return None

    # -- Darstellung -------------------------------------------------------
    @property
    def lane_offset(self):
        """Wandelt die visuelle Spur in den Bereich -1 bis +1 um."""
        return self.visual_lane - 1.0

    def current_sprite(self):
        """Waehlt das passende Sprite zum aktuellen Zustand."""
        if self.state == self.CRASHED:
            return ("crash", 0)
        if self.state == self.JUMPING:
            return ("jump", 0)
        if self.state == self.SLIDING:
            return ("slide", 0)
        return ("run", int(self.anim))

    def draw(self, surface):
        """Zeichnet die Figur inklusive Schatten, Schild und Blinken."""
        x, y, d = project(0.0, self.lane_offset, self.height)
        name, frame = self.current_sprite()
        sprite = sprites.scaled(name, SPRITE_SCALE_NEAR * d, frame)

        # Schatten am Boden - er verraet die Spur auch waehrend des Sprungs
        _, ground_y, _ = project(0.0, self.lane_offset, 0.0)
        shadow_w = int(sprite.get_width() * 0.7)
        shadow_h = max(2, int(shadow_w * 0.22))
        shrink = 1.0 - min(0.55, self.height * 0.009)
        shadow = pygame.Surface((max(2, int(shadow_w * shrink)), shadow_h),
                                pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 110))
        surface.blit(shadow, (x - shadow.get_width() // 2,
                              ground_y - shadow_h // 2))

        # Nach einem abgefangenen Treffer blinkt die Figur
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            sprite = sprite.copy()
            sprite.set_alpha(110)

        rect = sprite.get_rect(midbottom=(int(x), int(y)))
        surface.blit(sprite, rect)

        if self.shield:
            radius = int(sprite.get_width() * 0.85)
            ring = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*cfg.C_NEON_LIME, 90), (radius, radius),
                               radius, 2)
            surface.blit(ring, (rect.centerx - radius, rect.centery - radius))

    @property
    def head_height(self):
        """Hoehe des Kopfes ueber dem Boden, in Bildschirmpixeln.

        Beim Rutschen duckt sich die Figur, der Kopf sinkt also deutlich ab.
        Dieser Wert entscheidet, ob ein haengender Balken die Figur trifft.
        """
        if self.state == self.SLIDING:
            return SLIDE_HEAD_HEIGHT
        return self.height + STANDING_HEAD_HEIGHT


class WorldObject:
    """Gemeinsame Basis fuer alles, was auf die Figur zukommt."""

    sprite_name = "coin"
    sprite_scale = 1.0
    depth = 2.0                        # Laenge in z-Richtung
    height = 0.0

    def __init__(self, z, lane):
        self.z = z
        self.lane = lane
        self.alive = True

    @property
    def lane_offset(self):
        return self.lane - 1.0

    def advance(self, speed):
        """Bewegt das Objekt auf die Figur zu."""
        self.z -= speed
        if self.z < cfg.DESPAWN_DISTANCE:
            self.alive = False

    def in_hit_zone(self):
        """Prueft, ob sich das Objekt auf Hoehe der Figur befindet."""
        return (self.z <= HIT_Z_MAX) and (self.z + self.depth >= HIT_Z_MIN)

    def draw(self, surface):
        """Zeichnet das Objekt perspektivisch korrekt skaliert."""
        x, y, d = project(self.z, self.lane_offset, self.height)
        sprite = sprites.scaled(self.sprite_name, self.sprite_scale * d * 2.6)
        surface.blit(sprite, sprite.get_rect(midbottom=(int(x), int(y))))


class Barrier(WorldObject):
    """Niedrige Huerde - muss uebersprungen werden."""

    sprite_name = "barrier"
    sprite_scale = 1.15
    depth = 1.4
    action = "jump"
    clear_height = 20.0                # ab dieser Fusshoehe ist die Figur drueber

    def blocks(self, player):
        """Trifft, wenn die Figur nicht hoch genug in der Luft ist.

        EIGENLEISTUNG / WICHTIGE FAIRNESS-ENTSCHEIDUNG: Entscheidend ist die
        tatsaechliche Sprunghoehe, nicht der blosse Zustand "springt gerade".
        Wuerde nur der Zustand zaehlen, waere jeder Sprung entweder komplett
        sicher oder komplett wirkungslos - und das Zeitfenster fuer einen
        gelungenen Sprung waere nur wenige Frames breit. Mit der Hoehenpruefung
        ist die Figur ueber rund 25 Frames hinweg sicher, was sich beim Spielen
        deutlich gerechter anfuehlt.
        """
        return player.height < self.clear_height


class LowBar(WorldObject):
    """Haengender Balken - es muss darunter durchgerutscht werden."""

    sprite_name = "lowbar"
    sprite_scale = 1.15
    depth = 1.4
    height = cfg.LOWBAR_HEIGHT
    action = "slide"

    def blocks(self, player):
        """Trifft, wenn der Kopf der Figur zu hoch ist.

        Springen hilft hier nicht, im Gegenteil: es hebt den Kopf erst recht
        in den Balken hinein. Nur das Rutschen senkt ihn weit genug ab.
        """
        return player.head_height >= self.height


class Train(WorldObject):
    """Langer Waggon - blockiert die Spur vollstaendig."""

    sprite_name = "train"
    sprite_scale = 1.55
    depth = 9.0
    action = "dodge"

    def blocks(self, player):
        """Weder Springen noch Rutschen hilft - nur die Spur wechseln."""
        return True


class Coin(WorldObject):
    """Einsammelbare Muenze.

    Im Endless-Modus sind Muenzen Punkte, im Blackout-Modus sind sie
    Akkuladung und damit ueberlebenswichtig.
    """

    sprite_name = "coin"
    sprite_scale = 0.9
    depth = 2.4                        # grosszuegiger als Hindernisse
    action = "collect"

    def __init__(self, z, lane, height=cfg.COIN_HEIGHT):
        super().__init__(z, lane)
        self.height = height
        self.base_lane = float(lane)
        self.spin = random.random() * math.pi * 2

    def advance(self, speed):
        super().advance(speed)
        self.spin += 0.2

    def attract(self, player_lane):
        """Zieht die Muenze bei aktivem Magneten zur Figur.

        EIGENLEISTUNG: Der Magnet wirkt nicht schlagartig, sondern zieht die
        Muenze ueber mehrere Frames auf die Spur der Figur. Das sieht besser
        aus und bleibt nachvollziehbar.
        """
        target = float(player_lane)
        self.lane += (target - self.lane) * 0.22

    def draw(self, surface):
        """Zeichnet die Muenze mit einer Drehung als Breitenschwankung."""
        x, y, d = project(self.z, self.lane_offset, self.height)
        squeeze = abs(math.cos(self.spin)) * 0.75 + 0.25
        base = sprites.get("coin")
        w = max(1, int(base.get_width() * self.sprite_scale * d * 2.6 * squeeze))
        h = max(1, int(base.get_height() * self.sprite_scale * d * 2.6))
        sprite = pygame.transform.scale(base, (w, h))
        surface.blit(sprite, sprite.get_rect(midbottom=(int(x), int(y))))


class PowerUp(WorldObject):
    """Ein einsammelbares Extra: Magnet, Schild oder doppelte Muenzen."""

    KINDS = ("magnet", "shield", "double")
    LABELS = {
        "magnet": "MAGNET",
        "shield": "SCHILD",
        "double": "DOPPELTE MUENZEN",
    }
    COLORS = {
        "magnet": cfg.C_NEON_PINK,
        "shield": cfg.C_NEON_LIME,
        "double": cfg.C_NEON_AMBER,
    }
    DURATIONS = {"magnet": 480, "shield": 0, "double": 480}

    sprite_scale = 1.1
    depth = 2.6                        # grosszuegiger als Hindernisse
    action = "collect"

    def __init__(self, z, lane, kind):
        super().__init__(z, lane)
        self.kind = kind
        self.sprite_name = kind
        self.height = cfg.PICKUP_HEIGHT
        self.bob = random.random() * math.pi * 2

    def advance(self, speed):
        super().advance(speed)
        self.bob += 0.11

    def draw(self, surface):
        """Zeichnet das Extra mit leichter Schwebebewegung und Leuchtring."""
        bob_height = self.height + math.sin(self.bob) * 3.2
        x, y, d = project(self.z, self.lane_offset, bob_height)
        sprite = sprites.scaled(self.sprite_name, self.sprite_scale * d * 2.6)
        rect = sprite.get_rect(midbottom=(int(x), int(y)))

        radius = int(sprite.get_width() * 0.95)
        if radius > 2:
            ring = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*self.COLORS[self.kind], 70),
                               (radius, radius), radius, 1)
            surface.blit(ring, (rect.centerx - radius, rect.centery - radius))
        surface.blit(sprite, rect)


# --------------------------------------------------------------------------
# EIGENLEISTUNG: Fairer Hindernis-Generator.
#
# Zufall allein erzeugt regelmaessig Situationen, die gar nicht zu schaffen
# sind - etwa drei Zuege nebeneinander. Deshalb arbeitet der Generator mit
# festen Mustern. Jedes Muster laesst per Konstruktion mindestens eine Spur
# frei, und nach einem Muster folgt immer eine Verschnaufpause.
# --------------------------------------------------------------------------
# Kleinster erlaubter Abstand zwischen zwei Mustern, siehe _gap()
MIN_GAP = 42.0

PATTERNS = [
    # (Beschreibung, [(spur_relativ, typ), ...])
    ("single_jump",  [(0, "barrier")]),
    ("single_slide", [(0, "lowbar")]),
    ("single_train", [(0, "train")]),
    ("double_side",  [(-1, "barrier"), (1, "barrier")]),
    ("train_wall",   [(-1, "train"), (1, "train")]),
    ("mixed",        [(-1, "lowbar"), (1, "barrier")]),
    ("slide_pair",   [(-1, "lowbar"), (0, "lowbar")]),
    ("jump_pair",    [(0, "barrier"), (1, "barrier")]),
]

# Bis zu welcher Distanz welche Muster erlaubt sind - der Schwierigkeitsgrad
# steigt also nicht nur ueber das Tempo, sondern auch ueber die Auswahl.
UNLOCK_AT = {
    "single_jump": 0, "single_slide": 0, "single_train": 120,
    "double_side": 260, "mixed": 420, "jump_pair": 560,
    "slide_pair": 700, "train_wall": 900,
}


class LevelGenerator:
    """Erzeugt fortlaufend neue Hindernisse, Muenzen und Extras."""

    def __init__(self, seed=None, blackout=False):
        self.rng = random.Random(seed)
        self.blackout = blackout
        self.next_spawn_z = 40.0       # erste Hindernisse nicht sofort
        self.last_free_lane = 1
        self.since_powerup = 0

    def _gap(self, distance):
        """Abstand bis zum naechsten Muster - wird mit der Zeit kleiner.

        EIGENLEISTUNG / WICHTIGE BALANCE-REGEL: Der Abstand darf nie unter
        MIN_GAP fallen. Ein Sprung dauert rund 32 Frames. Beim Hoechsttempo
        von 1.35 Welteinheiten pro Frame legt ein Hindernis in dieser Zeit
        gut 43 Einheiten zurueck. Waere der Abstand kleiner, koennte die
        Figur nach der Landung gar nicht mehr rechtzeitig erneut abspringen -
        das Spiel waere dann nicht mehr fair, sondern schlicht unschaffbar.
        """
        base = 52.0 - min(14.0, distance / 220.0)
        return max(MIN_GAP, base + self.rng.uniform(-3.0, 6.0))

    def _available_patterns(self, distance):
        """Filtert die Muster nach bereits erreichter Distanz."""
        return [p for p in PATTERNS if distance >= UNLOCK_AT.get(p[0], 0)]

    def spawn(self, distance, out_obstacles, out_pickups):
        """Erzeugt bei Bedarf das naechste Muster.

        distance ist die zurueckgelegte Strecke und steuert damit die
        Schwierigkeit. Neue Objekte werden an die uebergebenen Listen
        angehaengt.
        """
        self.next_spawn_z -= 1.0
        if self.next_spawn_z > 0:
            return

        z = cfg.SPAWN_DISTANCE
        name, slots = self.rng.choice(self._available_patterns(distance))

        # Muster auf eine zufaellige Grundspur legen
        if any(s[0] != 0 for s in slots):
            base_lane = 1              # zweispurige Muster brauchen die Mitte
        else:
            base_lane = self.rng.randrange(cfg.LANE_COUNT)

        used = set()
        for rel, kind in slots:
            lane = base_lane + rel
            if not (0 <= lane < cfg.LANE_COUNT):
                continue
            used.add(lane)
            if kind == "barrier":
                out_obstacles.append(Barrier(z, lane))
            elif kind == "lowbar":
                out_obstacles.append(LowBar(z, lane))
            else:
                out_obstacles.append(Train(z, lane))

        free = [l for l in range(cfg.LANE_COUNT) if l not in used]
        # Sicherheitsnetz: es bleibt garantiert eine Spur passierbar
        if not free:
            fallback = self.rng.randrange(cfg.LANE_COUNT)
            out_obstacles[:] = [o for o in out_obstacles
                                if not (o.z == z and o.lane == fallback)]
            free = [fallback]

        self.last_free_lane = self.rng.choice(free)
        self._spawn_pickups(z, free, out_pickups)
        self.next_spawn_z = self._gap(distance)

    def _spawn_pickups(self, z, free_lanes, out_pickups):
        """Legt Muenzenreihen und gelegentlich ein Extra auf freie Spuren.

        EIGENLEISTUNG: Im Blackout-Modus haengt das Ueberleben an den
        Muenzen. Deshalb wird dort auf JEDER freien Spur eine Reihe gelegt -
        die Figur muss also nicht mehr raten, auf welcher Spur der Nachschub
        liegt, sondern nur noch eine erreichbare freie Spur waehlen. Im
        Endless-Modus bleibt es bei einer einzigen Reihe, weil das Einsammeln
        dort freiwillig ist und eine Entscheidung bleiben soll.
        """
        target_lanes = free_lanes if self.blackout else \
            [self.rng.choice(free_lanes)]

        chance = 0.96 if self.blackout else 0.72
        for lane in target_lanes:
            if self.rng.random() >= chance:
                continue
            count = self.rng.randint(4, 7) if self.blackout else \
                self.rng.randint(3, 6)
            for i in range(count):
                out_pickups.append(Coin(z + 6 + i * 3.4, lane))

        self.since_powerup += 1
        # Extras erscheinen weder zu haeufig noch voellig unvorhersehbar
        if self.since_powerup >= 5 and self.rng.random() < 0.35:
            self.since_powerup = 0
            kind = self.rng.choice(PowerUp.KINDS)
            pu_lane = self.rng.choice(free_lanes)
            out_pickups.append(PowerUp(z + 14, pu_lane, kind))
