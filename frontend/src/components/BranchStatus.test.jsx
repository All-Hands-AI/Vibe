import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import BranchStatus from './BranchStatus'

describe('BranchStatus', () => {
  it('displays default branch name when no branch is provided', () => {
    const app = {
      github_status: {
        tests_passing: true,
        last_commit: 'abc1234567890'
      }
    }

    render(<BranchStatus app={app} />)
    
    expect(screen.getByText('main')).toBeInTheDocument()
    expect(screen.getByText('✅ Passing')).toBeInTheDocument()
  })

  it('displays custom branch name when provided', () => {
    const app = {
      github_status: {
        branch: 'feature/new-feature',
        tests_passing: true,
        last_commit: 'abc1234567890'
      }
    }

    render(<BranchStatus app={app} />)
    
    expect(screen.getByText('feature/new-feature')).toBeInTheDocument()
  })

  it('displays failing status with generic failing check when tests are failing', () => {
    const app = {
      github_url: 'https://github.com/user/repo',
      github_status: {
        tests_passing: false,
        last_commit: 'abc1234567890'
      }
    }

    render(<BranchStatus app={app} />)
    
    expect(screen.getByText('❌ Failing')).toBeInTheDocument()
    expect(screen.getByText('Failing Checks')).toBeInTheDocument()
    expect(screen.getByText('CI Tests')).toBeInTheDocument()
  })

  it('displays specific failing checks when provided', () => {
    const app = {
      github_status: {
        tests_passing: false,
        last_commit: 'abc1234567890',
        failing_checks: [
          {
            name: 'Unit Tests',
            status: 'failure',
            conclusion: 'failure',
            details_url: 'https://github.com/user/repo/actions/runs/123'
          },
          {
            name: 'Lint Check',
            status: 'failure',
            conclusion: 'failure',
            details_url: 'https://github.com/user/repo/actions/runs/124'
          }
        ]
      }
    }

    render(<BranchStatus app={app} />)
    
    expect(screen.getByText('Unit Tests')).toBeInTheDocument()
    expect(screen.getByText('Lint Check')).toBeInTheDocument()
    expect(screen.getAllByText('View Details →')).toHaveLength(2)
  })

  it('displays running status when tests are pending', () => {
    const app = {
      github_status: {
        tests_passing: null,
        last_commit: 'abc1234567890'
      }
    }

    render(<BranchStatus app={app} />)
    
    expect(screen.getByText('🔄 Running')).toBeInTheDocument()
  })

  it('displays last commit hash when provided', () => {
    const app = {
      github_status: {
        tests_passing: true,
        last_commit: 'abc1234567890'
      }
    }

    render(<BranchStatus app={app} />)
    
    expect(screen.getByText('abc1234')).toBeInTheDocument()
  })

  it('handles app without github_status gracefully', () => {
    const app = {}

    render(<BranchStatus app={app} />)
    
    expect(screen.getByText('main')).toBeInTheDocument()
    expect(screen.getByText('🔄 Checking...')).toBeInTheDocument()
  })
})