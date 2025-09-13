import { Link, useLocation } from 'react-router-dom'

function Header() {
  const location = useLocation()
  
  const isActive = (path) => location.pathname === path

  return (
    <header className="bg-gray-850 border-b border-gray-700 sticky top-0 z-40">
      <div className="max-w-6xl mx-auto flex justify-between items-center px-8 py-4">
        <Link to="/" className="text-primary-300 no-underline">
          <h1 className="text-3xl font-bold m-0">OpenVibe</h1>
        </Link>
        <nav className="flex gap-8">
          <Link 
            to="/" 
            className={`text-white no-underline font-medium transition-colors duration-300 px-4 py-2 rounded ${
              isActive('/') 
                ? 'text-primary-300 bg-primary-300/20' 
                : 'hover:text-primary-300 hover:bg-primary-300/10'
            }`}
          >
            Projects
          </Link>
          <Link 
            to="/home" 
            className={`text-white no-underline font-medium transition-colors duration-300 px-4 py-2 rounded ${
              isActive('/home') 
                ? 'text-primary-300 bg-primary-300/20' 
                : 'hover:text-primary-300 hover:bg-primary-300/10'
            }`}
          >
            Home
          </Link>
          <Link 
            to="/about" 
            className={`text-white no-underline font-medium transition-colors duration-300 px-4 py-2 rounded ${
              isActive('/about') 
                ? 'text-primary-300 bg-primary-300/20' 
                : 'hover:text-primary-300 hover:bg-primary-300/10'
            }`}
          >
            About
          </Link>
          <Link 
            to="/contact" 
            className={`text-white no-underline font-medium transition-colors duration-300 px-4 py-2 rounded ${
              isActive('/contact') 
                ? 'text-primary-300 bg-primary-300/20' 
                : 'hover:text-primary-300 hover:bg-primary-300/10'
            }`}
          >
            Contact
          </Link>
        </nav>
      </div>
    </header>
  )
}

export default Header