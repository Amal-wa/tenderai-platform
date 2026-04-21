import { Suspense } from 'react'
import LoginPageClient from '@/components/auth/LoginPageClient'

export const metadata = {
  title: 'Connexion · TenderAI',
  description: 'Connectez-vous à votre espace TenderAI',
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Chargement...</div>}>
      <LoginPageClient />
    </Suspense>
  )
}
