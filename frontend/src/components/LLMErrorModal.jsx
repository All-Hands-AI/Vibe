import { useState } from 'react'
import PropTypes from 'prop-types'
import { resetLLM } from '../utils/llmService'

function LLMErrorModal({ isOpen, onClose, appSlug, riffSlug, onReset }) {
  const [isResetting, setIsResetting] = useState(false)
  const [resetError, setResetError] = useState('')

  const handleReset = async (e) => {
    console.log('🔄 Reset button clicked')
    
    // Prevent form submission if this button is inside a form
    e?.preventDefault()
    e?.stopPropagation()
    
    setIsResetting(true)
    setResetError('')

    try {
      console.log(`🔄 Starting LLM reset for ${appSlug}/${riffSlug}`)
      const result = await resetLLM(appSlug, riffSlug)
      console.log('🔄 Reset result:', result)
      
      if (result.success) {
        console.log('✅ LLM reset successful')
        onReset?.()
        onClose()
      } else {
        console.error('❌ LLM reset failed:', result.error)
        setResetError(result.error || 'Failed to reset LLM. Please try again.')
      }
    } catch (error) {
      console.error('❌ Error resetting LLM:', error)
      setResetError(`An error occurred while resetting: ${error.message}`)
    } finally {
      setIsResetting(false)
      console.log('🔄 Reset operation completed')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-red-500 rounded-lg p-6 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center mb-4">
          <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center mr-3">
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-400">LLM Not Ready</h3>
        </div>

        {/* Content */}
        <div className="mb-6">
          <p className="text-slate-400 mb-4">
            The AI assistant is not ready for this conversation. This can happen if the server was restarted or there was a connection issue.
          </p>
          <p className="text-slate-400">
            Click &quot;Reset LLM&quot; to reinitialize the AI assistant and continue your conversation.
          </p>
        </div>

        {/* Error message */}
        {resetError && (
          <div className="mb-4 p-3 bg-red-900 border border-red-500 rounded text-red-200 text-sm">
            {resetError}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isResetting}
            className="px-4 py-2 text-slate-400 hover:text-slate-200 border border-gray-600 hover:border-gray-500 rounded transition-colors duration-200 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={isResetting}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors duration-200 disabled:opacity-50 flex items-center"
          >
            {isResetting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Resetting...
              </>
            ) : (
              'Reset LLM'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

LLMErrorModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired,
  onReset: PropTypes.func
}

export default LLMErrorModal