import { Link, useLocation } from 'react-router-dom'

function Header() {
  const location = useLocation()
  
  const isActive = (path) => location.pathname === path

  return (
    <header className="bg-black border-b-2 border-cyber-border sticky top-0 z-40">
      <div className="max-w-6xl mx-auto flex justify-between items-center px-8 py-4">
        <Link to="/" className="text-cyber-text no-underline group hover:text-neon-green transition-colors duration-300">
          <h1 className="text-3xl font-bold m-0 font-mono">
            <span className="text-cyber-muted">{'<'}</span>
            OpenVibe
            <span className="text-cyber-muted">{'/>'}</span>
          </h1>
        </Link>
        <nav className="flex gap-6">
          <Link 
            to="/" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/') 
                ? 'text-black bg-neon-green border-neon-green' 
                : 'text-cyber-text border-cyber-border hover:border-neon-green hover:text-neon-green'
            }`}
          >
            🗂️ Projects
          </Link>
          <Link 
            to="/home" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/home') 
                ? 'text-black bg-neon-green border-neon-green' 
                : 'text-cyber-text border-cyber-border hover:border-neon-green hover:text-neon-green'
            }`}
          >
            🏠 Home
          </Link>
          <Link 
            to="/about" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/about') 
                ? 'text-black bg-neon-green border-neon-green' 
                : 'text-cyber-text border-cyber-border hover:border-neon-green hover:text-neon-green'
            }`}
          >
            ℹ️ About
          </Link>
          <Link 
            to="/contact" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/contact') 
                ? 'text-black bg-neon-green border-neon-green' 
                : 'text-cyber-text border-cyber-border hover:border-neon-green hover:text-neon-green'
            }`}
          >
            📞 Contact
          </Link>
        </nav>
      </div>
    </header>
  )
}

export default Header