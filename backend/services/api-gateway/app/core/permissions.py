# ==============================================================================
# PERMISSIONS.PY — Source de vérité unique pour les rôles et permissions
# ==============================================================================


from typing import Dict, List, Optional
from sqlalchemy.orm import Session


# ==============================================================================
# DÉFINITION DES 14 PERMISSIONS
# ==============================================================================
# Structure : {module: {action: description}}
# La description est utilisée pour la documentation et le Swagger.

PERMISSIONS: Dict[str, Dict[str, str]] = {
    "documents": {
        "read":    "Lire et télécharger les documents",
        "write":   "Créer et modifier les documents",
        "delete":  "Supprimer les documents (soft delete)",
        "analyze": "Lancer l'analyse de conformité d'un document",
    },
    "users": {
        "read":   "Lire la liste des utilisateurs du tenant",
        "write":  "Créer et modifier les utilisateurs",
        "delete": "Désactiver ou supprimer un utilisateur",
    },
    "tenants": {
        "read":  "Lire les informations du tenant",
        "write": "Modifier les paramètres du tenant",
    },
    "reports": {
        "read":     "Consulter les rapports de conformité",
        "generate": "Générer de nouveaux rapports",
    },
    "audit": {
        "read": "Consulter le journal d'audit (lecture seule, jamais modifiable)",
    },
    "admin": {
        #  RÉSERVÉ AU SUPERADMIN — donne accès à TOUT le système
        "all": "Accès administrateur complet (bypass toutes les vérifications)",
    },
}

# Liste plate de toutes les permissions pour validation rapide
# Résultat : {"documents:read", "documents:write", "users:read", ...}
ALL_PERMISSIONS: set = {
    f"{module}:{action}"
    for module, actions in PERMISSIONS.items()
    for action in actions
}


# ==============================================================================
#  MAPPING RÔLES → PERMISSIONS
# ==============================================================================
# Ce dictionnaire définit exactement ce que chaque rôle peut faire.
# Il est utilisé par :
#   1. check_permission() comme fallback si la DB ne charge pas le rôle
#   2. rbac_seed.py pour initialiser les rôles en base de données

ROLE_PERMISSIONS: Dict[str, dict] = {

    "superadmin": {
        "name": "Super Admin",
        "description": "Accès complet au système. Réservé aux administrateurs système.",
        # {"admin": "all"} est le signal qui bypass TOUTES les vérifications
        "permissions": {"admin": "all"},
        "is_system": True,
    },

    "admin": {
        "name": "Admin",
        "description": "Administrateur tenant. Gestion complète sauf accès système.",
        "permissions": {
            "documents": ["read", "write", "delete", "analyze"],
            "users":     ["read", "write", "delete"],
            "tenants":   ["read", "write"],
            "reports":   ["read", "generate"],
            "audit":     ["read"],
        },
        "is_system": True,
    },

    "manager": {
        "name": "Manager",
        "description": "Gestionnaire. Gère les documents, les utilisateurs et les rapports.",
        "permissions": {
            "documents": ["read", "write", "analyze"],
            "users":     ["read", "write"],
            "tenants":   ["read"],
            "reports":   ["read", "generate"],
            "audit":     ["read"],
        },
        "is_system": True,
    },

    "analyst": {
        "name": "Analyst",
        "description": "Analyste. Lit et analyse les documents, génère des rapports.",
        "permissions": {
            "documents": ["read", "analyze"],
            "users":     ["read"],
            "reports":   ["read", "generate"],
            "audit":     ["read"],
        },
        "is_system": True,
    },

    "contributor": {
        "name": "Contributor",
        "description": "Contributeur. Peut créer et modifier des documents.",
        "permissions": {
            "documents": ["read", "write"],
            "users":     ["read"],
            "reports":   ["read"],
        },
        "is_system": True,
    },

    "viewer": {
        "name": "Viewer",
        "description": "Lecteur. Accès en lecture seule aux documents et rapports.",
        "permissions": {
            "documents": ["read"],
            "reports":   ["read"],
        },
        "is_system": True,
    },
}


# ==============================================================================
#  FONCTIONS DE VÉRIFICATION
# ==============================================================================

def check_permission(
    user,  # Type User — pas importé ici pour éviter les imports circulaires
    permission: str,
    db: Optional[Session] = None,
) -> bool:
    """
    Vérifie si un utilisateur a une permission spécifique.

    
    """
    # Étape 1 : L'utilisateur doit exister et avoir un rôle assigné
    if not user or not getattr(user, "role_id", None):
        return False

    # Étape 2 : La permission doit être au bon format
    if ":" not in permission:
        return False

    # Étape 3 : Charger le rôle
    role = getattr(user, "role", None)

    if not role and db:
        # La relation n'est pas chargée → requête DB explicite
        from ..models.role import Role
        role = db.query(Role).filter(Role.id == user.role_id).first()

    if not role:
        # Pas de rôle trouvé, on essaie le fallback statique
        return _check_static_permission(getattr(user, "role_name", None), permission)

    permissions = role.permissions or []
    role_name = role.name

    if "admin:all" in permissions or "*" in permissions:
        return True

    if permission in permissions:
        return True


def _check_static_permission(role_name: Optional[str], permission: str) -> bool:
    """
    Fallback : vérifie une permission dans le mapping statique ROLE_PERMISSIONS.

   
    """
    if not role_name or role_name not in ROLE_PERMISSIONS:
        return False

    if role_name == "superadmin":
        return True

    role_data = ROLE_PERMISSIONS[role_name]
    perms = role_data.get("permissions", {})
    module, action = permission.split(":", 1)
    module_perms = perms.get(module, [])

    if isinstance(module_perms, list):
        return action in module_perms

    return module_perms in ["all", "*"]


def get_user_permissions(user, db: Optional[Session] = None) -> Dict[str, List[str]]:
    """
    Retourne toutes les permissions d'un utilisateur.

    
    """
    if not user or not getattr(user, "role_id", None):
        return {}

    role = getattr(user, "role", None)
    if not role and db:
        from ..models.role import Role
        role = db.query(Role).filter(Role.id == user.role_id).first()

    if not role:
        return {}

    return role.permissions or {}


def is_super_admin(user, db: Optional[Session] = None) -> bool:
    """
    Vérifie si un utilisateur est superadmin.

    
    """
    return check_permission(user, "admin:all", db)