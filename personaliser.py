"""
Génère des relances personnalisées (sans aucun appel à un modèle) pour les
contacts France déjà relancés une première fois.

Pour chaque contact restant (présent dans emails_france_filtres.json, pas
encore à ce stade de relance) :
1. Salutation : interroge l'API recherche-entreprises.api.gouv.fr pour
   savoir si le dirigeant est une personne physique ; sinon "Bonjour,".
2. Observation : visite la page d'accueil du site et teste, dans l'ordre
   fixe ci-dessous, la première condition qui échoue. Si aucune n'échoue,
   ou si le site est injoignable : pas d'envoi, statut "rien à signaler".
3. Compétence : une phrase de preuve choisie selon des règles fixes
   (boutique en ligne détectée > observation 1/2/4 > observation 3/5).
4. Assemblage dans le squelette Version A, objet "Audit gratuit de présence
   en ligne — {NOM}", 75-100 mots hors signature. Rejet si hors fourchette
   après ajustement, ou si une expression interdite de CLAUDE.md apparaît.

Sort emails_prets.csv (nom, email, objet, corps_html, observation,
competence, statut) et observations_etat.json (pour que la prochaine
relance utilise la 2e observation trouvée, si elle existe).
"""

import csv
import json
import os
import re
import time

import requests

FICHIER_SOURCE = "emails_france_filtres.json"
FICHIER_ENRICHI = "entreprises_france_pme_3_19_salaries_priorisees.csv"
FICHIER_SUIVI = "suivi_france.csv"
FICHIER_RELANCES = "relances_envoyees_france.json"
FICHIER_SORTIE = "emails_prets.csv"
FICHIER_ETAT_OBSERVATIONS = "observations_etat_france.json"

API_RECHERCHE_ENTREPRISES = "https://recherche-entreprises.api.gouv.fr/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 10

MOTS_INTERDITS = [
    "en général",
    "moyenne du secteur",
    "nos clients",
    "nos dossiers",
    "nos campagnes",
    "aucune campagne active",
    "j'ai regardé la présence",
]

SIGNATURE = (
    "Abdelatif Senhaji\n"
    "A.S.Digital — SIREN 979 115 862\n"
    "Pour ne plus recevoir de message, répondez STOP."
)

PROPOSITION_SHOPIFY = "Je vous propose un audit gratuit de votre présence en ligne, avec des pistes pour votre boutique en ligne."
PROPOSITION_REFONTE = "Je vous propose un audit gratuit de votre présence en ligne, avec une piste concrète pour moderniser votre page d'accueil."
PROPOSITION_CONTACT = "Je vous propose un audit gratuit de votre présence en ligne, avec des pistes pour faciliter la prise de contact."
PROPOSITION_CONTACT_COURTE = "Je vous propose un audit gratuit de votre présence en ligne."

COMPETENCE_SHOPIFY = "J'ai créé plusieurs boutiques Shopify et j'ai de l'expérience sur plusieurs comptes TikTok Ads (accroches, visuels, optimisation)."
COMPETENCE_REFONTE = "J'ai refondu la page d'accueil d'un site e-commerce, conçue d'abord pour mobile."
COMPETENCE_ADS = (
    "Sur un projet récent, une campagne Google Ads Search que j'ai mise en place "
    "a dépassé 9 % de CTR, réduit le coût par clic d'environ un tiers, et "
    "transformé un clic sur cinq en appel ou demande d'itinéraire."
)

OBSERVATIONS = {
    "https_absent": "En visitant votre site, j'ai remarqué qu'il s'ouvre sans connexion sécurisée (HTTPS) : les navigateurs affichent alors la mention « Non sécurisé », qui peut décourager des visiteurs.",
    "pas_viewport": "En visitant votre site, j'ai remarqué qu'il ne semble pas adapté à l'affichage sur téléphone, alors que beaucoup de visiteurs consultent un site depuis leur mobile.",
    "pas_tel": "En visitant votre site, j'ai remarqué que votre numéro n'est pas cliquable depuis un mobile : un visiteur doit le recopier pour vous appeler.",
    "copyright_ancien": "En visitant votre site, j'ai remarqué que le pied de page affiche encore « © {annee} » : un détail qui peut laisser penser que le site n'est plus entretenu.",
    "pas_formulaire": "En visitant votre site, je n'ai pas trouvé de formulaire de contact sur la page d'accueil, ce qui limite les façons de vous joindre.",
}

MARQUEURS_BOUTIQUE = ("panier", "/cart", "add-to-cart", "cdn.shopify.com", "woocommerce")

ANNEE_COURANTE = time.localtime().tm_year


def charger_json(chemin, defaut):
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    return defaut


MAX_RELANCES = 4
JOURS_MIN_ENTRE_RELANCES = 4


