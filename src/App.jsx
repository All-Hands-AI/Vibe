import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { SetupProvider, useSetup } from './context/SetupContext'
import Header from './components/Header'
import Footer from './components/Footer'
import SetupWindow from './components/SetupWindow'
import Home from './pages/Home'
import About from './pages/About'
import Contact from './pages/Contact'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import ConversationDetail from './pages/ConversationDetail'
import { LoadingSpinner } from './components/ui'
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
      <div className="fixed inset-0 bg-gray-900 flex items-center justify-center z-50">
        <LoadingSpinner size="lg" text="Loading OpenVibe..." />
      </div>
    )
  }

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-gray-900 text-white">
        {!isSetupComplete && (
          <SetupWindow onSetupComplete={completeSetup} />
        )}
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Projects />} />
            <Route path="/projects/:slug" element={<ProjectDetail />} />
            <Route path="/projects/:slug/conversations/:conversationSlug" element={<ConversationDetail />} />
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