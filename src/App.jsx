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
import { logger } from './utils/logger'
import './App.css'

function AppContent() {
  const { isSetupComplete, isLoading, completeSetup } = useSetup()
  
  // Log system information on app start
  React.useEffect(() => {
    logger.logSystemInfo()
    logger.info('🔧 Setup status:', { isSetupComplete, isLoading })
  }, [isSetupComplete, isLoading])

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading OpenVibe...</p>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div className="App">
        {!isSetupComplete && (
          <SetupWindow onSetupComplete={completeSetup} />
        )}
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Projects />} />
            <Route path="/projects/:slug" element={<ProjectDetail />} />
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