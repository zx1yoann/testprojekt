"""
audio.py - Alle Klaenge werden zur Laufzeit synthetisiert.

QUELLEN
-------
Keine uebernommenen Codefragmente und keine mitgelieferten Audiodateien.
Die Wellenform-Synthese, die Huellkurve und beide Musikstuecke sind
Eigenleistung.
Genutzte Bausteine aus der Dokumentation:
  pygame.sndarray.make_sound - https://www.pygame.org/docs/ref/sndarray.html
  pygame.mixer               - https://www.pygame.org/docs/ref/mixer.html

WARUM SYNTHETISIERTER SOUND?
----------------------------
Statt fertige WAV- oder MP3-Dateien mitzuliefern, berechnet das Spiel jeden
Ton selbst aus einer Wellenform. Das haelt das Projekt klein, es gibt keine
Lizenzfragen, und der typische 8-Bit-Klang entsteht genau so, wie ihn alte
Spielkonsolen erzeugt haben: aus Rechteck-, Dreieck- und Rauschsignalen.
"""

import numpy as np
import pygame

SAMPLE_RATE = 44100

# Halbtonabstaende zum Kammerton A, daraus wird jede Frequenz berechnet.
_SEMITONES = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}


def note_to_freq(name):
    """Wandelt eine Notenbezeichnung wie 'A4' oder 'C#5' in Hertz um.

    Eine Pause wird als '-' geschrieben und ergibt 0 Hz (Stille).
    """
    if name == "-":
        return 0.0
    letter = name[0].upper()
    rest = name[1:]
    sharp = 0
    if rest.startswith("#"):
        sharp = 1
        rest = rest[1:]
    octave = int(rest)
    semitone = _SEMITONES[letter] + sharp + (octave - 4) * 12
    return 440.0 * (2.0 ** (semitone / 12.0))


# --------------------------------------------------------------------------
# EIGENLEISTUNG: Wellenform-Generatoren.
# --------------------------------------------------------------------------
def _square(t, freq, duty=0.5):
    """Rechteckwelle - der klassische Chiptune-Lead."""
    if freq <= 0:
        return np.zeros_like(t)
    phase = (t * freq) % 1.0
    return np.where(phase < duty, 1.0, -1.0)


def _triangle(t, freq):
    """Dreieckwelle - weicher, gut fuer Bass."""
    if freq <= 0:
        return np.zeros_like(t)
    phase = (t * freq) % 1.0
    return 4.0 * np.abs(phase - 0.5) - 1.0


def _noise(t, seed=0):
    """Weisses Rauschen - Grundlage fuer Crash- und Rutschgeraeusche."""
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, size=t.shape)


def _envelope(length, attack=0.01, decay=0.06, sustain=0.6, release=0.12):
    """Huellkurve (ADSR), die einem Ton Anschlag und Ausklang gibt.

    Ohne Huellkurve klingt jeder synthetisierte Ton wie ein harter Piepser
    mit Knacken am Anfang und Ende.
    """
    a = int(SAMPLE_RATE * attack)
    d = int(SAMPLE_RATE * decay)
    r = int(SAMPLE_RATE * release)
    s = max(0, length - a - d - r)
    env = np.concatenate([
        np.linspace(0.0, 1.0, a, endpoint=False) if a else np.array([]),
        np.linspace(1.0, sustain, d, endpoint=False) if d else np.array([]),
        np.full(s, sustain),
        np.linspace(sustain, 0.0, r) if r else np.array([]),
    ])
    if len(env) < length:
        env = np.pad(env, (0, length - len(env)))
    return env[:length]