def charger_restants():
    """Contacts déjà relancés une 1re fois (relances_envoyees_france.json),
    éligibles à la relance suivante : espacement >= 4 jours, < 4 relances
    déjà envoyées, pas désabonné/rebond/pas intéressé/exclu sectoriel."""
    with open(FICHIER_SUIVI, encoding="utf-8-sig", newline="") as f:
        suivi = list(csv.DictReader(f, delimiter=";"))
    statut_par_email = {r["email"].strip().lower(): r["statut"] for r in suivi}

    historique_relances = charger_json(FICHIER_RELANCES, {})

    aujourdhui = time.strftime("%Y-%m-%d")
    aujourdhui_ord = time.mktime(time.strptime(aujourdhui, "%Y-%m-%d"))

    eligibles_emails = []
    for email, dates in historique_relances.items():
        statut = statut_par_email.get(email, "")
        if statut.startswith("exclu") or statut.startswith("en attente") or statut.startswith("rebond") or statut in ("désabonné", "pas intéressé", "échec envoi (adresse invalide)"):
            continue
        if len(dates) >= MAX_RELANCES:
            continue
        derniere_date = max(dates)
        derniere_ord = time.mktime(time.strptime(derniere_date, "%Y-%m-%d"))
        jours_ecoules = (aujourdhui_ord - derniere_ord) / 86400
        if jours_ecoules < JOURS_MIN_ENTRE_RELANCES:
            continue
        eligibles_emails.append(email)

    with open(FICHIER_SOURCE, encoding="utf-8") as f:
        source = json.load(f)
    par_email = {d["email"].strip().lower(): d for d in source}

    with open(FICHIER_ENRICHI, encoding="utf-8-sig", newline="") as f:
        enrichi = list(csv.DictReader(f, delimiter=";"))
    site_par_siren = {r["siren"]: r["site_web"] for r in enrichi if r.get("site_web")}

    resultat = []
    for email in eligibles_emails:
        d = par_email.get(email)
        if not d:
            continue
        site = site_par_siren.get(d["siren"], "")
        resultat.append({"siren": d["siren"], "nom": d["nom"], "email": email, "site_web": site})
    return resultat


def obtenir_dirigeant_personne_physique(siren):
    try:
        reponse = requests.get(
            API_RECHERCHE_ENTREPRISES, params={"q": siren}, headers=HEADERS, timeout=TIMEOUT
        )
        reponse.raise_for_status()
        resultats = reponse.json().get("results", [])
        for entreprise in resultats:
            if entreprise.get("siren") != siren:
                continue
            dirigeants = entreprise.get("dirigeants") or []
            for dirigeant in dirigeants:
                if dirigeant.get("type_dirigeant") == "personne physique" or (
                    dirigeant.get("prenoms") and dirigeant.get("nom")
                ):
                    prenom = (dirigeant.get("prenoms") or "").split(",")[0].strip().title()
                    nom = (dirigeant.get("nom") or "").strip().title()
                    if prenom and nom:
                        return prenom, nom
    except requests.RequestException:
        pass
    return None, None


def generer_salutation(siren):
    prenom, nom = obtenir_dirigeant_personne_physique(siren)
    if prenom and nom:
        return f"Bonjour {prenom} {nom},"
    return "Bonjour,"


def recuperer_page_accueil(url):
    if not url:
        return None
    if not url.startswith("http"):
        url = "https://" + url
    try:
        reponse = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if reponse.status_code >= 400:
            return None
        return reponse.url, reponse.text
    except requests.RequestException:
        return None


def tester_observations(url_finale, html):
    """Retourne la liste ordonnée des clés d'observation qui échouent."""
    echecs = []

    if not url_finale.startswith("https://"):
        echecs.append("https_absent")

    if not re.search(r'<meta[^>]+name=["\']viewport["\']', html, re.IGNORECASE):
        echecs.append("pas_viewport")

    if not re.search(r'href=["\']tel:', html, re.IGNORECASE):
        echecs.append("pas_tel")

    annees_copyright = re.findall(r"©\s*(\d{4})", html)
    if annees_copyright:
        derniere_annee = max(int(a) for a in annees_copyright)
        if ANNEE_COURANTE - derniere_annee > 2:
            echecs.append(("copyright_ancien", derniere_annee))

    if not re.search(r"<form[\s>]", html, re.IGNORECASE):
        echecs.append("pas_formulaire")

    return echecs


COMPLEMENT_AUDIT_DETAILLE = "L'audit couvre votre fiche Google, vos réseaux sociaux et votre site, avec des recommandations classées par priorité."


def choisir_competence(cle_observation, html):
    html_minuscule = html.lower()
    if any(marqueur in html_minuscule for marqueur in MARQUEURS_BOUTIQUE):
        return COMPETENCE_SHOPIFY, PROPOSITION_SHOPIFY, True

    if cle_observation in ("https_absent", "pas_viewport", "copyright_ancien"):
        return COMPETENCE_REFONTE, PROPOSITION_REFONTE, True

    return COMPETENCE_ADS, PROPOSITION_CONTACT, False


def compter_mots(texte):
    return len(texte.split())


