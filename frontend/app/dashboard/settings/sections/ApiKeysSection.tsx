'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useSettings } from '@/hooks/useSettings'
import { extractErrorMessage } from '@/lib/api'
import type { APIKey, APIKeyCreateRequest } from '@/types/settings'
import { Copy, Trash2, X } from 'lucide-react'

export default function ApiKeysSection({ onDirtyChange: _onDirtyChange }: { isDirty: boolean; onDirtyChange: (dirty: boolean) => void }) {
  const { user } = useAuth()
  const { listApiKeys, createApiKey, revokeApiKey } = useSettings()
  const [keys, setKeys] = useState<APIKey[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createModal, setCreateModal] = useState(false)
  const [displayModal, setDisplayModal] = useState(false)
  const [displayedKey, setDisplayedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createForm, setCreateForm] = useState({ name: '', scopes: [] as string[], expires_at: '' })

  const isAuthorized = ['admin', 'superadmin', 'manager'].includes(
    typeof user?.role === 'string' ? user.role : user?.role?.name || ''
  )

useEffect(() => {
  if (!isAuthorized) return
  const load = async () => {
    try {
      const res = await listApiKeys()
      setKeys(res.data)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }
  load()
}, [isAuthorized]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!isAuthorized) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
            Accès restreint
          </div>
          <div className="text-xs mt-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Section réservée aux administrateurs
          </div>
        </div>
      </div>
    )
  }

  const handleCreate = async () => {
    setCreating(true)
    setError(null)

    try {
      const res = await createApiKey({
        name: createForm.name,
        permissions: createForm.scopes,
        expires_at: createForm.expires_at || undefined,
      } as APIKeyCreateRequest)

      // Close create modal
      setCreateModal(false)
      setCreateForm({ name: '', scopes: [], expires_at: '' })

      // Show one-time display modal
      setDisplayedKey(res.data.key)
      setDisplayModal(true)

      // Refresh list
      const listRes = await listApiKeys()
      setKeys(listRes.data)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setCreating(false)
    }
  }

  const handleCopy = async () => {
    if (displayedKey) {
      await navigator.clipboard.writeText(displayedKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleRevoke = async (keyId: string) => {
    if (!confirm('Révoquer cette clé ? Elle ne sera plus utilisable.')) return

    try {
      await revokeApiKey(keyId)
      setKeys(keys.map(k => (k.id === keyId ? { ...k, revoked_at: new Date().toISOString() } : k)))
    } catch (err) {
      setError(extractErrorMessage(err))
    }
  }

  const scopes = [
    { value: 'documents:read', label: 'Lire les documents', desc: 'Accès en lecture aux documents importés' },
    { value: 'documents:write', label: 'Modifier les documents', desc: 'Upload et modification des documents' },
    { value: 'reports:read', label: 'Rapports de conformité', desc: 'Accès aux rapports de conformité' },
    { value: 'audit:read', label: 'Logs d\'audit', desc: 'Consultation des logs d\'audit' },
  ]

  return (
    <div className="space-y-6">
      {/* Card 1 — Keys List */}
      <div className="border rounded-lg" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        <div className="flex items-center justify-between p-5 border-b" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div>
            <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
              Clés API
            </div>
            <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
              Gérez vos clés d'accès à l'API TenderAI
            </div>
          </div>
          <button
            onClick={() => setCreateModal(true)}
            className="px-3 py-1.5 text-xs font-medium rounded text-white"
            style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
          >
            + Créer une clé
          </button>
        </div>

        {error && (
          <div className="px-5 py-3 border-b" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)', backgroundColor: 'var(--color-danger-bg, #FCEAEA)' }}>
            <div className="text-xs font-medium" style={{ color: 'var(--color-danger, #E24B4A)' }}>
              {error}
            </div>
          </div>
        )}

        {loading ? (
          <div className="p-5 text-xs text-center" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Chargement...
          </div>
        ) : keys.length === 0 ? (
          <div className="p-5 text-xs text-center" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Aucune clé API créée
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ backgroundColor: 'var(--color-bg-secondary, #F5F3EE)' }}>
                  <th className="px-5 py-2 text-left text-xs font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                    Nom
                  </th>
                  <th className="px-5 py-2 text-left text-xs font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                    Clé
                  </th>
                  <th className="px-5 py-2 text-left text-xs font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                    Permissions
                  </th>
                  <th className="px-5 py-2 text-left text-xs font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                    Dernière utilisée
                  </th>
                  <th className="px-5 py-2 text-left text-xs font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                    Statut
                  </th>
                  <th className="px-5 py-2 text-left text-xs font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {keys.map(key => (
                  <tr key={key.id} style={{ borderTop: '1px solid var(--color-border-tertiary, #E5E0D8)' }}>
                    <td className="px-5 py-3 text-xs" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                      {key.name}
                    </td>
                    <td className="px-5 py-3 text-xs font-mono" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                      {key.prefix}••••••••
                    </td>
                    <td className="px-5 py-3 text-xs" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                      {key.permissions?.length || 0} permissions
                    </td>
                    <td className="px-5 py-3 text-xs" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                      {key.last_used_at ? new Date(key.last_used_at).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td className="px-5 py-3 text-xs">
                      {key.revoked_at ? (
                        <span className="px-2 py-0.5 rounded" style={{ backgroundColor: '#E5E0D8', color: 'var(--color-text-secondary, #3A3530)' }}>
                          Révoquée
                        </span>
                      ) : key.last_used_at ? (
                        <span className="px-2 py-0.5 rounded" style={{ backgroundColor: 'var(--success-bg, #E1F5EE)', color: 'var(--success, #1D9E75)' }}>
                          Actif
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded" style={{ backgroundColor: '#F0F0F0', color: 'var(--color-text-secondary, #3A3530)' }}>
                          Inactif
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-xs">
                      <div className="flex gap-2">
                        <button
                          onClick={() => navigator.clipboard.writeText(key.prefix)}
                          className="p-1 rounded hover:opacity-60 transition"
                          title="Copier le préfixe"
                        >
                          <Copy size={14} style={{ color: 'var(--color-text-secondary, #3A3530)' }} />
                        </button>
                        {!key.revoked_at && (
                          <button
                            onClick={() => handleRevoke(key.id)}
                            className="p-1 rounded hover:opacity-60 transition"
                            title="Révoquer"
                          >
                            <Trash2 size={14} style={{ color: 'var(--color-danger, #E24B4A)' }} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Card 2 — Available Scopes */}
      <div className="border rounded-lg p-5" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        <div className="mb-4">
          <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
            Permissions disponibles
          </div>
          <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Ces permissions contrôlent l'accès API de votre clé
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {scopes.map(scope => (
            <div
              key={scope.value}
              className="p-3 border rounded"
              style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)' }}
            >
              <div className="text-xs font-medium font-mono" style={{ color: 'var(--navy, #0F1C35)' }}>
                {scope.value}
              </div>
              <div className="text-xs mt-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                {scope.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Create Modal */}
      {createModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-96 p-5" style={{ backgroundColor: 'var(--color-bg-primary, #FFFFFF)' }}>
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                Créer une nouvelle clé API
              </div>
              <button onClick={() => setCreateModal(false)} className="p-1">
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                  Nom
                </label>
                <input
                  value={createForm.name}
                  onChange={e => setCreateForm({ ...createForm, name: e.target.value })}
                  type="text"
                  placeholder="Mon application"
                  className="w-full h-8.5 px-2.5 border rounded text-xs"
                  style={{
                    borderColor: 'var(--color-border-secondary, #E5E0D8)',
                    backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                    color: 'var(--color-text-primary, #0F1C35)',
                  }}
                />
              </div>

              <div>
                <label className="text-xs font-medium block mb-2" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                  Permissions
                </label>
                <div className="flex flex-wrap gap-2">
                  {scopes.map(scope => (
                    <button
                      key={scope.value}
                      onClick={() => {
                        setCreateForm({
                          ...createForm,
                          scopes: createForm.scopes.includes(scope.value)
                            ? createForm.scopes.filter(s => s !== scope.value)
                            : [...createForm.scopes, scope.value],
                        })
                      }}
                      className="px-2.5 py-1 text-xs rounded border transition"
                      style={{
                        backgroundColor: createForm.scopes.includes(scope.value) ? 'var(--amber, #C4962A)' : 'transparent',
                        borderColor: createForm.scopes.includes(scope.value) ? 'var(--amber, #C4962A)' : 'var(--color-border-secondary, #E5E0D8)',
                        color: createForm.scopes.includes(scope.value) ? 'white' : 'var(--color-text-secondary, #3A3530)',
                      }}
                    >
                      {scope.value}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                  Expiration (optionnel)
                </label>
                <input
                  value={createForm.expires_at}
                  onChange={e => setCreateForm({ ...createForm, expires_at: e.target.value })}
                  type="date"
                  className="w-full h-8.5 px-2.5 border rounded text-xs"
                  style={{
                    borderColor: 'var(--color-border-secondary, #E5E0D8)',
                    backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                    color: 'var(--color-text-primary, #0F1C35)',
                  }}
                />
              </div>
            </div>

            <div className="flex gap-2 justify-end mt-5 pt-5 border-t" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <button
                onClick={() => setCreateModal(false)}
                className="px-4 py-2 text-xs font-medium rounded border"
                style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
              >
                Annuler
              </button>
              <button
                onClick={handleCreate}
                disabled={creating || !createForm.name}
                className="px-4 py-2 text-xs font-medium rounded text-white"
                style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
              >
                {creating ? 'Création...' : 'Créer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* One-Time Display Modal */}
      {displayModal && displayedKey && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-96 p-5" style={{ backgroundColor: 'var(--color-bg-primary, #FFFFFF)' }}>
            <div className="p-3 rounded mb-4 flex gap-2" style={{ backgroundColor: 'var(--amber-bg, #FFF8E1)', borderLeft: '3px solid var(--amber, #C4962A)' }}>
              <div style={{ color: 'var(--amber, #C4962A)' }}>⚠️</div>
              <div style={{ color: 'var(--amber, #C4962A)' }} className="text-xs font-medium">
                Cette clé ne sera jamais affichée à nouveau — copie-la maintenant
              </div>
            </div>

            <div className="mb-4">
              <label className="text-xs font-medium block mb-2" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                Votre clé API
              </label>
              <input
                value={displayedKey}
                readOnly
                type="text"
                className="w-full h-8.5 px-2.5 border rounded text-xs font-mono"
                style={{
                  borderColor: 'var(--color-border-secondary, #E5E0D8)',
                  backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                  color: 'var(--color-text-primary, #0F1C35)',
                }}
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="flex-1 px-3 py-2 text-xs font-medium rounded text-white"
                style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
              >
                {copied ? '✓ Copié' : 'Copier la clé'}
              </button>
              <button
                onClick={() => {
                  setDisplayModal(false)
                  setDisplayedKey(null)
                }}
                className="px-3 py-2 text-xs font-medium rounded border"
                style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
