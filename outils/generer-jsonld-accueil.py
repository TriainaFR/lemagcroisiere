#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Régénère le bloc JSON-LD de la page d'accueil à partir des cartes réelles de la
grille : identité du média, moteur de recherche interne, et liste ordonnée des
articles publiés.

À relancer après chaque publication, comme les autres générateurs — la liste
suit la grille, il n'y a rien à saisir à la main.

USAGE  python3 outils/generer-jsonld-accueil.py
"""
import io, os, re, json, html

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://lemagcroisieres.fr"
ACCUEIL = os.path.join(RACINE, "index.html")

DEBUT = "<!-- JSON-LD accueil — généré par outils/generer-jsonld-accueil.py -->"
FIN = "<!-- fin JSON-LD accueil -->"

CARTE = re.compile(
    r'<article class="pcard[^"]*"[^>]*>\s*<a href="([^"]+)">.*?<h3>(.*?)</h3>\s*'
    r'<p>(.*?)</p>', re.S)

# Les questions de « Avis aux navigateurs » et les lignes du « Relevé des
# compagnies » sont lues dans la page : le balisage ne peut donc pas diverger
# de ce que le lecteur voit — c'est la règle de Google et la nôtre.
QUESTION = re.compile(
    r'<summary>.*?<h3>(.*?)</h3>.*?</summary>\s*<div class="rep">(.*?)</div>', re.S)
LIGNE_RELEVE = re.compile(r'<a class="rrow[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)


def texte(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def date_article(slug):
    """Lit la date de publication dans le JSON-LD de l'article lui-même."""
    chemin = os.path.join(RACINE, slug, "index.html")
    if not os.path.isfile(chemin):
        return None
    s = io.open(chemin, encoding="utf-8").read()
    m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', s)
    return m.group(1) if m else None


def questions(src):
    """Les Q/R visibles de la section « Avis aux navigateurs »."""
    bloc = re.search(r'<section class="avis" id="avis">(.*?)</section>', src, re.S)
    if not bloc:
        return []
    return [{"q": texte(q), "r": texte(r)} for q, r in QUESTION.findall(bloc.group(1))]


def releve(src):
    """Les compagnies notées du « Relevé des compagnies », avec leur note visible."""
    bloc = re.search(r'<section class="releve" id="releve">(.*?)</section>', src, re.S)
    if not bloc:
        return []
    out = []
    for href, corps in LIGNE_RELEVE.findall(bloc.group(1)):
        nom = re.search(r"<h3>(.*?)</h3>", corps, re.S)
        note = re.search(r'<div class="sonde"><b>([\d,]+)</b>', corps)
        obs = re.search(r'<div class="obs">(.*?)</div>', corps, re.S)
        if not (nom and note):
            continue
        out.append({"slug": href.strip("/"), "nom": texte(nom.group(1)),
                    "note": float(note.group(1).replace(",", ".")),
                    "obs": texte(obs.group(1)).strip("«» ") if obs else None})
    return out


