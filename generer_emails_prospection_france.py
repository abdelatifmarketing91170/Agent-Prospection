"""
Génère les emails de prospection (objet personnalisé + 3 variantes
d'accroche validées) pour la campagne nationale, à partir du CSV priorisé.

Différence avec generer_emails_prospection.py (campagne IDF, 30
destinataires, secteurs curés à la main) : à l'échelle nationale
(1000+ entreprises), le secteur et le type de preuve (ads/shopify) sont
dérivés automatiquement du code NAF via secteurs_naf.py — voir ce
fichier pour le détail du principe. Aucun destinataire n'est exclu ici
pour franchise/filiale ou adresse générique : ce filtrage se fait
ENSUITE, à la main, sur le résultat (cf. consigne), avant tout envoi.

Sort deux fichiers :
- brouillons_emails_france.txt : lecture humaine (mêmes blocs que la
  campagne IDF).
- emails_france.json : la même donnée en structuré (liste de
  {siren, nom, email, secteur, variante, objet, corps}), pour que le
  script d'envoi n'ait pas à re-parser du texte.
"""

import csv
import json
import random
import re
import urllib.parse

from secteurs_naf import secteur_pour_code_naf

FICHIER_ENTREE = "entreprises_france_pme_3_19_salaries_priorisees.csv"
FICHIER_SORTIE_TXT = "brouillons_emails_france.txt"
FICHIER_SORTIE_JSON = "emails_france.json"

ACCROCHE_VARIANTES = [
    ("V1_constat", "J'ai regardé la présence Google Ads de {nom} sur « {secteur} {ville} » : aucune campagne active."),
    ("V2_concurrence", "Sur « {secteur} {ville} », ce sont vos concurrents qui tournent sur Google Ads — pas {nom}."),
    ("V3_question", "Une question simple : qui voit-on avant {nom} quand on cherche « {secteur} {ville} » sur Google ?"),
]

# Variante sans mention de secteur, utilisée quand secteurs_naf.py retombe sur le
# libellé générique "votre secteur" : citer "« votre secteur Ville »" comme si
# c'était un intitulé d'activité sonne artificiel, donc on reformule autour de la
# ville seule plutôt que de forcer le secteur dans le gabarit normal.
ACCROCHE_VARIANTES_SANS_SECTEUR = {
    "V1_constat": "J'ai regardé la présence Google Ads de {nom} à {ville} : aucune campagne active.",
    "V2_concurrence": "À {ville}, ce sont vos concurrents qui tournent sur Google Ads — pas {nom}.",
    "V3_question": "Une question simple : qui voit-on avant {nom} quand on cherche votre activité à {ville} sur Google ?",
}
PREUVE_SANS_SECTEUR = "Sur nos dossiers récents, nos campagnes Google Ads Search tournent à 8-9% de CTR, contre 2-3% de moyenne sur le secteur."
SUJET_SANS_SECTEUR = "{nom} : votre présence en ligne à {ville}"

PREUVES_ADS = [
    "Sur des dossiers {secteur}, nos campagnes Google Ads Search tournent à 8-9% de CTR, contre 2-3% de moyenne sur le secteur.",
    "En {secteur}, on obtient en général 8-9% de CTR sur Search, contre 2-3% pour la moyenne du secteur.",
]

PREUVES_SHOPIFY = [
    "On a accompagné plusieurs boutiques {secteur} sur Shopify, avec catalogue et paiement en ligne opérationnels en 2-3 semaines.",
    "Notre expérience Shopify sur des boutiques {secteur} permet de lancer une vitrine en ligne complète (catalogue + paiement) en 2-3 semaines.",
]

PROPOSITIONS = [
    "Je vous propose un audit digital gratuit (fiche Google Business, réseaux sociaux, site) pour repérer concrètement où vous perdez des clients.",
    "Un audit gratuit de votre présence digitale (Google Business, réseaux, site) montrerait rapidement où partent vos prospects.",
]

CTA = [
    "Un appel de 15 minutes cette semaine pour en discuter ?",
    "15 minutes cette semaine pour en parler ?",
]

