import PropTypes from 'prop-types'

function LoadingSpinner({ size = 'md', className = '', text = '' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  }

  return (
    <div className={`flex flex-col items-center justify-center space-y-2 ${className}`}>
      <div className={`animate-spin rounded-full border-4 border-gray-600 border-t-primary-300 ${sizeClasses[size]}`}></div>
      {text && (
        <p className="text-text-secondary text-sm">{text}</p>
      )}
    </div>
  )
}

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  className: PropTypes.string,
  text: PropTypes.string,
}

export default LoadingSpinner