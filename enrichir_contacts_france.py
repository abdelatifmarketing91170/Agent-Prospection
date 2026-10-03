"""
Enrichit le CSV national (produit par recherche_entreprises_france.py)
avec un site web et un email de contact.

Important : recherche-entreprises.api.gouv.fr n'expose aucun champ "site
web" (vérifié dans son schéma OpenAPI officiel : aucun champ ne contient
"site", "web" ou "url" dans toute la réponse). Trouver le site de chaque
entreprise nécessite donc une recherche web au cas par cas, faite en amont
et fournie ici via la colonne "site_web" du fichier d'entrée — ce script
ne fait PAS de recherche web lui-même, il se limite au scraping (étapes
2 à 5) : page d'accueil + page mentions légales/contact, extraction
d'email, gestion d'erreurs, export du CSV final.

Scalabilité (pensé pour 1000+ entreprises) :
- Parallélisation raisonnable (MAX_WORKERS threads) : chaque entreprise a
  en pratique un domaine différent, donc traiter plusieurs entreprises en
  même temps ne "bombarde" pas un même site. Pour rester poli malgré tout
  si deux entreprises partagent un domaine (franchise, groupe), un
  throttle PAR DOMAINE impose un délai minimum entre deux requêtes vers
  le même nom de domaine, quel que soit le nombre de threads.
- Reprise sur coupure : chaque email trouvé (ou confirmé absent) est
  sauvegardé immédiatement dans FICHIER_ETAT. Au redémarrage, les SIREN
  déjà traités ne sont pas re-scrapés.
"""

import csv
import json
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

FICHIER_ENTREE = "entreprises_france_avec_sites.csv"
FICHIER_SORTIE = "entreprises_france_pme_3_19_salaries_enrichi.csv"
FICHIER_ETAT = "etat_enrichissement_france.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 10
MAX_WORKERS = 8
DELAI_MIN_PAR_DOMAINE = 2.5  # secondes entre 2 requêtes vers le MÊME domaine

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

# Throttle par domaine, partagé entre threads.
_verrou_domaines = threading.Lock()
_dernier_acces_domaine = {}


def attendre_si_necessaire(url):
    """Impose un délai minimum entre deux requêtes vers le même domaine,
    même si elles viennent de threads différents — c'est le domaine qui
    compte pour la politesse envers un site, pas le nombre global de
    requêtes en cours sur des domaines différents."""
    domaine = urlparse(url).netloc.lower()
    with _verrou_domaines:
        dernier = _dernier_acces_domaine.get(domaine, 0)
        a_attendre = DELAI_MIN_PAR_DOMAINE - (time.monotonic() - dernier)
        _dernier_acces_domaine[domaine] = max(time.monotonic(), dernier) + max(a_attendre, 0)
        attente_programmee = _dernier_acces_domaine[domaine] - time.monotonic()
    if attente_programmee > 0:
        time.sleep(attente_programmee)


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
    """Récupère une page (en respectant le throttle par domaine) ; renvoie
    None en cas d'erreur (site injoignable, timeout, réponse non-2xx...),
    sans jamais lever d'exception."""
    attendre_si_necessaire(url)
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
        html_contact = recuperer_page(lien_contact)
        if html_contact:
            email = extraire_email(html_contact)

    return email


def charger_etat():
    if os.path.exists(FICHIER_ETAT):
        with open(FICHIER_ETAT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def sauvegarder_etat(etat):
    with open(FICHIER_ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False)


def traiter_une_entreprise(siren, site_web):
    return siren, extraire_contact_pour_site(site_web)


def main():
    with open(FICHIER_ENTREE, encoding="utf-8-sig", newline="") as fichier_entree:
        lecteur = csv.DictReader(fichier_entree, delimiter=";")
        lignes = list(lecteur)
        fieldnames = list(lecteur.fieldnames)

    if "site_web" not in fieldnames:
        fieldnames.append("site_web")
    if "email_contact" not in fieldnames:
        fieldnames.append("email_contact")

    etat = charger_etat()
    if etat:
        print(f"Reprise : {len(etat)} entreprises déjà traitées dans {FICHIER_ETAT}.\n")

    a_traiter = [
        (ligne["siren"], (ligne.get("site_web") or "").strip())
        for ligne in lignes
        if (ligne.get("site_web") or "").strip() and ligne["siren"] not in etat
    ]

    nb_termines = 0
    verrou_etat = threading.Lock()

    if a_traiter:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executeur:
            futures = {
                executeur.submit(traiter_une_entreprise, siren, site_web): siren
                for siren, site_web in a_traiter
            }
            for future in as_completed(futures):
                siren, email = future.result()
                with verrou_etat:
                    etat[siren] = email
                    nb_termines += 1
                    if nb_termines % 5 == 0:
                        sauvegarder_etat(etat)
                print(
                    f"[{nb_termines}/{len(a_traiter)}] {siren} "
                    f"email={'oui' if email else '-'}"
                )
        sauvegarder_etat(etat)

    nb_sites = 0
    nb_emails = 0
    for ligne in lignes:
        site_web = (ligne.get("site_web") or "").strip()
        if site_web:
            nb_sites += 1
        email = etat.get(ligne["siren"], "")
        ligne["email_contact"] = email
        if email:
            nb_emails += 1

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
