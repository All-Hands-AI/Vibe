import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import CIStatus from './CIStatus'

describe('CIStatus', () => {
  it('renders nothing when no PR status is provided', () => {
    const { container } = render(<CIStatus prStatus={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when PR status has no CI data', () => {
    const prStatus = {
      number: 123,
      title: 'Test PR',
      html_url: 'https://github.com/user/repo/pull/123',
    }
    const { container } = render(<CIStatus prStatus={prStatus} />)
    expect(container.firstChild).toBeNull()
  })

  it('displays success status when all checks pass', () => {
    const prStatus = {
      ci_status: 'success',
      checks: [
        { name: 'Test 1', status: 'completed', conclusion: 'success' },
        { name: 'Test 2', status: 'completed', conclusion: 'success' },
      ],
    }
    render(<CIStatus prStatus={prStatus} />)
    expect(screen.getByText('CI: All checks passed')).toBeInTheDocument()
    expect(screen.getByText('✅')).toBeInTheDocument()
  })

  it('displays failure status when any check fails', () => {
    const prStatus = {
      ci_status: 'success',
      checks: [
        { name: 'Test 1', status: 'completed', conclusion: 'success' },
        { name: 'Test 2', status: 'completed', conclusion: 'failure' },
      ],
    }
    render(<CIStatus prStatus={prStatus} />)
    expect(screen.getByText('CI: Some checks failed')).toBeInTheDocument()
    expect(screen.getByText('❌')).toBeInTheDocument()
  })

  it('displays pending status when any check is in progress', () => {
    const prStatus = {
      ci_status: 'pending',
      checks: [
        { name: 'Test 1', status: 'completed', conclusion: 'success' },
        { name: 'Test 2', status: 'in_progress' },
      ],
    }
    render(<CIStatus prStatus={prStatus} />)
    expect(screen.getByText('CI: Checks in progress')).toBeInTheDocument()
    expect(screen.getByText('🟡')).toBeInTheDocument()
  })

  it('shows popover with individual checks on hover', () => {
    const prStatus = {
      ci_status: 'success',
      checks: [
        { name: 'Unit Tests', status: 'completed', conclusion: 'success', details_url: 'https://example.com/1' },
        { name: 'Lint Check', status: 'completed', conclusion: 'failure', details_url: 'https://example.com/2' },
      ],
    }
    render(<CIStatus prStatus={prStatus} />)
    
    const statusElement = screen.getByText('CI: Some checks failed')
    fireEvent.mouseEnter(statusElement)
    
    expect(screen.getByText('CI Checks')).toBeInTheDocument()
    expect(screen.getByText('Unit Tests')).toBeInTheDocument()
    expect(screen.getByText('Lint Check')).toBeInTheDocument()
    expect(screen.getByText('Passed')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('hides popover when mouse leaves', () => {
    const prStatus = {
      ci_status: 'success',
      checks: [
        { name: 'Unit Tests', status: 'completed', conclusion: 'success' },
      ],
    }
    render(<CIStatus prStatus={prStatus} />)
    
    const statusElement = screen.getByText('CI: All checks passed')
    fireEvent.mouseEnter(statusElement)
    expect(screen.getByText('CI Checks')).toBeInTheDocument()
    
    fireEvent.mouseLeave(statusElement)
    expect(screen.queryByText('CI Checks')).not.toBeInTheDocument()
  })

  it('falls back to ci_status when no individual checks are available', () => {
    const prStatus = {
      ci_status: 'pending',
      checks: [],
    }
    render(<CIStatus prStatus={prStatus} />)
    expect(screen.getByText('CI: Checks in progress')).toBeInTheDocument()
  })

  it('handles unknown status gracefully', () => {
    const prStatus = {
      ci_status: 'unknown',
      checks: [
        { name: 'Test', status: 'unknown' },
      ],
    }
    render(<CIStatus prStatus={prStatus} />)
    expect(screen.getByText('CI: Status unknown')).toBeInTheDocument()
    expect(screen.getByText('❓')).toBeInTheDocument()
  })
})