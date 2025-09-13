import PropTypes from 'prop-types'
import { Container } from './ui'

function Layout({ children, className = '', containerSize = 'default' }) {
  return (
    <div className={`min-h-screen bg-gray-900 ${className}`}>
      <Container size={containerSize} className="py-8">
        {children}
      </Container>
    </div>
  )
}

Layout.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  containerSize: PropTypes.oneOf(['sm', 'default', 'lg', 'full']),
}

export default Layout