DESINSCRIPTION = "Pour vous désabonner de ces emails, répondez « STOP » à ce message."
SIGNATURE = "A.S.Digital"
SUJET_TEMPLATE = "{nom} : invisible sur « {secteur} {ville} »"


def extraire_ville(adresse):
    match = re.search(r"\d{5}\s+(.+)$", adresse)
    return match.group(1).title() if match else ""


def nettoyer_email(email):
    # Certains sites obfusquent leur mailto en encodage pourcent (%63%6f...)
    # pour gêner les robots : on décode pour obtenir une adresse exploitable.
    decode = urllib.parse.unquote(email)
    return decode if "@" in decode else email


def assigner_variantes(n):
    cles = [cle for cle, _ in ACCROCHE_VARIANTES]
    pool = (cles * ((n // len(cles)) + 1))[:n]
    random.shuffle(pool)
    return pool


def generer_sujet(nom, secteur, ville):
    if secteur == "votre secteur":
        return SUJET_SANS_SECTEUR.format(nom=nom, ville=ville)
    return SUJET_TEMPLATE.format(nom=nom, secteur=secteur, ville=ville)


def generer_corps(index, nom, variante_cle, secteur, ville, type_preuve):
    if secteur == "votre secteur":
        accroche = ACCROCHE_VARIANTES_SANS_SECTEUR[variante_cle].format(nom=nom, ville=ville)
        proposition = PROPOSITIONS[index % len(PROPOSITIONS)]
        cta = CTA[index % len(CTA)]
        return "\n".join([
            "Bonjour,", accroche, PREUVE_SANS_SECTEUR, proposition, cta, "", SIGNATURE, "", DESINSCRIPTION,
        ])

    accroche_template = dict(ACCROCHE_VARIANTES)[variante_cle]
    accroche = accroche_template.format(nom=nom, secteur=secteur, ville=ville)

    if type_preuve == "shopify":
        preuve = PREUVES_SHOPIFY[index % len(PREUVES_SHOPIFY)].format(secteur=secteur)
    else:
        preuve = PREUVES_ADS[index % len(PREUVES_ADS)].format(secteur=secteur)
    proposition = PROPOSITIONS[index % len(PROPOSITIONS)]
    cta = CTA[index % len(CTA)]

    return "\n".join([
        "Bonjour,",
        accroche,
        preuve,
        proposition,
        cta,
        "",
        SIGNATURE,
        "",
        DESINSCRIPTION,
    ])


def main():
    with open(FICHIER_ENTREE, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))

    destinataires = [ligne for ligne in lignes if ligne.get("email_contact")]
    print(f"{len(destinataires)} entreprises avec un email disponible sur {len(lignes)}.")

    variantes = assigner_variantes(len(destinataires))

    emails = []
    blocs = []
    for i, ligne in enumerate(destinataires):
        secteur, type_preuve = secteur_pour_code_naf(ligne.get("code_naf", ""))
        ville = extraire_ville(ligne["adresse"])
        variante_cle = variantes[i]
        nom = ligne["nom"]

        sujet = generer_sujet(nom, secteur, ville)
        corps = generer_corps(i, nom, variante_cle, secteur, ville, type_preuve)

        emails.append({
            "siren": ligne["siren"],
            "nom": nom,
            "email": nettoyer_email(ligne["email_contact"]),
            "secteur": secteur,
            "variante": variante_cle,
            "objet": sujet,
            "corps": corps,
        })
        blocs.append(
            f"Destinataire : {nom} <{ligne['email_contact']}>\n"
            f"Objet : {sujet}\n"
            f"Variante : {variante_cle}\n\n{corps}"
        )

    with open(FICHIER_SORTIE_TXT, "w", encoding="utf-8") as f:
        f.write(("\n\n" + "=" * 60 + "\n\n").join(blocs))
        f.write("\n")

    with open(FICHIER_SORTIE_JSON, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)

    repartition = {cle: variantes.count(cle) for cle, _ in ACCROCHE_VARIANTES}
    print(f"{len(emails)} emails générés dans {FICHIER_SORTIE_TXT} et {FICHIER_SORTIE_JSON}")
    print("Répartition des variantes :", repartition)


if __name__ == "__main__":
    main()
