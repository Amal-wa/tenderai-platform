'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import type { AxiosError } from 'axios'
import { useRegisterWizard } from '@/lib/hooks/useRegisterWizard'
import { registerUser, RegisterUserPayload, extractErrorMessage } from '@/lib/api'
import RegisterLeftPanel from '@/components/auth/RegisterLeftPanel'
import Step1Form from '@/components/auth/steps/Step1Form'
import Step2Form from '@/components/auth/steps/Step2Form'
import Step3Form from '@/components/auth/steps/Step3Form'
import Step4Confirm from '@/components/auth/steps/Step4Confirm'
import { detectDomainOrg } from '@/lib/utils/domainDetect'

export default function RegisterWizard(): JSX.Element {
  const router = useRouter()
  const wizard = useRegisterWizard()
  const [error, setError] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Clear any stale form data on first mount
  useEffect(() => {
    // Always clear draft on component mount to prevent showing stuck state from failed submission
    // This ensures fresh form state and allows browser autofill to restore fields if user wants
    wizard.clearDraft()
  }, [])

  // Detect org info from email domain if available
  const domainMatch = detectDomainOrg(wizard.data.email || '')

  // Handle step 1 submission
  const handleStep1 = (data: any) => {
    setError('')
    wizard.updateData(data)
    wizard.next()
  }

  // Handle step 2 submission
  const handleStep2 = (data: any) => {
    setError('')
    wizard.updateData(data)
    wizard.next()
  }

  // Handle step 3 submission
  const handleStep3 = (data: any) => {
    setError('')
    wizard.updateData(data)
    wizard.next()
  }

  // Handle final submission
  const handleFinalSubmit = async () => {
    setError('')
    setIsSubmitting(true)

    try {
      const payload: RegisterUserPayload = {
        first_name: wizard.data.firstName || '',
        last_name: wizard.data.lastName || '',
        email: wizard.data.email || '',
        password: wizard.data.password || '',
        org_name: wizard.data.orgName || '',
        sector: wizard.data.sector || '',
        country: wizard.data.country || 'TN',
        org_size: wizard.data.orgSize || '',
        portals: wizard.data.portals || [],
        plan: wizard.data.plan || 'avancee',
        billing: wizard.data.billing || 'annual',
      }

      await registerUser(payload)

      // DO NOT call getMe() or redirect to /dashboard yet
      // User must verify email first, then setup 2FA
      // Redirect immediately without clearing form to prevent flash
      router.replace(`/register/verify-email?email=${encodeURIComponent(wizard.data.email || '')}`)
    } catch (err: unknown) {
      // Extract user-friendly error message
      const axiosErr = err as AxiosError
      const status = axiosErr?.response?.status
      let errorMessage = 'Une erreur s\'est produite lors de la création du compte'
      let errorCode = ''

      if (status === 409) {
        // Conflict: organization name, email already exists, or email unverified
        // Check if backend returned a structured error with code
        const responseData = axiosErr?.response?.data
        if (typeof responseData === 'object' && responseData !== null && 'detail' in responseData) {
          const detail = (responseData as Record<string, unknown>).detail
          if (typeof detail === 'object' && detail !== null && 'code' in detail && 'message' in detail) {
            const detailedError = detail as Record<string, unknown>
            errorCode = detailedError.code as string
            errorMessage = detailedError.message as string
            
            // Handle EMAIL_UNVERIFIED - show resend link option
            if (errorCode === 'EMAIL_UNVERIFIED') {
              // Email unverified - redirect to verify-email page where they can resend
              setError(errorMessage)
              // After 2 seconds, redirect to verify-email page
              setTimeout(() => {
                router.replace(`/register/verify-email?email=${encodeURIComponent(wizard.data.email || '')}&unverified=true`)
              }, 2000)
              return
            }
            
            if (errorCode === 'EMAIL_EXISTS') {
              // Fully registered - redirect to login
              errorMessage = 'Un compte existe déjà avec cette adresse email. Redirection vers la connexion...'
              setError(errorMessage)
              setTimeout(() => {
                router.replace('/login')
              }, 2000)
              return
            }
            
            if (errorCode === 'TENANT_ALREADY_EXISTS') {
              errorMessage = detailedError.message as string || 'Une organisation avec ce nom existe déjà. Demandez à votre administrateur de vous inviter.'
            }
          }
        }
        // Fallback message
        if (errorMessage === 'Une erreur s\'est produite lors de la création du compte') {
          errorMessage = 'Un compte avec cet email existe déjà'
        }
      } else if (status === 422) {
        // Validation error
        errorMessage = extractErrorMessage(err) || 'Vérifiez les champs du formulaire'
      } else if (status === 429) {
        // Rate limit
        errorMessage = 'Trop de tentatives. Réessayez dans quelques minutes.'
      } else if (status === 500 || status === 502 || status === 503) {
        // Server errors
        errorMessage = `Erreur serveur (${status}). Veuillez réessayer dans quelques moments.`
      } else if (!axiosErr?.response) {
        // Network error
        errorMessage = 'Impossible de joindre le serveur. Vérifiez votre connexion.'
      } else {
        // Extract message from backend error response
        errorMessage = extractErrorMessage(err)
      }

      setError(errorMessage)
      setIsSubmitting(false)
    }
  }

  // Progress bar
  const progressPercent = (wizard.step / 4) * 100

  return (
    <div className="min-h-screen w-full flex flex-col">
      {/* Progress bar */}
      <div className="h-1 bg-cream-border">
        <div
          className="h-full bg-amber transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Main layout */}
      <div className="flex flex-1">
        {/* Left panel */}
        <RegisterLeftPanel step={wizard.step} />

        {/* Right panel */}
        <div className="w-full lg:w-[60%] bg-cream flex items-center justify-center p-8 lg:p-12 overflow-y-auto">
          <div className="w-full max-w-md">
            {/* Error alert */}
            {error && (
              <div className="p-3 bg-danger/10 border border-danger/20 rounded-lg text-xs text-danger flex items-start gap-2 mb-6">
                <svg
                  className="w-4 h-4 flex-shrink-0 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>{error}</span>
              </div>
            )}

            {/* Step 1 */}
            {wizard.step === 1 && wizard.isHydrated && (
              <Step1Form
                onSubmit={handleStep1}
                isLoading={isSubmitting}
                defaultValues={wizard.data}
              />
            )}

            {/* Step 2 */}
            {wizard.step === 2 && wizard.isHydrated && (
              <Step2Form
                onSubmit={handleStep2}
                onBack={() => wizard.back()}
                isLoading={isSubmitting}
                defaultValues={wizard.data}
                preFillOrgName={domainMatch?.orgName}
                preFillSector={domainMatch?.sector}
              />
            )}

            {/* Step 3 */}
            {wizard.step === 3 && wizard.isHydrated && (
              <Step3Form
                onSubmit={handleStep3}
                onBack={() => wizard.back()}
                isLoading={isSubmitting}
                defaultValues={wizard.data}
              />
            )}

            {/* Step 4 */}
            {wizard.step === 4 && wizard.isHydrated && (
              <Step4Confirm
                data={wizard.data}
                onSubmit={handleFinalSubmit}
                onBack={() => wizard.back()}
                onEdit={(step) => wizard.goToStep(step)}
                isLoading={isSubmitting}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
