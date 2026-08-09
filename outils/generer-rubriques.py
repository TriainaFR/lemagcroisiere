#!/usr/bin/env python3
"""
Génère les pages de rubrique de lemagcroisieres.fr dans rubriques/<slug>/.

Chaque page liste tous les articles portant le data-zone correspondant,
avec la DA « Carte Marine » du site et un JSON-LD CollectionPage + ItemList.

Les cartes sont reprises telles quelles depuis la grille de index.html :
un seul endroit à maintenir. Relancer le script après chaque publication.

USAGE
  python3 outils/generer-rubriques.py
"""
import os, re, json, html

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://lemagcroisieres.fr"
MOIS = {1:"janvier",2:"février",3:"mars",4:"avril",5:"mai",6:"juin",
        7:"juillet",8:"août",9:"septembre",10:"octobre",11:"novembre",12:"décembre"}

RUBRIQUES = [
    dict(zone="medit", slug="mediterranee", titre="Méditerranée",
         chapo="Deux bassins, cinq itinéraires testés, les ports incontournables et les prix réels de la zone la plus dense d'Europe.",
         meta="Tous nos articles sur la croisière en Méditerranée : itinéraires 2026, ports incontournables, compagnies et budget réel.",
         coord="43°N — 7°E · AVR→OCT"),
    dict(zone="caraibes", slug="caraibes-antilles", titre="Caraïbes & Antilles",
         chapo="Treize îles couvertes, du nord américain aux Petites Antilles françaises, avec le budget réel depuis la France, vol compris.",
         meta="Tous nos articles sur la croisière aux Caraïbes et aux Antilles : îles, itinéraires 2026, compagnies et budget réel depuis la France.",
         coord="15°N — 61°O · NOV→AVR"),
    dict(zone="nord", slug="grand-nord-poles", titre="Grand Nord & pôles",
         chapo="Fjords classés UNESCO, aurores boréales, Antarctique et Arctique : la navigation la plus exigeante qui soit.",
         meta="Tous nos articles sur les croisières polaires et nordiques : fjords de Norvège, aurores boréales, Antarctique, Arctique et expéditions.",
         coord="69°N — 18°E · MAI→SEPT / DÉC→FÉV"),
    dict(zone="fleuves", slug="fleuves", titre="Fleuves d'Europe & Nil",
         chapo="Rhin, Danube, Douro, Rhône, Seine, Nil : on accoste en centre-ville, jamais en rade.",
         meta="Tous nos articles sur la croisière fluviale : Rhin, Danube, Douro, Rhône, Seine, Nil, compagnies comparées et prix 2026.",
         coord="48°N — 16°E · TOUTE L'ANNÉE"),
    dict(zone="monde", slug="grands-voyages", titre="Grands voyages",
         chapo="Tours du monde et traversées au long cours : ce qu'il faut savoir avant de partir plusieurs mois.",
         meta="Tous nos articles sur les grands voyages en croisière : tour du monde, prix réels, compagnies comparées et checklist de départ.",
         coord="MONDE · DÉPARTS JANVIER"),
    dict(zone="luxe", slug="luxe-compagnies", titre="Luxe & avis compagnies",
         chapo="Les maisons ultra-luxe passées au crible et nos avis complets sur les compagnies que nous avons embarquées.",
         meta="Nos avis compagnies et notre comparatif des croisières de luxe : Silversea, Regent, Ponant, MSC, Norwegian, inclusions et prix réels.",
         coord="MONDE · TOUTE L'ANNÉE"),
    dict(zone="pratique", slug="guides-pratiques", titre="Guides pratiques",
         chapo="Budget, cabine, frais cachés, première fois : les dossiers de référence à lire avant de réserver.",
         meta="Nos guides pratiques de la croisière : budget réel, choix de la cabine, frais cachés, première croisière et astuces pour payer moins cher.",
         coord="AVANT D'EMBARQUER"),
]


