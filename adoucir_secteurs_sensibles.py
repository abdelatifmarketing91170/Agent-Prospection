"""
Adoucit le ton des emails pour les secteurs sensibles (santé : NAF
division 86/87 ; pompes funèbres : NAF 96.03Z) dans emails_france_filtres.json :
- Force l'accroche sur la variante V1 (constat factuel), jamais V2
  (comparaison concurrence) ni V3 (question directe), qui peuvent sonner
  comparatif/provocant pour ces secteurs.
- Remplace la proposition et l'objet par des formulations plus sobres,
  sans angle "vous perdez des clients" ni "invisible".
Modifie en place emails_france_filtres.json (tous les autres
destinataires restent inchangés).
"""

import json

FICHIER = "emails_france_filtres.json"

DIVISIONS_SANTE = {"86", "87"}

ACCROCHE_V1 = "J'ai regardé la présence Google Ads de {nom} sur « {secteur} {ville} » : aucune campagne active."
PROPOSITION_SOBRE = "Un audit digital gratuit (fiche Google Business, réseaux sociaux, site) peut faire un état des lieux concret de votre présence en ligne."
CTA_SOBRE = "Un échange de 15 minutes cette semaine, si cela vous intéresse ?"
SUJET_SOBRE = "{nom} — présence en ligne sur « {secteur} {ville} »"
SIGNATURE = "A.S.Digital"
DESINSCRIPTION = "Pour vous désabonner de ces emails, répondez « STOP » à ce message."


def est_secteur_sensible(code_naf):
    code_naf = (code_naf or "").strip()
    return code_naf[:2] in DIVISIONS_SANTE or code_naf.startswith("96.03")


def main():
    import csv
    with open("entreprises_france_pme_3_19_salaries_priorisees.csv", encoding="utf-8-sig", newline="") as f:
        naf_par_siren = {r["siren"]: r["code_naf"] for r in csv.DictReader(f, delimiter=";")}
    with open("entreprises_france_pme_3_19_salaries_priorisees.csv", encoding="utf-8-sig", newline="") as f:
        ville_par_siren = {}
        import re
        for r in csv.DictReader(f, delimiter=";"):
            m = re.search(r"\d{5}\s+(.+)$", r["adresse"])
            ville_par_siren[r["siren"]] = m.group(1).title() if m else ""

    with open(FICHIER, encoding="utf-8") as f:
        emails = json.load(f)

    n_modifies = 0
    for item in emails:
        code_naf = naf_par_siren.get(item["siren"], "")
        if not est_secteur_sensible(code_naf):
            continue

        secteur = item["secteur"]
        ville = ville_par_siren.get(item["siren"], "")
        nom = item["nom"]

        item["variante"] = "V1_constat"
        accroche = ACCROCHE_V1.format(nom=nom, secteur=secteur, ville=ville)
        item["objet"] = SUJET_SOBRE.format(nom=nom, secteur=secteur, ville=ville)
        item["corps"] = "\n".join([
            "Bonjour,",
            accroche,
            PROPOSITION_SOBRE,
            CTA_SOBRE,
            "",
            SIGNATURE,
            "",
            DESINSCRIPTION,
        ])
        n_modifies += 1
        print(f"Adouci : {nom} ({code_naf})")

    with open(FICHIER, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)

    print(f"\n{n_modifies} emails adoucis (secteurs santé/pompes funèbres) sur {len(emails)}.")


if __name__ == "__main__":
    main()
