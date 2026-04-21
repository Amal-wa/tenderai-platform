// =============================================================================
// lib/toast.ts — Simple toast notification system using browser API
// =============================================================================

export type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ToastOptions {
  duration?: number
  position?: 'top' | 'bottom'
}

const DEFAULT_DURATION = 3000

/**
 * Show a toast notification in the browser.
 * Creates a temporary DOM element with animations.
 * @param message - The message to display
 * @param type - The type of toast (success, error, info, warning)
 * @param options - Optional configuration (duration, position)
 */
export function showToast(message: string, type: ToastType = 'info', options?: ToastOptions): void {
  const { duration = DEFAULT_DURATION, position = 'top' } = options || {}

  // Create toast container if it doesn't exist
  let container = document.getElementById('toast-container')
  if (!container) {
    container = document.createElement('div')
    container.id = 'toast-container'
    container.style.cssText = `
      position: fixed;
      ${position}: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
    `
    document.body.appendChild(container)
  }

  // Create toast element
  const toast = document.createElement('div')
  const bgColor = {
    success: '#1D9E75',
    error: '#E24B4A',
    info: '#378ADD',
    warning: '#F59E0B',
  }[type]

  const bgLight = {
    success: '#E1F5EE',
    error: '#FCEAEA',
    info: '#EEF4FB',
    warning: '#FEF3C7',
  }[type]

  toast.style.cssText = `
    background-color: ${bgLight};
    border: 1px solid ${bgColor};
    border-radius: 6px;
    padding: 12px 16px;
    color: ${bgColor};
    font-size: 14px;
    font-weight: 500;
    animation: slideIn 0.3s ease-out;
    pointer-events: auto;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  `
  toast.textContent = message

  container.appendChild(toast)

  // Auto-remove after duration
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out'
    setTimeout(() => {
      container?.removeChild(toast)
      if (container?.children.length === 0) {
        document.body.removeChild(container)
        document.getElementById('toast-container')?.remove()
      }
    }, 300)
  }, duration)
}

// Add animations to document if not already present
if (typeof document !== 'undefined' && !document.getElementById('toast-animations')) {
  const style = document.createElement('style')
  style.id = 'toast-animations'
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `
  document.head.appendChild(style)
}
