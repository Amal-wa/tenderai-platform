import { useState, useCallback, useRef, useEffect } from 'react'
import type { AxiosError } from 'axios'
import api from '@/lib/api'
import { extractErrorMessage } from '@/lib/api'

interface UseCheckEmailReturn {
  exists: boolean | null
  isLoading: boolean
  error: string | null
}

/**
 * Hook pour vérifier l'unicité d'un email en temps réel.
 *
 * 🎯 Cas d'usage:
 * - Utilisé dans Step1Form pour afficher une erreur immédiate
 *   si l'email est déjà pris (à l'étape 1, pas à l'étape 4)
 *
 * 🔄 Débounce:
 * - Délai: 500ms
 * - Évite les requêtes réseau trop fréquentes
 * - Attendre 500ms après le dernier changement avant de requêter
 *
 * 📊 Retour:
 * - exists: true|false|null (null = pas encore checké)
 * - isLoading: true si requête en cours
 * - error: message d'erreur si requête échouée
 *
 * @param email - Email à vérifier
 * @returns {UseCheckEmailReturn} État du check
 */
export function useCheckEmail(email: string): UseCheckEmailReturn {
  const [exists, setExists] = useState<boolean | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Debounce: garder le timer ID pour annuler les requêtes précédentes
  const debounceTimer = useRef<NodeJS.Timeout | null>(null)

  const checkEmail = useCallback(
    async (emailToCheck: string): Promise<void> => {
      // Valider l'email avant de l'envoyer
      if (!emailToCheck || !emailToCheck.includes('@')) {
        setExists(null)
        setError(null)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const response = await api.get<{ exists: boolean }>(
          '/api/v1/auth/check-email',
          { params: { email: emailToCheck } }
        )

        setExists(response.data.exists)
      } catch (err: unknown) {
        const axiosErr = err as AxiosError

        // 422 = validation error (email format invalide)
        if (axiosErr?.response?.status === 422) {
          setError('Format email invalide')
          setExists(null)
        } else {
          // Autres erreurs réseau/serveur
          setError(extractErrorMessage(err))
          setExists(null)
        }
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    // Annuler le timer précédent
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }

    // Démarrer un nouveau timer (500ms de débounce)
    debounceTimer.current = setTimeout(() => {
      checkEmail(email)
    }, 500)

    // Cleanup: annuler le timer si le composant se démonte
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
    }
  }, [email, checkEmail])

  return { exists, isLoading, error }
}
