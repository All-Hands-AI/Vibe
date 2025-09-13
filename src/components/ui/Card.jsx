import PropTypes from 'prop-types'

function Card({ children, className = '', variant = 'default', hover = false, ...props }) {
  const baseClasses = 'rounded-lg border transition-all duration-200'
  
  const variantClasses = {
    default: 'bg-background-secondary border-gray-700',
    primary: 'bg-background-secondary border-primary-300/20',
    glass: 'bg-background-secondary/50 backdrop-blur-sm border-gray-700/50',
  }

  const hoverClasses = hover 
    ? 'hover:shadow-lg hover:shadow-primary-300/10 hover:border-primary-300/40 hover:-translate-y-1 cursor-pointer' 
    : ''

  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant]} ${hoverClasses} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  variant: PropTypes.oneOf(['default', 'primary', 'glass']),
  hover: PropTypes.bool,
}

export default Card