def lire_articles():
    """slug -> métadonnées lues dans chaque article."""
    out = {}
    for d in sorted(os.listdir(RACINE)):
        f = os.path.join(RACINE, d, "index.html")
        if not os.path.isfile(f):
            continue
        s = open(f, encoding="utf-8").read()
        dp = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', s)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        de = re.search(r'name="description" content="(.*?)"', s, re.S)
        if not (dp and h1):
            continue
        out[d] = dict(slug=d, date=dp.group(1),
                      titre=re.sub(r"<[^>]+>", "", h1.group(1)).strip(),
                      desc=de.group(1).strip() if de else "")
    return out


def cartes_par_zone():
    """zone -> [(slug, html de la carte)] dans l'ordre de la home."""
    h = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
    g = h.split('<div class="grid" id="grid">')[1].split('<div class="loadmore">')[0]
    par_zone = {}
    for c in re.findall(r"<article class=\"pcard.*?</article>", g, re.S):
        z = re.search(r'data-zone="(\w+)"', c)
        sl = re.search(r'<a href="([a-z0-9-]+)/"', c)
        if not (z and sl):
            continue
        carte = c.replace('href="%s/"' % sl.group(1), 'href="../../%s/"' % sl.group(1))
        carte = re.sub(r' style="--d:[^"]*"', "", carte)
        par_zone.setdefault(z.group(1), []).append((sl.group(1), carte))
    return par_zone


def fr(iso):
    y, m, d = map(int, iso.split("-"))
    return f"{d} {MOIS[m]} {y}"


GABARIT = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titre} — tous nos articles | Le Mag Croisières</title>
  <meta name="description" content="{meta}">
  <link rel="canonical" href="{base}/rubriques/{slug}/">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta property="og:title" content="{titre} — tous nos articles">
  <meta property="og:description" content="{meta}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{base}/rubriques/{slug}/">
  <meta property="og:site_name" content="Le Mag Croisières">
  <meta property="og:locale" content="fr_FR">
  <meta property="og:image" content="{base}/images/og-accueil.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Le Mag Croisières — le média qui cartographie la croisière">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{titre} — tous nos articles">
  <meta name="twitter:description" content="{meta}">
  <meta name="twitter:image" content="{base}/images/og-accueil.png">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <link rel="alternate" hreflang="fr" href="{base}/rubriques/{slug}/">
  <link rel="alternate" hreflang="x-default" href="{base}/rubriques/{slug}/">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:ital,wght@0,400..700;1,400..700&family=Fragment+Mono:ital@0;1&display=swap" rel="stylesheet">

  <script type="application/ld+json">
{jsonld}
  </script>

