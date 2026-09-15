"""
config.py - Zentrale Konstanten, Farbpalette und Einstellungs-Persistenz.

QUELLEN
-------
Keine uebernommenen Codefragmente. Saemtliche Werte, die Farbpalette
("Tokio Neon Night") und die Settings-Persistenz sind Eigenleistung.
Allgemeine PyGame-Grundlagen: https://www.pygame.org/docs/
"""

import json
import os

# --------------------------------------------------------------------------
# EIGENLEISTUNG: Virtuelle Aufloesung
# Das gesamte Spiel wird auf eine kleine 480x270-Surface gezeichnet und erst
# zum Schluss hochskaliert. Dadurch entstehen echte, harte Pixelkanten
# (Nearest-Neighbor-Skalierung) und der Fullscreen-Modus funktioniert auf
# jedem Monitor, ohne dass ein einziger Layout-Wert angepasst werden muss.
# --------------------------------------------------------------------------
VIRTUAL_W = 480
VIRTUAL_H = 270
WINDOW_SCALE = 3                      # Startfenster = 1440x810
WINDOW_W = VIRTUAL_W * WINDOW_SCALE
WINDOW_H = VIRTUAL_H * WINDOW_SCALE

FPS = 60
TITLE = "NEON RUSH"

# --------------------------------------------------------------------------
# Farbpalette "Tokio Neon Night" (Eigenleistung)
# Bewusst kontraststark gewaehlt: Hindernisse muessen auch bei hohem Tempo
# in Sekundenbruchteilen vom Hintergrund unterscheidbar sein.
# --------------------------------------------------------------------------
C_BG_DEEP     = (13, 10, 30)          # Nachthimmel ganz hinten
C_BG_MID      = (26, 20, 54)          # Skyline-Silhouette
C_BG_NEAR     = (40, 30, 74)          # Tunnelwand
C_TRACK       = (30, 24, 58)          # Gleisbett
C_TRACK_LINE  = (72, 58, 122)         # Lane-Trennlinien
C_RAIL        = (94, 80, 150)         # Schienen

C_NEON_PINK   = (255, 45, 149)        # Primaerakzent / Gefahr
C_NEON_CYAN   = (52, 235, 255)        # Sekundaerakzent / Spieler
C_NEON_LIME   = (170, 255, 70)        # Erfolg / Akku voll
C_NEON_AMBER  = (255, 186, 48)        # Muenzen / Warnung
C_NEON_VIOLET = (168, 92, 255)        # Power-Ups

C_WHITE       = (245, 245, 255)
C_LIGHT       = (198, 196, 224)
C_GREY        = (118, 112, 156)
C_DARK        = (22, 18, 42)
C_BLACK       = (6, 4, 16)

# --------------------------------------------------------------------------
# Spielfeld: drei Spuren in Pseudo-3D-Perspektive.
#
# EIGENLEISTUNG: Die Werte sind aufeinander abgestimmt. GROUND_Y liegt
# bewusst deutlich ueber dem unteren Bildrand, damit die Strasse hinter der
# Figur weiterlaeuft und aus dem Bild herausfaehrt. Endete sie exakt auf
# Hoehe der Figur, saehe es aus, als schwebe die Bahn in der Luft.
# --------------------------------------------------------------------------
LANE_COUNT = 3
HORIZON_Y = 92                        # Fluchtpunkt-Hoehe
GROUND_Y = 214                        # Bodenlinie, auf der die Figur steht
ROAD_W_FAR = 46                       # Strassenbreite am Horizont
ROAD_W_NEAR = 330                     # Strassenbreite auf Hoehe der Figur
ROAD_BEHIND_Z = -7.0                  # so weit wird hinter die Figur gezeichnet

# Spielbalance
BASE_SPEED = 0.55                     # Start-Tempo (Welt-Einheiten pro Frame)
MAX_SPEED = 1.35
SPEED_RAMP = 0.000045                 # Tempozuwachs pro Frame

