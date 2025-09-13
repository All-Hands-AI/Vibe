import { Link, useLocation } from 'react-router-dom'
import { Container } from './ui'

function Header() {
  const location = useLocation()
  
  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return true
    if (path !== '/' && location.pathname.startsWith(path)) return true
    return false
  }

  return (
    <header className="bg-background-secondary border-b border-gray-700 sticky top-0 z-40">
      <Container>
        <div className="flex justify-between items-center py-4">
          <Link to="/" className="text-primary-300 hover:text-primary-400 transition-colors">
            <h1 className="text-2xl font-bold">OpenVibe</h1>
          </Link>
          <nav className="flex space-x-8">
            <Link 
              to="/" 
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                isActive('/') 
                  ? 'text-primary-300 bg-primary-300/10' 
                  : 'text-text-primary hover:text-primary-300 hover:bg-gray-700/50'
              }`}
            >
              Projects
            </Link>
            <Link 
              to="/home" 
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                isActive('/home') 
                  ? 'text-primary-300 bg-primary-300/10' 
                  : 'text-text-primary hover:text-primary-300 hover:bg-gray-700/50'
              }`}
            >
              Home
            </Link>
            <Link 
              to="/about" 
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                isActive('/about') 
                  ? 'text-primary-300 bg-primary-300/10' 
                  : 'text-text-primary hover:text-primary-300 hover:bg-gray-700/50'
              }`}
            >
              About
            </Link>
            <Link 
              to="/contact" 
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                isActive('/contact') 
                  ? 'text-primary-300 bg-primary-300/10' 
                  : 'text-text-primary hover:text-primary-300 hover:bg-gray-700/50'
              }`}
            >
              Contact
            </Link>
          </nav>
        </div>
      </Container>
    </header>
  )
}

export default Header