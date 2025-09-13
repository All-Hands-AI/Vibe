import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ThemeProvider, useTheme } from './ThemeContext'

// Test component that uses the theme context
function TestComponent() {
  const { theme, toggleTheme, isDark } = useTheme()
  
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="isDark">{isDark.toString()}</span>
      <button onClick={toggleTheme}>Toggle Theme</button>
    </div>
  )
}

describe('ThemeContext', () => {
  it('provides default dark theme', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )
    
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(screen.getByTestId('isDark')).toHaveTextContent('true')
  })

  it('toggles theme when toggleTheme is called', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )
    
    const toggleButton = screen.getByRole('button', { name: 'Toggle Theme' })
    
    // Initially dark
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(screen.getByTestId('isDark')).toHaveTextContent('true')
    
    // Toggle to light
    fireEvent.click(toggleButton)
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(screen.getByTestId('isDark')).toHaveTextContent('false')
    
    // Toggle back to dark
    fireEvent.click(toggleButton)
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(screen.getByTestId('isDark')).toHaveTextContent('true')
  })

  it('applies theme class to wrapper div', () => {
    const { container } = render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )
    
    expect(container.firstChild).toHaveClass('app-theme-dark')
  })

  it('throws error when useTheme is used outside provider', () => {
    // Suppress console.error for this test
    const originalError = console.error
    console.error = () => {}
    
    expect(() => {
      render(<TestComponent />)
    }).toThrow('useTheme must be used within a ThemeProvider')
    
    console.error = originalError
  })
})