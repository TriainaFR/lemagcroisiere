#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapatrie sur le serveur toutes les images encore servies par images.unsplash.com.

Pour chaque URL distincte : téléchargement au format et à la taille demandés,
écriture d'un JPEG de repli et d'un AVIF (deux à trois fois plus léger, écrit
par `sips`, livré avec macOS — la machine n'a ni cwebp ni encodeur WebP).
Les balises <img> sont ensuite enveloppées dans un <picture>, et les URL des
métadonnées sociales et du JSON-LD deviennent absolues sur notre domaine.

Le script est idempotent et se relance après chaque publication : il ne traite
que les URL Unsplash encore présentes.

USAGE
  python3 outils/heberger-images.py            # migre
  python3 outils/heberger-images.py --simuler  # liste sans rien écrire
"""
import io, os, re, sys, json, glob, subprocess, urllib.request
import concurrent.futures as cf

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.lemagcroisieres.fr"
DOSSIER = os.path.join(RACINE, "images", "photos")
PUBLIC = "/images/photos"
MANIFESTE = os.path.join(DOSSIER, "manifeste.json")

URL = re.compile(r'https://images\.unsplash\.com/(photo-[A-Za-z0-9_-]+)\?([^"\s]*)')
QUALITE_AVIF = "62"


def nom_local(fichier_id, params):
    """photo-1519…-02fb + w=800 -> 1519…-02fb-800"""
    w = re.search(r"[?&]w=(\d+)", "?" + params)
    h = re.search(r"[?&]h=(\d+)", "?" + params)
    taille = w.group(1) if w else "src"
    if h:
        taille += "x" + h.group(1)
    return "%s-%s" % (fichier_id[len("photo-"):], taille)


def recenser():
    """{url complète: (nom local, [fichiers où elle apparaît])}"""
    trouvees = {}
    for chemin in fichiers_html():
        s = io.open(chemin, encoding="utf-8").read()
        for m in URL.finditer(s):
            complete = m.group(0)
            trouvees.setdefault(complete, [nom_local(m.group(1), m.group(2)), []])
            trouvees[complete][1].append(chemin)
    return trouvees


def fichiers_html():
    return sorted(set(glob.glob(os.path.join(RACINE, "*.html"))
                      + glob.glob(os.path.join(RACINE, "*", "index.html"))
                      + glob.glob(os.path.join(RACINE, "rubriques", "*", "index.html"))))


def telecharger(args):
    url, nom = args
    jpg = os.path.join(DOSSIER, nom + ".jpg")
    avif = os.path.join(DOSSIER, nom + ".avif")
    if os.path.exists(jpg) and os.path.exists(avif):
        return nom, os.path.getsize(jpg), os.path.getsize(avif), "déjà là"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "lemagcroisieres.fr/1.0"})
        donnees = urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        return nom, 0, 0, "ÉCHEC : %s" % e
    open(jpg, "wb").write(donnees)
    r = subprocess.run(["sips", "-s", "format", "avif",
                        "-s", "formatOptions", QUALITE_AVIF, jpg, "--out", avif],
                       capture_output=True)
    if r.returncode or not os.path.exists(avif):
        return nom, os.path.getsize(jpg), 0, "AVIF impossible"
    return nom, os.path.getsize(jpg), os.path.getsize(avif), "ok"


def reecrire(chemin, table):
    """Remplace les URL Unsplash d'un fichier ; renvoie (texte, nb img, nb méta)."""
    s = io.open(chemin, encoding="utf-8").read()
    n_img = n_meta = 0

    # 1. les balises <img> : on les enveloppe dans un <picture> avec source AVIF
    def img(m):
        nonlocal n_img
        balise = m.group(0)
        u = URL.search(balise)
        if not u or u.group(0) not in table:
            return balise
        nom = table[u.group(0)]
        n_img += 1
        neuve = balise.replace(u.group(0), "%s/%s.jpg" % (PUBLIC, nom))
        return ('<picture><source srcset="%s/%s.avif" type="image/avif">%s</picture>'
                % (PUBLIC, nom, neuve))

    s = re.sub(r"<img\s[^>]*>", img, s)

    # 2. métadonnées sociales et JSON-LD : URL absolues sur notre domaine
    for complete, nom in table.items():
        avant = s
        s = s.replace('"%s"' % complete, '"%s%s/%s.jpg"' % (BASE, PUBLIC, nom))
        if s != avant:
            n_meta += 1

    # 3. Le fond de la une fait exception : dans `.feat .bg`, qui combine
    #    position absolue, will-change et une animation Ken Burns, l'AVIF
    #    sélectionné par <picture> se décode mais n'est jamais peint — la une
    #    reste vide. On y sert le JPEG en <img> simple. Constaté le 11 août 2026.
    s = re.sub(r'(<span class="bg" id="featbg">\s*)<picture><source[^>]*>(<img[^>]*>)</picture>',
               r"\1\2", s)

    # 4. <picture> ne doit pas casser les chaînes de hauteur du CSS
    if "picture{display:contents}" not in s and n_img:
        s = s.replace("<style>", "<style>\n  picture{display:contents}", 1)

    # 5. le préconnect vers Unsplash n'a plus lieu d'être
    s = re.sub(r'\s*<link rel="preconnect" href="https://images\.unsplash\.com"[^>]*>', "", s)
    return s, n_img, n_meta


def main():
    simuler = "--simuler" in sys.argv
    os.makedirs(DOSSIER, exist_ok=True)
    trouvees = recenser()
    if not trouvees:
        print("Aucune image distante : tout est déjà hébergé.")
        return

    print("%d URL Unsplash distinctes, %d références au total"
          % (len(trouvees), sum(len(v[1]) for v in trouvees.values())))
    if simuler:
        for u, (nom, ou) in sorted(trouvees.items()):
            print("  %-46s ← %d page(s)" % (nom, len(ou)))
        return

    # ---- téléchargement + conversion ----
    taches = [(u, v[0]) for u, v in trouvees.items()]
    jpg_total = avif_total = 0
    echecs = []
    with cf.ThreadPoolExecutor(8) as ex:
        for nom, tj, ta, etat in ex.map(telecharger, taches):
            if etat.startswith("ÉCHEC") or etat == "AVIF impossible":
                echecs.append((nom, etat))
            jpg_total += tj
            avif_total += ta
    if echecs:
        for nom, etat in echecs:
            print("  ⚠ %-46s %s" % (nom, etat))
        raise SystemExit("%d image(s) en échec — rien n'a été réécrit." % len(echecs))

    print("  %d images enregistrées — JPEG %.1f Mo, AVIF %.1f Mo (%.0f %% de moins)"
          % (len(taches), jpg_total / 1e6, avif_total / 1e6,
             100 - 100.0 * avif_total / jpg_total))

    # ---- réécriture des pages ----
    table = {u: v[0] for u, v in trouvees.items()}
    total_img = total_meta = pages = 0
    for chemin in fichiers_html():
        s, n_img, n_meta = reecrire(chemin, table)
        if n_img or n_meta:
            io.open(chemin, "w", encoding="utf-8").write(s)
            pages += 1
            total_img += n_img
            total_meta += n_meta
    print("  %d pages réécrites — %d balises <img>, %d URL de métadonnées"
          % (pages, total_img, total_meta))

    # ---- provenance ----
    manifeste = {}
    if os.path.exists(MANIFESTE):
        manifeste = json.load(io.open(MANIFESTE, encoding="utf-8"))
    for u, (nom, ou) in trouvees.items():
        manifeste[nom] = {
            "source": u,
            "licence": "Unsplash License (https://unsplash.com/license)",
            "fichiers": ["%s/%s.jpg" % (PUBLIC, nom), "%s/%s.avif" % (PUBLIC, nom)],
        }
    io.open(MANIFESTE, "w", encoding="utf-8").write(
        json.dumps(manifeste, ensure_ascii=False, indent=2, sort_keys=True))
    print("  provenance consignée dans images/photos/manifeste.json (%d entrées)"
          % len(manifeste))


if __name__ == "__main__":
    main()
