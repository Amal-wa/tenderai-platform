// ──────────────────────────────────────────────────────────────────────────
// Domain Detection — Extract org name and sector from email domain
// ──────────────────────────────────────────────────────────────────────────

interface DomainDetectionResult {
  orgName: string
  sector: string
}

const DOMAIN_MAP: Record<string, DomainDetectionResult> = {
  'steg.com.tn': {
    orgName: 'STEG',
    sector: 'Énergie & Utilities',
  },
  'tunisietelecom.tn': {
    orgName: 'Tunisie Telecom',
    sector: 'Informatique & Télécommunications',
  },
  'oaca.nat.tn': {
    orgName: 'OACA',
    sector: 'Transport & Logistique',
  },
  'cnam.nat.tn': {
    orgName: 'CNAM',
    sector: 'Santé & Équipement médical',
  },
  'supcom.tn': {
    orgName: 'Sup\'Com',
    sector: 'Informatique & Télécommunications',
  },
  'sonede.com.tn': {
    orgName: 'SONEDE',
    sector: 'Énergie & Utilities',
  },
}

export function detectDomainOrg(
  email: string
): DomainDetectionResult | null {
  const domain = email.split('@')[1]?.toLowerCase()
  if (!domain) return null

  return DOMAIN_MAP[domain] || null
}