def construire_corps(salutation, observation_texte, competence_texte, proposition_texte, ajouter_complement):
    paragraphes = [salutation, observation_texte, competence_texte, proposition_texte]
    if ajouter_complement:
        paragraphes.append(COMPLEMENT_AUDIT_DETAILLE)
    corps = "\n\n".join(paragraphes)
    nb_mots = compter_mots(corps)

    if nb_mots > 100 and "," in proposition_texte:
        proposition_courte = proposition_texte.split(",")[0] + "."
        paragraphes[3] = proposition_courte
        corps = "\n\n".join(paragraphes)
        nb_mots = compter_mots(corps)

    if not (75 <= nb_mots <= 100):
        return None, nb_mots

    return corps, nb_mots


def contient_mot_interdit(texte):
    texte_minuscule = texte.lower()
    return any(mot in texte_minuscule for mot in MOTS_INTERDITS)


def corps_en_html(salutation, observation_texte, competence_texte, proposition_texte, complement_texte=None):
    complement_html = f'<p style="margin: 0 0 12px 0;">{complement_texte}</p>' if complement_texte else ""
    marge_proposition = "0 0 12px 0" if complement_texte else "0 0 20px 0"
    return (
        '<div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; '
        'color: #222222; line-height: 1.5; max-width: 560px;">'
        '<p style="margin: 0 0 16px 0; font-weight: bold; color: #222222;">A.S.Digital</p>'
        f'<p style="margin: 0 0 12px 0;">{salutation}</p>'
        f'<p style="margin: 0 0 12px 0;">{observation_texte}</p>'
        f'<p style="margin: 0 0 12px 0;">{competence_texte}</p>'
        f'<p style="margin: {marge_proposition};">{proposition_texte}</p>'
        f'{complement_html}'
        '<p style="margin: 0; font-size: 13px; color: #444444;">'
        "Abdelatif Senhaji<br>"
        "A.S.Digital — SIREN 979 115 862<br>"
        "Pour ne plus recevoir de message, répondez STOP."
        "</p></div>"
    )


def traiter_contact(contact, etat_observations):
    nom, email, siren, site = contact["nom"], contact["email"], contact["siren"], contact["site_web"]

    page = recuperer_page_accueil(site)
    if page is None:
        return {
            "nom": nom, "email": email, "objet": "", "corps_html": "",
            "observation": "", "competence": "", "statut": "site injoignable",
        }

    url_finale, html = page
    echecs = tester_observations(url_finale, html)

    if not echecs:
        return {
            "nom": nom, "email": email, "objet": "", "corps_html": "",
            "observation": "", "competence": "", "statut": "rien à signaler",
        }

    deja_utilisee = etat_observations.get(email, {}).get("observations_utilisees", [])
    disponibles = [e for e in echecs if (e[0] if isinstance(e, tuple) else e) not in deja_utilisee]
    if not disponibles:
        return {
            "nom": nom, "email": email, "objet": "", "corps_html": "",
            "observation": "", "competence": "", "statut": "rien à signaler",
        }

    retenue = disponibles[0]
    if isinstance(retenue, tuple):
        cle, annee = retenue
        observation_texte = OBSERVATIONS[cle].format(annee=annee)
    else:
        cle = retenue
        observation_texte = OBSERVATIONS[cle]

    etat_observations.setdefault(email, {"observations_utilisees": []})
    etat_observations[email]["observations_utilisees"].append(cle)

    salutation = generer_salutation(siren)
    competence_texte, proposition_texte, ajouter_complement = choisir_competence(cle, html)

    corps, nb_mots = construire_corps(
        salutation, observation_texte, competence_texte, proposition_texte, ajouter_complement
    )
    if corps is None:
        return {
            "nom": nom, "email": email, "objet": "", "corps_html": "",
            "observation": cle, "competence": competence_texte,
            "statut": f"rejeté (hors fourchette, {nb_mots} mots)",
        }

    if contient_mot_interdit(corps):
        return {
            "nom": nom, "email": email, "objet": "", "corps_html": "",
            "observation": cle, "competence": competence_texte,
            "statut": "rejeté (expression interdite)",
        }

    nom_sans_parenthese = nom.split("(")[0].strip()
    objet = f"Audit gratuit de présence en ligne — {nom_sans_parenthese}"
    complement_texte = COMPLEMENT_AUDIT_DETAILLE if ajouter_complement else None
    corps_html = corps_en_html(salutation, observation_texte, competence_texte, proposition_texte, complement_texte)

    return {
        "nom": nom, "email": email, "objet": objet, "corps_html": corps_html,
        "observation": cle, "competence": competence_texte, "statut": "prêt",
    }


def main():
    contacts = charger_restants()
    etat_observations = charger_json(FICHIER_ETAT_OBSERVATIONS, {})

    lignes = []
    for contact in contacts:
        ligne = traiter_contact(contact, etat_observations)
        lignes.append(ligne)
        time.sleep(0.3)

    with open(FICHIER_SORTIE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["nom", "email", "objet", "corps_html", "observation", "competence", "statut"]
        )
        writer.writeheader()
        writer.writerows(lignes)

    with open(FICHIER_ETAT_OBSERVATIONS, "w", encoding="utf-8") as f:
        json.dump(etat_observations, f, ensure_ascii=False, indent=2)

    prets = sum(1 for l in lignes if l["statut"] == "prêt")
    print(f"{prets} prêts / {len(lignes)} traités -> {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
