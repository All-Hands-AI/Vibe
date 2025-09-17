import { Link } from 'react-router-dom'

function RiffNavigation({ appSlug, riffSlug }) {
  return (
    <nav className="mb-4">
      <div className="flex items-center space-x-2 text-sm">
        <Link to="/" className="text-cyber-muted hover:text-neon-green transition-colors duration-200">
          Apps
        </Link>
        <span className="text-gray-500">/</span>
        <Link to={`/apps/${appSlug}`} className="text-cyber-muted hover:text-neon-green transition-colors duration-200">
          {appSlug}
        </Link>
        <span className="text-gray-500">/</span>
        <span className="text-cyber-muted">{riffSlug}</span>
      </div>
    </nav>
  )
}

export default RiffNavigation