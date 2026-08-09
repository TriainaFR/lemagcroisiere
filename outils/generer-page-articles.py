#!/usr/bin/env python3
"""
Génère articles/index.html : tous les articles du site, avec barre de recherche
instantanée (titre, chapô, rubrique) et filtres par rubrique.

Les cartes sont reprises de la grille de index.html : une seule source à maintenir.
Relancer après chaque publication.

USAGE  python3 outils/generer-page-articles.py
"""
import os, re, json, html

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.lemagcroisieres.fr"
MOIS = {1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
        7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"}

ZONES = [("medit", "Méditerranée"), ("caraibes", "Caraïbes & Antilles"),
         ("nord", "Grand Nord & pôles"), ("fleuves", "Fleuves & Nil"),
         ("monde", "Grands voyages"), ("luxe", "Luxe & compagnies"),
         ("pratique", "Guides pratiques")]


def fr(iso):
    y, m, d = map(int, iso.split("-"))
    return f"{d} {MOIS[m]} {y}"


def cartes():
    h = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
    g = h.split('<div class="grid" id="grid">')[1].split('<div class="loadmore">')[0]
    out = []
    for c in re.findall(r"<article class=\"pcard.*?</article>", g, re.S):
        sl = re.search(r'<a href="([a-z0-9-]+)/"', c)
        z = re.search(r'data-zone="(\w+)"', c)
        if not (sl and z):
            continue
        titre = re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", c, re.S).group(1)).strip()
        chapo = re.sub(r"<[^>]+>", "", re.search(r"<p>(.*?)</p>", c, re.S).group(1)).strip()
        f = os.path.join(RACINE, sl.group(1), "index.html")
        art = open(f, encoding="utf-8").read()
        dp = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', art).group(1)
        carte = c.replace('href="%s/"' % sl.group(1), 'href="../%s/"' % sl.group(1))
        carte = re.sub(r' style="--d:[^"]*"', "", carte)

        # index de recherche : titre, chapô, rubrique, meta description,
        # mots-clés du JSON-LD, entités citées et tous les intertitres
        morceaux = [titre, chapo, dict(ZONES).get(z.group(1), ""), sl.group(1).replace("-", " ")]
        m = re.search(r'name="description" content="(.*?)"', art, re.S)
        if m:
            morceaux.append(html.unescape(m.group(1)))
        m = re.search(r'"keywords":\s*"(.*?)"', art)
        if m:
            morceaux.append(m.group(1))
        morceaux += re.findall(r'"name": "([^"]+)", "sameAs"', art)
        morceaux += [re.sub(r"<[^>]+>", " ", t) for t in
                     re.findall(r"<h2[^>]*>(.*?)</h2>|<h3[^>]*>(.*?)</h3>", art, re.S)
                     for t in t if t]
        idx = " ".join(morceaux).lower()
        idx = re.sub(r"\s+", " ", idx)
        for a, b in zip("àâäéèêëïîôöùûüç", "aaaeeeeiioouuuc"):
            idx = idx.replace(a, b)
        carte = carte.replace("<article class=\"pcard",
                              f'<article data-q="{html.escape(idx, quote=True)}" data-date="{dp}" class="pcard')
        out.append((sl.group(1), dp, titre, chapo, z.group(1), carte))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def main():
    arts = cartes()
    n = len(arts)
    par_zone = {}
    for a in arts:
        par_zone[a[4]] = par_zone.get(a[4], 0) + 1

    liste = [("all", "Tout", n)] + [(z, t, par_zone[z]) for z, t in ZONES if par_zone.get(z)]
    puces = "\n".join(
        f'        <button class="chip{" on" if i == 0 else ""}" type="button" data-filter="{z}">{t} <i>{k}</i></button>'
        for i, (z, t, k) in enumerate(liste))

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Tous nos articles", "url": f"{BASE}/articles/", "inLanguage": "fr-FR",
        "description": f"Les {n} articles du Mag Croisières : guides de destination, avis compagnies et dossiers pratiques, avec recherche.",
        "isPartOf": {"@type": "WebSite", "name": "Le Mag Croisières", "url": BASE},
        "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": "Tous nos articles", "item": f"{BASE}/articles/"}]},
        "mainEntity": {"@type": "ItemList", "numberOfItems": n, "itemListElement": [
            {"@type": "ListItem", "position": i, "url": f"{BASE}/{sl}/", "name": t}
            for i, (sl, d, t, c, z, ca) in enumerate(arts, 1)]},
    }, ensure_ascii=False, indent=2)

    page = GABARIT.format(
        base=BASE, n=n, dernier=fr(arts[0][1]),
        jsonld="\n".join("  " + l for l in jsonld.splitlines()),
        puces=puces, cartes="\n".join("      " + a[5] for a in arts))

    d = os.path.join(RACINE, "articles")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)
    print(f"articles/index.html — {n} articles, recherche + {len(par_zone)} filtres")