# Sprungwerte in Bildschirmpixeln. Aus ihnen ergeben sich rechnerisch:
#   Scheitelhoehe = JUMP_POWER^2 / (2 * GRAVITY)   = rund 50 Pixel
#   Flugdauer     = 2 * JUMP_POWER / GRAVITY       = rund 32 Frames (0.53 s)
# Die Werte sind so gewaehlt, dass der Sprung knackig bleibt und die Figur
# gerade hoch genug kommt, um eine Huerde sauber zu ueberqueren.
JUMP_POWER = 6.25
GRAVITY = 0.39
SLIDE_FRAMES = 32
LANE_SWITCH_FRAMES = 7

# Hoehenangaben der Spielobjekte, ebenfalls in Bildschirmpixeln
LOWBAR_HEIGHT = 26.0                  # Unterkante des haengenden Balkens
COIN_HEIGHT = 14.0                    # Schwebehoehe der Muenzen
PICKUP_HEIGHT = 16.0                  # Schwebehoehe der Extras
PICKUP_REACH = 24.0                   # Greifweite nach oben und unten

SPAWN_DISTANCE = 78.0                 # Wie weit vorne Objekte erscheinen
DESPAWN_DISTANCE = -9.0

# Blackout-Modus (Eigenleistung, siehe scenes/play.py)
BLACKOUT_BATTERY_MAX = 100.0
# Akkuverlust pro Frame. Bei 0.13 reicht eine volle Ladung rund 13 Sekunden.
# Das ist der zentrale Schwierigkeitsregler des Blackout-Modus: er muss lang
# genug sein, um zwei verpasste Muenzreihen zu verzeihen, aber kurz genug,
# dass Einsammeln Pflicht bleibt und nicht nur nettes Beiwerk ist.
BLACKOUT_DRAIN = 0.13
BLACKOUT_COIN_GAIN = 13.0             # Akku pro eingesammelter Muenze
BLACKOUT_GRACE_FRAMES = 180           # 3 Sekunden Blindheit bis zum Aus

# Reichweite des Lichtkegels bei vollem und bei leerem Akku, in Pixeln.
# EIGENLEISTUNG / BALANCE: Der Radius bestimmt direkt, wie viel Vorwarnzeit
# bleibt. Bei 150 Pixeln sieht die Figur rund eine Sekunde weit voraus - das
# reicht, um auf einen Zug zu reagieren, laesst den Modus aber deutlich
# hektischer bleiben als den Endless Run.
LIGHT_RADIUS_FULL = 150
LIGHT_RADIUS_EMPTY = 30
LIGHT_LOOK_AHEAD = 32                 # Kegelmitte so weit vor die Figur legen

MODE_ENDLESS = "endless"
MODE_BLACKOUT = "blackout"

MODE_LABELS = {
    MODE_ENDLESS: "ENDLESS RUN",
    MODE_BLACKOUT: "BLACKOUT",
}

# Dateien liegen neben dem Projekt, nicht im Paket
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(_ROOT, "settings.json")
HIGHSCORE_FILE = os.path.join(_ROOT, "highscores.json")

DEFAULT_SETTINGS = {
    "music_volume": 0.6,
    "sfx_volume": 0.8,
    "muted": False,
    "fullscreen": False,
}


def load_settings():
    """Laedt die Einstellungen aus settings.json.

    Faellt bei fehlender oder beschaedigter Datei auf die Standardwerte
    zurueck, damit das Spiel nie wegen einer kaputten Konfiguration abstuerzt.
    """
    data = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
            stored = json.load(fh)
        for key in DEFAULT_SETTINGS:
            if key in stored:
                data[key] = stored[key]
    except (OSError, ValueError):
        pass
    return data


def save_settings(data):
    """Schreibt die Einstellungen zurueck auf die Festplatte."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except OSError:
        pass  # Speichern ist Komfort, kein Grund das Spiel zu beenden
