# Startseite – SCM Online (Shopify, Theme Horizon)

Neue, plakative Startseite mit wenig Text und großen Bildern, angelehnt an den Aufbau von ratandboa.com.

## Aufbau (`theme/templates/index.json`)

| # | Section | Inhalt |
|---|---|---|
| 1 | `scm-hero` | Vollbild-Video, riesige Zeile „Zweite Chance. Erste Wahl.“, zwei Buttons (Neu / Second Hand), Pause-Knopf |
| 2 | `scm-ticker` | Schwarzes Laufband mit kurzen Versprechen |
| 3 | `scm-worlds` | 50/50-Kacheln „Neu“ und „Second Hand“ mit Live-Artikelanzahl |
| 4 | `scm-categories` | Kategorie-Raster mit Umschalter Neu / Second Hand; leere Kategorien werden ausgeblendet |
| 5 | `scm-looks` | Shop the Look: drei Looks, beim Darüberfahren (mobil: im Blickfeld) läuft das Reel mit den Pfeilen |
| 6 | `scm-new-in` | Produkt-Rail „Neu eingetroffen“ mit Umschalter, Pfeilen, Fortschrittsbalken und Ziehen mit der Maus |
| 7 | `scm-statement` | Schwarzer Abschluss: „Online bestellen. Liefern lassen. Oder abholen.“ + Versand / Click & Collect |

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
