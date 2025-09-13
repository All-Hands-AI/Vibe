import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AppStatus from './AppStatus'

describe('AppStatus', () => {
  it('displays PR status when PR data is available', () => {
    const app = {
      name: 'test-app',
      slug: 'test-app',
      pr_status: {
        number: 123,
        title: 'Add new feature',
        html_url: 'https://github.com/user/repo/pull/123',
        draft: false,
        mergeable: true,
        changed_files: 5,
        ci_status: 'success',
        checks: [
          {
            name: 'Unit Tests',
            status: 'success',
            details_url: 'https://github.com/user/repo/actions/runs/123'
          }
        ]
      },
      deployment_status: {
        deploy_status: 'success',
        deployed: true,
        app_url: 'https://test-app-main.fly.dev'
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('Pull Request Status')).toBeInTheDocument()
    expect(screen.getByText('#123 - Add new feature')).toBeInTheDocument()
    expect(screen.getAllByText('✅ Passing')).toHaveLength(2) // CI and Deploy status
    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.getByText('Mergeable')).toBeInTheDocument()
    expect(screen.getByText('5 files')).toBeInTheDocument()
  })

  it('displays draft status correctly', () => {
    const app = {
      name: 'test-app',
      pr_status: {
        number: 456,
        title: 'Draft PR',
        html_url: 'https://github.com/user/repo/pull/456',
        draft: true,
        mergeable: null,
        changed_files: 2,
        ci_status: 'pending'
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('Draft')).toBeInTheDocument()
    expect(screen.getByText('Checking...')).toBeInTheDocument()
    expect(screen.getAllByText('🔄 Running')).toHaveLength(2) // CI and Deploy status
  })

  it('displays deployment status section', () => {
    const app = {
      name: 'my-project',
      slug: 'conversation-123',
      deployment_status: {
        deploy_status: 'success',
        deployed: true,
        app_url: 'https://my-project-conversation-123.fly.dev'
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('Deployment Status')).toBeInTheDocument()
    expect(screen.getByText('✅ Passing')).toBeInTheDocument()
    expect(screen.getByText('🚀 Deployed')).toBeInTheDocument()
    expect(screen.getByText('https://my-project-conversation-123.fly.dev')).toBeInTheDocument()
  })

  it('displays individual check commits', () => {
    const app = {
      pr_status: {
        number: 789,
        title: 'Fix bug',
        html_url: 'https://github.com/user/repo/pull/789',
        draft: false,
        mergeable: false,
        changed_files: 1,
        ci_status: 'failure',
        checks: [
          {
            name: 'Unit Tests',
            status: 'success',
            details_url: 'https://github.com/user/repo/actions/runs/123'
          },
          {
            name: 'Lint Check',
            status: 'failure',
            details_url: 'https://github.com/user/repo/actions/runs/124'
          }
        ]
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('Unit Tests')).toBeInTheDocument()
    expect(screen.getByText('Lint Check')).toBeInTheDocument()
    expect(screen.getByText('Conflicts')).toBeInTheDocument()
    expect(screen.getAllByText('View →')).toHaveLength(2)
  })

  it('handles missing PR data gracefully', () => {
    const app = {
      name: 'test-app',
      deployment_status: {
        deploy_status: 'pending',
        deployed: false
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('No active pull request found')).toBeInTheDocument()
    expect(screen.getByText('Deployment Status')).toBeInTheDocument()
    expect(screen.getByText('🔄 Running')).toBeInTheDocument()
  })

  it('generates correct fly.io app URL', () => {
    const app = {
      name: 'my-app',
      conversation_id: 'conv-456'
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('https://my-app-conv-456.fly.dev')).toBeInTheDocument()
  })

  it('handles empty app data gracefully', () => {
    const app = {}

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('App Status')).toBeInTheDocument()
    expect(screen.getByText('No active pull request found')).toBeInTheDocument()
    expect(screen.getByText('https://project-main.fly.dev')).toBeInTheDocument()
  })
})