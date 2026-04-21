'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { motion } from 'framer-motion'
import {
  Building2,
  ChevronDown,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  HelpCircle,
} from 'lucide-react'
import { step2Schema, type Step2Data } from '@/lib/validations/register'

interface Step2FormProps {
  onSubmit: (data: Step2Data) => void
  onBack: () => void
  isLoading?: boolean
  defaultValues?: Partial<Step2Data>
  preFillOrgName?: string
  preFillSector?: string
}

const SECTORS = [
  'Informatique & Télécommunications',
  'BTP & Travaux publics',
  'Santé & Équipement médical',
  'Énergie & Utilities',
  'Transport & Logistique',
  'Agroalimentaire',
  'Finance & Assurance',
  'Éducation & Formation',
  'Autre',
]

const PORTALS = [
  'TUNEPS',
  'CNSS',
  'ANPE',
  'Marchés GCC',
  'Portails européens',
  'Autre',
]

const SIZES = ['1-10', '11-50', '51-200', '201-500', '500+']

export default function Step2Form({
  onSubmit,
  onBack,
  isLoading = false,
  defaultValues,
  preFillOrgName,
  preFillSector,
}: Step2FormProps): JSX.Element {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    trigger,
    formState: { errors, isValid },
  } = useForm<Step2Data>({
    resolver: zodResolver(step2Schema),
    mode: 'onChange',
    defaultValues: {
      orgName: preFillOrgName || defaultValues?.orgName || '',
      sector: preFillSector || defaultValues?.sector || '',
      country: 'TN',
      orgSize: defaultValues?.orgSize,
      portals: defaultValues?.portals || [],
    },
  })

  const [sectorOpen, setSectorOpen] = useState(false)
  const [sectorFilter, setSectorFilter] = useState('')
  const [showTunepsTip, setShowTunepsTip] = useState(false)

  const sector = watch('sector')
  const orgSize = watch('orgSize')
  const portals = watch('portals')

  const filteredSectors = SECTORS.filter((s) =>
    s.toLowerCase().includes(sectorFilter.toLowerCase())
  )

  const handleSectorSelect = (s: string) => {
    setValue('sector', s)
    setSectorOpen(false)
    setSectorFilter('')
    // Trigger validation after sector selection
    trigger('sector')
  }

  const handlePortalToggle = (portal: string) => {
    const newPortals = portals?.includes(portal)
      ? portals.filter((p: string) => p !== portal)
      : [...(portals || []), portal]
    setValue('portals', newPortals)
    // Trigger validation after setting portals
    trigger('portals')
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
    >
      <h1 className="text-2xl font-bold text-navy mb-2">Votre organisation</h1>
      <p className="text-muted text-sm mb-6">Décrivez le contexte de votre équipe</p>

      <form onSubmit={handleSubmit((data: any) => onSubmit(data as Step2Data))} className="space-y-4">
        {/* Organization name */}
        <div>
          <label htmlFor="orgName" className="block text-xs font-semibold text-navy mb-1.5">
            Nom de l'organisation
          </label>
          <div className="relative">
            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <input
              {...register('orgName')}
              id="orgName"
              type="text"
              placeholder="Ex: Groupe Sfax Industries"
              className={`w-full pl-10 pr-4 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-3 transition-all ${
                errors.orgName
                  ? 'border-danger focus:ring-danger/20'
                  : 'border-cream-border focus:ring-amber/20 focus:border-amber'
              }`}
            />
          </div>
          {errors.orgName && (
            <p className="text-xs text-danger mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.orgName.message}
            </p>
          )}
          {preFillOrgName && (
            <p className="text-xs text-amber/60 mt-1">
              Domaine détecté — vous pouvez modifier
            </p>
          )}
        </div>

        {/* Sector combobox */}
        <div>
          <label className="block text-xs font-semibold text-navy mb-1.5">
            Secteur d'activité
          </label>
          <div className="relative">
            <button
              type="button"
              onClick={() => setSectorOpen(!sectorOpen)}
              className={`w-full px-4 py-3 rounded-xl border bg-white text-sm text-left flex items-center justify-between transition-all ${
                errors.sector
                  ? 'border-danger focus:ring-danger/20'
                  : 'border-cream-border focus:ring-amber/20 focus:border-amber'
              }`}
            >
              <span className={sector ? 'text-navy' : 'text-muted/50'}>
                {sector || 'Sélectionner un secteur'}
              </span>
              <ChevronDown
                className={`w-4 h-4 transition-transform ${
                  sectorOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            {sectorOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-cream-border rounded-xl shadow-lg z-50">
                {/* Filter input */}
                <div className="p-2 border-b border-cream-border">
                  <input
                    type="text"
                    placeholder="Rechercher..."
                    value={sectorFilter}
                    onChange={(e) => setSectorFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-cream-border rounded-lg text-sm placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-amber/20"
                  />
                </div>

                {/* Options */}
                <div ref={(el) => el?.scrollIntoView?.()} className="max-h-48 overflow-y-auto">
                  {filteredSectors.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => handleSectorSelect(s)}
                      className="w-full text-left px-4 py-2 text-sm text-navy hover:bg-cream transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          {errors.sector && (
            <p className="text-xs text-danger mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.sector.message}
            </p>
          )}
        </div>

        {/* Country — static display */}
        <div>
          <label className="block text-xs font-semibold text-navy mb-1.5">
            Pays principal
          </label>
          <div className="px-4 py-3 rounded-xl border border-cream-border bg-cream-bg text-sm text-navy flex items-center gap-2">
            <span>🇹🇳</span>
            Tunisie
          </div>
        </div>

        {/* Organization size — pill buttons */}
        <div>
          <label className="block text-xs font-semibold text-navy mb-2">
            Taille de l'organisation
          </label>
          <div className="flex flex-wrap gap-2">
            {SIZES.map((size) => (
              <button
                key={size}
                type="button"
                onClick={() => setValue('orgSize', size as Step2Data['orgSize'])}
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                  orgSize === size
                    ? 'bg-amber text-white border-amber'
                    : 'bg-white text-navy border-cream-border hover:border-amber/50'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
          {errors.orgSize && (
            <p className="text-xs text-danger mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.orgSize.message}
            </p>
          )}
        </div>

        {/* Portals — checkbox grid */}
        <div>
          <label className="block text-xs font-semibold text-navy mb-2">
            Portails d'appels d'offres utilisés
          </label>
          <div className="grid grid-cols-2 gap-3">
            {PORTALS.map((portal) => (
              <label
                key={portal}
                className="flex items-center gap-2 cursor-pointer relative"
              >
                <input
                  type="checkbox"
                  checked={portals?.includes(portal) || false}
                  onChange={() => handlePortalToggle(portal)}
                  className="accent-amber"
                />
                <span className="text-sm text-navy">
                  {portal}
                  {portal === 'TUNEPS' && (
                    <button
                      type="button"
                      onMouseEnter={() => setShowTunepsTip(true)}
                      onMouseLeave={() => setShowTunepsTip(false)}
                      className="ml-1 inline-block"
                    >
                      <HelpCircle className="w-3 h-3 text-muted hover:text-amber" />
                    </button>
                  )}
                </span>

                {/* Tooltip */}
                {portal === 'TUNEPS' && showTunepsTip && (
                  <div className="absolute bottom-full left-0 mb-2 p-2 bg-navy text-white text-xs rounded-lg whitespace-nowrap z-50 shadow-lg">
                    Votre identifiant TUNEPS se trouve dans votre espace entreprise
                    sur tuneps.nat.tn
                    <div className="absolute top-full left-2 w-2 h-2 bg-navy -mt-1" />
                  </div>
                )}
              </label>
            ))}
          </div>
          {errors.portals && (
            <p className="text-xs text-danger mt-2 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.portals.message}
            </p>
          )}
        </div>

        {/* Navigation */}
        <div className="flex gap-3 mt-6">
          <button
            type="button"
            onClick={onBack}
            className="flex-1 py-3.5 bg-white text-navy font-semibold rounded-xl border border-cream-border hover:border-amber/50 transition-all flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour
          </button>
          <button
            type="submit"
            disabled={!isValid || isLoading}
            className="flex-1 py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            Continuer
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </motion.div>
  )
}
