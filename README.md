# Le Mag Croisières

Site du média [lemagcroisieres.fr](https://www.lemagcroisieres.fr) — tests à bord, avis sur les
compagnies, comparatifs d'itinéraires et guides pratiques de la croisière maritime et fluviale.

Site **statique**, sans dépendance ni étape de compilation : le contenu de ce dépôt est servi
tel quel. Direction artistique « Carte Marine ».

## Contenu

| | |
|---|---|
| Articles | 15, dans un dossier au slug du canonical (`slug/index.html`) |
| Rubriques | 7, générées dans `rubriques/` |
| Pages éditeur | 7, générées (à propos, méthodologie, équipage, partenariats, contact, mentions légales, confidentialité) |
| Archives | `articles/`, avec recherche instantanée et filtres |
| Images | 141 photos auto-hébergées dans `images/photos/`, en AVIF avec repli JPEG |

## Lancer le site en local

```bash
python3 -m http.server 4873
```

Puis ouvrir <http://localhost:4873/>. Le script `Lancer le site.command` fait la même chose
depuis le Finder, et ouvre Safari.

## Générateurs

Tout ce qui est dérivé est produit par les scripts de `outils/`, jamais écrit à la main.
Après chaque publication, les enchaîner **dans cet ordre** :

```bash
python3 outils/heberger-images.py        # rapatrie les images distantes, AVIF + JPEG
python3 outils/generer-rubriques.py      # rubriques/, depuis les cartes de index.html
python3 outils/generer-page-articles.py  # articles/, recherche et filtres
python3 outils/generer-pages-editeur.py  # les 7 pages éditeur
python3 outils/generer-jsonld-accueil.py # le graphe schema.org de l'accueil
python3 outils/generer-llms.py           # llms.txt
python3 outils/generer-sitemap.py        # sitemap.xml
```

Deux scripts ne se lancent qu'à la demande :

- `outils/generer-visuels.py` — logo et image de partage, en cas de changement de marque
- `outils/maj-plus-lus.py` — bloc « Les plus lus » depuis Umami ou Plausible (clés en variables
  d'environnement, jamais dans le dépôt)

## Règles à respecter

- **Aucun contenu fabriqué.** Chaque carte, note ou statistique correspond à un article
  réellement publié.
- **Le balisage suit le visible.** Les FAQ et le relevé des compagnies sont lus dans le HTML
  par le générateur : le schéma ne peut pas diverger de ce que voit le lecteur.
- **Une seule adresse de contact**, au domaine du média. Le formulaire passe par EmailJS ;
  seule la clé publique figure dans les pages, jamais la clé privée.
- **Les images sont auto-hébergées.** Aucune requête vers un domaine tiers, hors les
  polices Google Fonts.

## Licence

Contenus © Triaina. Photographies : Unsplash (licence libre), provenance de chaque fichier
consignée dans `images/photos/manifeste.json`.
