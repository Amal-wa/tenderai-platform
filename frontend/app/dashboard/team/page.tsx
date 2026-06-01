'use client'

import { useState, useEffect } from 'react'
import { Users, Plus, Trash2, Loader2 } from 'lucide-react'
import { extractErrorMessage, deleteMember } from '@/lib/api'
import { useAdminAccess } from '@/hooks/useAdminAccess'
import InviteMemberModal from '@/components/team/InviteMemberModal'

interface TeamMember {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
  last_login_at?: string
}

export default function TeamPage(): JSX.Element {
  const { isLoading, user, isAdmin } = useAdminAccess()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [members, setMembers] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isDeleting, setIsDeleting] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [confirmTarget, setConfirmTarget] = useState<TeamMember | null>(null)

  const getRoleName = (role: any): string => {
    if (!role) return ''
    if (typeof role === 'string') return role
    if (role && typeof role === 'object' && role.name) return role.name
    return ''
  }

  const roleName = getRoleName(user?.role)
  const isSuperAdmin = roleName === 'superadmin'

  const canDeleteMember = (memberId: string): boolean =>
    isSuperAdmin && memberId !== user?.id
 
  useEffect(() => {
    if (user?.tenant_id && isAdmin) {
      fetchMembers()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.tenant_id, isAdmin])

  const fetchMembers = async (): Promise<void> => {
    try {
      setLoading(true)
      setError('')

      if (!user?.tenant_id) {
        setError('Tenant non trouvé')
        setLoading(false)
        return
      }

      const apiInstance = (await import('@/lib/api')).default

      if (!apiInstance) {
        throw new Error('API not available')
      }

      const response = await apiInstance.get(`/api/v1/${user.tenant_id}/users`)
      const data = response?.data

      if (!data) {
        setMembers([])
        return
      }

      if (Array.isArray(data?.items)) {
        setMembers(data.items)
      } else if (Array.isArray(data?.users)) {
        setMembers(data.users)
      } else if (Array.isArray(data)) {
        setMembers(data)
      } else if (Array.isArray(data?.members)) {
        setMembers(data.members)
      } else {
        setMembers([])
      }
    } catch (err) {
      const errorMsg = extractErrorMessage(err)
      setError(errorMsg || 'Erreur lors du chargement des membres')
      console.error('Error fetching team members:', err)
      setMembers([])
    } finally {
      setLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
          <p className="mt-4 text-sm text-gray-600">Chargement de vos données...</p>
        </div>
      </div>
    )
  }

  // After loading, if user is not set, show error
  if (!user) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div
          className="rounded-lg border p-6 text-center"
          style={{
            backgroundColor: 'var(--color-background-primary, #F5F3EE)',
            borderColor: 'var(--color-border-tertiary, #E5E0D8)',
          }}
        >
          <h2 className="text-lg font-semibold" style={{ color: 'var(--navy, #0F1C35)' }}>
            Erreur de chargement
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Une erreur est survenue lors de l'authentification. Veuillez réessayer.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 rounded text-white text-sm"
            style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
          >
            Rafraîchir
          </button>
        </div>
      </div>
    )
  }
  
  // Check if admin
  if (!isAdmin) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div
          className="rounded-lg border p-6 text-center"
          style={{
            backgroundColor: 'var(--color-background-primary, #F5F3EE)',
            borderColor: 'var(--color-border-tertiary, #E5E0D8)',
          }}
        >
          <h2 className="text-lg font-semibold" style={{ color: 'var(--navy, #0F1C35)' }}>
            Accès réservé
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Seuls les administrateurs peuvent gérer l'équipe.
          </p>
        </div>
      </div>
    )
  }

 

  const handleInviteSuccess = (_email: string): void => {
    fetchMembers()
  }

  const handleDelete = async (memberId: string): Promise<void> => {
    try {
      setIsDeleting(memberId)
      setDeleteError(null)
      setConfirmTarget(null)
      await deleteMember(memberId)
      setMembers(prev => prev.filter(m => m.id !== memberId))
    } catch (err) {
      setDeleteError(extractErrorMessage(err))
    } finally {
      setIsDeleting(null)
    }
  }

  return (
    <div className="flex-1 space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-heading font-semibold" style={{ color: 'var(--navy, #0F1C35)' }}>
            <Users size={32} style={{ color: 'var(--amber, #C4962A)' }} />
            Équipe
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Gérez les membres de votre organisation
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors"
          style={{
            backgroundColor: 'var(--navy, #0F1C35)',
            color: 'white',
          }}
        >
          <Plus size={20} />
          Inviter un membre
        </button>
      </div>

      {error && (
        <div className="rounded-md border p-4" style={{ borderColor: '#E24B4A', backgroundColor: '#FCEAEA' }}>
          <p className="text-sm font-medium" style={{ color: '#E24B4A' }}>
            {error}
          </p>
          <button
            onClick={() => fetchMembers()}
            className="mt-2 text-xs font-semibold underline"
            style={{ color: '#E24B4A' }}
          >
            Réessayer
          </button>
        </div>
      )}

      {deleteError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {deleteError}
        </div>
      )}

      {loading ? (
        <div className="rounded-lg border" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div className="flex items-center justify-center p-12">
            <p className="text-gray-500">Chargement des membres...</p>
          </div>
        </div>
      ) : members.length === 0 ? (
        <div
          className="rounded-lg border p-12 text-center"
          style={{
            backgroundColor: 'var(--color-background-primary, #F5F3EE)',
            borderColor: 'var(--color-border-tertiary, #E5E0D8)',
          }}
        >
          <Users size={48} className="mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-semibold" style={{ color: 'var(--navy, #0F1C35)' }}>
            Aucun membre trouvé
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            Commencez en invitant votre premier membre de l'équipe.
          </p>
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <table className="w-full">
            <thead>
              <tr style={{ backgroundColor: 'var(--color-background-secondary, #EDE9E2)', borderBottomColor: 'var(--color-border-tertiary, #E5E0D8)', borderBottomWidth: '1px' }}>
                <th className="px-6 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                  Nom
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                  Rôle
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                  Statut
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                  Dernière connexion
                </th>
                {isSuperAdmin && (
                  <th className="px-6 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr
                  key={member.id}
                  style={{
                    borderBottomColor: 'var(--color-border-tertiary, #E5E0D8)',
                    borderBottomWidth: '0.5px',
                  }}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-4 text-sm font-medium" style={{ color: 'var(--navy, #0F1C35)' }}>
                    {member.full_name || 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {member.email}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: 'var(--amber-soft, rgba(196,150,42,0.10))',
                        color: 'var(--amber, #C4962A)',
                      }}
                    >
                      {typeof member.role === 'object' && member.role !== null
                        ? (member.role as { name: string }).name
                        : member.role || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        member.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {member.is_active ? 'Actif' : 'Inactif'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {member.last_login_at ? new Date(member.last_login_at).toLocaleDateString('fr-FR') : 'Jamais'}
                  </td>
                  {isSuperAdmin && (
                    <td className="px-6 py-4 text-sm">
                      {canDeleteMember(member.id) && (
                        <button
                          onClick={() => setConfirmTarget(member)}
                          disabled={isDeleting === member.id}
                          className="p-1.5 rounded-md text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-40"
                          aria-label={`Supprimer ${member.full_name}`}
                        >
                          {isDeleting === member.id
                            ? <Loader2 className="w-4 h-4 animate-spin" />
                            : <Trash2 className="w-4 h-4" />
                          }
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Invite Member Modal */}
      <InviteMemberModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleInviteSuccess}
      />

      {/* Delete Member Confirmation Modal */}
      {confirmTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-xl border border-gray-200 mx-4">
            <h3 className="text-base font-semibold text-navy mb-2" style={{ color: 'var(--navy, #0F1C35)' }}>
              Supprimer {confirmTarget.full_name} ?
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Cette action est irréversible. Le membre perdra immédiatement l'accès à l'organisation.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmTarget(null)}
                className="px-4 py-2 text-sm font-medium text-navy border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                style={{ color: 'var(--navy, #0F1C35)', borderColor: 'var(--navy, #0F1C35)' }}
              >
                Annuler
              </button>
              <button
                onClick={() => handleDelete(confirmTarget.id)}
                disabled={isDeleting === confirmTarget.id}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
