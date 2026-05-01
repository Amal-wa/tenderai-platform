'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Upload } from 'lucide-react'
import api, { extractErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import { useSettings } from '@/hooks/useSettings'
import type { TenantSettings } from '@/types/settings'

// ─── Shared primitives ────────────────────────────────────────────────────────

const card = 'border rounded-lg p-5'
const cardBorder = { borderColor: 'var(--color-border-tertiary, #E5E0D8)' }
const navy = { backgroundColor: 'var(--navy, #0F1C35)', color: '#C4962A' }
const inputStyle = {
  borderColor: 'var(--color-border-secondary, #E5E0D8)',
  backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
  color: 'var(--color-text-primary, #0F1C35)',
}

function CardHeader({ title, sub }: { title: string; sub: string }) {
  return (
    <div className="mb-4">
      <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>{title}</p>
      <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>{sub}</p>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
        {label}
      </label>
      {children}
    </div>
  )
}

function Banner({ type, msg }: { type: 'success' | 'error'; msg: string }) {
  const styles =
    type === 'success'
      ? { backgroundColor: '#E1F5EE', color: '#1D9E75' }
      : { backgroundColor: '#FCEAEA', color: '#E24B4A' }
  return <div className="p-3 rounded text-xs font-medium" style={styles}>{msg}</div>
}

function RowActions({ onCancel, onSave, saving }: { onCancel: () => void; onSave: () => void; saving: boolean }) {
  return (
    <div className="flex justify-end gap-2 pt-3 border-t" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
      <button onClick={onCancel} className="px-4 py-2 text-xs font-medium rounded border" style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}>
        Annuler
      </button>
      <button onClick={onSave} disabled={saving} className="px-4 py-2 text-xs font-medium rounded" style={navy}>
        {saving ? 'Enregistrement...' : 'Enregistrer'}
      </button>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function OrganisationSection({
  onDirtyChange,
}: {
  isDirty: boolean
  onDirtyChange: (dirty: boolean) => void
}) {
  const router = useRouter()
  const { user } = useAuth()
  const { getTenantSettings, updateTenantSettings, uploadTenantLogo } = useSettings()
  const fileRef = useRef<HTMLInputElement>(null)

  const [tenant, setTenant] = useState<TenantSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [formData, setFormData] = useState({ name: '', sector: '', country: '' })
  const [preview, setPreview] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [uploadFeedback, setUploadFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [usersCount, setUsersCount] = useState(0)

  useEffect(() => {
    getTenantSettings()
      .then(res => {
        const t = res.data
        setTenant(t)
        setFormData({ name: t.name, sector: t.sector ?? '', country: t.country ?? '' })
        if (t.tenant_metadata?.logo_url) setPreview(t.tenant_metadata.logo_url)
      })
      .catch(err => setFeedback({ type: 'error', msg: extractErrorMessage(err) }))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!user?.tenant_id) return
    api.get(`/api/v1/${user.tenant_id}/users`)
      .then(res => {
        const users = res.data.users || res.data
        setUsersCount(Array.isArray(users) ? users.length : 0)
      })
      .catch(err => console.error('Failed to fetch users:', extractErrorMessage(err)))
  }, [user?.tenant_id])

  const userRole = typeof user?.role === 'string' ? user.role : user?.role?.name ?? ''
  if (!['admin', 'superadmin'].includes(userRole)) {
    return (
      <div className="flex items-center justify-center p-8 text-center">
        <div>
          <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>Accès restreint</p>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>Section réservée aux administrateurs</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return <div className="flex items-center justify-center p-8 text-xs" style={{ color: 'var(--color-text-secondary)' }}>Chargement...</div>
  }

  const patch = (key: keyof typeof formData, val: string) => {
    setFormData(prev => ({ ...prev, [key]: val }))
    onDirtyChange(true)
  }

  const handleSave = async () => {
    setSaving(true)
    setFeedback(null)
    try {
      await updateTenantSettings(formData)
      setFeedback({ type: 'success', msg: 'Organisation mise à jour' })
      onDirtyChange(false)
    } catch (err) {
      setFeedback({ type: 'error', msg: extractErrorMessage(err) })
    } finally {
      setSaving(false)
    }
  }

  const handleLogoUpload = async (file: File) => {
    if (!['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml'].includes(file.type))
      return setUploadFeedback({ type: 'error', msg: 'Format non supporté. Utilisez PNG, JPEG, WebP ou SVG' })
    if (file.size > 2 * 1024 * 1024)
      return setUploadFeedback({ type: 'error', msg: 'Fichier trop volumineux (max 2 MB)' })

    setUploading(true)
    setUploadFeedback(null)
    try {
      const res = await uploadTenantLogo(file)
      setPreview(res.data.logo_url)
      setUploadFeedback({ type: 'success', msg: 'Logo mis à jour' })
    } catch (err) {
      setUploadFeedback({ type: 'error', msg: extractErrorMessage(err) })
    } finally {
      setUploading(false)
    }
  }

  const handleLogoDelete = async () => {
    try {
      await updateTenantSettings({
        tenant_metadata: { ...tenant?.tenant_metadata, logo_url: null, logo_path: null },
      })
      setPreview(null)
    } catch (err) {
      setUploadFeedback({ type: 'error', msg: extractErrorMessage(err) })
    }
  }

  const selectClass = 'w-full h-8 px-2.5 border rounded text-sm'

  return (
    <div className="space-y-6">

      {/* ── Card 1 — Org info ── */}
      <div className={card} style={cardBorder}>
        <CardHeader title="Informations de l'organisation" sub="Données de votre workspace TenderAI" />
        <div className="space-y-3">
          <Field label="Nom de l'organisation">
            <input value={formData.name} onChange={e => patch('name', e.target.value)}
              type="text" className="w-full h-8 px-2.5 border rounded text-sm" style={inputStyle} />
          </Field>
          <Field label="Identifiant (slug)">
            <input value={tenant?.id ?? ''} disabled type="text"
              className="w-full h-8 px-2.5 border rounded text-sm opacity-60" style={inputStyle} />
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>Non modifiable après création</p>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Secteur">
              <select value={formData.sector} onChange={e => patch('sector', e.target.value)} className={selectClass} style={inputStyle}>
                <option value="">Sélectionner...</option>
                <option value="education">Enseignement supérieur</option>
                <option value="public">Administration publique</option>
                <option value="construction">BTP / Génie civil</option>
                <option value="health">Santé</option>
                <option value="tech">Technologie</option>
              </select>
            </Field>
            <Field label="Pays">
              <select value={formData.country} onChange={e => patch('country', e.target.value)} className={selectClass} style={inputStyle}>
                <option value="">Sélectionner...</option>
                <option value="TN">Tunisie</option>
                <option value="MA">Maroc</option>
                <option value="DZ">Algérie</option>
                <option value="FR">France</option>
              </select>
            </Field>
          </div>
          {feedback && <Banner type={feedback.type} msg={feedback.msg} />}
          <RowActions onCancel={() => onDirtyChange(false)} onSave={handleSave} saving={saving} />
        </div>
      </div>

      {/* ── Card 2 — Logo ── */}
      <div className={card} style={cardBorder}>
        <CardHeader title="Logo de l'organisation" sub="Formats acceptés : PNG, JPEG, WebP, SVG — max 2 MB" />
        <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml"
          onChange={e => e.target.files?.[0] && handleLogoUpload(e.target.files[0])} hidden />

        {preview ? (
          <div className="flex items-center gap-4">
            <img src={preview} alt="Logo" className="h-20 w-20 object-contain border rounded" style={cardBorder} />
            <div className="flex gap-2">
              <button onClick={() => fileRef.current?.click()} disabled={uploading}
                className="px-3 py-1 text-xs font-medium rounded border"
                style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}>
                {uploading ? 'Upload...' : 'Remplacer'}
              </button>
              <button onClick={handleLogoDelete}
                className="px-3 py-1 text-xs font-medium rounded border"
                style={{ borderColor: '#E24B4A', color: '#E24B4A' }}>
                Supprimer
              </button>
            </div>
          </div>
        ) : (
          <div onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:opacity-80 transition"
            style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', backgroundColor: 'var(--color-background-secondary, #F5F3EE)' }}>
            <Upload size={24} className="mx-auto mb-2" style={{ color: 'var(--color-text-tertiary)' }} />
            <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
              Glissez votre logo ici ou cliquez pour parcourir
            </p>
          </div>
        )}
        {uploadFeedback && <div className="mt-3"><Banner type={uploadFeedback.type} msg={uploadFeedback.msg} /></div>}
      </div>

      {/* ── Card 3 — Members ── */}
      <div className={card} style={cardBorder}>
        <div className="flex items-center justify-between mb-4">
          <CardHeader title="Membres" sub={`${usersCount} ${usersCount === 1 ? 'membre' : 'membres'} actif${usersCount !== 1 ? 's' : ''}`} />
          <button onClick={() => router.push('/dashboard/team')} className="px-3 py-1 text-xs font-medium rounded" style={navy}>+ Inviter</button>
        </div>
      </div>

    </div>
  )
}