import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import DeploymentBanner from './DeploymentBanner'

describe('DeploymentBanner', () => {
  it('renders nothing when deployment status is not pending', () => {
    const deploymentStatus = {
      status: 'success',
      message: 'Deployment completed successfully',
      details: {}
    }
    
    const { container } = render(
      <DeploymentBanner deploymentStatus={deploymentStatus} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders banner when deployment status is pending', () => {
    const deploymentStatus = {
      status: 'pending',
      message: 'Deployment is in progress',
      details: {}
    }
    
    render(
      <DeploymentBanner deploymentStatus={deploymentStatus} />
    )
    
    expect(screen.getByText('Hold tight, a new version is rolling out')).toBeInTheDocument()
  })

  it('renders GitHub Actions link when deployment status has workflow URL', () => {
    const deploymentStatus = {
      status: 'pending',
      message: 'Deployment is in progress',
      details: {
        workflow_url: 'https://github.com/user/repo/actions/runs/123',
        commit_sha: 'abc123',
        workflow_name: 'Deploy app'
      }
    }

    render(
      <DeploymentBanner deploymentStatus={deploymentStatus} />
    )
    
    expect(screen.getByText('Hold tight, a new version is rolling out')).toBeInTheDocument()
    
    const link = screen.getByText('View Progress →')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', 'https://github.com/user/repo/actions/runs/123')
    expect(link.closest('a')).toHaveAttribute('target', '_blank')
  })

  it('renders without link when deployment status has no workflow URL', () => {
    const deploymentStatus = {
      status: 'pending',
      message: 'Deployment is in progress',
      details: {
        commit_sha: 'abc123'
      }
    }

    render(
      <DeploymentBanner deploymentStatus={deploymentStatus} />
    )
    
    expect(screen.getByText('Hold tight, a new version is rolling out')).toBeInTheDocument()
    expect(screen.queryByText('View Progress →')).not.toBeInTheDocument()
  })

  it('renders nothing when deployment status is null', () => {
    const { container } = render(
      <DeploymentBanner deploymentStatus={null} />
    )
    expect(container.firstChild).toBeNull()
  })
})