<style>
  picture{{display:contents}}
  :root{{
    --chart:#EDF3F0;--chart-2:#E4EDE9;--ink:#0C3140;--ink-2:#3D6472;
    --deep:#12475A;--buoy:#F0561D;--cyan:#4E96A5;--sand:#D8C9A8;--paper:#F7FAF8;
    --hair:rgba(12,49,64,.35);--hair-soft:rgba(12,49,64,.16);
    --sans:"Familjen Grotesk",sans-serif;--mono:"Fragment Mono",monospace;
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  html{{scroll-behavior:smooth}}
  body{{background:var(--chart);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased;overflow-x:hidden;
    background-image:linear-gradient(rgba(12,49,64,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(12,49,64,.045) 1px,transparent 1px);
    background-size:130px 130px}}
  a{{color:inherit}} img{{display:block;max-width:100%}}
  .wrap{{max-width:1320px;margin:0 auto;padding-left:44px;padding-right:44px}}
  @media(max-width:760px){{.wrap{{padding-left:20px;padding-right:20px}}}}

  .crop{{position:fixed;width:24px;height:24px;z-index:60;pointer-events:none;opacity:.5}}
  .crop::before,.crop::after{{content:"";position:absolute;background:var(--ink)}}
  .crop::before{{width:100%;height:1px}} .crop::after{{width:1px;height:100%}}
  .crop.tl{{top:8px;left:8px}}.crop.tl::before{{top:0}}.crop.tl::after{{left:0}}
  .crop.tr{{top:8px;right:8px}}.crop.tr::before{{top:0}}.crop.tr::after{{right:0}}
  .crop.bl{{bottom:8px;left:8px}}.crop.bl::before{{bottom:0}}.crop.bl::after{{left:0}}
  .crop.br{{bottom:8px;right:8px}}.crop.br::before{{bottom:0}}.crop.br::after{{right:0}}
  @media(max-width:760px){{.crop{{display:none}}}}

  .instr{{border-bottom:1.5px solid var(--ink);background:var(--chart-2)}}
  .instr .wrap{{display:flex;justify-content:space-between;align-items:center;height:38px;gap:20px;
    font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;color:var(--ink-2);text-transform:uppercase}}
  .instr b{{color:var(--buoy);font-weight:400}}
  @media(max-width:900px){{.instr .mid{{display:none}}}}

  .routes{{position:sticky;top:0;z-index:150;background:rgba(237,243,240,.94);backdrop-filter:blur(10px);
    -webkit-backdrop-filter:blur(10px);border-top:1.5px solid var(--ink);border-bottom:1.5px solid var(--ink)}}
  .routes .wrap{{display:flex;align-items:stretch}}
  .rt-mark{{display:flex;align-items:center;font-weight:700;font-size:15px;letter-spacing:-.02em;text-transform:uppercase;
    padding-right:20px;margin-right:4px;border-right:1px dashed var(--hair);white-space:nowrap;text-decoration:none}}
  .rt-mark em{{font-style:italic;color:var(--buoy)}}
  .rt-scroll{{display:flex;flex:1;overflow-x:auto;scrollbar-width:none}}
  .rt-scroll::-webkit-scrollbar{{display:none}}
  .routes a.rt{{display:flex;align-items:baseline;gap:8px;padding:14px 20px;white-space:nowrap;text-decoration:none;
    border-right:1px dashed var(--hair);font-size:12.5px;font-weight:600;letter-spacing:.13em;text-transform:uppercase;transition:background .16s,color .16s}}
  .routes a.rt:first-child{{border-left:1px dashed var(--hair)}}
  .routes a.rt i{{font-style:normal;font-family:var(--mono);font-size:9px;color:var(--buoy)}}
  .routes a.rt:hover{{background:var(--ink);color:var(--chart)}}
  .routes a.rt.on{{background:var(--ink);color:var(--chart)}}
  .routes a.rt.on i{{color:var(--sand)}}

  nav[aria-label="breadcrumb"]{{padding:26px 0 0}}
  nav[aria-label="breadcrumb"] ol{{list-style:none;display:flex;flex-wrap:wrap;gap:8px;
    font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2)}}
  nav[aria-label="breadcrumb"] li::after{{content:"›";margin-left:8px;color:var(--buoy)}}
  nav[aria-label="breadcrumb"] li:last-child::after{{content:""}}
  nav[aria-label="breadcrumb"] a{{color:var(--deep);text-decoration:none;border-bottom:1px solid var(--hair-soft)}}
  nav[aria-label="breadcrumb"] a:hover{{color:var(--buoy);border-color:var(--buoy)}}

  .head{{padding:22px 0 10px}}
  .kick{{display:inline-flex;align-items:center;gap:9px;font-family:var(--mono);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--buoy)}}
  .kick .sq{{width:8px;height:8px;background:var(--buoy)}}
  h1{{margin:16px 0 16px;font-size:clamp(32px,5vw,64px);font-weight:700;letter-spacing:-.03em;line-height:1;max-width:18ch}}
  .chapo{{font-size:19px;line-height:1.55;color:var(--ink-2);max-width:62ch}}
  .cartouche-nb{{display:flex;align-items:center;gap:16px;margin:26px 0 0;padding:14px 18px;border:1.5px solid var(--ink);
    background:var(--paper);box-shadow:4px 4px 0 rgba(12,49,64,.16);font-family:var(--mono);font-size:9.5px;
    letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2);flex-wrap:wrap}}
  .cartouche-nb b{{color:var(--buoy);font-weight:400}}

  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;padding:34px 0 60px}}
  @media(max-width:1000px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
  @media(max-width:660px){{.grid{{grid-template-columns:1fr}}}}
  .pcard{{border:1.5px solid var(--ink);background:var(--paper);box-shadow:5px 5px 0 rgba(12,49,64,.16);
    transition:transform .18s,box-shadow .18s}}
  .pcard:hover{{transform:translate(-2px,-2px);box-shadow:8px 8px 0 rgba(12,49,64,.24)}}
  .pcard a{{text-decoration:none;display:block;height:100%}}
  .pcard .ph{{position:relative;display:block;border-bottom:1.5px solid var(--ink)}}
  .pcard .ph img{{width:100%;height:auto;aspect-ratio:16/10;object-fit:cover}}
  .pcard .cat{{position:absolute;left:0;bottom:0;background:var(--ink);color:var(--chart);
    font-family:var(--mono);font-size:8.5px;letter-spacing:.16em;text-transform:uppercase;padding:6px 11px}}
  .pcard .note{{position:absolute;right:0;top:0;background:var(--buoy);color:#fff;
    font-family:var(--mono);font-size:10px;letter-spacing:.1em;padding:6px 10px}}
  .pcard .txt{{display:block;padding:18px 20px 20px}}
  .pcard h3{{font-size:17.5px;font-weight:700;letter-spacing:-.015em;line-height:1.22;margin-bottom:9px}}
  .pcard p{{font-size:14.5px;line-height:1.5;color:var(--ink-2);margin-bottom:14px}}
  .pcard .m{{display:flex;justify-content:space-between;gap:10px;font-family:var(--mono);font-size:9px;
    letter-spacing:.1em;text-transform:uppercase;color:var(--ink-2);border-top:1px dashed var(--hair-soft);padding-top:11px}}
  .pcard .m b{{color:var(--ink);font-weight:400}}

  .autres{{border-top:1.5px solid var(--ink);padding:30px 0 0;margin-bottom:60px}}
  .autres h2{{font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-2);margin-bottom:16px}}
  .rubs{{display:flex;flex-wrap:wrap;gap:10px}}
  .rubs a{{font-family:var(--mono);font-size:10px;letter-spacing:.13em;text-transform:uppercase;text-decoration:none;
    border:1.5px solid var(--ink);background:var(--paper);padding:11px 15px;box-shadow:3px 3px 0 var(--ink);
    transition:transform .16s,box-shadow .16s}}
  .rubs a:hover{{transform:translate(2px,2px);box-shadow:1px 1px 0 var(--ink)}}
  .rubs a i{{font-style:normal;color:var(--buoy);margin-left:7px}}
  .rubs a.on{{background:var(--ink);color:var(--chart)}}

  .back{{display:inline-flex;align-items:center;gap:9px;margin-bottom:60px;font-family:var(--mono);font-size:10px;
    letter-spacing:.14em;text-transform:uppercase;text-decoration:none;border:1.5px solid var(--ink);
    background:var(--paper);padding:12px 18px;box-shadow:3px 3px 0 var(--ink);transition:transform .16s,box-shadow .16s}}
  .back:hover{{transform:translate(2px,2px);box-shadow:1px 1px 0 var(--ink)}}

  footer.site{{background:var(--ink);color:#DFEBE8;padding:60px 0 0}}
  .fgrid{{display:grid;grid-template-columns:1.5fr 1fr 1fr 1.2fr;gap:40px}}
  .fbrand{{font-weight:700;font-size:26px;letter-spacing:-.03em;text-transform:uppercase;line-height:1}}
  .fbrand em{{font-style:italic;color:#FFB48A}}
  .fdesc{{margin-top:13px;font-size:15px;line-height:1.65;color:rgba(223,235,232,.92);max-width:34ch}}
  .fcol h2{{font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:#A9D9D3;margin:0 0 14px}}
  .fcol a{{display:block;font-size:15px;font-weight:500;padding:6px 0;color:#DFEBE8;text-decoration:none;transition:color .15s,transform .15s}}
  .fcol a:hover{{color:#FFB48A;transform:translateX(3px)}}
  .fbot{{margin-top:48px;border-top:1px solid rgba(223,235,232,.35);padding:18px 0 22px;font-family:var(--mono);
    font-size:8.5px;letter-spacing:.13em;text-transform:uppercase;color:rgba(223,235,232,.5)}}
  .fbot .wrap{{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}}
  @media(max-width:920px){{.fgrid{{grid-template-columns:1fr 1fr}}}}
  @media(max-width:560px){{.fgrid{{grid-template-columns:1fr}}}}
  @media(prefers-reduced-motion:reduce){{*{{animation-duration:.001ms!important;transition-duration:.001ms!important}}}}
</style>
</head>
<body>

<span class="crop tl"></span><span class="crop tr"></span><span class="crop bl"></span><span class="crop br"></span>

<div class="instr">
  <div class="wrap">
    <span>Rubrique <b>{titre}</b></span>
    <span class="mid">{coord}</span>
    <span><b>{n}</b> article{s} publié{s}</span>
  </div>
</div>

<nav class="routes">
  <div class="wrap">
    <a class="rt-mark" href="../../">Le Mag <em>Croisières</em></a>
    <div class="rt-scroll">
      <a class="rt" href="../../#dernieres"><i>R-01</i>Dernières</a>
      <a class="rt" href="../../#zones"><i>R-03</i>Destinations</a>
      <a class="rt" href="../../#releve"><i>R-04</i>Palmarès</a>
      <a class="rt" href="../../#fil"><i>R-05</i>Le fil</a>
      <a class="rt" href="../../#guides"><i>R-06</i>Guides</a>
    </div>
  </div>
</nav>

<main>
  <div class="wrap">
    <nav aria-label="breadcrumb">
      <ol>
        <li><a href="../../">Accueil</a></li>
        <li><a href="../">Rubriques</a></li>
        <li>{titre}</li>
      </ol>
    </nav>

    <header class="head">
      <span class="kick"><span class="sq"></span>Rubrique — {coord}</span>
      <h1>{titre}</h1>
      <p class="chapo">{chapo}</p>
      <div class="cartouche-nb">
        <span><b>{n}</b> article{s} dans cette rubrique</span>
        <span>Dernière publication : <b>{derniere}</b></span>
        <span>Tous nos articles sont rédigés et vérifiés par la rédaction</span>
      </div>
    </header>

    <div class="grid">
{cartes}
    </div>

    <section class="autres">
      <h2>Les autres rubriques</h2>
      <div class="rubs">
{liens}
      </div>
    </section>

    <a class="back" href="../../">⟵ Retour à la une</a>
  </div>
</main>

<footer class="site">
  <div class="wrap">
    <div class="fgrid">
      <div>
        <div class="fbrand">Le Mag <br><em>Croisières</em></div>
        <p class="fdesc">Média indépendant. Nous cartographions la croisière : tests en mer, palmarès sondés, guides rectifiés chaque saison.</p>
      </div>
      <div class="fcol">
        <h2>Routes</h2>
        <a href="../../#dernieres">Dernières publications</a>
        <a href="../../#zones">Destinations</a>
        <a href="../../#releve">Palmarès</a>
        <a href="../../#guides">Guides</a>
        <a href="../../#fil">Le fil</a>
      </div>
      <div class="fcol">
        <h2>Le bord</h2>
        <a href="../../a-propos/">À propos</a>
        <a href="../../methodologie/">Méthodologie</a>
        <a href="../../equipage/">L'équipage</a>
        <a href="../../partenariats/">Partenariats</a>
        <a href="../../contact/">Contact</a>
      </div>
      <div class="fcol">
        <h2>Rubriques</h2>
{liens_footer}
      </div>
      <div class="fcol">
        <h2>Le groupe Triaina</h2>
        <a href="https://www.lejournalduvin.fr/" rel="noopener" target="_blank">Le Journal du Vin ↗</a>
        <a href="https://lejournaldesecoles.fr/" rel="noopener" target="_blank">Le Journal des Écoles ↗</a>
      </div>
    </div>
  </div>
  <div class="fbot">
    <div class="wrap">
      <span>© 2026 lemagcroisieres.fr</span>
      <span><a href="../../mentions-legales/" style="color:inherit">Mentions légales</a> · <a href="../../politique-de-confidentialite/" style="color:inherit">Confidentialité</a></span>
    </div>
  </div>
</footer>

</body>
</html>
"""


def main():
    arts = lire_articles()
    par_zone = cartes_par_zone()
    os.makedirs(os.path.join(RACINE, "rubriques"), exist_ok=True)
    recap = []

    for r in RUBRIQUES:
        items = par_zone.get(r["zone"], [])
        slugs = [s for s, _ in items]
        n = len(items)
        if not n:
            print("  (vide, ignorée) :", r["slug"]); continue

        cartes = "\n".join("      " + c for _, c in items)
        derniere = max(arts[s]["date"] for s in slugs if s in arts)

        liens = "\n".join(
            '        <a href="../{sl}/"{on}>{t}<i>{k}</i></a>'.format(
                sl=o["slug"], t=o["titre"], k=len(par_zone.get(o["zone"], [])),
                on=' class="on"' if o["slug"] == r["slug"] else "")
            for o in RUBRIQUES if par_zone.get(o["zone"]))
        liens_footer = "\n".join(
            '        <a href="../{sl}/">{t}</a>'.format(sl=o["slug"], t=o["titre"])
            for o in RUBRIQUES if par_zone.get(o["zone"]))

        jsonld = json.dumps({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": f"{r['titre']} — tous nos articles",
            "description": r["meta"],
            "url": f"{BASE}/rubriques/{r['slug']}/",
            "inLanguage": "fr-FR",
            "isPartOf": {"@type": "WebSite", "name": "Le Mag Croisières", "url": BASE},
            "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Accueil", "item": BASE},
                {"@type": "ListItem", "position": 2, "name": "Rubriques", "item": f"{BASE}/rubriques/"},
                {"@type": "ListItem", "position": 3, "name": r["titre"], "item": f"{BASE}/rubriques/{r['slug']}/"},
            ]},
            "mainEntity": {"@type": "ItemList", "numberOfItems": n,
                "itemListElement": [
                    {"@type": "ListItem", "position": i,
                     "url": f"{BASE}/{s}/",
                     "name": arts[s]["titre"]}
                    for i, s in enumerate(slugs, 1) if s in arts]},
        }, ensure_ascii=False, indent=2)

        page = GABARIT.format(
            base=BASE, slug=r["slug"], titre=r["titre"],
            meta=html.escape(r["meta"], quote=True), chapo=r["chapo"], coord=r["coord"],
            n=n, s="s" if n > 1 else "", derniere=fr(derniere),
            cartes=cartes, liens=liens, liens_footer=liens_footer,
            jsonld="\n".join("  " + l for l in jsonld.splitlines()))

        d = os.path.join(RACINE, "rubriques", r["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)
        recap.append((r["slug"], n))
        print(f"  rubriques/{r['slug']:20} {n} article(s)")

    # ---- page d'index des rubriques ----
    total = sum(n for _, n in recap)
    cartes_hub = []
    for o in RUBRIQUES:
        items = par_zone.get(o["zone"], [])
        if not items:
            continue
        prem = items[0][1]
        img = re.search(r'<img src="([^"]+)" alt="([^"]*)"', prem)
        cartes_hub.append(
            '      <article class="pcard">\n'
            f'        <a href="{o["slug"]}/">\n'
            '          <span class="ph">\n'
            f'            <img src="{img.group(1)}" alt="{img.group(2)}" loading="lazy" decoding="async">\n'
            f'            <span class="cat">{len(items)} article{"s" if len(items) > 1 else ""}</span>\n'
            '          </span>\n'
            '          <span class="txt">\n'
            f'            <h3>{o["titre"]}</h3>\n'
            f'            <p>{o["chapo"]}</p>\n'
            f'            <span class="m"><b>Voir la rubrique</b><span>{o["coord"]}</span></span>\n'
            '          </span>\n'
            '        </a>\n'
            '      </article>')

    n_rub = len(cartes_hub)
    liens = "\n".join(
        '        <a href="{sl}/">{t}<i>{k}</i></a>'.format(
            sl=o["slug"], t=o["titre"], k=len(par_zone.get(o["zone"], [])))
        for o in RUBRIQUES if par_zone.get(o["zone"]))
    liens_footer = "\n".join(
        '        <a href="{sl}/">{t}</a>'.format(sl=o["slug"], t=o["titre"])
        for o in RUBRIQUES if par_zone.get(o["zone"]))

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Toutes nos rubriques", "url": f"{BASE}/rubriques/", "inLanguage": "fr-FR",
        "description": "Les rubriques du Mag Croisières : destinations, fleuves, pôles, luxe, avis compagnies et guides pratiques.",
        "isPartOf": {"@type": "WebSite", "name": "Le Mag Croisières", "url": BASE},
        "mainEntity": {"@type": "ItemList", "numberOfItems": n_rub, "itemListElement": [
            {"@type": "ListItem", "position": i, "name": o["titre"],
             "url": f"{BASE}/rubriques/{o['slug']}/"}
            for i, o in enumerate([x for x in RUBRIQUES if par_zone.get(x["zone"])], 1)]},
    }, ensure_ascii=False, indent=2)

    hub = (GABARIT
           # Le hub vit dans rubriques/, un cran plus haut que les pages de rubrique :
           # tous ses liens relatifs remontent donc d'un niveau de moins.
           .replace('href="../../', 'href="../')
           .replace('href="../{sl}/"', 'href="{sl}/"')
           .replace('<li><a href="../">Rubriques</a></li>\n        <li>{titre}</li>',
                    '<li>Rubriques</li>')
           .format(
               base=BASE, slug="", titre="Toutes nos rubriques",
               meta="Les rubriques du Mag Croisières : Méditerranée, Caraïbes, pôles, fleuves, luxe, avis compagnies et guides pratiques.",
               chapo="Sept rubriques, quinze articles. Chaque rubrique regroupe tous nos guides et avis publiés sur le sujet.",
               coord=f"{total} ARTICLES · {n_rub} RUBRIQUES", n=n_rub, s="s",
               derniere=fr(max(a["date"] for a in arts.values())),
               cartes="\n".join(cartes_hub), liens=liens, liens_footer=liens_footer,
               jsonld="\n".join("  " + l for l in jsonld.splitlines())))
    hub = hub.replace("<title>Toutes nos rubriques — tous nos articles |",
                      "<title>Toutes nos rubriques |")
    hub = hub.replace(f'href="{BASE}/rubriques//"', f'href="{BASE}/rubriques/"')
    hub = hub.replace(f'content="{BASE}/rubriques//"', f'content="{BASE}/rubriques/"')
    hub = hub.replace("Rubrique — ", "").replace("<span>Rubrique <b>Toutes nos rubriques</b></span>",
                                                 "<span>Le Mag <b>Croisières</b></span>")
    hub = hub.replace("article{s} dans cette rubrique", "rubriques au total")
    hub = hub.replace("<b>7</b> rubriques au total", "<b>7</b> rubriques")
    hub = hub.replace("<h2>Les autres rubriques</h2>", "<h2>Accès direct</h2>")
    open(os.path.join(RACINE, "rubriques", "index.html"), "w", encoding="utf-8").write(hub)
    print(f"  rubriques/{'(index)':20} {n_rub} rubriques")

    print(f"\n{len(recap)} rubriques générées, {total} articles référencés.")


if __name__ == "__main__":
    main()
