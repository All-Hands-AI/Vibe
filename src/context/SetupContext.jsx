import { createContext, useContext, useState, useEffect } from 'react'

const SetupContext = createContext()

export const useSetup = () => {
  const context = useContext(SetupContext)
  if (!context) {
    throw new Error('useSetup must be used within a SetupProvider')
  }
  return context
}

export const SetupProvider = ({ children }) => {
  const [isSetupComplete, setIsSetupComplete] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Backend URL - in production, backend runs on same domain
  const BACKEND_URL = process.env.NODE_ENV === 'production' 
    ? '' 
    : 'http://localhost:8000'

  // Check if all API keys are already configured
  const checkSetupStatus = async () => {
    try {
      const providers = ['anthropic', 'github', 'fly']
      const checks = await Promise.all(
        providers.map(async (provider) => {
          try {
            const response = await fetch(`${BACKEND_URL}/integrations/${provider}`)
            const data = await response.json()
            return data.valid
          } catch (error) {
            console.error(`Failed to check ${provider} API key:`, error)
            return false
          }
        })
      )

      // All keys must be valid for setup to be complete
      const allValid = checks.every(valid => valid)
      setIsSetupComplete(allValid)
    } catch (error) {
      console.error('Failed to check setup status:', error)
      setIsSetupComplete(false)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkSetupStatus()
  }, [])

  const completeSetup = () => {
    setIsSetupComplete(true)
  }

  const resetSetup = () => {
    setIsSetupComplete(false)
  }

  const value = {
    isSetupComplete,
    isLoading,
    completeSetup,
    resetSetup,
    checkSetupStatus
  }

  return (
    <SetupContext.Provider value={value}>
      {children}
    </SetupContext.Provider>
  )
}