def _to_sound(wave, volume=0.35):
    """Wandelt ein Float-Array in ein abspielbares Stereo-Sound-Objekt."""
    wave = np.clip(wave * volume, -1.0, 1.0)
    samples = (wave * 32767).astype(np.int16)
    stereo = np.repeat(samples.reshape(-1, 1), 2, axis=1)
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _tone(freq, duration, wave="square", duty=0.5, volume=0.35, **env_kw):
    """Erzeugt einen einzelnen Ton als Sound-Objekt."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    if wave == "square":
        data = _square(t, freq, duty)
    elif wave == "triangle":
        data = _triangle(t, freq)
    else:
        data = _noise(t)
    return _to_sound(data * _envelope(n, **env_kw), volume)


def _sweep(f_start, f_end, duration, wave="square", volume=0.35, **env_kw):
    """Erzeugt einen Ton mit gleitender Tonhoehe (Glissando).

    Die Phase wird aufintegriert, sonst entstehen beim Frequenzwechsel
    hoerbare Spruenge im Signal.
    """
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freqs = np.linspace(f_start, f_end, n)
    phase = np.cumsum(freqs) / SAMPLE_RATE
    if wave == "square":
        data = np.where(phase % 1.0 < 0.5, 1.0, -1.0)
    else:
        data = 4.0 * np.abs((phase % 1.0) - 0.5) - 1.0
    return _to_sound(data * _envelope(n, **env_kw), volume)


# --------------------------------------------------------------------------
# EIGENLEISTUNG: Die beiden Musikstuecke als Notenlisten.
# Jeder Eintrag ist (Note, Schlaege). Die Melodien laufen in a-Moll, der
# Blackout-Track eine Oktave tiefer und halb so schnell fuer die duestere
# Stimmung.
# --------------------------------------------------------------------------
LEAD_ENDLESS = [
    ("A4", 1), ("C5", 1), ("E5", 1), ("D5", 1),
    ("C5", 1), ("A4", 1), ("G4", 1), ("A4", 1),
    ("F4", 1), ("A4", 1), ("C5", 1), ("A4", 1),
    ("G4", 1), ("B4", 1), ("D5", 1), ("E5", 1),
    ("A4", 1), ("C5", 1), ("E5", 1), ("G5", 1),
    ("E5", 1), ("C5", 1), ("A4", 1), ("E4", 1),
    ("F4", 2), ("G4", 2),
    ("A4", 2), ("-", 2),
]

BASS_ENDLESS = [
    ("A2", 2), ("A2", 2), ("F2", 2), ("G2", 2),
    ("A2", 2), ("A2", 2), ("F2", 2), ("E2", 2),
    ("A2", 2), ("A2", 2), ("C3", 2), ("E3", 2),
    ("F2", 2), ("G2", 2), ("A2", 2), ("-", 2),
]

LEAD_BLACKOUT = [
    ("A3", 2), ("-", 1), ("C4", 1), ("B3", 2), ("-", 2),
    ("E3", 2), ("-", 1), ("G3", 1), ("F3", 2), ("-", 2),
    ("A3", 2), ("C4", 2), ("E4", 2), ("D4", 2),
    ("C4", 4), ("-", 4),
]

BASS_BLACKOUT = [
    ("A1", 4), ("F1", 4), ("G1", 4), ("E1", 4),
    ("A1", 4), ("C2", 4), ("D2", 4), ("-", 4),
]


def _render_track(notes, beat, wave, duty, volume, detune=1.0):
    """Rendert eine Notenliste in ein durchgehendes Float-Array."""
    chunks = []
    for name, beats in notes:
        duration = beat * beats
        n = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n, endpoint=False)
        freq = note_to_freq(name) * detune
        if wave == "square":
            data = _square(t, freq, duty)
        else:
            data = _triangle(t, freq)
        # Kurzes Release am Notenende verhindert Knacksen beim Uebergang.
        chunks.append(data * _envelope(n, attack=0.008, decay=0.04,
                                       sustain=0.75, release=0.05))
    if not chunks:
        return np.zeros(1)
    return np.concatenate(chunks) * volume


def _build_music(lead, bass, bpm):
    """Mischt Lead, Bass und einen einfachen Schlagzeug-Puls zu einem Loop."""
    beat = 60.0 / bpm / 2.0           # ein "Schlag" = Achtelnote
    lead_wave = _render_track(lead, beat, "square", 0.25, 0.30)
    bass_wave = _render_track(bass, beat, "triangle", 0.5, 0.42)

    length = max(len(lead_wave), len(bass_wave))
    # Beide Spuren auf gleiche Laenge bringen, kuerzere wird wiederholt.
    lead_wave = np.resize(lead_wave, length)
    bass_wave = np.resize(bass_wave, length)

    # Hi-Hat: alle zwei Schlaege ein kurzer Rauschimpuls.
    drum = np.zeros(length)
    step = int(SAMPLE_RATE * beat * 2)
    hit_len = int(SAMPLE_RATE * 0.03)
    rng = np.random.default_rng(7)
    for start in range(0, length - hit_len, step):
        hit = rng.uniform(-1, 1, hit_len) * np.linspace(1.0, 0.0, hit_len) ** 3
        drum[start:start + hit_len] += hit * 0.18

    return _to_sound(lead_wave + bass_wave + drum, volume=0.55)


class AudioManager:
    """Verwaltet Musik und Effekte inklusive Mute und Lautstaerke.

    Der ganze Manager ist so gebaut, dass er auch auf Rechnern ohne
    funktionierende Soundkarte nicht abstuerzt: schlaegt die Initialisierung
    fehl, laeuft das Spiel einfach stumm weiter (self.available bleibt False).
    """

    def __init__(self, settings):
        self.settings = settings
        self.available = False
        self.sfx = {}
        self.music = {}
        self.current_track = None

        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.set_num_channels(16)
            self.available = True
        except pygame.error:
            return

        try:
            self._build_all()
        except (pygame.error, ValueError):
            # Synthese fehlgeschlagen: lieber stumm als abgestuerzt.
            self.available = False
            return

        self.apply_volumes()

    def _build_all(self):
        """Synthetisiert einmalig alle Effekte und Musikstuecke."""
        self.sfx = {
            # Sprung: aufsteigender Ton
            "jump": _sweep(330, 700, 0.16, volume=0.30, attack=0.005,
                           decay=0.02, sustain=0.7, release=0.08),
            # Landung: kurzer tiefer Impuls
            "land": _tone(150, 0.07, "triangle", volume=0.22, attack=0.002,
                          decay=0.02, sustain=0.4, release=0.04),
            # Rutschen: gefiltertes Rauschen
            "slide": _tone(0, 0.22, "noise", volume=0.13, attack=0.01,
                           decay=0.05, sustain=0.45, release=0.14),
            # Muenze: heller Doppelklick
            "coin": _sweep(880, 1320, 0.11, volume=0.26, attack=0.002,
                           decay=0.02, sustain=0.8, release=0.06),
            # Power-Up: aufsteigende Fanfare
            "power": _sweep(440, 1200, 0.30, volume=0.28, attack=0.01,
                            decay=0.05, sustain=0.75, release=0.14),
            # Crash: abfallendes Rauschen
            "crash": _sweep(420, 60, 0.55, "triangle", volume=0.40,
                            attack=0.004, decay=0.10, sustain=0.6,
                            release=0.34),
            # Menue-Klick
            "click": _tone(620, 0.06, volume=0.22, duty=0.3, attack=0.002,
                           decay=0.015, sustain=0.5, release=0.035),
            # Button unter dem Mauszeiger
            "hover": _tone(880, 0.035, volume=0.11, duty=0.2, attack=0.002,
                           decay=0.01, sustain=0.4, release=0.02),
            # Akku-Warnung im Blackout-Modus
            "warn": _tone(240, 0.16, "triangle", volume=0.30, attack=0.005,
                          decay=0.03, sustain=0.7, release=0.10),
            # Neuer Highscore
            "fanfare": _sweep(520, 1560, 0.55, volume=0.32, attack=0.01,
                              decay=0.06, sustain=0.8, release=0.26),
        }
        self.music = {
            "endless": _build_music(LEAD_ENDLESS, BASS_ENDLESS, bpm=138),
            "blackout": _build_music(LEAD_BLACKOUT, BASS_BLACKOUT, bpm=92),
            "menu": _build_music(LEAD_ENDLESS, BASS_ENDLESS, bpm=104),
        }

    # -- Lautstaerke -------------------------------------------------------
    def apply_volumes(self):
        """Uebertraegt die aktuellen Einstellungen auf alle Sound-Objekte."""
        if not self.available:
            return
        muted = self.settings.get("muted", False)
        sfx_vol = 0.0 if muted else float(self.settings.get("sfx_volume", 0.8))
        mus_vol = 0.0 if muted else float(self.settings.get("music_volume", 0.6))
        for sound in self.sfx.values():
            sound.set_volume(sfx_vol)
        for sound in self.music.values():
            sound.set_volume(mus_vol)

    def toggle_mute(self):
        """Schaltet stumm und wieder zurueck. Gibt den neuen Zustand zurueck."""
        self.settings["muted"] = not self.settings.get("muted", False)
        self.apply_volumes()
        return self.settings["muted"]

    # -- Wiedergabe --------------------------------------------------------
    def play(self, name):
        """Spielt einen Effekt ab, sofern Sound verfuegbar und nicht stumm."""
        if not self.available or self.settings.get("muted", False):
            return
        sound = self.sfx.get(name)
        if sound is not None:
            sound.play()

    def play_music(self, track):
        """Startet einen Musik-Loop. Ein bereits laufender Track bleibt."""
        if not self.available:
            return
        if self.current_track == track:
            return
        self.stop_music()
        sound = self.music.get(track)
        if sound is not None:
            sound.play(loops=-1)
            self.current_track = track

    def stop_music(self):
        """Stoppt die laufende Musik."""
        if not self.available:
            return
        for sound in self.music.values():
            sound.stop()
        self.current_track = None
