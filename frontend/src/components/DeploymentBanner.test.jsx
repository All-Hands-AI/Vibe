import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import DeploymentBanner from './DeploymentBanner'

describe('DeploymentBanner', () => {
  it('renders nothing when deployment status is not running', () => {
    const { container } = render(
      <DeploymentBanner deployStatus="success" prStatus={null} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders banner when deployment status is running', () => {
    render(
      <DeploymentBanner deployStatus="running" prStatus={null} />
    )
    
    expect(screen.getByText('Hold tight, a new version is rolling out')).toBeInTheDocument()
  })

  it('renders GitHub Actions link when PR status has checks with details_url', () => {
    const prStatus = {
      checks: [
        {
          name: 'Deploy to Production',
          status: 'running',
          details_url: 'https://github.com/user/repo/actions/runs/123'
        }
      ]
    }

    render(
      <DeploymentBanner deployStatus="running" prStatus={prStatus} />
    )
    
    expect(screen.getByText('Hold tight, a new version is rolling out')).toBeInTheDocument()
    
    const link = screen.getByText('View Progress →')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', 'https://github.com/user/repo/actions/runs/123')
    expect(link.closest('a')).toHaveAttribute('target', '_blank')
  })

  it('prioritizes deploy-related checks for GitHub Actions URL', () => {
    const prStatus = {
      checks: [
        {
          name: 'Unit Tests',
          status: 'success',
          details_url: 'https://github.com/user/repo/actions/runs/456'
        },
        {
          name: 'Deploy to Production',
          status: 'running',
          details_url: 'https://github.com/user/repo/actions/runs/123'
        }
      ]
    }

    render(
      <DeploymentBanner deployStatus="running" prStatus={prStatus} />
    )
    
    const link = screen.getByText('View Progress →')
    expect(link.closest('a')).toHaveAttribute('href', 'https://github.com/user/repo/actions/runs/123')
  })

  it('falls back to any check with details_url when no deploy check exists', () => {
    const prStatus = {
      checks: [
        {
          name: 'Unit Tests',
          status: 'success',
          details_url: 'https://github.com/user/repo/actions/runs/456'
        }
      ]
    }

    render(
      <DeploymentBanner deployStatus="running" prStatus={prStatus} />
    )
    
    const link = screen.getByText('View Progress →')
    expect(link.closest('a')).toHaveAttribute('href', 'https://github.com/user/repo/actions/runs/456')
  })

  it('renders without link when no checks have details_url', () => {
    const prStatus = {
      checks: [
        {
          name: 'Unit Tests',
          status: 'success'
        }
      ]
    }

    render(
      <DeploymentBanner deployStatus="running" prStatus={prStatus} />
    )
    
    expect(screen.getByText('Hold tight, a new version is rolling out')).toBeInTheDocument()
    expect(screen.queryByText('View Progress →')).not.toBeInTheDocument()
  })
})