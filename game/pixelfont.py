"""
pixelfont.py - Eine komplett selbst definierte Bitmap-Pixelschrift.

QUELLEN
-------
Keine. Jede einzelne Glyphe, die Render-Pipeline, das Caching und der
Neon-Glow-Effekt sind vollstaendig Eigenleistung.

WARUM EINE EIGENE SCHRIFT?
--------------------------
Die Wegleitung verlangt unter Kriterium 7 ausdruecklich "eine eigene
Schrift". Statt eine fertige TTF-Datei herunterzuladen, ist hier jeder
Buchstabe als 5x7-Pixelraster von Hand gezeichnet. Die Schrift ist damit
Teil des Quellcodes, benoetigt keine externe Datei und skaliert
verlustfrei auf jede Pixelgroesse, weil sie beim Rendern schlicht als
Rechtecke gezeichnet wird.

AUFBAU
------
Jede Glyphe besteht aus 7 Zeilen zu 5 Zeichen. '#' bedeutet Pixel
gesetzt, '.' bedeutet transparent.
"""

import pygame

GLYPH_W = 5
GLYPH_H = 7

# --------------------------------------------------------------------------
# EIGENLEISTUNG: Das komplette Alphabet als Pixelraster.
# --------------------------------------------------------------------------
GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],

    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],

    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    ";": [".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
    '"': [".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "[": ["..###", "..#..", "..#..", "..#..", "..#..", "..#..", "..###"],
    "]": ["###..", "..#..", "..#..", "..#..", "..#..", "..#..", "###.."],
    "<": ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."],
    ">": [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."],
    "*": [".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."],
    "%": ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    "#": [".#.#.", "#####", ".#.#.", ".#.#.", ".#.#.", "#####", ".#.#."],
    "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "@": [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
    "x": [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
}

# Unbekannte Zeichen werden als leeres Kaestchen dargestellt, damit ein
# Tippfehler sofort sichtbar wird statt das Layout zu zerschiessen.
FALLBACK = ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#####"]

# Deutsche Sonderzeichen werden auf ihre Ersatzschreibweise abgebildet,
# statt fuer jeden Umlaut eine eigene Glyphe zu pflegen.
TRANSLITERATE = {
    "Ä": "AE", "Ö": "OE", "Ü": "UE",
    "ä": "AE", "ö": "OE", "ü": "UE",
    "ß": "SS",
}

# Render-Cache: identische Texte werden nur einmal gezeichnet. Ohne diesen
# Cache waere das HUD in jedem Frame ein Haufen unnoetiger Rect-Aufrufe.
_cache = {}


def _normalise(text):
    """Wandelt einen beliebigen String in darstellbare Grossbuchstaben um."""
    out = []
    for ch in str(text):
        if ch in TRANSLITERATE:
            out.append(TRANSLITERATE[ch])
        else:
            out.append(ch)
    return "".join(out).upper()


def text_size(text, scale=1, spacing=1):
    """Berechnet die Pixelmasse eines Textes, ohne ihn zu rendern."""
    norm = _normalise(text)
    if not norm:
        return (0, GLYPH_H * scale)
    width = len(norm) * (GLYPH_W + spacing) * scale - spacing * scale
    return (width, GLYPH_H * scale)


def render(text, scale=1, color=(255, 255, 255), spacing=1):
    """Rendert Text als Surface mit transparentem Hintergrund.

    scale   - Kantenlaenge eines Schriftpixels in echten Pixeln
    spacing - Luecke zwischen zwei Glyphen in Schriftpixeln
    """
    key = (str(text), scale, color, spacing)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    norm = _normalise(text)
    w, h = text_size(text, scale, spacing)
    surf = pygame.Surface((max(w, 1), max(h, 1)), pygame.SRCALPHA)

    cursor = 0
    for ch in norm:
        rows = GLYPHS.get(ch, FALLBACK)
        for row_index, row in enumerate(rows):
            for col_index, pixel in enumerate(row):
                if pixel == "#":
                    surf.fill(
                        color,
                        (cursor + col_index * scale, row_index * scale, scale, scale),
                    )
        cursor += (GLYPH_W + spacing) * scale

    _cache[key] = surf
    return surf


def draw(target, text, pos, scale=1, color=(255, 255, 255),
         align="left", spacing=1, shadow=None, glow=None):
    """Zeichnet Text direkt auf eine Ziel-Surface.

    align  - "left", "center" oder "right", bezogen auf pos[0]
    shadow - Farbe eines um 1 Schriftpixel versetzten Schlagschattens
    glow   - Farbe eines weichen Neon-Scheins rund um die Schrift

    Gibt das belegte Rechteck zurueck, damit Aufrufer weiterlayouten koennen.
    """
    surf = render(text, scale, color, spacing)
    x, y = pos
    if align == "center":
        x -= surf.get_width() // 2
    elif align == "right":
        x -= surf.get_width()

    # EIGENLEISTUNG: Neon-Glow. Die Schrift wird mehrfach in der Glow-Farbe
    # mit fallender Deckkraft versetzt gezeichnet. Das erzeugt den weichen
    # Leuchtrand, ohne dass ein Blur-Filter noetig waere.
    if glow is not None:
        # Der Versatz waechst bewusst nur halb so schnell wie die Schriftgroesse.
        # Wuerde er voll mitskalieren, wuerde eine grosse Ueberschrift in einer
        # breiten Wolke verschwimmen statt sauber zu leuchten.
        step = max(1, scale // 2)
        for radius, alpha in ((2, 55), (1, 105)):
            ghost = render(text, scale, glow, spacing).copy()
            ghost.set_alpha(alpha)
            offset = radius * step
            for dx, dy in ((-offset, 0), (offset, 0), (0, -offset), (0, offset)):
                target.blit(ghost, (x + dx, y + dy))

    if shadow is not None:
        target.blit(render(text, scale, shadow, spacing), (x + scale, y + scale))

    target.blit(surf, (x, y))
    return pygame.Rect(x, y, surf.get_width(), surf.get_height())


def wrap(text, max_width, scale=1, spacing=1):
    """Bricht einen Text an Wortgrenzen auf die gewuenschte Breite um."""
    words = str(text).split()
    lines = []
    current = ""
    for word in words:
        probe = word if not current else current + " " + word
        if text_size(probe, scale, spacing)[0] <= max_width or not current:
            current = probe
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
