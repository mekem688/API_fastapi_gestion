"""
permissions.py — Gestion des permissions granulaires des directeurs

Permissions disponibles :
  VOIR_PROFITS    → accès aux bénéfices (article et total)
  FAIRE_ACHATS    → entrées de stock (stock/in)
  CREER_ARTICLES  → créer de nouveaux articles
  VOIR_ALERTES    → voir les alertes stock faible
  GERER_VENDEURS  → créer et suspendre les vendeurs de sa boutique

Règles :
  - Le PDG n'est jamais limité par les permissions (il a tout).
  - Un directeur suspendu (est_actif=False) ne peut plus du tout se connecter.
  - Un directeur actif doit avoir la permission explicitement dans sa liste.
"""

from fastapi import HTTPException, status

# Liste de toutes les permissions valides
TOUTES_LES_PERMISSIONS = [
    "voir_profits",
    "faire_achats",
    "creer_articles",
    "voir_alertes",
    "gerer_vendeurs",
]

# Labels lisibles pour l'affichage
LABELS_PERMISSIONS = {
    "voir_profits"   : "Voir les bénéfices",
    "faire_achats"   : "Faire des achats (stock/in)",
    "creer_articles" : "Créer des articles",
    "voir_alertes"   : "Voir les alertes stock faible",
    "gerer_vendeurs" : "Gérer les vendeurs (créer, suspendre)",
}


def verifier_permission(utilisateur, permission: str) -> None:
    """
    Vérifie qu'un utilisateur a le droit d'effectuer une action.

    - PDG         → toujours autorisé (aucune vérification)
    - Vendeur     → n'a jamais de permissions granulaires (routes fixes)
    - Directeur   → doit avoir la permission dans sa liste JSON

    Lève HTTPException 403 si le droit est absent ou si le compte est suspendu.
    """
    # Le PDG a tous les droits, aucune vérification nécessaire
    if utilisateur.role == "pdg":
        return

    # Compte suspendu → refus immédiat
    if not utilisateur.est_actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte a été suspendu par le PDG. Contactez-le pour le rétablir.",
        )

    # Vérification de la permission dans la liste JSON
    permissions_actuelles = utilisateur.permissions or []

    if permission not in permissions_actuelles:
        label = LABELS_PERMISSIONS.get(permission, permission)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission manquante : « {label} ». Demandez au PDG de vous l'accorder.",
        )
