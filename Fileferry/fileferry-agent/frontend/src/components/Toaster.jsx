import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react'

let toastId = 0

export function Toaster() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    // Listen for custom toast events
    const handleToast = (event) => {
      const { message, type } = event.detail
      addToast(message, type)
    }

    window.addEventListener('toast', handleToast)
    return () => window.removeEventListener('toast', handleToast)
  }, [])

  const addToast = (message, type = 'info') => {
    const id = toastId++
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => removeToast(id), 5000)
  }

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  )
}

function Toast({ toast, onClose }) {
  const config = {
    success: {
      icon: CheckCircle,
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
    },
    error: {
      icon: XCircle,
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
    },
    warning: {
      icon: AlertCircle,
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
    },
    info: {
      icon: Info,
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
    },
  }

  const { icon: Icon, bg, border, text } = config[toast.type] || config.info

  return (
    <div
      className={`${bg} ${border} border rounded-lg shadow-lg p-4 min-w-[300px] max-w-md animate-slide-in`}
    >
      <div className="flex items-start space-x-3">
        <Icon size={20} className={text} />
        <p className={`flex-1 text-sm ${text}`}>{toast.message}</p>
        <button onClick={onClose} className={`${text} hover:opacity-70`}>
          ×
        </button>
      </div>
    </div>
  )
}

// Helper function to show toasts from anywhere
export function showToast(message, type = 'info') {
  window.dispatchEvent(new CustomEvent('toast', { detail: { message, type } }))
}
