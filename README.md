# Second Chance – Motion Graphics für Instagram

Ruhige, dezente Motion Graphics für die drei Looks, im Format 9:16 (1080 × 1920, 30 fps) für Reels und Stories.

## Fertige Videos (`export/`)

| Datei | Länge | Inhalt |
|---|---|---|
| `secondchance-reel.mp4` | 24,6 s | Intro-Karte → Look 01 → Look 02 → Look 03 → Outro, weiche Überblendungen |
| `look-01.mp4` | 8 s | Look 01 „Mokka“, nahtlos loopbar |
| `look-02.mp4` | 8 s | Look 02 „Salbei“, nahtlos loopbar |
| `look-03.mp4` | 8 s | Look 03 „Karo & Kette“, nahtlos loopbar |

Cover-Standbilder liegen in `export/stills/`.

Die Videos haben eine stille Tonspur. Musik am besten direkt in Instagram hinzufügen.

## Bewegungselemente

- **Langsamer Push-in** auf das Foto (max. 4–4,5 %), mit Subpixel-Genauigkeit, damit nichts ruckelt
- **Wanderndes Fensterlicht**: weiche, diagonale Lichtbahnen ziehen langsam über die Wand
- **Staubpartikel**: wenige, kaum sichtbare Partikel, die im Licht schweben
- **Typografie**: Markenzeile oben links; unten links eine Akzentlinie, die sich aufbaut, die Look-Nummer, der Name (Buchstabe für Buchstabe) und die Teile
- Jeder Look hat eine eigene Akzentfarbe (Mokka, Salbei, Bordeaux)

Alle Texte liegen in der Safe Zone für Reels und Stories, also nicht unter der Instagram-Oberfläche oben und unten.
Die Einzelclips laufen in sich periodisch ab, sodass der Loop in Instagram keinen sichtbaren Sprung hat.

## Texte anpassen und neu rendern

Markenname, Look-Namen, Teile und Akzentfarben stehen in `motion/config.json`.

```bash
pip install numpy pillow     # ffmpeg muss installiert sein
python3 motion/render.py                 # alle Videos
python3 motion/render.py --only look-02  # nur ein Video
python3 motion/render.py --stills        # nur Vorschaubilder, schnell zum Prüfen
```

## Schriften

Die Schriften Cormorant Garamond und Inter liegen in `assets/fonts/` und stehen beide unter der SIL Open Font License.
