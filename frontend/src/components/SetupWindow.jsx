import { useState } from 'react'
import PropTypes from 'prop-types'
import { useSetup } from '../context/SetupContext'

const SetupWindow = ({ onSetupComplete }) => {
  const { userUUID } = useSetup()
  const [apiKeys, setApiKeys] = useState({
    anthropic: '',
    github: '',
    fly: ''
  })
  
  const [validationStatus, setValidationStatus] = useState({
    anthropic: { valid: false, message: '', loading: false },
    github: { valid: false, message: '', loading: false },
    fly: { valid: false, message: '', loading: false }
  })

  // Check if all keys are valid
  const allKeysValid = Object.values(validationStatus).every(status => status.valid)

  const validateApiKey = async (provider, apiKey) => {
    if (!apiKey.trim() || !userUUID) {
      setValidationStatus(prev => ({
        ...prev,
        [provider]: { valid: false, message: '', loading: false }
      }))
      return
    }

    setValidationStatus(prev => ({
      ...prev,
      [provider]: { ...prev[provider], loading: true }
    }))

    try {
      const response = await fetch(`/api/integrations/${provider}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-UUID': userUUID
        },
        body: JSON.stringify({ 
          api_key: apiKey
        })
      })

      const data = await response.json()
      
      setValidationStatus(prev => ({
        ...prev,
        [provider]: {
          valid: data.valid,
          message: data.message,
          loading: false
        }
      }))
    } catch {
      setValidationStatus(prev => ({
        ...prev,
        [provider]: {
          valid: false,
          message: `Failed to validate ${provider} API key`,
          loading: false
        }
      }))
    }
  }

  const handleInputChange = (provider, value) => {
    setApiKeys(prev => ({
      ...prev,
      [provider]: value
    }))
  }

  const handleInputBlur = (provider) => {
    const apiKey = apiKeys[provider]
    if (apiKey.trim()) {
      validateApiKey(provider, apiKey)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (allKeysValid) {
      onSetupComplete()
    }
  }

  const getStatusIcon = (status) => {
    if (status.loading) return '⏳'
    if (status.valid) return '✅'
    if (status.message && !status.valid) return '❌'
    return ''
  }

  const getStatusClass = (status) => {
    if (status.loading) return 'border-yellow-500 bg-yellow-50/10'
    if (status.valid) return 'border-green-500 bg-green-50/10'
    if (status.message && !status.valid) return 'border-red-500 bg-red-50/10'
    return 'border-cyber-border'
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="terminal-window max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="terminal-header">
          <h2 className="text-2xl font-bold mb-2">🚀 Welcome to OpenVibe</h2>
          <p className="text-cyber-muted">Please configure your API keys to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="terminal-content">
          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="anthropic-key" className="flex items-center text-sm font-medium text-cyber-text font-mono">
                  <span className="mr-2">🤖</span>
                  Anthropic API Key
                </label>
                <a 
                  href="https://console.anthropic.com/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-cyber-muted hover:text-neon-green transition-colors duration-200 font-mono"
                >
                  Get API Key
                </a>
              </div>
              <div className="relative">
                <input
                  id="anthropic-key"
                  type="password"
                  placeholder="sk-ant-..."
                  value={apiKeys.anthropic}
                  onChange={(e) => handleInputChange('anthropic', e.target.value)}
                  onBlur={() => handleInputBlur('anthropic')}
                  className={`w-full px-3 py-2 bg-black text-cyber-text font-mono border-2 transition-colors duration-200 focus:outline-none focus:border-neon-green ${getStatusClass(validationStatus.anthropic)}`}
                />
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lg">
                  {getStatusIcon(validationStatus.anthropic)}
                </span>
              </div>
              {validationStatus.anthropic.message && (
                <div className={`mt-2 text-sm px-3 py-2 rounded ${
                  validationStatus.anthropic.valid 
                    ? 'text-green-400 bg-green-900/20' 
                    : validationStatus.anthropic.loading 
                      ? 'text-yellow-400 bg-yellow-900/20'
                      : 'text-red-400 bg-red-900/20'
                }`}>
                  {validationStatus.anthropic.message}
                </div>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="github-key" className="flex items-center text-sm font-medium text-cyber-text font-mono">
                  <span className="mr-2">🐙</span>
                  GitHub API Key
                </label>
                <a 
                  href="https://github.com/settings/tokens/new?description=openhands-app&scopes=repo,user,workflow" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-cyber-muted hover:text-neon-green transition-colors duration-200 font-mono"
                >
                  Get API Key
                </a>
              </div>
              <div className="relative">
                <input
                  id="github-key"
                  type="password"
                  placeholder="ghp_..."
                  value={apiKeys.github}
                  onChange={(e) => handleInputChange('github', e.target.value)}
                  onBlur={() => handleInputBlur('github')}
                  className={`w-full px-3 py-2 bg-black text-cyber-text font-mono border-2 transition-colors duration-200 focus:outline-none focus:border-neon-green ${getStatusClass(validationStatus.github)}`}
                />
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lg">
                  {getStatusIcon(validationStatus.github)}
                </span>
              </div>
              {validationStatus.github.message && (
                <div className={`mt-2 text-sm px-3 py-2 rounded ${
                  validationStatus.github.valid 
                    ? 'text-green-400 bg-green-900/20' 
                    : validationStatus.github.loading 
                      ? 'text-yellow-400 bg-yellow-900/20'
                      : 'text-red-400 bg-red-900/20'
                }`}>
                  {validationStatus.github.message}
                </div>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="fly-key" className="flex items-center text-sm font-medium text-cyber-text font-mono">
                  <span className="mr-2">🪰</span>
                  Fly.io API Key
                </label>
                <a 
                  href="https://fly.io/user/personal_access_tokens" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-cyber-muted hover:text-neon-green transition-colors duration-200 font-mono"
                >
                  Get API Key
                </a>
              </div>
              <div className="relative">
                <input
                  id="fly-key"
                  type="password"
                  placeholder="fo1_..."
                  value={apiKeys.fly}
                  onChange={(e) => handleInputChange('fly', e.target.value)}
                  onBlur={() => handleInputBlur('fly')}
                  className={`w-full px-3 py-2 bg-black text-cyber-text font-mono border-2 transition-colors duration-200 focus:outline-none focus:border-neon-green ${getStatusClass(validationStatus.fly)}`}
                />
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lg">
                  {getStatusIcon(validationStatus.fly)}
                </span>
              </div>
              {validationStatus.fly.message && (
                <div className={`mt-2 text-sm px-3 py-2 rounded ${
                  validationStatus.fly.valid 
                    ? 'text-green-400 bg-green-900/20' 
                    : validationStatus.fly.loading 
                      ? 'text-yellow-400 bg-yellow-900/20'
                      : 'text-red-400 bg-red-900/20'
                }`}>
                  {validationStatus.fly.message}
                </div>
              )}
            </div>
          </div>

          <div className="mt-8 border-t border-cyber-border pt-6">
            <button 
              type="submit" 
              className={`w-full py-3 px-4 font-medium font-mono transition-all duration-200 ${
                allKeysValid 
                  ? 'btn-hacker-primary' 
                  : 'bg-cyber-accent text-cyber-muted cursor-not-allowed border-2 border-cyber-border'
              }`}
              disabled={!allKeysValid}
            >
              {allKeysValid ? '✨ Continue to OpenVibe' : '🔑 Enter all API keys to continue'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

SetupWindow.propTypes = {
  onSetupComplete: PropTypes.func.isRequired
}

export default SetupWindow
