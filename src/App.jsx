import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { SetupProvider, useSetup } from './context/SetupContext'
import Header from './components/Header'
import Footer from './components/Footer'
import SetupWindow from './components/SetupWindow'
import MatrixRain from './components/MatrixRain'
import Home from './pages/Home'
import About from './pages/About'
import Contact from './pages/Contact'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import ConversationDetail from './pages/ConversationDetail'
import { logger } from './utils/logger'

function AppContent() {
  const { isSetupComplete, isLoading, completeSetup } = useSetup()
  
  // Log system information on app start
  React.useEffect(() => {
    logger.logSystemInfo()
    logger.info('🔧 Setup status:', { isSetupComplete, isLoading })
  }, [isSetupComplete, isLoading])

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black flex items-center justify-center z-50 matrix-bg">
        <div className="text-center terminal-window">
          <div className="terminal-header">
            💻 SYSTEM BOOT
          </div>
          <div className="terminal-content">
            <div className="w-10 h-10 border-4 border-cyber-border border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-cyber-text text-base font-mono">
              <span>{'>'}</span> Initializing OpenVibe...
            </p>
            <p className="text-cyber-muted text-sm mt-2">
              🔐 Loading hacker protocols...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-black text-cyber-text transition-colors duration-300 relative">
        <MatrixRain />
        {!isSetupComplete && (
          <SetupWindow onSetupComplete={completeSetup} />
        )}
        <Header />
        <main className="flex-1 relative z-10">
          <Routes>
            <Route path="/" element={<Projects />} />
            <Route path="/projects/:slug" element={<ProjectDetail />} />
            <Route path="/projects/:slug/conversations/:conversationSlug" element={<ConversationDetail />} />
            <Route path="/conversations/:conversationSlug" element={<ConversationDetail />} />
            <Route path="/home" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </main>
        <Footer />
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