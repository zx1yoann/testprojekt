"""
main.py - Startpunkt des Spiels NEON RUSH.

PROJEKT
-------
Ein Pixel-Endless-Runner mit PyGame, entstanden im Rahmen des
Informatik-Programmierprojekts.

QUELLEN
-------
Der gesamte Code dieses Projekts ist eigenstaendig geschrieben. Es wurden
keine Codefragmente aus Tutorials uebernommen und keine externen Bild-,
Schrift- oder Audiodateien eingebunden. Saemtliche Grafiken, die Schrift und
alle Klaenge werden zur Laufzeit im Code erzeugt.

Verwendete Bibliotheken:
  PyGame  - Spielebibliothek, https://www.pygame.org/docs/
  NumPy   - Zahlenfelder fuer die Klangsynthese, https://numpy.org/doc/

Spielprinzip inspiriert vom Endless-Runner-Genre (z.B. Subway Surfers).
Die Umsetzung erfolgte ohne Vorlage.

Die Quellenangaben je Datei stehen jeweils am Dateianfang.

START
-----
    python main.py

BEENDEN
-------
Jederzeit mit ESCAPE oder ueber den Kreuz-Button des Fensters.
"""

import sys

from game.scene import App
from game.scenes.audio_screen import AudioScene
from game.scenes.gameover import GameOverScene
from game.scenes.howto import HowToScene
from game.scenes.menu import MenuScene_
from game.scenes.modes import ModeScene
from game.scenes.play import PlayScene
from game.scenes.scores import ScoreScene


def build_app():
    """Erzeugt die Anwendung und meldet alle Screens an.

    Die Screens werden einmalig erzeugt und unter einem Namen registriert.
    Der Wechsel laeuft danach nur noch ueber app.go("name").
    """
    app = App()
    app.register("menu", MenuScene_(app))
    app.register("modes", ModeScene(app))
    app.register("howto", HowToScene(app))
    app.register("audio", AudioScene(app))
    app.register("scores", ScoreScene(app))
    app.register("play", PlayScene(app))
    app.register("gameover", GameOverScene(app))
    return app


def main():
    """Startet das Spiel im Hauptmenue."""
    app = build_app()
    app.go("menu")
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
