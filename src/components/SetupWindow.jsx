import { useState, useEffect } from 'react';
import './SetupWindow.css';

const SetupWindow = ({ onSetupComplete }) => {
  const [apiKeys, setApiKeys] = useState({
    anthropic: '',
    github: '',
    fly: ''
  });

  const [validationStatus, setValidationStatus] = useState({
    anthropic: null, // null = not checked, true = valid, false = invalid
    github: null,
    fly: null
  });

  const [isValidating, setIsValidating] = useState({
    anthropic: false,
    github: false,
    fly: false
  });

  const [errors, setErrors] = useState({
    anthropic: '',
    github: '',
    fly: ''
  });

  const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:3001';

  // Check if all keys are valid
  const allKeysValid = Object.values(validationStatus).every(status => status === true);

  // Validate a specific API key
  const validateApiKey = async (service, apiKey) => {
    if (!apiKey.trim()) {
      setValidationStatus(prev => ({ ...prev, [service]: null }));
      setErrors(prev => ({ ...prev, [service]: '' }));
      return;
    }

    setIsValidating(prev => ({ ...prev, [service]: true }));
    setErrors(prev => ({ ...prev, [service]: '' }));

    try {
      const response = await fetch(`${API_BASE_URL}/integrations/${service}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ apiKey }),
      });

      const data = await response.json();

      if (response.ok && data.valid) {
        setValidationStatus(prev => ({ ...prev, [service]: true }));
      } else {
        setValidationStatus(prev => ({ ...prev, [service]: false }));
        setErrors(prev => ({ ...prev, [service]: data.error || 'Invalid API key' }));
      }
    } catch (error) {
      console.error(`Error validating ${service} API key:`, error);
      setValidationStatus(prev => ({ ...prev, [service]: false }));
      setErrors(prev => ({ ...prev, [service]: 'Failed to validate API key' }));
    } finally {
      setIsValidating(prev => ({ ...prev, [service]: false }));
    }
  };

  // Handle input changes
  const handleInputChange = (service, value) => {
    setApiKeys(prev => ({ ...prev, [service]: value }));
    
    // Reset validation status when input changes
    setValidationStatus(prev => ({ ...prev, [service]: null }));
    setErrors(prev => ({ ...prev, [service]: '' }));
  };

  // Handle input blur (validate when user leaves the field)
  const handleInputBlur = (service) => {
    const apiKey = apiKeys[service];
    if (apiKey.trim()) {
      validateApiKey(service, apiKey);
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (allKeysValid) {
      onSetupComplete();
    } else {
      // Validate all keys that haven't been validated yet
      Object.keys(apiKeys).forEach(service => {
        if (validationStatus[service] === null && apiKeys[service].trim()) {
          validateApiKey(service, apiKeys[service]);
        }
      });
    }
  };

  // Check existing API keys on component mount
  useEffect(() => {
    const checkExistingKeys = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/integrations/status`);
        if (response.ok) {
          const status = await response.json();
          setValidationStatus(status);
          
          // If all keys are already valid, complete setup
          if (Object.values(status).every(valid => valid === true)) {
            onSetupComplete();
          }
        }
      } catch (error) {
        console.error('Error checking existing API keys:', error);
      }
    };

    checkExistingKeys();
  }, [onSetupComplete]);

  const getValidationIcon = (service) => {
    if (isValidating[service]) {
      return <span className="validation-icon validating">⏳</span>;
    }
    
    if (validationStatus[service] === true) {
      return <span className="validation-icon valid">✅</span>;
    }
    
    if (validationStatus[service] === false) {
      return <span className="validation-icon invalid">❌</span>;
    }
    
    return null;
  };

  return (
    <div className="setup-overlay">
      <div className="setup-window">
        <div className="setup-header">
          <h2>🚀 Welcome to OpenVibe!</h2>
          <p>Please configure your API keys to get started. All keys are required.</p>
        </div>

        <form onSubmit={handleSubmit} className="setup-form">
          {/* Anthropic API Key */}
          <div className="form-group">
            <label htmlFor="anthropic-key">
              Anthropic API Key
              {getValidationIcon('anthropic')}
            </label>
            <input
              id="anthropic-key"
              type="password"
              value={apiKeys.anthropic}
              onChange={(e) => handleInputChange('anthropic', e.target.value)}
              onBlur={() => handleInputBlur('anthropic')}
              placeholder="sk-ant-..."
              className={validationStatus.anthropic === false ? 'error' : ''}
            />
            {errors.anthropic && (
              <span className="error-message">{errors.anthropic}</span>
            )}
          </div>

          {/* GitHub API Key */}
          <div className="form-group">
            <label htmlFor="github-key">
              GitHub API Key
              {getValidationIcon('github')}
            </label>
            <input
              id="github-key"
              type="password"
              value={apiKeys.github}
              onChange={(e) => handleInputChange('github', e.target.value)}
              onBlur={() => handleInputBlur('github')}
              placeholder="ghp_..."
              className={validationStatus.github === false ? 'error' : ''}
            />
            {errors.github && (
              <span className="error-message">{errors.github}</span>
            )}
          </div>

          {/* Fly.io API Key */}
          <div className="form-group">
            <label htmlFor="fly-key">
              Fly.io API Key
              {getValidationIcon('fly')}
            </label>
            <input
              id="fly-key"
              type="password"
              value={apiKeys.fly}
              onChange={(e) => handleInputChange('fly', e.target.value)}
              onBlur={() => handleInputBlur('fly')}
              placeholder="fo1_..."
              className={validationStatus.fly === false ? 'error' : ''}
            />
            {errors.fly && (
              <span className="error-message">{errors.fly}</span>
            )}
          </div>

          <div className="setup-actions">
            <button 
              type="submit" 
              className="setup-button"
              disabled={!allKeysValid}
            >
              {allKeysValid ? 'Complete Setup' : 'Validate All Keys'}
            </button>
          </div>

          <div className="setup-help">
            <p>Need help getting your API keys?</p>
            <ul>
              <li><a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer">Get Anthropic API Key</a></li>
              <li><a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer">Get GitHub API Key</a></li>
              <li><a href="https://fly.io/user/personal_access_tokens" target="_blank" rel="noopener noreferrer">Get Fly.io API Key</a></li>
            </ul>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SetupWindow;