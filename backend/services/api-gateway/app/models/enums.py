# ==============================================================================
# ENUMERATIONS - 📋 Constantes pour statuts et types
# ==============================================================================


from enum import Enum


# ==============================================================================
# 💳 SUBSCRIPTION PLAN - Plans d'abonnement des tenants
# ==============================================================================

class SubscriptionPlan(str, Enum):
    """
    Plans d'abonnement pour les tenants
    """
    FONDEMENTS = "Fondements"                 # Petit plan payant
    AVANCEE = "avancée"       # Plan moyen (fonctionnalités avancées)
    ENTERPRISE = "enterprise"           #  Plan premium (tout inclus)



# ==============================================================================
# DOCUMENT STATUS - Statut de traitement des documents
# ==============================================================================

class DocumentStatus(str, Enum):
    """
    Statuts pour les documents uploadés
    
    Utilisé dans : Document.status
    
    """
    UPLOADED = "uploaded"               # ⬆ Document uploadé avec succès
                                        # → Fichier stocké, métadonnées sauvegardées
    
    READY = "ready"                     #  Document validé et prêt
                                        # → Peut être consulté, téléchargé
                                        # → Visible dans l'interface
    
    ERROR = "error"                     #  Erreur lors du traitement
                                        # → Fichier corrompu, format non supporté
                                        # → Nécessite intervention ou réessai



# ==============================================================================
#  LOGIN FAILURE REASON - Raisons d'échec de connexion
# ==============================================================================

class LoginFailureReason(str, Enum):
    """
    Raisons d'échec de connexion
    
     Utilisé dans : LoginAttempt.failure_reason
    
     SÉCURITÉ :
    → Permet de tracker POURQUOI une connexion a échoué
    → Utile pour détecter les attaques (brute force, énumération)
    → Permet d'améliorer les messages d'erreur pour l'utilisateur
    
     ATTENTION : Ne jamais révéler la raison exacte à l'utilisateur !
    → "Email ou mot de passe incorrect" (générique)
    → Pas "Cet email n'existe pas" (révèle l'existence du compte)
    """
    BAD_PASSWORD = "bad_password"               #  Mot de passe incorrect
                                                 # → Email correct, mauvais mot de passe
                                                 # → Potentielle attaque par force brute
    
    USER_NOT_FOUND = "user_not_found"           #  Utilisateur inexistant
                                                 # → Email n'existe pas dans la base
                                                 # → Potentielle énumération d'emails
    
    ACCOUNT_INACTIVE = "account_inactive"       #  Compte désactivé
                                                 # → User existe mais is_active = False
                                                 # → Peut informer l'user de contacter l'admin
    
    ACCOUNT_DELETED = "account_deleted"         #  Compte supprimé (soft-delete)
                                                 # → User existe mais is_deleted = True
                                                 # → Peut proposer de restaurer le compte
    
    TOO_MANY_ATTEMPTS = "too_many_attempts"     # Trop de tentatives échouées
                                                 # → Protection contre brute force
                                                 # → Bloquer temporairement (5-15 min)




# ==============================================================================
#  AUDIT ACTION - Actions loggées dans l'audit trail
# ==============================================================================

class AuditAction(str, Enum):
    """
    Actions loggées dans l'audit trail — noun.verb convention
    
     Utilisé dans : AuditLog.action
    
    Permet de tracer QUI a fait QUOI et QUAND
    → Conformité RGPD (traçabilité)
    → Investigation en cas d'incident
    → Analytique (qui utilise quoi ?)
    
    Naming Convention: noun.verb (e.g., "user.created", "session.started")
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    #  SESSION ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    SESSION_STARTED = "session.started"            # Login successful
    SESSION_ENDED = "session.ended"                # Logout
    SESSION_FAILED = "session.failed"              # Login failed
    SESSION_REFRESHED = "session.refreshed"        # Token refresh
    SESSION_SUSPICIOUS = "session.suspicious"      # Security alert (token theft, etc.)
    
    # ═══════════════════════════════════════════════════════════════════════
    #  DOCUMENT ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    DOCUMENT_CREATED = "document.created"          # Document uploaded/created
    DOCUMENT_UPDATED = "document.updated"          # Document metadata updated
    DOCUMENT_DELETED = "document.deleted"          # Document deleted
    DOCUMENT_DOWNLOADED = "document.downloaded"    # Document download link generated
    
    # ═══════════════════════════════════════════════════════════════════════
    #  USER ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    USER_CREATED = "user.created"                  # New user created
    USER_UPDATED = "user.updated"                  # User profile/settings updated
    USER_DELETED = "user.deleted"                  # User deleted/deactivated
    
    # ═══════════════════════════════════════════════════════════════════════
    #  ROLE ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    ROLE_CREATED = "role.created"                  # New role created
    ROLE_ASSIGNED = "role.assigned"                # Role assigned to user (especially admin roles)
    
    # ═══════════════════════════════════════════════════════════════════════
    #  2FA/TOTP ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    TOTP_ENABLED = "totp.enabled"                  # 2FA enabled (setup completed)
    TOTP_VERIFIED = "totp.verified"                # 2FA code verification attempt
    TOTP_DISABLED = "totp.disabled"                # 2FA disabled
    
    # ═══════════════════════════════════════════════════════════════════════
    #  API KEY ACTIONS
    # ═══════════════════════════════════════════════════════════════════════
    API_KEY_CREATED = "api_key.created"            # New API key created
    API_KEY_REVOKED = "api_key.revoked"            # API key revoked
    
   




# ==============================================================================
#  AUDIT RESOURCE TYPE - Types de ressources loggées
# ==============================================================================

class AuditResourceType(str, Enum):
    """
    Types de ressources loggées dans l'audit trail
    
     Utilisé dans : AuditLog.resource_type
    
     Permet de savoir SUR QUEL TYPE de ressource l'action a été effectuée
    """
    USER = "user"                           #  Utilisateur
    ROLE = "role"                           #  Rôle
    DOCUMENT = "document"                   #  Document uploadé
    TENANT = "tenant"                       #  Tenant/organisation
    AUTH_SESSION = "auth_session"           #  Session d'authentification





# ==============================================================================
#  AUDIT STATUS - Statut des actions auditées
# ==============================================================================

class AuditStatus(str, Enum):
    """
    Statut des actions auditées
    
     Utilisé dans : AuditLog.status
    
     Permet de savoir si l'action a RÉUSSI ou ÉCHOUÉ
    → Important pour l'investigation d'incidents
    """
    SUCCESS = "success"                 #  Action réussie
                                        # → L'action s'est déroulée correctement

    FAILURE = "failure"                 #  Action échouée
                                        # → Erreur lors de l'action




