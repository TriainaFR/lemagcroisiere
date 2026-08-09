#!/usr/bin/env python3
"""
Régénère sitemap.xml : accueil + articles + rubriques + pages éditeur.
Les pages en noindex sont exclues automatiquement.

USAGE  python3 outils/generer-sitemap.py
"""
import os, re, datetime, xml.dom.minidom

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://lemagcroisieres.fr"
# Date du jour, calculée à l'exécution : plus de date figée à corriger à la main.
AUJOURDHUI = datetime.date.today().isoformat()
EDITEUR = ["a-propos", "methodologie", "equipage", "partenariats", "contact",
           "mentions-legales", "politique-de-confidentialite"]
INDEX = ["articles"]          # pages d'index à forte priorité


def lire(chemin):
    return open(os.path.join(RACINE, chemin), encoding="utf-8").read()


def indexable(s):
    m = re.search(r'<meta name="robots" content="([^"]*)"', s)
    return not (m and "noindex" in m.group(1))


def main():
    urls = [("", AUJOURDHUI, "1.0", "daily")]
    articles = {}

    for d in sorted(os.listdir(RACINE)):
        f = os.path.join(d, "index.html")
        if not os.path.isfile(os.path.join(RACINE, f)) or d in ("rubriques", "outils"):
            continue
        s = lire(f)
        if not indexable(s):
            continue
        m = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})"', s)
        if m:                       # article
            articles[d] = m.group(1)
            urls.append((d + "/", m.group(1), "0.8", "monthly"))
        elif d in EDITEUR:          # page éditeur
            urls.append((d + "/", AUJOURDHUI, "0.4", "yearly"))
        elif d in INDEX:            # archives
            urls.append((d + "/", AUJOURDHUI, "0.9", "daily"))

    art = sorted([u for u in urls if u[0].rstrip("/") in articles],
                 key=lambda u: u[1], reverse=True)
    edit = [u for u in urls if u[0].rstrip("/") in EDITEUR]
    idx  = [u for u in urls if u[0].rstrip("/") in INDEX]

    rub = []
    rdir = os.path.join(RACINE, "rubriques")
    if os.path.isdir(rdir):
        rub.append(("rubriques/", AUJOURDHUI, "0.7", "weekly"))
        for d in sorted(os.listdir(rdir)):
            f = os.path.join("rubriques", d, "index.html")
            if not os.path.isfile(os.path.join(RACINE, f)):
                continue
            s = lire(f)
            ds = [articles[sl] for sl in set(re.findall(r'href="\.\./\.\./([a-z0-9-]+)/"', s))
                  if sl in articles]
            rub.append((f"rubriques/{d}/", max(ds) if ds else AUJOURDHUI, "0.7", "weekly"))

    final = [urls[0]] + idx + art + rub + edit

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    # Les dates issues du JSON-LD servent au tri ; le lastmod publié est celui du jour.
    for loc, _tri, pr, fr in final:
        o += ["  <url>", f"    <loc>{BASE}/{loc}</loc>", f"    <lastmod>{AUJOURDHUI}</lastmod>",
              f"    <changefreq>{fr}</changefreq>", f"    <priority>{pr}</priority>", "  </url>"]
    o.append("</urlset>")
    chemin = os.path.join(RACINE, "sitemap.xml")
    open(chemin, "w", encoding="utf-8").write("\n".join(o) + "\n")

    xml.dom.minidom.parse(chemin)     # lève si le XML est invalide
    print(f"sitemap.xml — {len(final)} URL")
    print(f"  1 accueil · {len(idx)} archives · {len(art)} articles · {len(rub)} rubriques · {len(edit)} pages éditeur")


if __name__ == "__main__":
    main()
