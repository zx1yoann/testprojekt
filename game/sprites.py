"""
sprites.py - Saemtliche Grafiken des Spiels, direkt im Code gezeichnet.

QUELLEN
-------
Keine uebernommenen Codefragmente und keine heruntergeladenen Bilddateien.
Alle Pixelraster, die Palette und der Aufbau der Skyline sind Eigenleistung.
Verwendete PyGame-Bausteine: pygame.Surface, Surface.fill, SRCALPHA
(https://www.pygame.org/docs/ref/surface.html)

WARUM PROZEDURALE SPRITES?
--------------------------
Das Projekt kommt ohne einen einzigen externen Bild-Download aus. Jedes
Sprite ist ein Textraster im Quellcode, das beim Programmstart einmalig in
eine Surface uebersetzt wird. Vorteil: nichts kann fehlen oder kaputt
gehen, und jede Farbe laesst sich an einer einzigen Stelle aendern.
"""

import math
import random

import pygame

from . import config as cfg

# --------------------------------------------------------------------------
# Farbschluessel fuer die Pixelraster weiter unten.
# --------------------------------------------------------------------------
PALETTE = {
    ".": None,                        # transparent
    "H": (38, 28, 62),                # Haare / dunkle Kontur
    "S": (255, 206, 168),             # Haut
    "J": cfg.C_NEON_CYAN,             # Jacke hell
    "D": (24, 148, 184),              # Jacke Schatten
    "P": (128, 78, 214),              # Hose
    "B": cfg.C_NEON_PINK,             # Schuhe
    "W": cfg.C_WHITE,
    "Y": cfg.C_NEON_AMBER,
    "O": (214, 128, 24),              # Muenze Schatten
    "R": (232, 46, 70),               # Warnrot
    "G": cfg.C_NEON_LIME,
    "V": cfg.C_NEON_VIOLET,
    "K": cfg.C_BLACK,
    "M": (96, 102, 128),              # Metall
    "N": (56, 60, 82),                # Metall Schatten
    "C": (176, 186, 214),             # Metall Glanz
}


def from_pattern(rows, palette=None):
    """Uebersetzt ein Textraster in eine transparente Surface.

    Jedes Zeichen einer Zeile wird zu genau einem Pixel. Ein Punkt bleibt
    transparent, jedes andere Zeichen wird in der Palette nachgeschlagen.
    """
    palette = palette or PALETTE
    height = len(rows)
    width = max(len(r) for r in rows) if rows else 0
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color is not None:
                surf.set_at((x, y), color)
    return surf


# --------------------------------------------------------------------------
# EIGENLEISTUNG: Die Spielfigur in vier Zustaenden, gezeichnet aus der
# Verfolgerperspektive (Blick auf den Ruecken), wie im Vorbild ueblich.
# --------------------------------------------------------------------------
_RUN_A = [
    "....HHHH....",
    "...HHHHHH...",
    "...HHHHHH...",
    "...HSSSSH...",
    "..DJJJJJJD..",
    ".JJJJJJJJJJ.",
    ".JJJJWWJJJJ.",
    "SJJJJWWJJJJS",
    "SDJJJJJJJJDS",
    "..JJJJJJJJ..",
    "..DJJJJJJD..",
    "...PPPPPP...",
    "...PPPPPP...",
    "...PP..PP...",
    "...PP..PP...",
    "...PP..PP...",
    "..BBB..BBB..",
    "..BBB..BBB..",
]

_RUN_B = [
    "....HHHH....",
    "...HHHHHH...",
    "...HHHHHH...",
    "...HSSSSH...",
    "..DJJJJJJD..",
    ".JJJJJJJJJJ.",
    "SJJJJWWJJJJ.",
    "SJJJJWWJJJJS",
    ".DJJJJJJJJDS",
    "..JJJJJJJJ..",
    "..DJJJJJJD..",
    "...PPPPPP...",
    "...PPPPPP...",
    "..PPP...PP..",
    "..PP....PP..",
    "..PP....PPP.",
    ".BBB.....BBB",
    ".BBB.....BBB",
]

_RUN_C = [
    "....HHHH....",
    "...HHHHHH...",
    "...HHHHHH...",
    "...HSSSSH...",
    "..DJJJJJJD..",
    ".JJJJJJJJJJ.",
    ".JJJJWWJJJJS",
    "SJJJJWWJJJJS",
    "SDJJJJJJJJD.",
    "..JJJJJJJJ..",
    "..DJJJJJJD..",
    "...PPPPPP...",
    "...PPPPPP...",
    "..PP...PPP..",
    "..PP....PP..",
    ".PPP....PP..",
    "BBB.....BBB.",
    "BBB.....BBB.",
]

