#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique les visuels de marque du site : logo carré (schéma Organization) et
image de partage 1200x630 (Open Graph / Twitter Card).

Aucune dépendance : on écrit un PDF à la main, puis `sips` (livré avec macOS)
le convertit en PNG.

USAGE  python3 outils/generer-visuels.py
"""
import io, os, subprocess, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(RACINE, "images")

ENCRE = (0.047, 0.192, 0.251)      # --ink   #0C3140
PROFOND = (0.071, 0.278, 0.353)    # --deep  #12475A
BOUEE = (0.941, 0.337, 0.114)      # --buoy  #F0561D
CRAIE = (0.929, 0.953, 0.941)      # --chart #EDF3F0
TRAME = (0.078, 0.235, 0.298)      # lignes de la trame, à peine plus claires

# Largeurs Helvetica-Bold (unités /1000), suffisantes pour nos capitales.
LARGEURS = {" ": 278, "-": 333, "·": 278, ",": 278, ".": 278, ":": 333, "'": 238}
for c, w in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                [722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833,
                 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611]):
    LARGEURS[c] = w
for accent, base in (("È", "E"), ("É", "E"), ("Ê", "E"), ("À", "A"), ("Ô", "O"), ("Î", "I")):
    LARGEURS[accent] = LARGEURS[base]

# Table WinAnsi pour les rares accents que l'on emploie.
WINANSI = {"È": 0xC8, "É": 0xC9, "Ê": 0xCA, "À": 0xC0, "Ô": 0xD4, "Î": 0xCE}


def largeur(texte, corps, interlettre=0.0):
    """Largeur d'une ligne en points."""
    n = sum(LARGEURS.get(c, 600) for c in texte) / 1000.0 * corps
    return n + max(0, len(texte) - 1) * interlettre


def echapper(texte):
    """Chaîne PDF : parenthèses échappées, accents en WinAnsi."""
    out = bytearray()
    for c in texte:
        if c in WINANSI:
            out.append(WINANSI[c])
        elif c in "()\\":
            out += b"\\" + c.encode("latin-1")
        else:
            out += c.encode("latin-1", "replace")
    return bytes(out)


def ligne(texte, police, corps, y, largeur_page, couleur, interlettre=0.0):
    """Une ligne de texte centrée horizontalement."""
    x = (largeur_page - largeur(texte, corps, interlettre)) / 2
    return (b"%.3f %.3f %.3f rg BT /%s %g Tf %g Tc %.2f %.2f Td ("
            % (couleur + (police, corps, interlettre, x, y))
            + echapper(texte) + b") Tj ET\n")


def ecrire_pdf(chemin, l, h, contenu):
    polices = {b"F1": b"/Helvetica-Bold", b"F2": b"/Helvetica-BoldOblique",
               b"F3": b"/Courier-Bold"}
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %g %g] /Resources << /Font "
        b"<< /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> /Contents 4 0 R >>" % (l, h),
        b"<< /Length %d >>\nstream\n" % len(contenu) + contenu + b"\nendstream",
    ]
    for nom in (b"F1", b"F2", b"F3"):
        objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont %s /Encoding "
                    b"/WinAnsiEncoding >>" % polices[nom])

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    positions = []
    for i, o in enumerate(objs, 1):
        positions.append(out.tell())
        out.write(b"%d 0 obj\n" % i + o + b"\nendobj\n")
    debut_xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for p in positions:
        out.write(b"%010d 00000 n \n" % p)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
              % (len(objs) + 1, debut_xref))
    open(chemin, "wb").write(out.getvalue())


def trame(l, h, pas):
    """Quadrillage discret, comme le fond du site."""
    c = b"%.3f %.3f %.3f RG 1 w\n" % TRAME
    x = pas
    while x < l:
        c += b"%g 0 m %g %g l S\n" % (x, x, h)
        x += pas
    y = pas
    while y < h:
        c += b"0 %g m %g %g l S\n" % (y, l, y)
        y += pas
    return c


def png(nom, l, h, contenu, largeur_finale=None):
    pdf = os.path.join(IMAGES, nom + ".pdf")
    cible = os.path.join(IMAGES, nom + ".png")
    ecrire_pdf(pdf, l, h, contenu)
    cmd = ["sips", "-s", "format", "png", pdf, "--out", cible]
    if largeur_finale:
        cmd = ["sips", "-s", "format", "png", "-Z", str(largeur_finale), pdf, "--out", cible]
    r = subprocess.run(cmd, capture_output=True)
    os.remove(pdf)
    if r.returncode:
        sys.exit("sips a échoué sur %s : %s" % (nom, r.stderr.decode()))
    print("  images/%-18s %d octets" % (nom + ".png", os.path.getsize(cible)))


def main():
    os.makedirs(IMAGES, exist_ok=True)

    # ---- logo carré 600x600, pour le schéma Organization ----
    c = b"%.3f %.3f %.3f rg 0 0 600 600 re f\n" % ENCRE
    c += trame(600, 600, 75)
    c += b"%.3f %.3f %.3f rg 40 40 520 520 re f\n" % ENCRE
    c += b"%.3f %.3f %.3f RG 2 w 40 40 520 520 re S\n" % BOUEE
    c += ligne("LE MAG", b"F1", 88, 330, 600, CRAIE)
    c += ligne("CROISIÈRES", b"F2", 62, 250, 600, BOUEE)
    c += b"%.3f %.3f %.3f RG 1.5 w 220 215 m 380 215 l S\n" % CRAIE
    c += ligne("EST. 2026", b"F3", 15, 178, 600, (0.56, 0.76, 0.74), 3.0)
    png("logo", 600, 600, c)

    # ---- image de partage 1200x630 ----
    c = b"%.3f %.3f %.3f rg 0 0 1200 630 re f\n" % ENCRE
    c += trame(1200, 630, 90)
    c += b"%.3f %.3f %.3f rg 0 0 1200 12 re f\n" % BOUEE
    c += b"%.3f %.3f %.3f rg 0 618 1200 12 re f\n" % PROFOND
    c += ligne("LE MAG", b"F1", 130, 375, 1200, CRAIE)
    c += ligne("CROISIÈRES", b"F2", 104, 250, 1200, BOUEE)
    c += b"%.3f %.3f %.3f RG 1.5 w 380 218 m 820 218 l S\n" % CRAIE
    c += ligne("LE MÉDIA QUI CARTOGRAPHIE LA CROISIÈRE",
               b"F3", 19, 168, 1200, (0.56, 0.76, 0.74), 3.2)
    c += ligne("TESTS À BORD · PALMARÈS · COMPARATIFS · GUIDES",
               b"F3", 14, 118, 1200, (0.42, 0.60, 0.63), 2.4)
    png("og-accueil", 1200, 630, c)

    print("\nVisuels régénérés. Pensez à vider le cache des réseaux sociaux si l'image change.")


if __name__ == "__main__":
    main()
