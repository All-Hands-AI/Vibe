import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders hello world message', () => {
    render(<App />)
    
    expect(screen.getByText('Hello World!')).toBeInTheDocument()
    expect(screen.getByText('Welcome to OpenVibe - Your React App is Running!')).toBeInTheDocument()
  })

  it('has proper structure', () => {
    render(<App />)
    
    const header = screen.getByRole('banner')
    expect(header).toBeInTheDocument()
    expect(header).toHaveClass('App-header')
  })
})