"""
Table générique code NAF -> (libellé secteur court, type de preuve
"ads"/"shopify"), utilisée pour générer des emails de prospection
personnalisés à l'échelle (1000+ entreprises) sans curation manuelle
par entreprise (qui ne passait pas à l'échelle au-delà d'une trentaine
de cas traités à la main).

Principe : on mappe au niveau de la DIVISION NAF (les 2 premiers
chiffres du code, ex. "47" pour "47.71Z") sur un libellé court en
français, ce qui suffit pour une accroche de prospection ("boulangerie"
plutôt que l'intitulé officiel verbeux de la classe à 5 caractères).
Une division inconnue retombe sur un libellé générique neutre plutôt
que de faire échouer la génération.

Type de preuve : "shopify" uniquement pour les classes de commerce de
détail de PRODUITS qui se prêtent naturellement à une boutique en ligne
(habillement, bijouterie, cosmétique, électronique, meubles, vente à
distance...) ; "ads" par défaut pour tout le reste (services locaux,
B2B, commerce alimentaire/périssable, commerce de gros...).
"""

import re

LIBELLES_PAR_DIVISION = {
    "01": "agriculture", "10": "agroalimentaire", "11": "boissons",
    "13": "textile", "14": "habillement", "15": "cuir et chaussure",
    "16": "travail du bois", "17": "papier-carton", "18": "imprimerie",
    "20": "industrie chimique", "22": "plasturgie", "23": "matériaux de construction",
    "25": "métallurgie", "26": "électronique", "27": "équipements électriques",
    "28": "fabrication de machines", "29": "industrie automobile",
    "31": "fabrication de meubles", "32": "industrie manufacturière",
    "33": "réparation de machines",
    "41": "promotion immobilière et construction", "42": "travaux publics",
    "43": "travaux de construction spécialisés",
    "45": "commerce et réparation automobile", "46": "commerce de gros",
    "47": "commerce de détail",
    "49": "transport routier", "50": "transport maritime", "51": "transport aérien",
    "52": "entreposage et logistique", "53": "activités de poste et courrier",
    "55": "hébergement touristique", "56": "restauration",
    "58": "édition", "59": "production audiovisuelle",
    "60": "diffusion radio/TV", "61": "télécommunications",
    "62": "services informatiques", "63": "services d'information",
    "64": "services financiers", "65": "assurance",
    "66": "conseil financier",
    "68": "activités immobilières",
    "69": "activités juridiques et comptables", "70": "conseil de gestion",
    "71": "architecture et ingénierie", "72": "recherche et développement",
    "73": "publicité et études de marché", "74": "activités spécialisées diverses",
    "75": "activités vétérinaires",
    "77": "location et location-bail", "78": "activités liées à l'emploi",
    "79": "agences de voyage", "80": "sécurité", "81": "services aux bâtiments",
    "82": "services administratifs de bureau",
    "85": "formation",
    "86": "activités de santé", "87": "hébergement médico-social",
    "90": "activités créatives et artistiques", "91": "patrimoine culturel",
    "92": "jeux de hasard et d'argent", "93": "sport et loisirs",
    "95": "réparation d'ordinateurs et biens personnels", "96": "services personnels",
    "97": "emploi à domicile",
}

LIBELLE_PAR_DEFAUT = "votre secteur"

# Classes de commerce de détail (division 47) qui se prêtent à une
# boutique Shopify : produits non périssables, achat réfléchi/en ligne
# courant. Le reste de la division 47 (alimentaire, carburant, marchés)
# reste sur l'angle Google Ads.
CLASSES_SHOPIFY_DIVISION_47 = {
    "41", "42", "43",  # équipement de l'information et de la communication
    "51", "52", "53", "54", "59",  # textiles, quincaillerie, tapis, livres, autres équipements du foyer
    "63", "64", "65",  # matériel audio/photo, articles de sport, jeux/jouets
    "71", "72", "73", "74", "75", "76", "77", "78", "79",  # habillement, chaussures, parfumerie, fleurs, horlogerie-bijouterie, bagages...
    "91",  # vente à distance
}


def secteur_pour_code_naf(code_naf):
    """Renvoie (libelle_secteur, type_preuve) pour un code NAF (ex "47.71Z")."""
    code_naf = (code_naf or "").strip().upper()
    match = re.match(r"(\d{2})\.?(\d{2})?", code_naf)
    if not match:
        return LIBELLE_PAR_DEFAUT, "ads"

    division, classe = match.group(1), match.group(2)
    libelle = LIBELLES_PAR_DIVISION.get(division, LIBELLE_PAR_DEFAUT)

    type_preuve = "ads"
    if division == "47" and classe in CLASSES_SHOPIFY_DIVISION_47:
        type_preuve = "shopify"

    return libelle, type_preuve
