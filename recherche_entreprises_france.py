"""
Recherche d'entreprises sur toute la France via l'API publique gratuite
recherche-entreprises.api.gouv.fr, et export des résultats en CSV.

Variante nationale de recherche_entreprises_idf.py : seul le filtre
région a été retiré (aucun paramètre "region" envoyé à l'API = recherche
sur l'ensemble du territoire). Tous les autres critères sont identiques :

- Effectif salarié : 3 à 19 salariés (codes INSEE "02", "03", "11")
- Catégorie        : PME
- État             : entreprises actives uniquement
- Exclusions       : associations/fondations/syndicats/administrations
                      (via la nature juridique) et certains secteurs NAF
                      peu propices à la prospection commerciale.

Fichiers séparés de la campagne Île-de-France (entreprises_idf_*) pour
ne jamais interférer avec elle : voir FICHIER_SORTIE et FICHIER_ETAT.
"""

import csv
import json
import os
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://recherche-entreprises.api.gouv.fr/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

CATEGORIE_ENTREPRISE = "PME"
ETAT_ADMINISTRATIF_ACTIF = "A"

# Codes NAF (activité principale) à cibler. Liste vide = tous les secteurs.
NAF_CIBLES = []

TRANCHES_EFFECTIF_3_A_19 = {
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
}

NATURE_JURIDIQUE_PREFIXES_EXCLUES = ("7", "8", "9")

CODES_NAF_DIVISIONS_EXCLUES = {"84", "88", "94"}
CODES_NAF_EXCLUS = {"64.20Z", "70.10Z"}

PER_PAGE = 25
MAX_PAR_TRANCHE = 334    # ~1000 au total (334+333+333), "environ 330 par tranche"
PAUSE_ENTRE_REQUETES = 0.3
NB_TENTATIVES_MAX = 3

CSV_FIELDNAMES = [
    "siren",
    "nom",
    "adresse",
    "code_naf",
    "tranche_effectif_salarie_code",
    "tranche_effectif_salarie_libelle",
]

FICHIER_SORTIE = "entreprises_france_pme_3_19_salaries.csv"
FICHIER_ETAT = "etat_recherche_entreprises_france.json"


def appeler_api(params):
    derniere_erreur = None
    for tentative in range(1, NB_TENTATIVES_MAX + 1):
        try:
            reponse = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            if reponse.status_code >= 500:
                raise requests.HTTPError(f"Erreur serveur {reponse.status_code}")
            reponse.raise_for_status()
            return reponse.json()
        except requests.RequestException as erreur:
            derniere_erreur = erreur
            attente = 2 * tentative
            print(f"  Échec de la requête ({erreur}), nouvelle tentative dans {attente}s...")
            time.sleep(attente)
    raise RuntimeError(f"L'API n'a pas répondu après {NB_TENTATIVES_MAX} tentatives : {derniere_erreur}")


def entreprise_est_prospect(entreprise):
    nature_juridique = entreprise.get("nature_juridique") or ""
    if nature_juridique[:1] in NATURE_JURIDIQUE_PREFIXES_EXCLUES:
        return False

    code_naf = entreprise.get("activite_principale") or ""
    if code_naf in CODES_NAF_EXCLUS or code_naf[:2] in CODES_NAF_DIVISIONS_EXCLUES:
        return False

    return True


def charger_etat():
    if os.path.exists(FICHIER_ETAT):
        with open(FICHIER_ETAT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def sauvegarder_etat(entreprises_par_siren):
    with open(FICHIER_ETAT, "w", encoding="utf-8") as f:
        json.dump(entreprises_par_siren, f, ensure_ascii=False)


def recuperer_entreprises_pour_tranche(tranche_code, entreprises_par_siren):
    retenues_pour_tranche = sum(
        1 for e in entreprises_par_siren.values()
        if e.get("tranche_effectif_salarie") == tranche_code
    )
    if retenues_pour_tranche >= MAX_PAR_TRANCHE:
        print(f"  Tranche {tranche_code} ({TRANCHES_EFFECTIF_3_A_19[tranche_code]}) déjà complète (reprise) — ignorée.")
        return

    page = 1
    while retenues_pour_tranche < MAX_PAR_TRANCHE:
        params = {
            # Pas de "region" : recherche sur toute la France.
            "categorie_entreprise": CATEGORIE_ENTREPRISE,
            "etat_administratif": ETAT_ADMINISTRATIF_ACTIF,
            "tranche_effectif_salarie": tranche_code,
            "page": page,
            "per_page": PER_PAGE,
        }
        if NAF_CIBLES:
            params["activite_principale"] = ",".join(NAF_CIBLES)

        data = appeler_api(params)
        resultats_page = data.get("results", [])
        total_pages = data.get("total_pages", page)

        print(
            f"  Tranche {tranche_code} ({TRANCHES_EFFECTIF_3_A_19[tranche_code]}) "
            f"- page {page}/{total_pages} - {len(resultats_page)} entreprises reçues "
            f"- {retenues_pour_tranche}/{MAX_PAR_TRANCHE} retenues"
        )

        if not resultats_page:
            break

        for entreprise in resultats_page:
            siren = entreprise.get("siren")
            if not siren or siren in entreprises_par_siren:
                continue
            if not entreprise_est_prospect(entreprise):
                continue

            entreprises_par_siren[siren] = entreprise
            retenues_pour_tranche += 1
            if retenues_pour_tranche >= MAX_PAR_TRANCHE:
                break

        sauvegarder_etat(entreprises_par_siren)

        if page >= total_pages:
            break

        page += 1
        time.sleep(PAUSE_ENTRE_REQUETES)


def extraire_ligne_csv(entreprise):
    siege = entreprise.get("siege") or {}
    adresse = siege.get("adresse") or ""
    tranche_code = entreprise.get("tranche_effectif_salarie") or siege.get("tranche_effectif_salarie") or ""

    return {
        "siren": entreprise.get("siren", ""),
        "nom": entreprise.get("nom_complet") or entreprise.get("nom_raison_sociale") or "",
        "adresse": adresse,
        "code_naf": entreprise.get("activite_principale", ""),
        "tranche_effectif_salarie_code": tranche_code,
        "tranche_effectif_salarie_libelle": TRANCHES_EFFECTIF_3_A_19.get(tranche_code, ""),
    }


def main():
    entreprises_par_siren = charger_etat()
    if entreprises_par_siren:
        print(f"Reprise : {len(entreprises_par_siren)} entreprises déjà collectées dans {FICHIER_ETAT}.\n")

    for tranche_code in TRANCHES_EFFECTIF_3_A_19:
        recuperer_entreprises_pour_tranche(tranche_code, entreprises_par_siren)

    lignes = [extraire_ligne_csv(e) for e in entreprises_par_siren.values()]

    with open(FICHIER_SORTIE, "w", newline="", encoding="utf-8-sig") as fichier_csv:
        writer = csv.DictWriter(fichier_csv, fieldnames=CSV_FIELDNAMES, delimiter=";")
        writer.writeheader()
        writer.writerows(lignes)

    print(f"\n{len(lignes)} entreprises exportées dans {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
