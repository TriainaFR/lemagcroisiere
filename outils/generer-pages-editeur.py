#!/usr/bin/env python3
"""
Génère les pages éditeur : à propos, méthodologie, équipage, partenariats, contact.
Même DA que le reste du site. Les chiffres sont lus dans les fichiers d'articles.

Les informations que seul Lucas peut fournir sont balisées [À COMPLÉTER] :
raison sociale, adresse, directeur de publication, hébergeur, e-mails.
Chercher « À COMPLÉTER » dans les pages générées pour les repérer.

USAGE  python3 outils/generer-pages-editeur.py
"""
import os, re, json, html, datetime

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.lemagcroisieres.fr"
TROU = '<mark class="todo">[À COMPLÉTER]</mark>'
# Une seule adresse, au domaine du média : aucune adresse Triaina ou Yonder
# ne doit apparaître sur le site.
MAIL = "contact@lemagcroisieres.fr"          # à créer ou à rediriger
MAIL_LEGAL = MAIL                            # contact légal / RGPD

# Formulaire de contact — EmailJS, API REST directe, sans SDK.
# Seule la clé publique figure ici : elle est faite pour être exposée.
# La clé privée ne sert qu'aux appels serveur et ne doit JAMAIS être publiée.
EMAILJS_SERVICE = "service_a0wxewc"
EMAILJS_TEMPLATE = "template_4n5km5l"
EMAILJS_PUBLIC = "E7cFvIw50eYZ8er2v"


SCRIPT_FORMULAIRE = """
<script>
/* Formulaire de contact — API REST EmailJS, sans SDK.
   La clé publique ci-dessous est prévue pour être exposée côté navigateur ;
   la clé privée du compte ne doit jamais figurer dans une page. */
(function () {
  var form = document.getElementById('contact-form');
  if (!form) return;
  var etat = document.getElementById('cf-status');
  var bouton = document.getElementById('cf-send');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (form.site_web.value) return;              // piège à robots : un humain le laisse vide

    if (!form.checkValidity()) {                  // messages natifs du navigateur
      form.reportValidity();
      return;
    }

    bouton.disabled = true;
    etat.className = 'form-status';
    etat.textContent = 'Envoi en cours…';

    var nom = form.nom.value.trim();
    var courriel = form.email.value.trim();
    var objet = form.sujet.value;
    var message = form.message.value.trim();

    fetch('https://api.emailjs.com/api/v1.0/email/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        service_id: '%(service)s',
        template_id: '%(template)s',
        user_id: '%(public)s',
        template_params: {
          // plusieurs noms, pour couvrir les variables usuelles du gabarit
          name: nom, from_name: nom,
          email: courriel, from_email: courriel, reply_to: courriel,
          subject: objet, title: objet,
          message: message,
          page: location.href
        }
      })
    }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      etat.className = 'form-status ok';
      etat.textContent = 'Message envoyé — merci. Réponse sous 3 jours ouvrés en moyenne.';
      form.reset();
    }).catch(function () {
      etat.className = 'form-status err';
      etat.innerHTML = "L'envoi a échoué. Réessayez dans quelques minutes, "
        + 'ou écrivez à <a href="mailto:%(mail)s">%(mail)s</a>.';
    }).then(function () {
      bouton.disabled = false;
    });
  });
})();
</script>""" % {"service": EMAILJS_SERVICE, "template": EMAILJS_TEMPLATE,
                 "public": EMAILJS_PUBLIC, "mail": MAIL}


def stats():
    n, zones = 0, set()
    dernier = ""
    for d in sorted(os.listdir(RACINE)):
        f = os.path.join(RACINE, d, "index.html")
        if not os.path.isfile(f):
            continue
        s = open(f, encoding="utf-8").read()
        m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', s)
        if m:
            n += 1
            dernier = max(dernier, m.group(1))
    h = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
    zones = set(re.findall(r'data-zone="(\w+)"', h))
    srcs = 0
    for d in sorted(os.listdir(RACINE)):
        f = os.path.join(RACINE, d, "index.html")
        if os.path.isfile(f):
            srcs += len(re.findall(r'<section class="sources">.*?</section>',
                                   open(f, encoding="utf-8").read(), re.S))
    return n, len(zones), dernier


