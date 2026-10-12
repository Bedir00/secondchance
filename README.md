# Second Chance – Motion Graphics für Instagram

Ruhige, dezente Motion Graphics für die drei Looks, im Format 9:16 (1080 × 1920, 30 fps) für Reels und Stories.

## Fertige Videos (`export/`)

| Datei | Länge | Inhalt |
|---|---|---|
| `secondchance-reel.mp4` | 27,6 s | Intro-Karte → Look 01 → Look 02 → Look 03 → Outro, weiche Überblendungen |
| `look-01.mp4` | 9 s | Look 01 „Mokka“, nahtlos loopbar |
| `look-02.mp4` | 9 s | Look 02 „Salbei“, nahtlos loopbar |
| `look-03.mp4` | 9 s | Look 03 „Karo & Kette“, nahtlos loopbar |
| `look-04-reel.mp4` | 14 s | **Finales Look-04-Video**: gefilmter Clip mit Preisen, mitlaufenden Pfeilen und Rabatt-CTA (24 fps) |
| `look-04-cta.mp4` | 15 s | Look 04 als Foto-Version (Standbild mit Push-in), gleicher CTA |

Cover-Standbilder liegen in `export/stills/`.

Die Videos haben eine stille Tonspur. Musik am besten direkt in Instagram hinzufügen.

## Bewegungselemente

- **Langsamer Push-in** auf das Foto (max. 4–4,5 %), mit Subpixel-Genauigkeit, damit nichts ruckelt
- **Wanderndes Fensterlicht**: weiche, diagonale Lichtbahnen ziehen langsam über die Wand
- **Staubpartikel**: wenige, kaum sichtbare Partikel, die im Licht schweben
- **Typografie**: Markenzeile oben links; unten links eine Akzentlinie, die sich aufbaut, die Look-Nummer und der Name (Buchstabe für Buchstabe)
- **Weiße Pfeile**: Jedes Teil (Oberteil, Tuch, Gürtel, Hose) hat eine kleine Beschriftung. Von dort zeichnet sich nacheinander ein dünner, geschwungener weißer Pfeil zum Kleidungsstück. Ein ganz leichter Schatten hält ihn auf der hellen Wand lesbar. Die Pfeilspitzen wandern mit dem Zoom mit und bleiben so auf dem Teil.
- Jeder Look hat eine eigene Akzentfarbe (Mokka, Salbei, Bordeaux)

Alle Texte liegen in der Safe Zone für Reels und Stories, also nicht unter der Instagram-Oberfläche oben und unten.
Die Einzelclips laufen in sich periodisch ab, sodass der Loop in Instagram keinen sichtbaren Sprung hat.

## Look 04 – finales Video (`look-04-reel.mp4`)

Grundlage ist der gefilmte Clip `assets/video/look-04-source.mp4` (Selfie-Walk, dann Stativ-Einstellung). Er wird auf 1080 × 1920 hochskaliert und behält seine 24 fps, damit keine Bewegung ruckelt. Alle Texte sind in Montserrat gesetzt, die Schriftfarbe ist #FEFEFE.

1. **0–4,2 s, Selfie-Walk**: Oben steht die Markenzeile. Rechts erscheinen „Oberteil 44,90 €“ und „Rock 49,90 €“. Von jedem Preis zeichnet sich ein dünner weißer Pfeil zum Teil. Die Pfeilspitzen folgen Pullover und Rock, während die Person auf den Spiegel zugeht (Optical-Flow-Tracking).
2. **Übergang**: Der harte Schnitt im Original wird zu einer kurzen, weichen Überblendung (8 Frames). Davor blenden die Preise sanft aus.
3. **4,1–14 s, Stativ-Einstellung + CTA**: Von unten legt sich ein Verlauf ins Bild. Dann erscheint der CTA Zeile für Zeile:
   „Outfit zusammenbestellen“ / groß **„20 % Rabatt“** / „kostenlosen Versand erhalten.“
   Darunter steht eine kleine Preistabelle: „Rock 39,92 € statt 49,90 €“ und „Oberteil 35,92 € statt 44,90 €“. Die alten Preise werden dabei dezent durchgestrichen.
   Der Clip endet fast ruhig. Sein letztes Bild bleibt deshalb noch 4,3 s stehen, mit einem sehr langsamen Push-in (3,5 %). So ist der CTA rund 9 s zu sehen.
4. Das Video blendet aus Schwarz ein und am Ende kurz nach Schwarz aus. So hat der Loop in Instagram keinen harten Sprung.

Texte, Preise, Positionen der Beschriftungen, Pfeilziele und Timing stehen in `motion/look-04-video.json`:

```bash
pip install numpy pillow opencv-python-headless   # ffmpeg muss installiert sein
python3 motion/render_video.py           # Video + Standbilder
python3 motion/render_video.py --stills  # nur Standbilder (Preis-Szene und CTA-Szene)
python3 motion/render_video.py --debug   # zeigt die getrackten Punkte in motion/debug/
```

## Look 04 als Foto-Version (`look-04-cta.mp4`)

Eigenes Video im Corporate Design: alle Texte in **Montserrat**, Schriftfarbe **#FEFEFE**.

1. **0–6,6 s**: Langsamer Push-in auf das Foto. Oben steht die Markenzeile. Rechts erscheinen nacheinander „Oberteil 44,90 €“ und „Rock 49,90 €“. Von jedem Preis zeichnet sich ein dünner weißer Pfeil zum Teil.
2. **6,6–8,2 s**: Die Preise blenden weich aus. Von unten legt sich ein leichter Verlauf ins Bild, damit der CTA gut lesbar ist.
3. **7,5–14 s**: Eine kurze Linie baut sich auf, dann erscheint der CTA Zeile für Zeile:
   „Outfit zusammenbestellen / und 20 % Rabatt erhalten“, darunter „Rock 49,90 € · Oberteil 44,90 €“.
4. Das Video blendet aus Schwarz ein und am Ende nach Schwarz aus. So läuft der Loop in Instagram ohne Sprung.

Texte, Preise und Pfeilpositionen stehen in `motion/look-04.json`:

```bash
python3 motion/render_cta.py           # Video + Standbilder
python3 motion/render_cta.py --stills  # nur Standbilder (Preis-Szene und CTA-Szene)
```

## Texte anpassen und neu rendern

Markenname, Look-Namen, Akzentfarben und die Pfeil-Beschriftungen stehen in `motion/config.json`.

Pro Pfeil (`callouts`):
- `text`: die Beschriftung
- `at`: Position der Beschriftung (x, Grundlinie y) im 1080×1920-Bild
- `align`: Ausrichtung der Beschriftung, `left` oder `right`; der Pfeil startet an der Seite, die zum Bild zeigt
- `to`: der Punkt auf dem Kleidungsstück, auf den die Pfeilspitze zeigt
- `bend`: wie stark der Pfeil gebogen ist; das Vorzeichen bestimmt die Richtung

```bash
pip install numpy pillow     # ffmpeg muss installiert sein
python3 motion/render.py                 # alle Videos
python3 motion/render.py --only look-02  # nur ein Video
python3 motion/render.py --stills        # nur Vorschaubilder, schnell zum Prüfen
```

## Schriften

Die Schriften Cormorant Garamond, Inter und Montserrat liegen in `assets/fonts/`. Alle drei stehen unter der SIL Open Font License.
