import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import Header from './Header'

const HeaderWithRouter = () => (
  <BrowserRouter>
    <Header />
  </BrowserRouter>
)

describe('Header', () => {
  it('renders the logo', () => {
    render(<HeaderWithRouter />)
    
    expect(screen.getByText('OpenVibe')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(<HeaderWithRouter />)
    
    expect(screen.getByText('🗂️ Apps')).toBeInTheDocument()
    expect(screen.getByText('🏠 Home')).toBeInTheDocument()
    expect(screen.getByText('ℹ️ About')).toBeInTheDocument()
    expect(screen.getByText('📞 Contact')).toBeInTheDocument()
  })

  it('has proper navigation structure', () => {
    render(<HeaderWithRouter />)
    
    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
    
    const appsLink = screen.getByRole('link', { name: '🗂️ Apps' })
    expect(appsLink).toHaveAttribute('href', '/')
    
    const homeLink = screen.getByRole('link', { name: '🏠 Home' })
    expect(homeLink).toHaveAttribute('href', '/home')
    
    const aboutLink = screen.getByRole('link', { name: 'ℹ️ About' })
    expect(aboutLink).toHaveAttribute('href', '/about')
    
    const contactLink = screen.getByRole('link', { name: '📞 Contact' })
    expect(contactLink).toHaveAttribute('href', '/contact')
  })
})