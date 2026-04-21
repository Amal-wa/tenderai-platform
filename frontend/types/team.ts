// =============================================================================
// types/team.ts — Type definitions for team management
// =============================================================================

export type InviteRole = 'admin' | 'manager' | 'analyst' | 'contributor' | 'viewer'

export interface InviteMemberPayload {
  email: string
  role: InviteRole
  message?: string
}

export interface InviteMemberModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (email: string) => void
}

export const ROLE_DESCRIPTIONS: Record<InviteRole, string> = {
  admin: 'Accès complet à l\'administration et gestion de l\'équipe',
  manager: 'Peut gérer les AO, valider les documents, inviter des membres',
  analyst: 'Peut analyser les AO et générer des rapports',
  contributor: 'Peut soumettre des documents et compléter des tâches',
  viewer: 'Accès lecture seule à tous les AO du tenant',
}

export const INVITE_ROLES: InviteRole[] = ['admin', 'manager', 'analyst', 'contributor', 'viewer']