_JUMP = [
    "..S.HHHH.S..",
    "..SHHHHHHS..",
    "..SHHHHHHS..",
    "..SHSSSSHS..",
    "..DJJJJJJD..",
    "..JJJJJJJJ..",
    "..JJJWWJJJ..",
    "..JJJWWJJJ..",
    "..DJJJJJJD..",
    "...PPPPPP...",
    "...PPPPPP...",
    "..PPP..PPP..",
    "..PP....PP..",
    "..PP....PP..",
    "..BBB..BBB..",
    "..BBB..BBB..",
    "............",
    "............",
]

_SLIDE = [
    "............",
    "............",
    "............",
    "............",
    "............",
    "............",
    "............",
    "....HHHH....",
    "..HHHHHHSS..",
    "SDJJJJJJJJS.",
    "SJJJWWJJJJ..",
    ".JJJJJJJPPP.",
    "..PPPPPPPPP.",
    "..PPPPPPPP..",
    ".BBB...BBB..",
    ".BBB...BBB..",
    "............",
    "............",
]

_CRASH = [
    "..W......W..",
    "...W....W...",
    "....HHHH....",
    "...HSSSSH...",
    "..HHHHHHHH..",
    "SD.JJJJJJ.DS",
    ".JJJJRRJJJJ.",
    "..JJJRRJJJ..",
    "..DJJJJJJD..",
    "...PPPPPP...",
    "..PPP..PPP..",
    ".PP......PP.",
    ".BB......BB.",
    ".BBB....BBB.",
    "............",
    "..W......W..",
    "............",
    "............",
]

# --------------------------------------------------------------------------
# Hindernisse. Jedes Hindernis erzwingt genau eine richtige Reaktion.
# --------------------------------------------------------------------------
_BARRIER = [                          # ueberspringen
    "RRRRWWWWRRRRWWWW",
    "RRRRWWWWRRRRWWWW",
    "WWWWRRRRWWWWRRRR",
    "WWWWRRRRWWWWRRRR",
    "MMMMMMMMMMMMMMMM",
    "NNNNNNNNNNNNNNNN",
    "..M..........M..",
    "..M..........M..",
    "..M..........M..",
    "..N..........N..",
]

_LOW_BAR = [                          # darunter durchrutschen
    "..M..........M..",
    "..M..........M..",
    "MMMMMMMMMMMMMMMM",
    "YYYYKKKKYYYYKKKK",
    "YYYYKKKKYYYYKKKK",
    "MMMMMMMMMMMMMMMM",
    "..N..........N..",
    "..N..........N..",
    "..N..........N..",
    "..N..........N..",
]

_TRAIN = [                            # nur ausweichen
    ".MMMMMMMMMMMMMM.",
    "MCCCCCCCCCCCCCCM",
    "MCVVVVVVVVVVVVCM",
    "MCVWWWVVVVWWWVCM",
    "MCVWWWVVVVWWWVCM",
    "MCVWWWVVVVWWWVCM",
    "MCVVVVVVVVVVVVCM",
    "MCVVVVVVVVVVVVCM",
    "MCNNNNNNNNNNNNCM",
    "MCVVVVVVVVVVVVCM",
    "MCVVVYYYYYYVVVCM",
    "MCVVVYYYYYYVVVCM",
    "MCVVVVVVVVVVVVCM",
    "MCCCCCCCCCCCCCCM",
    "MMMMMMMMMMMMMMMM",
    ".NN.NNNNNNNN.NN.",
]

_COIN = [
    "..YYYY..",
    ".YYOOYY.",
    "YYOWWOYY",
    "YOWWWWOY",
    "YOWWWWOY",
    "YYOWWOYY",
    ".YYOOYY.",
    "..YYYY..",
]

_PU_MAGNET = [
    "..RRRR..",
    ".RRRRRR.",
    "RR....RR",
    "RR....RR",
    "RR....RR",
    "WW....WW",
    "WW....WW",
    "........",
]

_PU_SHIELD = [
    "..GGGG..",
    ".GGGGGG.",
    "GGWWWWGG",
    "GGWGGWGG",
    "GGWGGWGG",
    ".GGWWGG.",
    "..GGGG..",
    "...GG...",
]

_PU_DOUBLE = [
    "YY....YY",
    "YYY..YYY",
    ".YYYYYY.",
    "..YYYY..",
    "..YYYY..",
    ".YYYYYY.",
    "YYY..YYY",
    "YY....YY",
]

# Zur Laufzeit gefuellter Speicher, damit jede Surface nur einmal entsteht.
_store = {}


