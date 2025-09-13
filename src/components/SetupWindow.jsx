import { useState } from 'react'
import PropTypes from 'prop-types'
import { useSetup } from '../context/SetupContext'
import './SetupWindow.css'

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

  // Backend URL - in production, backend runs on same domain
  const BACKEND_URL = import.meta.env.MODE === 'production' 
    ? '' 
    : 'http://localhost:8000'

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
      const response = await fetch(`${BACKEND_URL}/integrations/${provider}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          api_key: apiKey,
          uuid: userUUID
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
    if (status.loading) return 'validating'
    if (status.valid) return 'valid'
    if (status.message && !status.valid) return 'invalid'
    return ''
  }

  return (
    <div className="setup-overlay">
      <div className="setup-window">
        <div className="setup-header">
          <h2>🚀 Welcome to OpenVibe</h2>
          <p>Please configure your API keys to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="setup-form">
          <div className="api-key-section">
            <div className="input-group">
              <label htmlFor="anthropic-key">
                <span className="provider-icon">🤖</span>
                Anthropic API Key
              </label>
              <div className="input-with-status">
                <input
                  id="anthropic-key"
                  type="password"
                  placeholder="sk-ant-..."
                  value={apiKeys.anthropic}
                  onChange={(e) => handleInputChange('anthropic', e.target.value)}
                  onBlur={() => handleInputBlur('anthropic')}
                  className={getStatusClass(validationStatus.anthropic)}
                />
                <span className="status-icon">
                  {getStatusIcon(validationStatus.anthropic)}
                </span>
              </div>
              {validationStatus.anthropic.message && (
                <div className={`status-message ${getStatusClass(validationStatus.anthropic)}`}>
                  {validationStatus.anthropic.message}
                </div>
              )}
            </div>

            <div className="input-group">
              <label htmlFor="github-key">
                <span className="provider-icon">🐙</span>
                GitHub API Key
              </label>
              <div className="input-with-status">
                <input
                  id="github-key"
                  type="password"
                  placeholder="ghp_..."
                  value={apiKeys.github}
                  onChange={(e) => handleInputChange('github', e.target.value)}
                  onBlur={() => handleInputBlur('github')}
                  className={getStatusClass(validationStatus.github)}
                />
                <span className="status-icon">
                  {getStatusIcon(validationStatus.github)}
                </span>
              </div>
              {validationStatus.github.message && (
                <div className={`status-message ${getStatusClass(validationStatus.github)}`}>
                  {validationStatus.github.message}
                </div>
              )}
            </div>

            <div className="input-group">
              <label htmlFor="fly-key">
                <span className="provider-icon">🪰</span>
                Fly.io API Key
              </label>
              <div className="input-with-status">
                <input
                  id="fly-key"
                  type="password"
                  placeholder="fo1_..."
                  value={apiKeys.fly}
                  onChange={(e) => handleInputChange('fly', e.target.value)}
                  onBlur={() => handleInputBlur('fly')}
                  className={getStatusClass(validationStatus.fly)}
                />
                <span className="status-icon">
                  {getStatusIcon(validationStatus.fly)}
                </span>
              </div>
              {validationStatus.fly.message && (
                <div className={`status-message ${getStatusClass(validationStatus.fly)}`}>
                  {validationStatus.fly.message}
                </div>
              )}
            </div>
          </div>

          <div className="setup-footer">
            <button 
              type="submit" 
              className="continue-button"
              disabled={!allKeysValid}
            >
              {allKeysValid ? '✨ Continue to OpenVibe' : '🔑 Enter all API keys to continue'}
            </button>
            
            <div className="help-text">
              <p>Need help getting your API keys?</p>
              <ul>
                <li><a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer">Get Anthropic API Key</a></li>
                <li><a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer">Get GitHub API Key</a></li>
                <li><a href="https://fly.io/user/personal_access_tokens" target="_blank" rel="noopener noreferrer">Get Fly.io API Key</a></li>
              </ul>
            </div>
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