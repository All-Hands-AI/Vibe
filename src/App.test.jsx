import { render, screen } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import App from './App'

// Mock fetch globally for App tests too
global.fetch = vi.fn()

describe('App', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    fetch.mockClear()
    
    // Mock successful API responses
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Hello from the API!', endpoint: '/api/hello' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy', service: 'OpenVibe Backend' })
      })
  })

  it('renders the main layout components', () => {
    render(<App />)
    
    // Check for header logo specifically
    expect(screen.getByRole('link', { name: 'OpenVibe' })).toBeInTheDocument()
    
    // Check for home page content (default route) - updated text
    expect(screen.getByText('Welcome to OpenVibe')).toBeInTheDocument()
    expect(screen.getByText('Your React App is Running with Python Backend!')).toBeInTheDocument()
    
    // Check for footer
    expect(screen.getByText('© 2025 OpenVibe. All rights reserved.')).toBeInTheDocument()
  })

  it('has proper navigation structure', () => {
    render(<App />)
    
    // Check navigation links in header specifically
    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
    
    // Use getAllByRole to handle multiple links with same name
    const homeLinks = screen.getAllByRole('link', { name: 'Home' })
    expect(homeLinks.length).toBeGreaterThan(0)
    
    const aboutLinks = screen.getAllByRole('link', { name: 'About' })
    expect(aboutLinks.length).toBeGreaterThan(0)
    
    const contactLinks = screen.getAllByRole('link', { name: 'Contact' })
    expect(contactLinks.length).toBeGreaterThan(0)
  })

  it('renders with theme provider', () => {
    const { container } = render(<App />)
    
    // Check that theme class is applied
    expect(container.querySelector('.app-theme-dark')).toBeInTheDocument()
  })
})