def build():
    """Erzeugt alle Surfaces einmalig. Muss nach pygame.init() laufen."""
    if _store:
        return _store
    _store.update({
        "run": [from_pattern(_RUN_A), from_pattern(_RUN_B),
                from_pattern(_RUN_A), from_pattern(_RUN_C)],
        "jump": from_pattern(_JUMP),
        "slide": from_pattern(_SLIDE),
        "crash": from_pattern(_CRASH),
        "barrier": from_pattern(_BARRIER),
        "lowbar": from_pattern(_LOW_BAR),
        "train": from_pattern(_TRAIN),
        "coin": from_pattern(_COIN),
        "magnet": from_pattern(_PU_MAGNET),
        "shield": from_pattern(_PU_SHIELD),
        "double": from_pattern(_PU_DOUBLE),
    })
    return _store


def get(name):
    """Liefert ein Sprite und baut den Speicher bei Bedarf auf."""
    if not _store:
        build()
    return _store[name]


def scaled(name, factor, frame=0):
    """Skaliert ein Sprite ganzzahlig-weich fuer die Pseudo-3D-Tiefe.

    Es wird bewusst pygame.transform.scale (Nearest Neighbor) verwendet,
    damit die Pixelkanten hart bleiben und der Retro-Look erhalten bleibt.
    """
    sprite = get(name)
    if isinstance(sprite, list):
        sprite = sprite[frame % len(sprite)]
    w = max(1, int(sprite.get_width() * factor))
    h = max(1, int(sprite.get_height() * factor))
    return pygame.transform.scale(sprite, (w, h))


# --------------------------------------------------------------------------
# EIGENLEISTUNG: Der Hintergrund wird einmal als Parallax-Streifen erzeugt.
# Die Skyline entsteht aus zufaelligen, aber mit festem Seed reproduzierbaren
# Hochhaeusern - so sieht jeder Durchlauf identisch aus, ohne dass ein Bild
# mitgeliefert werden muss.
# --------------------------------------------------------------------------
def build_skyline(width, height, seed, near=False):
    """Zeichnet eine Hochhaus-Silhouette mit beleuchteten Fenstern."""
    rng = random.Random(seed)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    body = cfg.C_BG_NEAR if near else cfg.C_BG_MID
    window_colors = [cfg.C_NEON_AMBER, cfg.C_NEON_CYAN, cfg.C_NEON_PINK]

    x = 0
    while x < width:
        bw = rng.randint(14, 34)
        bh = rng.randint(int(height * 0.3), int(height * 0.95))
        top = height - bh
        surf.fill(body, (x, top, bw, bh))

        # Antenne auf jedem dritten Hochhaus
        if rng.random() < 0.3:
            surf.fill(body, (x + bw // 2, max(0, top - 8), 1, 8))
            surf.fill(cfg.C_NEON_PINK, (x + bw // 2, max(0, top - 9), 1, 2))

        # Fensterraster
        for wy in range(top + 3, height - 2, 5):
            for wx in range(x + 2, x + bw - 2, 4):
                if rng.random() < 0.34:
                    surf.fill(rng.choice(window_colors), (wx, wy, 2, 2))
        x += bw + rng.randint(1, 4)
    return surf


def build_gradient(width, height, top_color, bottom_color):
    """Erzeugt einen vertikalen Farbverlauf als Himmel."""
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        surf.fill(
            (
                int(top_color[0] + (bottom_color[0] - top_color[0]) * t),
                int(top_color[1] + (bottom_color[1] - top_color[1]) * t),
                int(top_color[2] + (bottom_color[2] - top_color[2]) * t),
            ),
            (0, y, width, 1),
        )
    return surf


def build_stars(width, height, seed, count=70):
    """Streut Sterne mit unterschiedlicher Helligkeit in den Nachthimmel."""
    rng = random.Random(seed)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for _ in range(count):
        x = rng.randrange(width)
        y = rng.randrange(height)
        brightness = rng.randint(90, 230)
        surf.set_at((x, y), (brightness, brightness, min(255, brightness + 25)))
    return surf


def build_vignette(width, height, strength=150):
    """Dunkelt die Bildraender ab und lenkt den Blick zur Bildmitte."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    cx, cy = width / 2, height / 2
    max_dist = math.hypot(cx, cy)
    step = 4                           # grobes Raster, das reicht optisch
    for y in range(0, height, step):
        for x in range(0, width, step):
            dist = math.hypot(x - cx, y - cy) / max_dist
            alpha = int(max(0, (dist - 0.45)) * strength * 2.2)
            if alpha > 0:
                surf.fill((0, 0, 0, min(255, alpha)), (x, y, step, step))
    return surf
