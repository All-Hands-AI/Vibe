import React from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { SetupProvider, useSetup } from './context/SetupContext'
import SetupWindow from './components/SetupWindow'
import VibeFlow from './components/VibeFlow'
import Apps from './pages/Apps'
import AppDetail from './pages/AppDetail'
import RiffDetail from './pages/RiffDetail'
import { logger } from './utils/logger'

// Component to handle scroll to top on route changes
function ScrollToTop() {
  const location = useLocation()
  
  React.useEffect(() => {
    window.scrollTo(0, 0)
  }, [location.pathname])
  
  return null
}

function AppContent() {
  const { isSetupComplete, isLoading, completeSetup } = useSetup()
  
  // Log system information on app start
  React.useEffect(() => {
    logger.logSystemInfo()
    logger.info('🔧 Setup status:', { isSetupComplete, isLoading })
  }, [isSetupComplete, isLoading])

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-slate-900 flex items-center justify-center z-50 vibe-bg">
        <div className="text-center creative-window">
          <div className="creative-header">
            ✨ VIBE LOADING
          </div>
          <div className="creative-content">
            <div className="w-10 h-10 border-4 border-slate-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-200 text-base font-mono">
              <span>{'~'}</span> Warming up the vibes...
            </p>
            <p className="text-slate-400 text-sm mt-2">
              🎨 Loading creative energy...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <ScrollToTop />
      <div className="min-h-screen flex flex-col bg-slate-900 text-slate-200 transition-colors duration-300 relative">
        <VibeFlow />
        {!isSetupComplete && (
          <SetupWindow onSetupComplete={completeSetup} />
        )}
        <main className="flex-1 relative z-10">
          <Routes>
            <Route path="/" element={<Apps />} />
            <Route path="/apps/:slug" element={<AppDetail />} />
            <Route path="/apps/:slug/riffs/:riffSlug" element={<RiffDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

function App() {
  return (
    <ThemeProvider>
      <SetupProvider>
        <AppContent />
      </SetupProvider>
    </ThemeProvider>
  )
}

export default App