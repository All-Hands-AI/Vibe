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
      <div className="fixed inset-0 bg-gray-900 dark:bg-gray-950 flex items-center justify-center z-50">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-gray-600 border-t-primary-300 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-base">Loading OpenVibe...</p>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-gray-900 text-white dark:bg-gray-950 transition-colors duration-300">
        {!isSetupComplete && (
          <SetupWindow onSetupComplete={completeSetup} />
        )}
        <Header />
        <main className="flex-1">
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