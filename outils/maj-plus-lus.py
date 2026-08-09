#!/usr/bin/env python3
"""
Met à jour le bloc « Les plus lus » de index.html avec les vraies pages
les plus consultées, lues depuis Umami ou Plausible.

Le site reste 100 % statique : ce script tourne côté machine (ou en cron),
la clé d'API ne part jamais dans le navigateur.

USAGE
  # Umami Cloud (gratuit jusqu'à 100 000 événements/mois)
  export ANALYTICS=umami
  export UMAMI_URL=https://cloud.umami.is
  export UMAMI_SITE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  export UMAMI_TOKEN=api_xxxxxxxxxxxx
  python3 outils/maj-plus-lus.py

  # Plausible
  export ANALYTICS=plausible
  export PLAUSIBLE_SITE=lemagcroisieres.fr
  export PLAUSIBLE_TOKEN=xxxxxxxxxxxx
  python3 outils/maj-plus-lus.py

  # Vérifier sans écrire
  python3 outils/maj-plus-lus.py --dry-run
"""
import os, re, sys, json, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(RACINE, "index.html")
JOURS = 7          # fenêtre « 7 derniers jours » affichée dans le bloc
COMBIEN = 5        # nombre de lignes du palmarès
DRY = "--dry-run" in sys.argv


def _get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def depuis_umami():
    base = os.environ["UMAMI_URL"].rstrip("/")
    site = os.environ["UMAMI_SITE_ID"]
    fin = int(datetime.now(timezone.utc).timestamp() * 1000)
    debut = int((datetime.now(timezone.utc) - timedelta(days=JOURS)).timestamp() * 1000)
    q = urllib.parse.urlencode({"type": "url", "startAt": debut, "endAt": fin})
    data = _get(f"{base}/api/websites/{site}/metrics?{q}",
                {"x-umami-api-key": os.environ["UMAMI_TOKEN"], "Accept": "application/json"})
    return [(d["x"], d["y"]) for d in data]


def depuis_plausible():
    site = os.environ["PLAUSIBLE_SITE"]
    q = urllib.parse.urlencode({
        "site_id": site, "period": f"{JOURS}d",
        "property": "event:page", "metrics": "pageviews", "limit": 50,
    })
    data = _get(f"https://plausible.io/api/v1/stats/breakdown?{q}",
                {"Authorization": "Bearer " + os.environ["PLAUSIBLE_TOKEN"]})
    return [(d["page"], d["pageviews"]) for d in data["results"]]


def slug(chemin):
    """/croisiere-luxe/ ou /croisiere-luxe/index.html -> croisiere-luxe"""
    c = chemin.split("?")[0].strip("/")
    c = c[:-len("index.html")].strip("/") if c.endswith("index.html") else c
    return c


def articles():
    """slug -> (titre court, rubrique), lus directement dans les fichiers."""
    out = {}
    for d in sorted(os.listdir(RACINE)):
        f = os.path.join(RACINE, d, "index.html")
        if not os.path.isfile(f):
            continue
        s = open(f, encoding="utf-8").read()
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        kick = re.search(r'<span class="kick">.*?</span>(.*?)</span>', s, re.S)
        if not h1:
            continue
        titre = re.sub(r"<[^>]+>", "", h1.group(1)).strip()
        if len(titre) > 56:
            titre = titre[:53].rsplit(" ", 1)[0] + "…"
        rub = re.sub(r"<[^>]+>", "", kick.group(1)).split("—")[0].strip() if kick else "Guide"
        out[d] = (titre, rub)
    return out


def main():
    moteur = os.environ.get("ANALYTICS", "").lower()
    if moteur == "umami":
        brut = depuis_umami()
    elif moteur == "plausible":
        brut = depuis_plausible()
    else:
        sys.exit("ANALYTICS doit valoir 'umami' ou 'plausible' — voir l'en-tête du fichier.")

    connus = articles()
    cumul = {}
    for chemin, vues in brut:
        sl = slug(chemin)
        if sl in connus:
            cumul[sl] = cumul.get(sl, 0) + int(vues)

    top = sorted(cumul.items(), key=lambda kv: kv[1], reverse=True)[:COMBIEN]
    if not top:
        sys.exit("Aucune vue enregistrée sur un article connu — rien à écrire.")

    lignes = []
    for i, (sl, vues) in enumerate(top, 1):
        titre, rub = connus[sl]
        lignes.append(
            f'        <a href="{sl}/"><span class="n">{i}</span><span>'
            f"<h3>{titre}</h3>"
            f'<span class="mm">{rub} · {vues:,} lectures</span></span></a>'.replace(",", " ")
        )
    bloc = "\n".join(lignes) + "\n"

    html = open(INDEX, encoding="utf-8").read()
    motif = re.compile(r'(<div class="most-hd">.*?</div>\n)(.*?)(?=\s*</aside>)', re.S)
    if not motif.search(html):
        sys.exit("Bloc « Les plus lus » introuvable dans index.html.")

    print(f"Top {len(top)} sur {JOURS} jours ({moteur}) :")
    for i, (sl, v) in enumerate(top, 1):
        print(f"  {i}. {sl:32} {v:>7} vues")

    if DRY:
        print("\n--dry-run : index.html non modifié.")
        return
    html = motif.sub(lambda m: m.group(1) + bloc, html, count=1)
    open(INDEX, "w", encoding="utf-8").write(html)
    print("\nindex.html mis à jour.")


if __name__ == "__main__":
    main()
