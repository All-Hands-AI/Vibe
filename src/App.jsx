import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import Header from './components/Header'
import Footer from './components/Footer'
import SetupWindow from './components/SetupWindow'
import Home from './pages/Home'
import About from './pages/About'
import Contact from './pages/Contact'
import './App.css'

function App() {
  const [isSetupComplete, setIsSetupComplete] = useState(false)
  const [isCheckingSetup, setIsCheckingSetup] = useState(true)

  const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:3001'

  // Check if setup is complete on app load
  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/integrations/status`)
        if (response.ok) {
          const status = await response.json()
          const allValid = Object.values(status).every(valid => valid === true)
          setIsSetupComplete(allValid)
        }
      } catch (error) {
        console.error('Error checking setup status:', error)
        // If backend is not available, show setup window
        setIsSetupComplete(false)
      } finally {
        setIsCheckingSetup(false)
      }
    }

    checkSetupStatus()
  }, [])

  const handleSetupComplete = () => {
    setIsSetupComplete(true)
  }

  // Show loading while checking setup status
  if (isCheckingSetup) {
    return (
      <div className="App">
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          fontSize: '1.2rem',
          color: '#666'
        }}>
          Loading...
        </div>
      </div>
    )
  }

  return (
    <ThemeProvider>
      <Router>
        <div className="App">
          {!isSetupComplete && (
            <SetupWindow onSetupComplete={handleSetupComplete} />
          )}
          <Header />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/about" element={<About />} />
              <Route path="/contact" element={<Contact />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App