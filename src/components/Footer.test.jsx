import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Footer from './Footer'

describe('Footer', () => {
  it('renders the footer content', () => {
    render(<Footer />)
    
    expect(screen.getByText('OpenVibe')).toBeInTheDocument()
    expect(screen.getByText('Building amazing experiences with React')).toBeInTheDocument()
  })

  it('renders quick links section', () => {
    render(<Footer />)
    
    expect(screen.getByText('Quick Links')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'About' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Contact' })).toBeInTheDocument()
  })

  it('renders connect section with external links', () => {
    render(<Footer />)
    
    expect(screen.getByText('Connect')).toBeInTheDocument()
    
    const githubLink = screen.getByRole('link', { name: 'GitHub' })
    expect(githubLink).toHaveAttribute('target', '_blank')
    expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer')
    
    const twitterLink = screen.getByRole('link', { name: 'Twitter' })
    expect(twitterLink).toHaveAttribute('target', '_blank')
    
    const linkedinLink = screen.getByRole('link', { name: 'LinkedIn' })
    expect(linkedinLink).toHaveAttribute('target', '_blank')
  })

  it('renders copyright notice', () => {
    render(<Footer />)
    
    expect(screen.getByText('© 2025 OpenVibe. All rights reserved.')).toBeInTheDocument()
  })
})