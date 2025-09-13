import PropTypes from 'prop-types'

function Input({ 
  label, 
  error, 
  className = '', 
  containerClassName = '',
  ...props 
}) {
  const baseClasses = 'w-full px-3 py-2 bg-background-secondary border rounded-lg text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background-primary transition-colors duration-200'
  
  const stateClasses = error 
    ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
    : 'border-gray-600 focus:ring-primary-300 focus:border-primary-300 hover:border-gray-500'

  return (
    <div className={`space-y-1 ${containerClassName}`}>
      {label && (
        <label className="block text-sm font-medium text-text-primary">
          {label}
        </label>
      )}
      <input
        className={`${baseClasses} ${stateClasses} ${className}`}
        {...props}
      />
      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}
    </div>
  )
}

Input.propTypes = {
  label: PropTypes.string,
  error: PropTypes.string,
  className: PropTypes.string,
  containerClassName: PropTypes.string,
}

export default Input