GABARIT = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tous nos articles | Le Mag Croisières</title>
  <meta name="description" content="Les {n} articles du Mag Croisières : guides de destination, avis compagnies et dossiers pratiques. Recherche instantanée et filtres par rubrique.">
  <link rel="canonical" href="{base}/articles/">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta property="og:title" content="Tous nos articles — Le Mag Croisières">
  <meta property="og:description" content="Les {n} articles du Mag Croisières, avec recherche instantanée et filtres par rubrique.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{base}/articles/">
  <meta property="og:site_name" content="Le Mag Croisières">
  <meta property="og:locale" content="fr_FR">
  <meta property="og:image" content="{base}/images/og-accueil.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Le Mag Croisières — le média qui cartographie la croisière">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Tous nos articles — Le Mag Croisières">
  <meta name="twitter:description" content="Les {n} articles du Mag Croisières, avec recherche instantanée et filtres par rubrique.">
  <meta name="twitter:image" content="{base}/images/og-accueil.png">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <link rel="alternate" hreflang="fr" href="{base}/articles/">
  <link rel="alternate" hreflang="x-default" href="{base}/articles/">
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

  nav[aria-label="breadcrumb"]{{padding:26px 0 0}}
  nav[aria-label="breadcrumb"] ol{{list-style:none;display:flex;flex-wrap:wrap;gap:8px;
    font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2)}}
  nav[aria-label="breadcrumb"] li::after{{content:"›";margin-left:8px;color:var(--buoy)}}
  nav[aria-label="breadcrumb"] li:last-child::after{{content:""}}
  nav[aria-label="breadcrumb"] a{{color:var(--deep);text-decoration:none;border-bottom:1px solid var(--hair-soft)}}
  nav[aria-label="breadcrumb"] a:hover{{color:var(--buoy);border-color:var(--buoy)}}

  .head{{padding:22px 0 6px}}
  .kick{{display:inline-flex;align-items:center;gap:9px;font-family:var(--mono);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--buoy)}}
  .kick .sq{{width:8px;height:8px;background:var(--buoy)}}
  h1{{margin:16px 0 14px;font-size:clamp(32px,5vw,60px);font-weight:700;letter-spacing:-.03em;line-height:1;max-width:16ch}}
  .chapo{{font-size:19px;line-height:1.55;color:var(--ink-2);max-width:60ch}}

  /* ---------- recherche ---------- */
  .chercher{{position:sticky;top:52px;z-index:120;margin:28px 0 0;padding:16px 0 14px;background:var(--chart)}}
  .champ{{display:flex;align-items:center;gap:0;border:1.5px solid var(--ink);background:var(--paper);
    box-shadow:5px 5px 0 rgba(12,49,64,.18)}}
  .champ .loupe{{padding:0 4px 0 18px;font-family:var(--mono);font-size:15px;color:var(--buoy);flex:none;line-height:1}}
  .champ input{{flex:1;border:none;outline:none;background:transparent;padding:17px 14px;min-width:0;
    font-family:var(--sans);font-size:17px;color:var(--ink)}}
  .champ input::placeholder{{color:var(--ink-2);opacity:.75}}
  .champ .vider{{border:none;background:transparent;cursor:pointer;padding:0 18px;font-family:var(--mono);
    font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2);display:none}}
  .champ .vider:hover{{color:var(--buoy)}}
  .champ.plein .vider{{display:block}}

  .barre{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:14px}}
  .chip{{cursor:pointer;border:1.5px solid var(--ink);background:var(--paper);padding:9px 14px;
    font-family:var(--mono);font-size:9.5px;letter-spacing:.13em;text-transform:uppercase;
    transition:background .16s,color .16s}}
  .chip i{{font-style:normal;color:var(--buoy);margin-left:7px}}
  .chip:hover{{background:var(--chart-2)}}
  .chip.on{{background:var(--ink);color:var(--chart)}}
  .chip.on i{{color:var(--sand)}}
  .compte{{margin-left:auto;font-family:var(--mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2)}}

  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;padding:30px 0 20px}}
  @media(max-width:1000px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
  @media(max-width:660px){{.grid{{grid-template-columns:1fr}}}}
  .pcard{{border:1.5px solid var(--ink);background:var(--paper);box-shadow:5px 5px 0 rgba(12,49,64,.16);
    transition:transform .18s,box-shadow .18s}}
  .pcard.hide{{display:none}}
  .pcard:hover{{transform:translate(-2px,-2px);box-shadow:8px 8px 0 rgba(12,49,64,.24)}}
  .pcard a{{text-decoration:none;display:block;height:100%}}
  .pcard .ph{{position:relative;display:block;border-bottom:1.5px solid var(--ink)}}
  .pcard .ph img{{width:100%;height:auto;aspect-ratio:16/10;object-fit:cover}}
  .pcard .cat{{position:absolute;left:0;bottom:0;background:var(--ink);color:var(--chart);
    font-family:var(--mono);font-size:8.5px;letter-spacing:.16em;text-transform:uppercase;padding:6px 11px}}
  .pcard .note{{position:absolute;right:0;top:0;background:var(--buoy);color:#fff;font-family:var(--mono);font-size:10px;padding:6px 10px}}
  .pcard .txt{{display:block;padding:18px 20px 20px}}
  .pcard h3{{font-size:17.5px;font-weight:700;letter-spacing:-.015em;line-height:1.22;margin-bottom:9px}}
  .pcard p{{font-size:14.5px;line-height:1.5;color:var(--ink-2);margin-bottom:14px}}
  .pcard .m{{display:flex;justify-content:space-between;gap:10px;font-family:var(--mono);font-size:9px;
    letter-spacing:.1em;text-transform:uppercase;color:var(--ink-2);border-top:1px dashed var(--hair-soft);padding-top:11px}}
  .pcard .m b{{color:var(--ink);font-weight:400}}
  mark{{background:rgba(240,86,29,.25);color:inherit;padding:0 2px}}

  .vide{{display:none;border:1.5px dashed var(--hair);background:var(--chart-2);padding:34px 30px;margin:20px 0 40px;text-align:center}}
  .vide.on{{display:block}}
  .vide p{{font-size:17px;line-height:1.6;margin-bottom:14px}}
  .vide button{{cursor:pointer;border:1.5px solid var(--ink);background:var(--paper);padding:11px 17px;
    font-family:var(--mono);font-size:10px;letter-spacing:.13em;text-transform:uppercase;box-shadow:3px 3px 0 var(--ink)}}

  .back{{display:inline-flex;align-items:center;gap:9px;margin:10px 0 60px;font-family:var(--mono);font-size:10px;
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
  @media(prefers-reduced-motion:reduce){{*{{transition-duration:.001ms!important}}}}
</style>
</head>
<body>

<span class="crop tl"></span><span class="crop tr"></span><span class="crop bl"></span><span class="crop br"></span>

<div class="instr">
  <div class="wrap">
    <span>Archives — <b>{n} articles</b></span>
    <span class="mid">Recherche instantanée · filtres par rubrique</span>
    <span>Dernière publication : <b>{dernier}</b></span>
  </div>
</div>

<nav class="routes">
  <div class="wrap">
    <a class="rt-mark" href="../">Le Mag <em>Croisières</em></a>
    <div class="rt-scroll">
      <a class="rt" href="../#dernieres"><i>R-01</i>Dernières</a>
      <a class="rt" href="../rubriques/"><i>R-02</i>Rubriques</a>
      <a class="rt" href="../#zones"><i>R-03</i>Destinations</a>
      <a class="rt" href="../#releve"><i>R-04</i>Palmarès</a>
      <a class="rt" href="../#guides"><i>R-06</i>Guides</a>
    </div>
  </div>
</nav>

<main>
  <div class="wrap">
    <nav aria-label="breadcrumb">
      <ol>
        <li><a href="../">Accueil</a></li>
        <li>Tous nos articles</li>
      </ol>
    </nav>

    <header class="head">
      <span class="kick"><span class="sq"></span>Archives — {n} articles publiés</span>
      <h1>Tous nos articles</h1>
      <p class="chapo">Cherchez par mot-clé — une destination, un navire, une compagnie, un budget — ou filtrez par rubrique.</p>
    </header>

    <div class="chercher">
      <div class="champ" id="champ">
        <span class="loupe" aria-hidden="true">⌕</span>
        <input type="search" id="q" placeholder="Chercher : Antarctique, MSC, cabine, fjord, budget…"
               aria-label="Chercher un article" autocomplete="off">
        <button class="vider" type="button" id="vider">Effacer</button>
      </div>
      <div class="barre">
{puces}
        <span class="compte" id="compte">{n} articles</span>
      </div>
    </div>

    <div class="grid" id="grid">
{cartes}
    </div>

    <div class="vide" id="vide">
      <p>Aucun article ne correspond à cette recherche.</p>
      <button type="button" id="reset">Tout réafficher</button>
    </div>

    <a class="back" href="../">⟵ Retour à la une</a>
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
        <a href="../#dernieres">Dernières publications</a>
        <a href="../rubriques/">Toutes les rubriques</a>
        <a href="../#zones">Destinations</a>
        <a href="../#releve">Palmarès</a>
        <a href="../#guides">Guides</a>
      </div>
      <div class="fcol">
        <h2>Le bord</h2>
        <a href="../a-propos/">À propos</a>
        <a href="../methodologie/">Méthodologie</a>
        <a href="../equipage/">L'équipage</a>
        <a href="../partenariats/">Partenariats</a>
        <a href="../contact/">Contact</a>
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
      <span><a href="../mentions-legales/" style="color:inherit">Mentions légales</a> · <a href="../politique-de-confidentialite/" style="color:inherit">Confidentialité</a></span>
    </div>
  </div>
</footer>

<script>
(function(){{
  var q       = document.getElementById('q'),
      champ   = document.getElementById('champ'),
      vider   = document.getElementById('vider'),
      grid    = document.getElementById('grid'),
      compte  = document.getElementById('compte'),
      vide    = document.getElementById('vide'),
      reset   = document.getElementById('reset'),
      chips   = [].slice.call(document.querySelectorAll('.chip')),
      cartes  = [].slice.call(grid.querySelectorAll('.pcard')),
      zone    = 'all';

  /* mémorise le texte d'origine pour pouvoir surligner puis restaurer */
  cartes.forEach(function(c){{
    var h3 = c.querySelector('h3'), p = c.querySelector('.txt p');
    c._h3 = h3.textContent; c._p = p.textContent;
  }});

  function sansAccent(s){{
    return s.toLowerCase()
      .replace(/[àâä]/g,'a').replace(/[éèêë]/g,'e').replace(/[ïî]/g,'i')
      .replace(/[ôö]/g,'o').replace(/[ùûü]/g,'u').replace(/ç/g,'c');
  }}

  function surligner(el, texte, mots){{
    if(!mots.length){{ el.textContent = texte; return; }}
    var plat = sansAccent(texte), out = '', i = 0;
    var trous = [];
    mots.forEach(function(m){{
      var p = 0;
      while((p = plat.indexOf(m, p)) !== -1){{ trous.push([p, p + m.length]); p += m.length; }}
    }});
    if(!trous.length){{ el.textContent = texte; return; }}
    trous.sort(function(a,b){{ return a[0] - b[0]; }});
    var fusion = [trous[0]];
    for(var k = 1; k < trous.length; k++){{
      var d = fusion[fusion.length - 1];
      if(trous[k][0] <= d[1]) d[1] = Math.max(d[1], trous[k][1]);
      else fusion.push(trous[k]);
    }}
    fusion.forEach(function(t){{
      out += escape_(texte.slice(i, t[0])) + '<mark>' + escape_(texte.slice(t[0], t[1])) + '</mark>';
      i = t[1];
    }});
    out += escape_(texte.slice(i));
    el.innerHTML = out;
  }}
  function escape_(s){{
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }}

  function filtrer(){{
    var brut = q.value.trim();
    var mots = sansAccent(brut).split(/\\s+/).filter(Boolean);
    champ.classList.toggle('plein', brut.length > 0);
    var n = 0;
    cartes.forEach(function(c){{
      var okZone = (zone === 'all') || c.getAttribute('data-zone') === zone;
      var idx = c.getAttribute('data-q');
      var okTexte = mots.every(function(m){{ return idx.indexOf(m) !== -1; }});
      var ok = okZone && okTexte;
      c.classList.toggle('hide', !ok);
      if(ok){{
        n++;
        surligner(c.querySelector('h3'), c._h3, mots);
        surligner(c.querySelector('.txt p'), c._p, mots);
      }}
    }});
    compte.textContent = n === 0 ? 'aucun résultat'
                       : n + (n > 1 ? ' articles' : ' article') + (brut ? (n > 1 ? ' trouvés' : ' trouvé') : '');
    vide.classList.toggle('on', n === 0);
  }}

  q.addEventListener('input', filtrer);
  q.addEventListener('search', filtrer);
  vider.addEventListener('click', function(){{ q.value = ''; q.focus(); filtrer(); }});
  reset.addEventListener('click', function(){{
    q.value = ''; zone = 'all';
    chips.forEach(function(x){{ x.classList.toggle('on', x.getAttribute('data-filter') === 'all'); }});
    filtrer(); q.focus();
  }});
  chips.forEach(function(c){{
    c.addEventListener('click', function(){{
      chips.forEach(function(x){{ x.classList.remove('on'); }});
      c.classList.add('on');
      zone = c.getAttribute('data-filter');
      filtrer();
    }});
  }});

  /* ?q=… dans l'URL, et raccourci « / » pour aller au champ */
  var p = new URLSearchParams(location.search).get('q');
  if(p){{ q.value = p; filtrer(); }}
  document.addEventListener('keydown', function(e){{
    if(e.key === '/' && document.activeElement !== q){{ e.preventDefault(); q.focus(); }}
    if(e.key === 'Escape' && document.activeElement === q){{ q.value = ''; filtrer(); }}
  }});
}})();
</script>

</body>
</html>
"""

if __name__ == "__main__":
    main()
