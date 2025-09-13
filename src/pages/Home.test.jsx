import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Home from './Home'

describe('Home', () => {
  it('renders the hero section', () => {
    render(<Home />)
    
    expect(screen.getByText('Welcome to OpenVibe')).toBeInTheDocument()
    expect(screen.getByText('Your React App is Running!')).toBeInTheDocument()
  })

  it('renders hero buttons', () => {
    render(<Home />)
    
    expect(screen.getByRole('button', { name: 'Get Started' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Learn More' })).toBeInTheDocument()
  })

  it('renders features section', () => {
    render(<Home />)
    
    expect(screen.getByText('Features')).toBeInTheDocument()
    
    // Check for feature cards
    expect(screen.getByText('⚡ Fast')).toBeInTheDocument()
    expect(screen.getByText('🧪 Tested')).toBeInTheDocument()
    expect(screen.getByText('🔧 Modern')).toBeInTheDocument()
    expect(screen.getByText('🚀 CI/CD')).toBeInTheDocument()
  })

  it('renders feature descriptions', () => {
    render(<Home />)
    
    expect(screen.getByText('Built with Vite for lightning-fast development and builds')).toBeInTheDocument()
    expect(screen.getByText('Comprehensive testing setup with Vitest and React Testing Library')).toBeInTheDocument()
    expect(screen.getByText('Latest React features with hooks, context, and modern JavaScript')).toBeInTheDocument()
    expect(screen.getByText('GitHub Actions workflow for automated testing and deployment')).toBeInTheDocument()
  })
})