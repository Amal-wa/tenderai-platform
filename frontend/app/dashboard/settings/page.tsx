import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import SettingsClient from './SettingsClient'

export const metadata: Metadata = {
  title: 'Paramètres - TenderAI',
  description: 'Gérez vos paramètres personnels, sécurité et organisation',
}

export default async function SettingsPage() {
  const cookieStore = await cookies()
  const hasToken = cookieStore.has('access_token')

  if (!hasToken) {
    redirect('/login')
  }

  return <SettingsClient />
}