def main():
    src = io.open(ACCUEIL, encoding="utf-8").read()
    grille = re.search(r'<div class="grid" id="grid">(.*?)\n    </div>', src, re.S)
    if not grille:
        raise SystemExit("grille introuvable dans index.html")

    articles = []
    for href, titre, chapo in CARTE.findall(grille.group(1)):
        slug = href.strip("/")
        articles.append({"slug": slug, "titre": texte(titre), "chapo": texte(chapo),
                         "date": date_article(slug)})
    if not articles:
        raise SystemExit("aucune carte trouvée dans la grille")

    redactrice = {
        "@type": "Person",
        "@id": f"{BASE}/#camille-laveran",
        "name": "Camille Laveran",
        "jobTitle": "Rédactrice",
        "url": f"{BASE}/equipage/",
        "image": f"{BASE}/images/equipe/camille-laveran.jpg",
        "sameAs": ["https://www.linkedin.com/in/camille-laveran/"],
        "knowsLanguage": "fr-FR",
        "knowsAbout": [
            "Croisière maritime", "Croisière fluviale", "Croisière d'expédition",
            "Compagnies de croisière", "Itinéraires de croisière",
            "Budget de voyage", "Tourisme maritime",
        ],
        "worksFor": {"@id": f"{BASE}/#editeur"},
    }

    editeur = {
        "@type": "NewsMediaOrganization",
        "@id": f"{BASE}/#editeur",
        "name": "Le Mag Croisières",
        # Toutes les graphies sous lesquelles on nous cherche : avec ou sans
        # article, avec ou sans accent, au singulier comme au pluriel. C'est ce
        # qui apprend à un moteur que ces chaînes désignent la même entité.
        "alternateName": [
            "Mag Croisières", "Le Mag Croisière", "Mag Croisière",
            "Le Mag Croisieres", "Mag Croisieres", "LeMagCroisieres",
            "lemagcroisieres.fr", "Le Mag Croisières — le média de la croisière",
        ],
        "url": f"{BASE}/",
        "logo": {"@type": "ImageObject", "url": f"{BASE}/images/logo.png",
                 "width": 600, "height": 600},
        "image": f"{BASE}/images/og-accueil.png",
        "description": "Média indépendant consacré à la croisière maritime et fluviale : "
                       "tests à bord, palmarès des compagnies, comparatifs d'itinéraires "
                       "et guides pratiques.",
        "inLanguage": "fr-FR",
        "foundingDate": "2026",
        "publishingPrinciples": f"{BASE}/methodologie/",
        "ethicsPolicy": f"{BASE}/methodologie/",
        "actionableFeedbackPolicy": f"{BASE}/contact/",
        "diversityPolicy": f"{BASE}/a-propos/",
        "masthead": f"{BASE}/equipage/",
        "knowsLanguage": "fr-FR",
        "knowsAbout": ["Croisière maritime", "Croisière fluviale", "Compagnies de croisière",
                       "Itinéraires de croisière", "Voyage en mer"],
        "parentOrganization": {"@type": "Organization", "name": "Triaina"},
        "sameAs": ["https://www.lejournalduvin.fr/", "https://lejournaldesecoles.fr/"],
        "areaServed": "FR",
        "employee": {"@id": f"{BASE}/#camille-laveran"},
        # Champ du Trust Project : les moteurs de réponse s'en servent pour juger
        # l'indépendance d'un média avant de le citer.
        "ownershipFundingInfo":
            "Le Mag Croisières est un média indépendant édité par Triaina, financé sur "
            "fonds propres. Aucune compagnie de croisière, aucun voyagiste et aucune "
            "agence ne rémunère sa présence, sa note ou son classement. Aucun contenu "
            "n'est sponsorisé, aucun lien sortant n'est monétisé. Les invitations et "
            "voyages de presse, lorsqu'ils sont acceptés, sont signalés dans l'article "
            "et n'engagent aucune contrepartie éditoriale.",
        "contactPoint": [
            {"@type": "ContactPoint", "contactType": "editorial",
             "url": f"{BASE}/contact/", "availableLanguage": "French",
             "email": "contact@lemagcroisieres.fr"},
            {"@type": "ContactPoint", "contactType": "partnerships",
             "url": f"{BASE}/partenariats/", "availableLanguage": "French"},
        ],
        "correctionsPolicy": f"{BASE}/methodologie/",
    }

    site = {
        "@type": "WebSite",
        "@id": f"{BASE}/#site",
        "name": "Le Mag Croisières",
        "alternateName": ["Mag Croisières", "Le Mag Croisière", "Mag Croisière",
                          "Le Mag Croisieres", "lemagcroisieres.fr"],
        "url": f"{BASE}/",
        "inLanguage": "fr-FR",
        "about": {"@id": f"{BASE}/#editeur"},
        "publisher": {"@id": f"{BASE}/#editeur"},
        "copyrightHolder": {"@id": f"{BASE}/#editeur"},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint",
                       "urlTemplate": f"{BASE}/articles/?q={{search_term_string}}"},
            "query-input": "required name=search_term_string",
        },
    }

    accueil = {
        "@type": "CollectionPage",
        "@id": f"{BASE}/#accueil",
        "url": f"{BASE}/",
        "name": "Le Mag Croisières — Le média qui cartographie la croisière",
        "description": "Tests à bord, palmarès des compagnies, comparatifs d'itinéraires "
                       "et guides pratiques. Le média indépendant de la croisière maritime "
                       "et fluviale.",
        "inLanguage": "fr-FR",
        "isPartOf": {"@id": f"{BASE}/#site"},
        "about": {"@id": f"{BASE}/#editeur"},
        "primaryImageOfPage": {"@type": "ImageObject", "url": f"{BASE}/images/og-accueil.png",
                               "width": 1200, "height": 630},
        "mainEntity": {
            "@type": "ItemList",
            "name": "Nos articles publiés",
            "numberOfItems": len(articles),
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "url": f"{BASE}/{a['slug']}/",
                 "item": {k: v for k, v in (
                     ("@type", "Article"),
                     ("@id", f"{BASE}/{a['slug']}/#article"),
                     ("headline", a["titre"]),
                     ("description", a["chapo"]),
                     ("url", f"{BASE}/{a['slug']}/"),
                     ("datePublished", a["date"]),
                     ("inLanguage", "fr-FR"),
                     ("author", {"@type": "Person", "name": "Camille Laveran",
                                 "url": f"{BASE}/equipage/"}),
                     ("publisher", {"@id": f"{BASE}/#editeur"}),
                 ) if v is not None}}
                for i, a in enumerate(articles, 1)],
        },
    }

    noeuds = [editeur, redactrice, site, accueil]

    # ---- la FAQ visible de « Avis aux navigateurs » ----
    qr = questions(src)
    if qr:
        noeuds.append({
            "@type": "FAQPage",
            "@id": f"{BASE}/#avis-aux-navigateurs",
            "name": "Avis aux navigateurs — les questions qu'on nous pose",
            "inLanguage": "fr-FR",
            "isPartOf": {"@id": f"{BASE}/#accueil"},
            "publisher": {"@id": f"{BASE}/#editeur"},
            "mainEntity": [
                {"@type": "Question", "name": x["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": x["r"],
                                    "author": {"@id": f"{BASE}/#editeur"}}}
                for x in qr],
        })

    # ---- le relevé des compagnies, en classement citable ----
    lignes = releve(src)
    if lignes:
        noeuds.append({
            "@type": "ItemList",
            "@id": f"{BASE}/#releve-compagnies",
            "name": "Notre relevé des compagnies de croisière",
            "description": "Les compagnies que nous avons embarquées, avec la note "
                           "issue de notre avis complet. Notes sur 10, non arrondies.",
            "inLanguage": "fr-FR",
            "numberOfItems": len(lignes),
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "isPartOf": {"@id": f"{BASE}/#accueil"},
            "itemListElement": [
                {"@type": "ListItem", "position": i, "url": f"{BASE}/{x['slug']}/",
                 "item": {k: v for k, v in (
                     ("@type", "Review"),
                     ("@id", f"{BASE}/{x['slug']}/#avis"),
                     ("url", f"{BASE}/{x['slug']}/"),
                     ("name", f"Notre avis sur {x['nom']}"),
                     ("itemReviewed", {"@type": "Organization", "name": x["nom"]}),
                     ("reviewRating", {"@type": "Rating", "ratingValue": x["note"],
                                       "bestRating": 10, "worstRating": 0}),
                     ("reviewBody", x["obs"]),
                     ("author", {"@id": f"{BASE}/#camille-laveran"}),
                     ("publisher", {"@id": f"{BASE}/#editeur"}),
                 ) if v is not None}}
                for i, x in enumerate(lignes, 1)],
        })

    graphe = json.dumps({"@context": "https://schema.org", "@graph": noeuds},
                        ensure_ascii=False, indent=2)

    bloc = (DEBUT + '\n<script type="application/ld+json">\n'
            + graphe + "\n</script>\n" + FIN)

    if DEBUT in src and FIN in src:
        src = re.sub(re.escape(DEBUT) + r".*?" + re.escape(FIN), lambda _: bloc, src, flags=re.S)
    else:
        src = src.replace("</head>", bloc + "\n</head>", 1)

    io.open(ACCUEIL, "w", encoding="utf-8").write(src)
    print("JSON-LD accueil régénéré")
    print("  %d nœuds : %s" % (len(noeuds), ", ".join(n["@type"] for n in noeuds)))
    print("  %d articles dans l'ItemList" % len(articles))
    print("  %d questions reprises de « Avis aux navigateurs »" % len(qr))
    print("  %d compagnies notées dans le relevé : %s"
          % (len(lignes), ", ".join("%s %s/10" % (x["nom"], x["note"]) for x in lignes)))


if __name__ == "__main__":
    main()
