import { ReactNode } from 'react'
import AuthLayout from '@/components/auth/AuthLayout'
import ForgotPasswordForm from '@/components/auth/ForgotPasswordForm'

export const metadata = {
  title: 'Mot de passe oublié · TenderAI',
  description: 'Réinitialisez votre mot de passe TenderAI',
}

export default function ForgotPasswordPage(): ReactNode {
  return (
    <AuthLayout>
      <ForgotPasswordForm />
    </AuthLayout>
  )
}
