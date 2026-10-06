# Startseite – SCM Online (Shopify, Theme Horizon)

Neue, plakative Startseite mit wenig Text und großen Bildern, angelehnt an den Aufbau von ratandboa.com.

## Aufbau (`theme/templates/index.json`)

| # | Section | Inhalt |
|---|---|---|
| 1 | `scm-hero` | Hero-Bild (Blumenweste) mit Text direkt im Bild: Desktop links neben der Person „Zweite / Chance. / Erste / Wahl.“ + zwei Buttons untereinander, mobil unten als Zweizeiler. Dunkle Verläufe nur dort, wo Text steht. Alternativ „Geteilt“ oder Video |
| 2 | `scm-ticker` | Schwarzes Laufband: Neu & Second Hand · Einzelstücke mit Charakter · Versandkostenfrei ab 75 € · 14 Tage Anprobe |
| 3 | `scm-worlds` | 50/50-Kacheln „Neu“ und „Second Hand“ |
| 4 | `scm-categories` | Kategorie-Raster mit Umschalter Neu / Second Hand; Kategorien unter 3 Artikeln werden ausgeblendet, die Kachel „Alle ansehen“ füllt die letzte Reihe immer exakt |
| 5 | `scm-looks` | Shop the Look: drei Looks (Name + Pfeil), beim Darüberfahren (mobil: im Blickfeld) läuft das Reel |
| 6 | `scm-new-in` | „New In“-Rail mit Umschalter, Pfeilen, Fortschrittsbalken und Ziehen mit der Maus; Größe nur bei Second Hand |
| 7 | `scm-statement` | Abschluss in Stein: „Online bestellen. Liefern lassen. Oder abholen.“ + Versand / Click & Collect |

Gestaltungsregeln: ein einheitlicher Section-Abstand (nie doppelt), alle Texte und Raster auf derselben Gutter-Linie, 4 px Bildfugen, keine Zähler oder Nummern ohne Nutzen.

Gemeinsame Styles und Scripts liegen in `theme/assets/scm-home.css` und `theme/assets/scm-home.js`, eingebunden über `theme/snippets/scm-home-head.liquid`.
Alle Texte, Bilder, Links und Kollektionen lassen sich im Theme-Editor ändern.

## UX-Details

- Kaum Text, große Schrift (Montserrat 800, Großbuchstaben), klare Wege: jede Kachel ist komplett klickbar.
- Video pausiert außerhalb des Sichtfelds und lässt sich anhalten. Bei „Bewegung reduzieren“ laufen keine Animationen.
- Reiter sind per Tastatur bedienbar (Pfeiltasten), Fokus ist sichtbar, Klickflächen sind mindestens 44 px groß.
- Second-Hand-Titel im Format „Marke | Art | Größe“ werden als Marke + „Art · Größe“ dargestellt. Ausverkaufte Einzelstücke erscheinen nicht in der Rail.
- Der Hinweis „inkl. MwSt., zzgl. Versand“ kommt aus der bestehenden Übersetzung `custom.price.tax_shipping`.

## Bilder und Videos

- Look-Bilder: `assets/looks/look-0X.webp`, liegen in Shopify unter *Inhalte → Dateien* als `scm-look-0X.webp`
- Look-Reels: `export/look-0X.mp4`, liegen ebenfalls unter *Inhalte → Dateien* als `scm-look-0X.mp4`
- Hero: `assets/hero/scm-hero-blumenweste.webp` (2× hochgerechnet aus dem 1089 × 1445 px Original), in Shopify als `scm-hero-blumenweste.webp`. Ausschnitt per Fokuspunkt in *Inhalte → Dateien* steuerbar

## Produktseite (PDP) – `theme/templates/product.json`

Horizon liefert weiterhin Galerie (Zoom), Varianten, Warenkorb, Express-Checkout und die Sticky-Leiste. Darum herum:

| Teil | Datei | Inhalt |
|---|---|---|
| Kopf | `blocks/scm-pdp-head.liquid` | Chips (Neu / Second Hand + Einzelstück / Look 0X), Marke, riesiger Titel, Kurz-Claim. „Marke \| Art \| Größe“-Titel werden zerlegt |
| Preis-Hinweis | `blocks/scm-pdp-meta.liquid` | inkl. MwSt. · zzgl. Versand (Link zur Versandrichtlinie) |
| Versprechen | `blocks/scm-pdp-promise.liquid` | Versandkostenfrei ab 75 € · Click & Collect · 14 Tage Anprobe |
| Infos | `blocks/scm-pdp-info.liquid` | Aufklapper: Details, Versand & Rückgabe, Abholen in Espelkamp |
| So trägst du es | `sections/scm-pdp-looks.liquid` | Look-Bild mit Reel, alle Teile mit Preis, „Du bist hier“, Summe „Ganzer Look“ |
| Mehr davon | `sections/scm-pdp-more.liquid` | Rail mit Artikeln aus derselben Kategorie |

Galerie: zwei Spalten, erstes Bild groß, 4:5, randlos. Ein einzelnes letztes Bild läuft über die volle Breite.

## Looks (Metaobjekte)

- Definition `look` (Inhalte → Metaobjekte → Look): Nummer, Name, Bild, Reel-Link, Teile
- `look-01-mokka`, `look-02-salbei`, `look-03-karo-kette`
- Produkt-Metafeld `custom.looks` verknüpft Produkte mit ihren Looks
- „Shop the Look“ auf der Startseite liest die Looks per Handle, die Teile werden dort zu Links

## Artikel aus Shop the Look (als Entwurf angelegt)

| Artikel | Handle | Preis (Vorschlag) |
|---|---|---|
| Tupfenbluse Mokka | `tupfenbluse-mokka` | 29,90 € |
| Oversize-Shirt Salbei | `oversize-shirt-salbei` | 24,90 € |
| Paisley-Tuch | `paisley-tuch` | 12,90 € |
| Print-Bluse Karo & Kette | `print-bluse-karo-kette` | 29,90 € |
| Weite Hose (Mokka, Salbei, Schwarz) | `weite-hose` | 34,90 € |
| Gürtel (bestand schon) | `brauner-gurtel-mit-goldfarbener-schnalle` | 9,90 € |

Produktbilder: Ausschnitte aus den Look-Fotos in `product-images/`.