SHELL = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titre} | Le Mag Croisières</title>
  <meta name="description" content="{meta}">
  <link rel="canonical" href="{base}/{slug}/">
  <meta name="robots" content="{robots}">
  <meta property="og:title" content="{titre} — Le Mag Croisières">
  <meta property="og:description" content="{meta}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{base}/{slug}/">
  <meta property="og:site_name" content="Le Mag Croisières">
  <meta property="og:locale" content="fr_FR">
  <meta property="og:image" content="{base}/images/og-accueil.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Le Mag Croisières — le média qui cartographie la croisière">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{titre} — Le Mag Croisières">
  <meta name="twitter:description" content="{meta}">
  <meta name="twitter:image" content="{base}/images/og-accueil.png">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <link rel="alternate" hreflang="fr" href="{base}/{slug}/">
  <link rel="alternate" hreflang="x-default" href="{base}/{slug}/">
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
    --deep:#12475A;--buoy:#F0561D;--stamp:#BC3F2C;--cyan:#4E96A5;--sand:#D8C9A8;--paper:#F7FAF8;
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

  .head{{padding:22px 0 30px;border-bottom:1.5px solid var(--ink)}}
  .kick{{display:inline-flex;align-items:center;gap:9px;font-family:var(--mono);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--buoy)}}
  .kick .sq{{width:8px;height:8px;background:var(--buoy)}}
  h1{{margin:16px 0 16px;font-size:clamp(32px,5vw,60px);font-weight:700;letter-spacing:-.03em;line-height:1;max-width:18ch}}
  .chapo{{font-size:19px;line-height:1.55;color:var(--ink-2);max-width:64ch}}

  .layout{{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:56px;align-items:start;padding:38px 0 70px}}
  @media(max-width:1080px){{.layout{{grid-template-columns:minmax(0,1fr);gap:34px}}}}

  .body h2{{font-size:clamp(21px,2.4vw,29px);font-weight:700;letter-spacing:-.026em;text-transform:uppercase;line-height:1.06;
    margin:48px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--ink);display:flex;gap:14px;align-items:baseline}}
  .body h2:first-child{{margin-top:0}}
  .body h2 .n{{font-family:var(--mono);font-size:13px;color:var(--buoy);flex:none}}
  .body h3{{font-size:17.5px;font-weight:700;letter-spacing:-.012em;margin:26px 0 8px}}
  .body p{{margin:14px 0;font-size:16.5px;line-height:1.62;max-width:70ch}}
  .body ul,.body ol{{margin:14px 0 14px 22px;max-width:70ch}}
  .body li{{margin:8px 0;font-size:16px;line-height:1.55}}
  .body a{{color:var(--deep);border-bottom:1px solid var(--buoy);text-decoration:none}}
  .body a:hover{{color:var(--buoy)}}
  mark.todo{{background:rgba(240,86,29,.18);color:var(--stamp);font-family:var(--mono);font-size:11px;
    letter-spacing:.1em;padding:3px 8px;border:1px dashed var(--stamp)}}

  .principe{{border:1.5px solid var(--ink);background:var(--paper);box-shadow:4px 4px 0 rgba(12,49,64,.16);
    padding:20px 22px;margin:18px 0}}
  .principe .k{{font-family:var(--mono);font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:var(--buoy);display:block;margin-bottom:8px}}
  .principe p{{margin:0;font-size:15.5px;line-height:1.55}}
  .principe.oui{{border-color:var(--deep)}} .principe.oui .k{{color:var(--deep)}}
  .principe.non{{border-color:var(--stamp)}} .principe.non .k{{color:var(--stamp)}}

  .duo{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:24px 0}}
  @media(max-width:820px){{.duo{{grid-template-columns:1fr}}}}
  .duo>div{{border:1.5px solid var(--ink);background:var(--paper);padding:18px 20px;box-shadow:4px 4px 0 rgba(12,49,64,.16)}}
  .duo h3{{margin:0 0 10px;font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase}}
  .duo .oui{{border-color:var(--deep)}} .duo .oui h3{{color:var(--deep)}}
  .duo .non{{border-color:var(--stamp)}} .duo .non h3{{color:var(--stamp)}}
  .duo ul{{margin:0;padding-left:18px}} .duo li{{font-size:15px;line-height:1.5}}

  .chiffres{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:26px 0}}
  @media(max-width:820px){{.chiffres{{grid-template-columns:1fr 1fr}}}}
  .chiffres div{{border:1.5px solid var(--ink);background:var(--paper);padding:16px 18px;box-shadow:3px 3px 0 rgba(12,49,64,.16)}}
  .chiffres b{{display:block;font-size:30px;font-weight:700;letter-spacing:-.03em;line-height:1;color:var(--deep)}}
  .chiffres span{{display:block;margin-top:7px;font-family:var(--mono);font-size:8.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-2);line-height:1.7}}

  .fiche{{border:1.5px solid var(--ink);background:var(--paper);box-shadow:4px 4px 0 rgba(12,49,64,.16);
    padding:22px 24px;margin:20px 0}}
  .fiche.perso{{display:grid;grid-template-columns:150px minmax(0,1fr);gap:24px;align-items:start}}
  .fiche.perso .portrait{{border:1.5px solid var(--ink);box-shadow:4px 4px 0 rgba(12,49,64,.22);overflow:hidden;position:relative}}
  .fiche.perso .portrait img{{width:100%;height:auto;aspect-ratio:1/1;object-fit:cover;display:block}}
  .carnet{{overflow-x:auto;margin:24px 0;border:1.5px solid var(--ink);background:var(--paper);box-shadow:4px 4px 0 rgba(12,49,64,.16)}}
  .carnet table{{width:100%;border-collapse:collapse;font-size:14px;min-width:560px}}
  .carnet thead{{background:var(--ink);color:var(--chart)}}
  .carnet th{{font-family:var(--mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;font-weight:400;text-align:left;padding:12px 14px}}
  .carnet td{{border-top:1px dashed var(--hair-soft);padding:12px 14px;vertical-align:top}}
  .carnet tbody tr:nth-child(even){{background:var(--chart-2)}}
  .carnet tbody tr:hover{{background:rgba(240,86,29,.07)}}
  .carnet td.zone{{font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--ink-2);white-space:nowrap}}
  .carnet td a{{color:var(--deep);border-bottom:1px solid var(--buoy);text-decoration:none}}
  .carnet td a:hover{{color:var(--buoy)}}
  .specs{{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 0}}
  .specs span{{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;
    border:1px solid var(--hair);padding:5px 10px;color:var(--ink-2)}}
  .fiche.perso .portrait::after{{content:"";position:absolute;inset:0;pointer-events:none;opacity:.16;
    background-image:linear-gradient(rgba(237,243,240,.6) 1px,transparent 1px),linear-gradient(90deg,rgba(237,243,240,.6) 1px,transparent 1px);
    background-size:34px 34px}}
  @media(max-width:640px){{.fiche.perso{{grid-template-columns:1fr}}.fiche.perso .portrait{{max-width:170px}}}}
  .fiche h3{{margin:0 0 4px;font-size:20px}}
  .fiche .role{{font-family:var(--mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--buoy);display:block;margin-bottom:12px}}
  .fiche p{{margin:10px 0 0;font-size:15.5px;line-height:1.55}}
  .fiche dl{{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-family:var(--mono);font-size:9.5px;
    letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);margin-top:14px;padding-top:12px;border-top:1px dashed var(--hair)}}
  .fiche dd{{color:var(--ink);text-align:right}}

  .contact-list{{display:grid;gap:14px;margin:24px 0}}
  .contact-list a,.contact-list div{{display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;
    border:1.5px solid var(--ink);background:var(--paper);padding:18px 20px;box-shadow:4px 4px 0 rgba(12,49,64,.16);
    text-decoration:none;transition:transform .16s,box-shadow .16s}}
  .contact-list a:hover{{transform:translate(2px,2px);box-shadow:2px 2px 0 rgba(12,49,64,.16)}}
  .contact-list .quoi{{font-size:16.5px;font-weight:600}}
  .contact-list .qui{{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--buoy)}}
  .contact-list .note{{flex-basis:100%;font-size:14.5px;line-height:1.5;color:var(--ink-2);margin-top:4px}}

  /* ---------- formulaire de contact ---------- */
  .cform{{border:1.5px solid var(--ink);background:var(--paper);box-shadow:6px 6px 0 rgba(12,49,64,.18);
    padding:26px 28px 28px;margin:24px 0 10px;display:grid;gap:18px}}
  .cform .frow{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
  @media(max-width:640px){{.cform{{padding:20px 18px 22px}}.cform .frow{{grid-template-columns:1fr}}}}
  .cform .fgroup{{display:grid;gap:7px}}
  .cform label{{font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-2)}}
  .cform input,.cform select,.cform textarea{{
    font-family:var(--sans);font-size:15.5px;color:var(--ink);background:var(--chart);
    border:1.5px solid var(--ink);padding:12px 13px;width:100%;border-radius:0;
    -webkit-appearance:none;appearance:none;transition:box-shadow .16s,border-color .16s}}
  .cform select{{background-image:linear-gradient(45deg,transparent 50%,var(--ink) 50%),linear-gradient(135deg,var(--ink) 50%,transparent 50%);
    background-position:calc(100% - 18px) 50%,calc(100% - 13px) 50%;background-size:5px 5px,5px 5px;background-repeat:no-repeat;padding-right:38px}}
  .cform textarea{{resize:vertical;min-height:150px;line-height:1.5}}
  .cform input:focus,.cform select:focus,.cform textarea:focus{{
    outline:none;border-color:var(--buoy);box-shadow:3px 3px 0 rgba(240,86,29,.28)}}
  .cform .hpot{{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}}
  .btn-mail{{display:inline-flex;align-items:center;justify-content:center;gap:10px;justify-self:start;
    font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;cursor:pointer;
    background:var(--buoy);color:#fff;border:1.5px solid var(--ink);padding:15px 24px;
    box-shadow:4px 4px 0 var(--ink);transition:transform .16s,box-shadow .16s,opacity .16s}}
  .btn-mail:hover{{transform:translate(2px,2px);box-shadow:2px 2px 0 var(--ink)}}
  .btn-mail:disabled{{opacity:.55;cursor:progress;transform:none;box-shadow:4px 4px 0 var(--ink)}}
  .btn-mail svg{{width:17px;height:17px;flex:none}}
  .form-status{{margin:0;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;
    color:var(--ink-2);min-height:1.2em}}
  .form-status.ok{{color:var(--deep)}}
  .form-status.err{{color:var(--stamp)}}
  .cform .rgpd{{margin:0;font-size:13px;line-height:1.5;color:var(--ink-2);
    border-top:1px dashed var(--hair);padding-top:14px}}
  .cform .rgpd a{{color:var(--deep);border-bottom:1px solid var(--hair-soft)}}
  .cform .rgpd a:hover{{color:var(--buoy);border-color:var(--buoy)}}

  .toc{{border:1.5px solid var(--ink);background:var(--paper);box-shadow:4px 4px 0 rgba(12,49,64,.16);position:sticky;top:76px}}
  .toc .hd{{background:var(--ink);color:var(--chart);padding:11px 16px;font-family:var(--mono);font-size:9.5px;letter-spacing:.16em;text-transform:uppercase}}
  .toc ol{{list-style:none;padding:8px 0;margin:0}}
  .toc li{{border-bottom:1px dashed var(--hair-soft)}} .toc li:last-child{{border-bottom:none}}
  .toc a{{display:grid;grid-template-columns:30px 1fr;gap:10px;padding:10px 16px;font-size:13.5px;line-height:1.3;text-decoration:none;transition:background .16s}}
  .toc a span{{font-family:var(--mono);font-size:9px;color:var(--buoy)}}
  .toc a:hover{{background:var(--chart-2);color:var(--buoy)}}
  @media(max-width:1080px){{.toc{{position:static}}}}

  .back{{display:inline-flex;align-items:center;gap:9px;margin-top:10px;font-family:var(--mono);font-size:10px;
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
    <span>Le bord — <b>{titre}</b></span>
    <span class="mid">{sur}</span>
    <span>Mis à jour le <b>{maj}</b></span>
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
        <li><a href="../a-propos/">Le bord</a></li>
        <li>{titre}</li>
      </ol>
    </nav>

    <header class="head">
      <span class="kick"><span class="sq"></span>Le bord — {kicker}</span>
      <h1>{h1}</h1>
      <p class="chapo">{chapo}</p>
    </header>

    <div class="layout">
      <div class="body">
{corps}
        <a class="back" href="../">⟵ Retour à la une</a>
      </div>

      <aside>
        <nav class="toc" aria-label="Le bord">
          <div class="hd">Le bord</div>
          <ol>
            <li><a href="../a-propos/"><span>01</span>À propos</a></li>
            <li><a href="../methodologie/"><span>02</span>Méthodologie</a></li>
            <li><a href="../equipage/"><span>03</span>L'équipage</a></li>
            <li><a href="../partenariats/"><span>04</span>Partenariats</a></li>
            <li><a href="../contact/"><span>05</span>Contact</a></li>
          </ol>
        </nav>
      </aside>
    </div>
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
        <a href="../articles/">Tous les articles</a>
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
{scripts}
</body>
</html>
"""


def main():
    n_art, n_zones, dernier = stats()
    # Ces pages sont réécrites à chaque exécution : la date affichée est celle du jour.
    _a = datetime.date.today()
    _mois = {1:'janvier',2:'février',3:'mars',4:'avril',5:'mai',6:'juin',7:'juillet',
             8:'août',9:'septembre',10:'octobre',11:'novembre',12:'décembre'}
    maj = '%d %s %d' % (_a.day, _mois[_a.month], _a.year)
    P = []

    # ---------------------------------------------------------------- À PROPOS
    P.append(dict(slug="a-propos", titre="À propos", kicker="Qui nous sommes",
        h1="À propos du Mag Croisières",
        chapo="Un média indépendant consacré à la croisière maritime et fluviale. On teste, on chiffre, on écrit. Et on dit quand on n'a pas testé.",
        meta="Le Mag Croisières est un média indépendant sur la croisière maritime et fluviale : guides vérifiés, prix réels, aucun contenu sponsorisé.",
        sur="Média indépendant · groupe Triaina", robots="index, follow, max-image-preview:large",
        jsonld={"@type": "AboutPage"},
        corps=f"""        <h2><span class="n">01</span>Ce qu'est ce site</h2>
        <p><strong>Le Mag Croisières</strong> est un média indépendant consacré à la croisière maritime et fluviale. Nous publions des guides de destination, des avis de compagnies et des dossiers pratiques — budget, cabines, frais cachés — destinés à des voyageurs francophones qui préparent une croisière et cherchent des chiffres plutôt que des superlatifs.</p>
        <p>Le site est édité par <strong>Triaina</strong>, société par actions simplifiée basée à Paris, qui publie plusieurs médias indépendants sectoriels — dont <a href="https://www.lejournalduvin.fr/" rel="noopener noreferrer nofollow" target="_blank">Le Journal du Vin</a> et <a href="https://lejournaldesecoles.fr/" rel="noopener noreferrer nofollow" target="_blank">Le Journal des Écoles</a>. Directeur de la publication : Lucas Lecoq-Pellizzon. Les mentions légales complètes sont sur la page <a href="../mentions-legales/">Mentions légales</a>.</p>

        <div class="chiffres">
          <div><b>{n_art}</b><span>articles publiés</span></div>
          <div><b>{n_zones}</b><span>rubriques couvertes</span></div>
          <div><b>2</b><span>compagnies embarquées et notées</span></div>
          <div><b>0 €</b><span>reçu pour influencer une note</span></div>
        </div>

        <h2><span class="n">02</span>Notre parti pris</h2>
        <p>La croisière est un secteur où la communication des compagnies occupe presque tout l'espace. Les brochures annoncent des prix d'appel ; le montant réellement débité est souvent le double. Les « tout compris » ne le sont presque jamais. Notre travail consiste à écrire ce qui manque entre les deux.</p>

        <div class="principe oui">
          <span class="k">Ce qu'on met en avant</span>
          <p>Le prix réel, vol et pourboires compris. Les contraintes concrètes — largeur d'un fjord qui interdit l'accès aux grands navires, quota de 100 passagers à terre en Antarctique, niveau d'eau du Rhin en été. Et ce qui déçoit, quand ça déçoit.</p>
        </div>

        <div class="principe non">
          <span class="k">Ce qu'on refuse</span>
          <p>Aucun article sponsorisé, aucune note négociée, aucun lien vendu. Aucune compagnie n'est consultée avant publication, et aucune ne relit nos textes.</p>
        </div>

        <h2><span class="n">03</span>Comment lire nos articles</h2>
        <p>Chaque article porte un encadré <em>Transparence</em> qui précise d'où viennent les chiffres et ce que nous avons parcouru nous-mêmes. Les sources sont listées en fin d'article et datées. Les tarifs sont des relevés à date : ils bougent, parfois vite.</p>
        <p>Le détail de nos procédures est sur la page <a href="../methodologie/">Méthodologie</a>. Si vous relevez une erreur, elle nous intéresse — voir <a href="../contact/">Contact</a>.</p>

        <h2><span class="n">04</span>Où commencer</h2>
        <p>Les <a href="../rubriques/">{n_zones} rubriques</a> regroupent tous nos articles par sujet. Si c'est votre première croisière, commencez par <a href="../premiere-croisiere-conseils/">Première croisière : tout ce qu'on aurait aimé savoir</a>, puis <a href="../budget-croisiere/">Budget croisière : combien ça coûte vraiment</a>.</p>"""))

    # ------------------------------------------------------------ MÉTHODOLOGIE
    P.append(dict(slug="methodologie", titre="Méthodologie", kicker="Comment on travaille",
        h1="Notre méthodologie",
        chapo="D'où viennent nos chiffres, ce que nous testons vraiment, ce que nous documentons sans l'avoir vécu, et comment nous corrigeons nos erreurs.",
        meta="La méthodologie éditoriale du Mag Croisières : sources des prix, ce que nous testons, choix des visuels, liens sortants et politique de correction.",
        sur="Procédures éditoriales · révision continue", robots="index, follow, max-image-preview:large",
        jsonld={"@type": "WebPage"},
        corps=f"""        <h2><span class="n">01</span>Ce que nous testons, ce que nous documentons</h2>
        <p>Nous distinguons deux registres, et nous l'écrivons toujours dans l'article.</p>
        <div class="duo">
          <div class="oui">
            <h3>Testé</h3>
            <ul>
              <li>Navire embarqué par la rédaction</li>
              <li>Escale parcourue à pied ou en excursion</li>
              <li>Prix payé, ticket à l'appui</li>
            </ul>
          </div>
          <div class="non">
            <h3>Documenté</h3>
            <ul>
              <li>Programme officiel de la compagnie</li>
              <li>Tarif relevé en ligne à une date donnée</li>
              <li>Donnée publique (UNESCO, IAATO, CLIA)</li>
            </ul>
          </div>
        </div>
        <p>Un guide de destination mélange presque toujours les deux. L'encadré <em>Transparence</em> en tête d'article précise lequel s'applique à quoi.</p>

        <h2><span class="n">02</span>Les prix</h2>
        <p>Les tarifs annoncés sont des <strong>prix d'appel relevés sur les programmes officiels</strong>, hors promotion ponctuelle, en occupation double et en cabine intérieure sauf mention contraire. Ils excluent presque toujours le vol : quand c'est le cas, nous le disons et nous ajoutons une ligne « vol » au tableau de budget.</p>
        <p>Un prix de croisière n'est pas une donnée stable. Nous datons chaque article et nous le révisons à chaque saison. Un tarif de plus de six mois doit être vérifié avant réservation.</p>

        <h2><span class="n">03</span>Les sources</h2>
        <p>Chaque article se termine par ses sources, cliquables et nommées. Nous privilégions dans cet ordre : la donnée officielle de l'opérateur, l'organisme de référence du secteur (CLIA, IAATO, UNESCO), puis la presse spécialisée. Tous les liens sortants sont en <code>nofollow</code> : <strong>aucun lien de nos articles n'est vendu</strong>.</p>

        <h2><span class="n">04</span>Les visuels</h2>
        <p>Les photographies proviennent de banques d'images sous licence libre. Chaque visuel est <strong>regardé avant intégration</strong>, pas seulement choisi sur son intitulé : nous vérifions que l'image correspond bien au lieu et au propos. Nous n'illustrons jamais un article consacré à une compagnie par le navire d'une autre, ni une plage des Antilles par une photo prise ailleurs.</p>
        <p>Quand aucune image fidèle n'existe, nous le signalons en légende plutôt que d'en approcher une. C'est le cas des avis compagnies : la mention « photo d'illustration » signifie que le navire visible n'est pas celui dont parle l'article.</p>

        <h2><span class="n">05</span>Indépendance</h2>
        <div class="principe non">
          <span class="k">Règle absolue</span>
          <p>Aucune compagnie n'est contactée avant publication et aucune ne relit nos textes. Nous n'acceptons ni voyage de presse conditionné à un article, ni rémunération liée à une note. Les conditions d'un partenariat éventuel sont publiques : voir <a href="../partenariats/">Partenariats</a>.</p>
        </div>

        <h2><span class="n">06</span>Corrections</h2>
        <p>Nous nous trompons. Quand une erreur factuelle nous est signalée et qu'elle est avérée, nous corrigeons l'article, nous mettons à jour sa date de modification, et nous indiquons la correction en pied de page si elle change le sens du texte.</p>
        <p>Pour signaler une erreur : <a href="../contact/">page Contact</a>. Merci d'indiquer l'article, le passage et, si possible, la source qui contredit le nôtre.</p>

        <h2><span class="n">07</span>Intelligence artificielle</h2>
        <p><strong>Oui, nous utilisons l'intelligence artificielle comme outil d'aide à la rédaction.</strong> Nous préférons l'écrire noir sur blanc plutôt que de laisser la question ouverte.</p>
        <p>Concrètement, elle intervient pendant l'écriture : structuration d'un plan, mise en forme d'un premier jet, reformulation d'un passage. C'est un outil de mise en mots, au même titre qu'un correcteur orthographique l'était il y a vingt ans.</p>

        <div class="principe non">
          <span class="k">Ce qu'elle ne fait pas</span>
          <p>Elle n'embarque pas : aucune expérience de bord décrite sur ce site n'a été produite par une machine. Elle ne décide ni des notes, ni des recommandations, ni de ce qu'on choisit de critiquer. Elle ne remplace pas les sources — les chiffres viennent des programmes officiels et des organismes cités en fin d'article. Et elle ne choisit pas seule les visuels : chaque image est regardée avant intégration.</p>
        </div>

        <p>Chaque article est relu et signé par une personne, qui en assume la responsabilité éditoriale. Une erreur qui passe est la nôtre, pas celle de l'outil — et nous la corrigeons dans les conditions décrites plus haut.</p>"""))

    # ---------------------------------------------------------------- ÉQUIPAGE
    P.append(dict(slug="equipage", titre="L'équipage", kicker="Qui écrit",
        h1="L'équipage",
        chapo="Qui signe les articles que vous lisez, et ce que chacun a réellement embarqué.",
        meta="La rédaction du Mag Croisières : qui écrit, quelles compétences, quelles croisières réellement embarquées.",
        sur="Rédaction · signatures vérifiables", robots="index, follow, max-image-preview:large",
        jsonld={"@type": "AboutPage", "mainEntity": {
            "@type": "Person",
            "name": "Camille Laveran",
            "jobTitle": "Rédactrice",
            "url": f"{BASE}/equipage/",
            "image": f"{BASE}/images/equipe/camille-laveran.jpg",
            "sameAs": ["https://www.linkedin.com/in/camille-laveran/"],
            "worksFor": {"@type": "Organization", "name": "Le Mag Croisières", "url": BASE},
            "knowsAbout": ["Croisière maritime", "Croisière fluviale", "Croisière d'expédition"]}},
        corps=f"""        <h2><span class="n">01</span>La rédaction</h2>
        <p>Toutes les signatures du site correspondent à des personnes réelles. Chaque article indique son auteur, sa date de publication et sa date de dernière révision.</p>

        <div class="fiche perso">
          <div class="portrait">
            <img src="../images/equipe/camille-laveran.jpg" width="640" height="640"
                 alt="Portrait de Camille Laveran, rédactrice du Mag Croisières" loading="eager" decoding="async">
          </div>
          <div>
            <h3>Camille Laveran</h3>
            <span class="role">Rédactrice</span>
            <p>Camille a une obsession : l'écart entre le prix affiché et le montant réellement débité. Elle l'a mesuré pour la première fois en débarquant d'une Méditerranée réservée 1 200 € avec une facture de bord bien plus lourde — et elle tient depuis un carnet de dépenses sur chaque traversée. Ces relevés sont devenus la matière de nos guides budget et de notre enquête sur les frais cachés.</p>
            <p>Elle a embarqué une douzaine de navires, du paquebot de 4 000 passagers au brise-glace d'expédition, sur cinq compagnies et quatre zones. Elle paie ses croisières : aucun de ses embarquements n'a été offert par un opérateur, et aucune compagnie n'a relu ses textes.</p>
            <p>Sur le reste, elle documente plutôt qu'elle ne raconte, et elle l'écrit. Un guide qui compare six maisons ultra-luxe ne prétend pas les avoir toutes embarquées — la <a href="../methodologie/">méthodologie</a> détaille où passe la frontière.</p>
            <div class="specs">
              <span>Budget &amp; frais réels</span><span>Cabines</span><span>Avis compagnies</span><span>Fluvial</span><span>Expéditions polaires</span>
            </div>
            <dl>
              <dt>Signe</dt><dd>{n_art - 1} articles sur {n_art}</dd>
              <dt>Navires embarqués</dt><dd>12 et plus</dd>
              <dt>LinkedIn</dt><dd><a href="https://www.linkedin.com/in/camille-laveran/" rel="noopener noreferrer nofollow" target="_blank">camille-laveran ↗</a></dd>
            </dl>
          </div>
        </div>

        <div class="fiche">
          <h3>Équipe Le Mag Croisières</h3>
          <span class="role">Rédaction collective</span>
          <p>Certains guides sont écrits à plusieurs mains et signés au nom de la rédaction. C'est le cas du guide Caraïbes.</p>
          <dl>
            <dt>Signe</dt><dd>1 article sur {n_art}</dd>
          </dl>
        </div>

        <h2><span class="n">02</span>Le carnet de bord</h2>
        <p>Ce que Camille a réellement embarqué, et l'article où elle en rend compte. Quand un guide couvre un navire qu'elle n'a pas pris, il le dit.</p>

        <div class="carnet">
          <table>
            <thead>
              <tr><th scope="col">Navire</th><th scope="col">Compagnie</th><th scope="col">Zone</th><th scope="col">Ce qu'elle en a tiré</th></tr>
            </thead>
            <tbody>
              <tr><td><strong>MSC Musica</strong></td><td>MSC</td><td class="zone">Méditerranée</td><td><a href="../msc-croisieres-avis/">Avis MSC Croisières</a></td></tr>
              <tr><td><strong>MSC Orchestra</strong></td><td>MSC</td><td class="zone">Méditerranée</td><td><a href="../msc-croisieres-avis/">Avis MSC Croisières</a></td></tr>
              <tr><td><strong>MSC Bellissima</strong></td><td>MSC</td><td class="zone">Méditerranée</td><td><a href="../frais-caches-croisiere/">Enquête frais cachés</a></td></tr>
              <tr><td><strong>Costa Smeralda</strong></td><td>Costa</td><td class="zone">Médit. · nov. 2025</td><td><a href="../croisiere-pas-cher/">Croisière pas cher</a></td></tr>
              <tr><td><strong>Norwegian Escape</strong></td><td>Norwegian</td><td class="zone">Caraïbes · Miami</td><td><a href="../norwegian-cruise-line-avis/">Avis Norwegian</a></td></tr>
              <tr><td><strong>Norwegian Getaway</strong></td><td>Norwegian</td><td class="zone">Médit. · Barcelone</td><td><a href="../norwegian-cruise-line-avis/">Avis Norwegian</a></td></tr>
              <tr><td><strong>Navire d'expédition, 176 passagers</strong></td><td>—</td><td class="zone">Antarctique · déc. 2023</td><td><a href="../croisiere-expedition/">Guide expédition</a></td></tr>
              <tr><td><strong>15 bateaux fluviaux</strong></td><td>CroisiEurope et autres</td><td class="zone">Rhin · Danube · Rhône · Douro</td><td><a href="../croisiere-fluviale/">Guide fluvial</a></td></tr>
            </tbody>
          </table>
        </div>

        <p>S'y ajoutent les escales parcourues à pied — Oia à Santorin au couchant, Dubrovnik à 8 h avant l'arrivée des autres navires, l'Acropole au lever du soleil — et le premier embarquement, un matin de septembre au terminal MPCT de Marseille, raconté dans <a href="../premiere-croisiere-conseils/">Première croisière</a>.</p>

        <h2><span class="n">03</span>Nos engagements de signature</h2>
        <ul>
          <li>Un article est signé par la personne qui l'a écrit, jamais par une identité d'emprunt.</li>
          <li>Quand un auteur n'a pas embarqué le navire dont il parle, l'article le dit.</li>
          <li>Les liens d'intérêt éventuels d'un rédacteur avec une compagnie sont déclarés en pied d'article.</li>
        </ul>
        <p>Le détail des procédures est sur la page <a href="../methodologie/">Méthodologie</a>.</p>"""))

    # ------------------------------------------------------------ PARTENARIATS
    P.append(dict(slug="partenariats", titre="Partenariats", kicker="Ce qu'on accepte",
        h1="Partenariats",
        chapo="Ce que nous acceptons, ce que nous refusons, et pourquoi la frontière est écrite noir sur blanc.",
        meta="Les conditions de partenariat du Mag Croisières : ce que nous acceptons, ce que nous refusons, et notre politique d'affiliation.",
        sur="Conditions publiques · sans exception", robots="index, follow, max-image-preview:large",
        jsonld={"@type": "WebPage"},
        corps=f"""        <h2><span class="n">01</span>Le principe</h2>
        <p>Un média de recommandation ne vaut que par la confiance qu'on lui accorde. Nos conditions de partenariat sont donc publiques, et elles ne se négocient pas au cas par cas.</p>

        <div class="duo">
          <div class="oui">
            <h3>Ce que nous acceptons</h3>
            <ul>
              <li>L'accès à un navire ou à une escale pour un test, sans contrepartie éditoriale</li>
              <li>La mise à disposition de données officielles, tarifs et fiches techniques</li>
              <li>Des espaces publicitaires identifiés comme tels, distincts des articles</li>
              <li>Des liens d'affiliation, systématiquement signalés au lecteur</li>
            </ul>
          </div>
          <div class="non">
            <h3>Ce que nous refusons</h3>
            <ul>
              <li>L'article sponsorisé présenté comme un article éditorial</li>
              <li>La relecture ou la validation d'un texte par une compagnie</li>
              <li>Toute note, tout classement ou tout lien vendu</li>
              <li>Le voyage de presse conditionné à une publication</li>
              <li>Le retrait d'un passage critique contre contrepartie</li>
            </ul>
          </div>
        </div>

        <h2><span class="n">02</span>Affiliation</h2>
        <!-- À reprendre le jour où un programme d'affiliation est mis en place :
             nature des liens, commission perçue, mention dans chaque article concerné. -->
        <p><strong>Le Mag Croisières n'utilise aucun lien d'affiliation.</strong> Aucun lien sortant du site n'est monétisé, aucune commission n'est perçue sur une réservation, et tous les liens externes sont en <code>nofollow</code>. Nous ne gagnons rien si vous réservez la croisière dont nous parlons.</p>
        <p>Si cela devait changer, trois choses seraient indiquées ici et rappelées dans chaque article concerné : quels liens sont affiliés, quelle commission nous percevons, et le fait que le prix payé par le lecteur reste identique.</p>

        <h2><span class="n">03</span>Publicité</h2>
        <!-- À reprendre le jour où des espaces publicitaires sont ouverts :
             formats, tarifs, audience. -->
        <p><strong>Aucun espace publicitaire n'est commercialisé à ce jour.</strong> Le site ne diffuse ni bannière, ni publirédactionnel, ni contenu sponsorisé, et n'accueille aucune régie.</p>
        <p>Si des formats venaient à être ouverts, ils seraient visuellement distincts du contenu éditorial, porteraient une mention explicite, et n'ouvriraient aucun droit de regard sur nos notes, nos classements ou le calendrier de nos publications.</p>

        <h2><span class="n">04</span>Nous contacter</h2>
        <p>Pour une proposition de partenariat, une demande d'espace publicitaire ou une invitation à bord : voir la page <a href="../contact/">Contact</a>. Les sollicitations reçues n'engagent en rien notre traitement éditorial de la compagnie concernée — et une invitation refusée n'a jamais d'effet sur une note, dans un sens comme dans l'autre.</p>"""))

    # ----------------------------------------------------------------- CONTACT
    P.append(dict(slug="contact", titre="Contact", kicker="Nous écrire",
        h1="Nous écrire",
        chapo="Une erreur à signaler, une précision à apporter, une proposition à faire : le formulaire arrive directement dans la boîte de la rédaction.",
        meta="Contacter Le Mag Croisières : signaler une erreur factuelle, exercer un droit de réponse, proposer un partenariat ou poser une question de lecteur.",
        sur="Réponse sous 3 jours ouvrés en moyenne", robots="index, follow",
        jsonld={"@type": "ContactPage"},
        scripts=SCRIPT_FORMULAIRE,
        corps=f"""        <h2><span class="n">01</span>Le formulaire</h2>

        <p>Choisissez l'objet, écrivez, envoyez : le message part directement à la rédaction. Nous répondons sous <strong>3 jours ouvrés en moyenne</strong>. Si vous préférez votre propre messagerie, écrivez à <a href="mailto:{MAIL}">{MAIL}</a>.</p>

        <form id="contact-form" class="cform" novalidate>
          <div class="frow">
            <div class="fgroup">
              <label for="cf-nom">Votre nom</label>
              <input id="cf-nom" name="nom" type="text" autocomplete="name" required maxlength="80">
            </div>
            <div class="fgroup">
              <label for="cf-email">Votre e-mail</label>
              <input id="cf-email" name="email" type="email" autocomplete="email" required maxlength="120">
            </div>
          </div>
          <div class="fgroup">
            <label for="cf-sujet">Objet du message</label>
            <select id="cf-sujet" name="sujet" required>
              <option value="" selected disabled>Choisir un objet…</option>
              <option>Signaler une erreur factuelle</option>
              <option>Droit de réponse d'une compagnie</option>
              <option>Partenariat, publicité, invitation</option>
              <option>Question de lecteur</option>
              <option>Exercer mes droits sur mes données</option>
              <option>Autre</option>
            </select>
          </div>
          <div class="fgroup">
            <label for="cf-message">Votre message</label>
            <textarea id="cf-message" name="message" rows="7" required maxlength="4000"
              placeholder="Pour une erreur factuelle : indiquez l'article, le passage concerné et, si possible, la source qui contredit la nôtre."></textarea>
          </div>
          <input class="hpot" type="text" name="site_web" tabindex="-1" autocomplete="off" aria-hidden="true">
          <button class="btn-mail" type="submit" id="cf-send">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
              <rect x="2.5" y="5" width="19" height="14" rx="1"/>
              <path d="m2.5 6.5 9.5 7 9.5-7"/>
            </svg>
            Envoyer le message
          </button>
          <p class="form-status" id="cf-status" role="status" aria-live="polite"></p>
          <p class="rgpd">Votre nom, votre adresse et votre message ne servent qu'à vous répondre. L'envoi transite par notre prestataire EmailJS — détail dans la <a href="../politique-de-confidentialite/">politique de confidentialité</a>.</p>
        </form>

        <h2><span class="n">02</span>Ce que nous faisons de votre message</h2>

        <div class="contact-list">
          <div>
            <span class="quoi">Signaler une erreur factuelle</span>
            <span class="qui">le plus utile</span>
            <span class="note">Toute erreur avérée est corrigée et la date de modification de l'article mise à jour. Indiquez l'article, le passage et la source qui contredit la nôtre.</span>
          </div>
          <div>
            <span class="quoi">Droit de réponse d'une compagnie</span>
            <span class="qui">publié tel quel</span>
            <span class="note">Nous publions les réponses argumentées des opérateurs cités, sans les faire précéder ni suivre d'un commentaire de la rédaction.</span>
          </div>
          <div>
            <span class="quoi">Partenariats, publicité, invitations</span>
            <span class="qui">conditions publiques</span>
            <span class="note">Nos règles sont écrites noir sur blanc : voir <a href="../partenariats/">Partenariats</a>. Merci de les avoir lues avant d'écrire.</span>
          </div>
          <div>
            <span class="quoi">Questions de lecteurs</span>
            <span class="qui">pas de conseil personnalisé</span>
            <span class="note">Nous ne faisons ni conseil sur mesure ni réservation. En revanche, une question qui revient souvent devient souvent un article.</span>
          </div>
        </div>

        <h2><span class="n">03</span>Qui édite ce site</h2>
        <p>Le détail complet — éditeur, directeur de la publication, hébergeur, propriété intellectuelle — est sur la page <a href="../mentions-legales/">Mentions légales</a>. Le traitement de vos données est décrit dans la <a href="../politique-de-confidentialite/">politique de confidentialité</a>.</p>"""))

    # -------------------------------------------------------- MENTIONS LÉGALES
    P.append(dict(slug="mentions-legales", titre="Mentions légales", kicker="Informations légales",
        h1="Mentions légales",
        chapo="Qui édite ce site, qui le dirige, qui l'héberge. Informations obligatoires au titre de la loi pour la confiance dans l'économie numérique.",
        meta="Mentions légales de lemagcroisieres.fr : éditeur, directeur de la publication, hébergeur, propriété intellectuelle et contact.",
        sur="Informations obligatoires — LCEN", robots="index, follow",
        jsonld={"@type": "WebPage"},
        corps=f"""        <h2 id="mentions"><span class="n">01</span>Éditeur du site</h2>

        <div class="fiche">
          <h3>Triaina</h3>
          <dl>
            <dt>Forme juridique</dt><dd>Société par actions simplifiée (SAS)</dd>
            <dt>Capital social</dt><dd>1 000 €</dd>
            <dt>Siège social</dt><dd>60 rue François I<sup>er</sup>, 75008 Paris, France</dd>
            <dt>RCS</dt><dd>999 402 654 R.C.S. Paris</dd>
            <dt>SIRET</dt><dd>999 402 654 00019</dd>
            <dt>TVA intracommunautaire</dt><dd>FR54999402654</dd>
            <dt>Code APE</dt><dd>70.22Z</dd>
            <dt>Directeur de la publication</dt><dd>Lucas Lecoq-Pellizzon, président</dd>
            <dt>Téléphone</dt><dd>06 14 91 62 95</dd>
            <dt>Contact</dt><dd><a href="mailto:{MAIL}">{MAIL}</a></dd>
          </dl>
        </div>

        <p>Pour toute question, la voie la plus rapide reste le <a href="../contact/">formulaire de contact</a>.</p>

        <h2><span class="n">02</span>Hébergement</h2>

        <div class="fiche">
          <h3>Hébergeur et diffusion</h3>
          <dl>
            <dt>Hébergeur</dt><dd>Railway Corp.</dd>
            <dt>Adresse</dt><dd>548 Market Street PMB 68956, San Francisco, CA 94104, États-Unis</dd>
            <dt>Diffusion (CDN)</dt><dd>Cloudflare, Inc.</dd>
            <dt>Adresse</dt><dd>101 Townsend Street, San Francisco, CA 94107, États-Unis</dd>
          </dl>
        </div>

        <h2><span class="n">03</span>Propriété intellectuelle</h2>
        <p>Les textes publiés sur lemagcroisieres.fr sont la propriété de Triaina. Toute reproduction intégrale est soumise à autorisation ; une citation courte reste possible sous réserve d'attribution et d'un lien vers l'article d'origine.</p>
        <p>Les photographies sont issues de banques d'images sous licence libre (Unsplash) et restent la propriété de leurs auteurs. Elles sont hébergées sur nos serveurs ; la provenance de chaque fichier est consignée dans <code>images/photos/manifeste.json</code>.</p>

        <h2><span class="n">04</span>Signaler un contenu</h2>
        <p>Une erreur factuelle, un contenu que vous estimez illicite, une demande de retrait : écrivez par le <a href="../contact/">formulaire</a> en choisissant l'objet correspondant. Nous accusons réception et traitons la demande sous 3 jours ouvrés en moyenne.</p>
        <p>Notre méthode de travail et nos règles de correction sont publiques : voir <a href="../methodologie/">Méthodologie</a>.</p>"""))

    # ---------------------------------------------- POLITIQUE DE CONFIDENTIALITÉ
    P.append(dict(slug="politique-de-confidentialite", titre="Politique de confidentialité",
        kicker="Vos données", h1="Politique de confidentialité",
        chapo="Ce site ne dépose aucun cookie de suivi. Les seules données que nous traitons sont celles que vous nous envoyez volontairement.",
        meta="Politique de confidentialité de lemagcroisieres.fr : aucune donnée de navigation collectée, traitement du formulaire de contact, durée de conservation et exercice de vos droits.",
        sur="Aucun cookie de suivi, aucun traceur publicitaire", robots="index, follow",
        jsonld={"@type": "WebPage"},
        corps=f"""        <h2><span class="n">01</span>Ce que nous ne faisons pas</h2>

        <div class="principe oui">
          <span class="k">Navigation</span>
          <p>Le Mag Croisières ne dépose <strong>aucun cookie de suivi</strong> et n'utilise <strong>aucun traceur publicitaire</strong>. Vous pouvez lire l'intégralité du site sans qu'aucune donnée de navigation ne soit collectée à des fins commerciales, et sans bandeau de consentement — puisqu'il n'y a rien à consentir.</p>
        </div>

        <h2><span class="n">02</span>Responsable du traitement</h2>
        <p>Triaina, SAS, 60 rue François I<sup>er</sup>, 75008 Paris — <a href="mailto:{MAIL}">{MAIL}</a>. Coordonnées complètes sur la page <a href="../mentions-legales/">Mentions légales</a>.</p>

        <h2><span class="n">03</span>Le formulaire de contact</h2>
        <p><strong>Données collectées.</strong> Uniquement celles que vous saisissez : votre nom, votre adresse e-mail, l'objet et le contenu de votre message. Aucun champ caché ne collecte autre chose que l'adresse de la page depuis laquelle vous écrivez, pour situer votre demande.</p>
        <p><strong>Finalité et base légale.</strong> Vous répondre. Base légale : l'intérêt légitime à traiter une sollicitation entrante.</p>
        <p><strong>Sous-traitant.</strong> L'envoi transite par <strong>EmailJS</strong> (EmailJS.com, États-Unis), qui achemine le message vers notre boîte sans le conserver au-delà du traitement technique. Ce transfert hors Union européenne est encadré par les clauses contractuelles types de la Commission européenne. Si vous préférez l'éviter, écrivez-nous directement à <a href="mailto:{MAIL}">{MAIL}</a>.</p>
        <p><strong>Durée de conservation.</strong> 36 mois maximum à compter du dernier échange, puis suppression.</p>
        <p><strong>Destinataires.</strong> La seule rédaction du Mag Croisières. Vos données ne sont ni vendues, ni louées, ni transmises à un tiers commercial.</p>

        <h2><span class="n">04</span>Vos droits</h2>
        <p>Vous disposez d'un droit d'accès, de rectification, d'effacement, de limitation et d'opposition sur vos données. Pour l'exercer, passez par le <a href="../contact/">formulaire</a> en choisissant l'objet « Exercer mes droits sur mes données », ou écrivez à <a href="mailto:{MAIL}">{MAIL}</a>. Nous répondons sous un mois.</p>
        <p>En cas de désaccord persistant, vous pouvez saisir la <a href="https://www.cnil.fr/fr/plaintes" rel="noopener noreferrer nofollow" target="_blank">CNIL</a>.</p>

        <h2><span class="n">05</span>Services tiers</h2>
        <p><strong>Polices de caractères.</strong> Les typographies sont chargées depuis Google Fonts, ce qui transmet votre adresse IP à Google. <strong>Images.</strong> Toutes les images sont hébergées sur nos serveurs : aucune requête vers un service tiers.</p>
        <!-- À reprendre le jour où une mesure d'audience est installée. Avec Umami ou
             Plausible, le paragraphe « aucun traceur » reste vrai (ces outils sont sans
             cookie), mais il faudra déclarer ici l'outil, les données agrégées collectées
             et l'absence d'identification individuelle. -->
        <p><strong>Mesure d'audience.</strong> Aucun outil de mesure d'audience n'est installé à ce jour : ni Google Analytics, ni Matomo, ni aucun équivalent. Nous ne savons pas combien de personnes lisent cette page, ni d'où elles viennent. Le jour où une mesure sera mise en place, elle sera décrite ici avant d'être activée.</p>"""))

    for p in P:
        d = os.path.join(RACINE, p["slug"])
        os.makedirs(d, exist_ok=True)
        ld = {"@context": "https://schema.org", **p["jsonld"],
              "name": p["titre"], "url": f"{BASE}/{p['slug']}/", "inLanguage": "fr-FR",
              "description": p["meta"],
              "isPartOf": {"@type": "WebSite", "name": "Le Mag Croisières", "url": BASE},
              "publisher": {"@type": "Organization", "name": "Le Mag Croisières", "url": BASE},
              "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": "Accueil", "item": BASE},
                  {"@type": "ListItem", "position": 2, "name": p["titre"], "item": f"{BASE}/{p['slug']}/"}]}}
        page = SHELL.format(
            base=BASE, slug=p["slug"], titre=p["titre"], kicker=p["kicker"], h1=p["h1"],
            chapo=p["chapo"], meta=html.escape(p["meta"], quote=True), sur=p["sur"],
            robots=p["robots"], corps=p["corps"], scripts=p.get("scripts", ""),
            maj=maj,
            jsonld="\n".join("  " + l for l in json.dumps(ld, ensure_ascii=False, indent=2).splitlines()))
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)
        trous = page.count("À COMPLÉTER")
        print(f"  {p['slug']:16} {trous} champ(s) à compléter")

    print(f"\n{len(P)} pages générées.")


if __name__ == "__main__":
    main()
