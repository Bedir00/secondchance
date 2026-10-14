# Second Chance – Motion Graphics für Instagram

Ruhige, dezente Motion Graphics für die drei Looks, im Format 9:16 (1080 × 1920, 30 fps) für Reels und Stories.

## Fertige Videos (`export/`)

| Datei | Länge | Inhalt |
|---|---|---|
| `secondchance-reel.mp4` | 27,6 s | Intro-Karte → Look 01 → Look 02 → Look 03 → Outro, weiche Überblendungen |
| `look-01.mp4` | 9 s | Look 01 „Mokka“, nahtlos loopbar |
| `look-02.mp4` | 9 s | Look 02 „Salbei“, nahtlos loopbar |
| `look-03.mp4` | 9 s | Look 03 „Karo & Kette“, nahtlos loopbar |

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

Die Schriften Cormorant Garamond und Inter liegen in `assets/fonts/` und stehen beide unter der SIL Open Font License.

---

# Passform-Hinweise im Produktbild (Shopify PDP)

Auf der Produktseite liegen auf dem ersten Produktbild animierte Hinweis-Punkte zu Größe und Passform. Sie sollen unsicheren Kundinnen helfen. Zurzeit gibt es sie für den **Strukturpullover mit flauschigen Ärmelabschlüssen** und den **Plisseerock mit Gürtel ANISE**.

## Bewegung

- Oben links gleitet der Chip „Passt mir das?“ ins Bild. Ein Lichtschimmer läuft einmal darüber, nach ein paar Sekunden klappt der Chip zum Maßband-Symbol zusammen.
- Die Punkte ploppen nacheinander auf. Von jedem Punkt zeichnet sich eine dünne weiße Linie zur Beschriftung (Größe, Ärmel, Länge …), danach gleitet die Beschriftung ein.
- Ein ruhiger Sonar-Ring pulsiert um jeden Punkt.
- Ein Tipp auf einen Punkt (oder auf den Chip) öffnet unten im Bild eine Karte mit dem Hinweis. Mit Pfeilen, Pfeiltasten oder den Punkten blättert man weiter, mit Esc oder ✕ schließt man sie.
- Bei „Bewegung reduzieren“ im Betriebssystem ist alles sofort sichtbar, ohne Animation.

## Dateien (`shopify/`)

| Datei | Zweck |
|---|---|
| `snippets/scm-fit-hotspots.liquid` | Markup, CSS und JavaScript der Hinweise |
| `snippets/product-media.liquid` | Horizon-Snippet. Rendert die Hinweise auf dem ersten Galeriebild der Produktseite, nicht im Zoom-Dialog |
| `metafields/*.json` | Inhalte pro Produkt, gespeichert im Produkt-Metafeld `scm_pdp.passform_hinweise` (JSON) |

## Inhalte und Positionen ändern

Die Inhalte stehen im Shopify-Admin am Produkt unter **Metafelder → Passform-Hinweise (Produktbild)**:

- `x`, `y`: Position in Prozent des Originalbilds (0–100, von links und von oben). Die Punkte werden auf den sichtbaren Bildausschnitt umgerechnet.
- `side`: `left` oder `right`, also auf welcher Seite die Beschriftung steht
- `label`: kurze Beschriftung am Punkt
- `title`, `text`: Inhalt der Karte
- `headline`, `footer`: Text des Chips und die Zeile unten in der Karte

**Punkte per Maus setzen:** Theme-Vorschau mit `?passform-edit` an der Produkt-URL öffnen (im Theme-Editor ist der Modus automatisch an). Punkte an die richtige Stelle ziehen, auf „JSON kopieren“ klicken und den Text ins Metafeld einfügen.

Ein anderes Produkt bekommt die Hinweise, sobald sein Metafeld gefüllt ist. Am Theme muss dafür nichts geändert werden.

---

# Produktbilder im Format 3:4

Alle Produktbilder werden im Shop einheitlich im Hochformat 3:4 angezeigt. Das gilt für die Galerie der Produktseite, die Produktkarten in Kollektionen, Suche und Empfehlungen, die Leisten „Neu eingetroffen“ und „Mehr davon“ und die Teile-Liste der Looks.

Die Bilddateien bleiben unverändert. Fotos mit anderem Seitenverhältnis werden mittig beschnitten. Soll ein Bild einen anderen Ausschnitt zeigen, setzt du im Admin unter Inhalte → Dateien einen Fokuspunkt. Die Zoom-Ansicht zeigt weiter das ganze Bild. Look-Bilder (9:16), Kategorie-Kacheln und Hero behalten ihr Format.

Umgesetzt in `shopify/snippets/scm-product-image-ratio.liquid`, global eingebunden über `shopify/snippets/stylesheets.liquid`.
