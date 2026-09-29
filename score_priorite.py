"""
Calcule un score de priorité de prospection (0 à 100) pour chaque
entreprise du CSV enrichi, et exporte un nouveau CSV trié par score
décroissant.

Formule (documentée en détail plus bas, avec les constantes) :

    score_priorite = 0.5 * score_effectif + 0.5 * score_digital

- score_effectif (0, 50 ou 100) : plus la tranche d'effectif est grande,
  plus ce sous-score est élevé. Les 3 tranches possibles dans ce fichier
  sont ordonnées : "3 à 5 salariés" = 0, "6 à 9 salariés" = 50,
  "10 à 19 salariés" = 100.

- score_digital (0, 50 ou 100) : plus la présence digitale est faible,
  plus ce sous-score est élevé. Site + email trouvés = 0 (déjà
  joignable), site trouvé mais pas d'email = 50 (présence web mais pas
  de contact direct), pas de site du tout = 100 (aucune présence
  digitale identifiée, priorité maximale).

Les deux sous-scores comptent pour moitié chacun, donc score_priorite
vaut toujours 0, 25, 50, 75 ou 100. En cas d'égalité de score, les
lignes sont triées par nom pour que le résultat soit stable et
reproductible d'une exécution à l'autre.
"""

import csv

FICHIER_ENTREE = "entreprises_idf_pme_3_19_salaries_enrichi.csv"
FICHIER_SORTIE = "entreprises_idf_pme_3_19_salaries_priorisees.csv"

# Ordre des tranches d'effectif, de la plus petite à la plus grande.
SCORE_EFFECTIF_PAR_TRANCHE = {
    "02": 0,    # 3 à 5 salariés
    "03": 50,   # 6 à 9 salariés
    "11": 100,  # 10 à 19 salariés
}

POIDS_EFFECTIF = 0.5
POIDS_DIGITAL = 0.5


def score_effectif(tranche_code):
    # Tranche inconnue -> score neutre (milieu de l'échelle) plutôt que
    # de fausser le tri avec une valeur arbitraire.
    return SCORE_EFFECTIF_PAR_TRANCHE.get(tranche_code, 50)


def score_digital(site_web, email_contact):
    if not site_web:
        return 100
    if not email_contact:
        return 50
    return 0


def calculer_score(ligne):
    s_effectif = score_effectif(ligne.get("tranche_effectif_salarie_code", ""))
    s_digital = score_digital(ligne.get("site_web", ""), ligne.get("email_contact", ""))
    score = POIDS_EFFECTIF * s_effectif + POIDS_DIGITAL * s_digital
    return round(score)


def main():
    with open(FICHIER_ENTREE, encoding="utf-8-sig", newline="") as fichier_entree:
        lecteur = csv.DictReader(fichier_entree, delimiter=";")
        lignes = list(lecteur)
        fieldnames = list(lecteur.fieldnames)

    if "score_priorite" not in fieldnames:
        fieldnames.append("score_priorite")

    for ligne in lignes:
        ligne["score_priorite"] = calculer_score(ligne)

    lignes.sort(key=lambda ligne: (-ligne["score_priorite"], ligne.get("nom", "")))

    with open(FICHIER_SORTIE, "w", newline="", encoding="utf-8-sig") as fichier_sortie:
        writer = csv.DictWriter(fichier_sortie, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(lignes)

    repartition = {}
    for ligne in lignes:
        repartition[ligne["score_priorite"]] = repartition.get(ligne["score_priorite"], 0) + 1

    print(f"{len(lignes)} entreprises scorées et triées par priorité décroissante.")
    print("Répartition des scores :", dict(sorted(repartition.items(), reverse=True)))
    print(f"Résultat exporté dans {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()
