# ==============================================================================
# AUTHZ.PY — Décorateurs et dépendances FastAPI pour le contrôle d'accès RBAC
# ==============================================================================

from fastapi import Depends, HTTPException, status

from ..auth import get_current_user
from ..database import get_db
from ..models.user import User
from sqlalchemy.orm import Session

from .permissions import (
    check_permission,   # Fonction de vérification principale
    is_super_admin,     # Helper superadmin
    get_user_permissions,  # Helper liste des permissions
    ALL_PERMISSIONS,    # Set de toutes les permissions valides
    ROLE_PERMISSIONS,   # Mapping rôles → permissions (pour référence)
    PERMISSIONS,        # Définition des 14 permissions avec descriptions
)

# Réexporter pour que les autres modules puissent importer depuis authz.py
__all__ = [
    "require_permission",
    "require_role",
    "require_any_role",
    "check_permission",
    "is_super_admin",
    "get_user_permissions",
    "ALL_PERMISSIONS",
    "ROLE_PERMISSIONS",
    "PERMISSIONS",
]


# ==============================================================================
#  require_permission() — Protéger un endpoint par permission
# ==============================================================================

def require_permission(permission: str):
    """
    Dépendance FastAPI — Vérifie qu'un utilisateur a une permission spécifique.

    """
    # Validation au démarrage de l'application (pas à chaque requête)
    # Si une faute de frappe est dans le code, on la détecte immédiatement.
    if permission not in ALL_PERMISSIONS:
        raise ValueError(
            f"Permission inconnue : '{permission}'. "
            f"Permissions valides : {sorted(ALL_PERMISSIONS)}"
        )

    async def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        """
        Fonction interne exécutée par FastAPI à chaque requête.

        CLOSURE :
        La variable 'permission' est "capturée" depuis la fonction parente.
        Même si require_permission() a fini de s'exécuter, _check() se
        souvient de la valeur de 'permission'. C'est une "closure" Python.
        """
        if not check_permission(current_user, permission, db):
            user_role = getattr(current_user.role, "name", "aucun") if current_user else "non connecté"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "permission_denied",
                    "message": f"Permission manquante : '{permission}'",
                    "your_role": user_role,
                    "required_permission": permission,
                    # Aide au debug : liste les permissions du rôle actuel
                    "your_permissions": get_user_permissions(current_user, db),
                }
            )
        return current_user

    return _check


# ==============================================================================
#  require_role() — Protéger un endpoint par rôle exact
# ==============================================================================

def require_role(role_name: str):
    """
    Dépendance FastAPI — Vérifie que l'utilisateur a exactement un rôle donné.

    
    """
    # Validation au démarrage
    if role_name not in ROLE_PERMISSIONS:
        raise ValueError(
            f"Rôle inconnu : '{role_name}'. "
            f"Rôles valides : {list(ROLE_PERMISSIONS.keys())}"
        )

    async def _check_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = getattr(current_user.role, "name", None) if current_user else None

        #  Le superadmin bypass TOUJOURS les vérifications de rôle
        if user_role == "superadmin":
            return current_user

        if user_role != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "role_required",
                    "message": f"Rôle requis : '{role_name}'",
                    "your_role": user_role or "aucun",
                    "required_role": role_name,
                }
            )
        return current_user

    return _check_role


# ==============================================================================
#  require_any_role() — Accepter plusieurs rôles possibles
# ==============================================================================

def require_any_role(*role_names: str):
    """
    Dépendance FastAPI — Accepte un endpoint si l'utilisateur a l'un des rôles.

    
    """
    # Validation au démarrage — tous les rôles doivent exister
    for role in role_names:
        if role not in ROLE_PERMISSIONS:
            raise ValueError(
                f"Rôle inconnu : '{role}'. "
                f"Rôles valides : {list(ROLE_PERMISSIONS.keys())}"
            )

    async def _check_any_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = getattr(current_user.role, "name", None) if current_user else None

        #  Le superadmin bypass TOUJOURS les vérifications de rôle
        if user_role == "superadmin":
            return current_user

        if user_role not in role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "role_required",
                    "message": f"Un des rôles suivants est requis : {list(role_names)}",
                    "your_role": user_role or "aucun",
                    "accepted_roles": list(role_names),
                }
            )
        return current_user

    return _check_any_role