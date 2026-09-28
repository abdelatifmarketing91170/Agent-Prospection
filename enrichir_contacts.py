"""
Enrichit le CSV d'entreprises (produit par recherche_entreprises_idf.py)
avec un site web et un email de contact.

Important : recherche-entreprises.api.gouv.fr n'expose aucun champ "site
web" (vérifié dans son schéma OpenAPI officiel : aucun champ ne contient
"site", "web" ou "url" dans toute la réponse). Trouver le site de chaque
entreprise nécessite donc une recherche web au cas par cas, faite en amont
et fournie ici via la colonne "site_web" du fichier d'entrée — ce script
ne fait PAS de recherche web lui-même, il se limite au scraping (étapes
2 à 5) : page d'accueil + page mentions légales/contact, extraction
d'email, pause de courtoisie, gestion d'erreurs, export du CSV final.
"""

import csv
import random
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

FICHIER_ENTREE = "entreprises_idf_avec_sites.csv"
FICHIER_SORTIE = "entreprises_idf_pme_3_19_salaries_enrichi.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 10
PAUSE_MIN = 2.0
PAUSE_MAX = 3.0

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Adresses/domaines "techniques" à ignorer : pixels de tracking, CMS,
# polices, exemples de documentation, etc. — jamais un vrai contact.
DOMAINES_EMAIL_A_IGNORER = {
    "sentry.io", "wixpress.com", "example.com", "domain.com",
    "yourdomain.com", "w3.org", "schema.org", "godaddy.com",
    "cloudflare.com", "gstatic.com", "sentry-next.wixpress.com",
    "email.com",
}
EXTENSIONS_IMAGE = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")

MOTS_CLES_CONTACT = ["mentions-legales", "mentions_legales", "mentionslegales", "legal", "contact"]


def email_valide(email):
    email = email.strip().strip(".,;:)")
    domaine = email.split("@")[-1].lower()
    if domaine in DOMAINES_EMAIL_A_IGNORER:
        return False
    if email.lower().endswith(EXTENSIONS_IMAGE):
        return False
    return True


def extraire_email(html):
    """Cherche d'abord un lien mailto:, sinon un email dans le texte visible."""
    soup = BeautifulSoup(html, "html.parser")

    for lien in soup.select('a[href^="mailto:"]'):
        email = lien["href"].split("mailto:", 1)[1].split("?")[0].strip()
        if email and email_valide(email):
            return email

    texte = soup.get_text(" ")
    for match in EMAIL_REGEX.findall(texte):
        if email_valide(match):
            return match

    return ""


def trouver_lien_contact(html, base_url):
    """Cherche un lien vers une page 'mentions légales' ou 'contact'."""
    soup = BeautifulSoup(html, "html.parser")
    for lien in soup.find_all("a", href=True):
        texte = (lien.get_text() or "").strip().lower()
        href = lien["href"].strip().lower()
        if any(mot in texte or mot in href for mot in MOTS_CLES_CONTACT):
            return urljoin(base_url, lien["href"])
    return None


def recuperer_page(url):
    """Récupère une page ; renvoie None en cas d'erreur (site injoignable,
    timeout, réponse non-2xx, etc.), sans jamais lever d'exception."""
    try:
        reponse = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        reponse.raise_for_status()
        return reponse.text
    except requests.RequestException:
        return None


def extraire_contact_pour_site(site_web):
    """Scrape la page d'accueil puis, si besoin, la page mentions
    légales/contact d'un site, et renvoie l'email trouvé (ou "")."""
    if not site_web:
        return ""

    url = site_web if site_web.startswith("http") else f"https://{site_web}"

    html_accueil = recuperer_page(url)
    if html_accueil is None:
        return ""

    email = extraire_email(html_accueil)
    if email:
        return email

    lien_contact = trouver_lien_contact(html_accueil, url)
    if lien_contact and lien_contact != url:
        time.sleep(random.uniform(1.0, 1.5))
        html_contact = recuperer_page(lien_contact)
        if html_contact:
            email = extraire_email(html_contact)

    return email


def main():
    with open(FICHIER_ENTREE, encoding="utf-8-sig", newline="") as fichier_entree:
        lecteur = csv.DictReader(fichier_entree, delimiter=";")
        lignes = list(lecteur)
        fieldnames = list(lecteur.fieldnames)

    if "site_web" not in fieldnames:
        fieldnames.append("site_web")
    if "email_contact" not in fieldnames:
        fieldnames.append("email_contact")

    nb_sites = 0
    nb_emails = 0

    for i, ligne in enumerate(lignes, start=1):
        site_web = (ligne.get("site_web") or "").strip()
        if site_web:
            nb_sites += 1

        email = extraire_contact_pour_site(site_web)
        ligne["email_contact"] = email
        if email:
            nb_emails += 1

        print(
            f"[{i}/{len(lignes)}] {ligne.get('nom', '')[:40]:40s} "
            f"site={'oui' if site_web else '-':3s} email={'oui' if email else '-'}"
        )

        if site_web:
            time.sleep(random.uniform(PAUSE_MIN, PAUSE_MAX))

    with open(FICHIER_SORTIE, "w", newline="", encoding="utf-8-sig") as fichier_sortie:
        writer = csv.DictWriter(fichier_sortie, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(lignes)

    print(
        f"\n{nb_sites}/{len(lignes)} entreprises avec un site web renseigné, "
        f"{nb_emails}/{len(lignes)} avec un email trouvé"
    )
    print(f"Résultat exporté dans {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
