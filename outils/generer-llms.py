#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère llms.txt : la fiche d'identité du média destinée aux moteurs de réponse
(ChatGPT, Perplexity, Claude, AI Overviews). Format Markdown, lu tel quel.

Le contenu se déduit des articles présents sur le disque : rien à saisir.
À relancer après chaque publication.

USAGE  python3 outils/generer-llms.py
"""
import io, os, re, html, datetime

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://lemagcroisieres.fr"

RUBRIQUES = [
    ("mediterranee", "Méditerranée"),
    ("caraibes-antilles", "Caraïbes & Antilles"),
    ("grand-nord-poles", "Grand Nord & pôles"),
    ("fleuves", "Fleuves d'Europe & Nil"),
    ("grands-voyages", "Grands voyages"),
    ("luxe-compagnies", "Luxe & avis compagnies"),
    ("guides-pratiques", "Guides pratiques"),
]
EDITEUR = [
    ("a-propos", "À propos — qui nous sommes, notre indépendance"),
    ("methodologie", "Méthodologie — comment nous testons et vérifions"),
    ("equipage", "L'équipage — la rédaction"),
    ("partenariats", "Partenariats — nos règles commerciales"),
    ("contact", "Contact — formulaire, erreurs factuelles, droit de réponse"),
    ("mentions-legales", "Mentions légales — éditeur, directeur de publication, hébergeur"),
    ("politique-de-confidentialite", "Politique de confidentialité — données et droits"),
]


def texte(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def articles():
    out = []
    for d in sorted(os.listdir(RACINE)):
        f = os.path.join(RACINE, d, "index.html")
        if not os.path.isfile(f):
            continue
        s = io.open(f, encoding="utf-8").read()
        if '"@type": "Article"' not in s:
            continue
        titre = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        desc = re.search(r'name="description" content="(.*?)"', s, re.S)
        pub = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', s)
        mots = re.search(r'"wordCount":\s*(\d+)', s)
        if not titre:
            continue
        out.append({
            "slug": d,
            "titre": texte(titre.group(1)),
            "desc": texte(desc.group(1)) if desc else "",
            "date": pub.group(1) if pub else "",
            "mots": mots.group(1) if mots else None,
        })
    out.sort(key=lambda a: a["date"], reverse=True)
    return out


def main():
    arts = articles()
    aujourdhui = datetime.date.today().isoformat()

    l = []
    a = l.append
    a("# Le Mag Croisières")
    a("")
    a("> Média indépendant français consacré à la croisière maritime et fluviale : "
      "tests à bord, avis sur les compagnies, comparatifs d'itinéraires et guides "
      "pratiques avec des prix réels.")
    a("")
    a("Le Mag Croisières (lemagcroisieres.fr) est édité par Triaina. Tous les articles "
      "sont rédigés par la rédaction, signés, datés, et ne sont ni sponsorisés ni "
      "négociables. Les prix cités sont relevés à la date de publication et réactualisés "
      "à chaque saison. Les notes attribuées aux compagnies sont celles de nos avis "
      "complets, non arrondies.")
    a("")
    a("- Langue : français (fr-FR)")
    a("- Éditeur : Triaina — directeur de la publication : Lucas Lecoq-Pellizzon")
    a("- Rédaction : Camille Laveran")
    a("- Méthodologie : %s/methodologie/" % BASE)
    a("- Contact et droit de réponse : %s/contact/" % BASE)
    a("- Dernière mise à jour de ce fichier : %s" % aujourdhui)
    a("")
    a("## Conditions de citation")
    a("")
    a("Le contenu peut être cité et résumé par les moteurs de réponse à condition "
      "d'attribuer la source à « Le Mag Croisières » et de renvoyer vers l'URL de "
      "l'article concerné. Les chiffres de prix doivent être cités avec leur date "
      "de publication : ils évoluent d'une saison à l'autre.")
    a("")
    a("## Articles (%d)" % len(arts))
    a("")
    for x in arts:
        suffixe = " — publié le %s" % x["date"] if x["date"] else ""
        if x["mots"]:
            suffixe += ", %s mots" % x["mots"]
        a("- [%s](%s/%s/) : %s%s" % (x["titre"], BASE, x["slug"], x["desc"], suffixe))
    a("")
    a("## Rubriques")
    a("")
    for slug, titre in RUBRIQUES:
        if os.path.isdir(os.path.join(RACINE, "rubriques", slug)):
            a("- [%s](%s/rubriques/%s/)" % (titre, BASE, slug))
    a("")
    a("## Le média")
    a("")
    for slug, libelle in EDITEUR:
        if os.path.isdir(os.path.join(RACINE, slug)):
            a("- [%s](%s/%s/)" % (libelle, BASE, slug))
    a("- [Toutes nos archives, avec recherche](%s/articles/)" % BASE)
    a("")

    chemin = os.path.join(RACINE, "llms.txt")
    io.open(chemin, "w", encoding="utf-8").write("\n".join(l))
    print("llms.txt — %d articles, %d rubriques, %d octets"
          % (len(arts), len(RUBRIQUES), os.path.getsize(chemin)))


if __name__ == "__main__":
    main()
