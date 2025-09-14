import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import AppStatus from './AppStatus'

describe('AppStatus', () => {
  beforeEach(() => {
    // Mock fetch to prevent actual API calls
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          status: 'success',
          message: 'Deployment completed successfully',
          details: {}
        })
      })
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })
  it('displays PR status when PR data is available', async () => {
    const app = {
      slug: 'test-app',
      branch: 'feature-branch',
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
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('🌿 feature-branch')).toBeInTheDocument()
    expect(screen.getByText('🔗 #123 - Add new feature')).toBeInTheDocument()
    
    // Wait for deployment status to load, then check for both CI and Deploy status
    await waitFor(() => {
      expect(screen.getAllByText('✅ Passing')).toHaveLength(2) // CI and Deploy status
    })
    
    expect(screen.getByText('🟢 Open')).toBeInTheDocument()
    expect(screen.getByText('✅ Mergeable')).toBeInTheDocument()
    expect(screen.getByText('📁 5 files')).toBeInTheDocument()
  })

  it('displays draft status correctly', () => {
    const app = {
      slug: 'test-app',
      branch: 'draft-feature',
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
    
    expect(screen.getByText('🌿 draft-feature')).toBeInTheDocument()
    expect(screen.getByText('📝 Draft')).toBeInTheDocument()
    expect(screen.getByText('🔄 Checking...')).toBeInTheDocument()
    expect(screen.getAllByText('🔄 Running')).toHaveLength(2) // CI and Deploy status
  })

  it('displays deployment status section', async () => {
    const app = {
      slug: 'conversation-123',
      branch: 'main'
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('🌿 main')).toBeInTheDocument()
    
    // Wait for deployment status to load
    await waitFor(() => {
      expect(screen.getByText('✅ Passing')).toBeInTheDocument()
    })
    
    expect(screen.getByText('🚀 https://conversation-123-conversation-123.fly.dev')).toBeInTheDocument()
  })

  it('displays individual check commits', () => {
    const app = {
      branch: 'bugfix-branch',
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
    
    expect(screen.getByText('🌿 bugfix-branch')).toBeInTheDocument()
    expect(screen.getByText('Unit Tests')).toBeInTheDocument()
    expect(screen.getByText('Lint Check')).toBeInTheDocument()
    expect(screen.getByText('⚠️ Conflicts')).toBeInTheDocument()
    expect(screen.getAllByText('View →')).toHaveLength(2)
  })

  it('handles missing PR data gracefully for non-main branch', () => {
    const app = {
      slug: 'test-app',
      branch: 'feature-branch',
      github_status: {
        tests_passing: false,
        last_commit: 'abc1234567890'
      },
      deployment_status: {
        deploy_status: 'pending',
        deployed: false
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('🌿 feature-branch')).toBeInTheDocument()
    expect(screen.getByText('❌ No active pull request found')).toBeInTheDocument()
    expect(screen.getByText('❌ Failing')).toBeInTheDocument() // Branch CI status
    expect(screen.getByText('📝 abc1234')).toBeInTheDocument() // Last commit
    expect(screen.getByText('🔄 Running')).toBeInTheDocument() // Deploy status
  })

  it('generates correct fly.io app URL', () => {
    const app = {
      slug: 'my-app',
      conversation_id: 'conv-456',
      branch: 'main'
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('🌿 main')).toBeInTheDocument()
    expect(screen.getByText('🚀 https://my-app-conv-456.fly.dev')).toBeInTheDocument()
  })

  it('handles main branch without PR gracefully', () => {
    const app = {
      slug: 'test-app',
      branch: 'main',
      github_status: {
        tests_passing: true,
        last_commit: 'def5678901234'
      }
    }

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('🌿 main')).toBeInTheDocument()
    expect(screen.queryByText('No active pull request found')).not.toBeInTheDocument() // Should not show for main
    expect(screen.getByText('✅ Passing')).toBeInTheDocument() // Branch CI status
    expect(screen.getByText('📝 def5678')).toBeInTheDocument() // Last commit
    expect(screen.getByText('🚀 https://test-app-test-app.fly.dev')).toBeInTheDocument()
  })

  it('handles empty app data gracefully', () => {
    const app = {}

    render(<AppStatus app={app} />)
    
    expect(screen.getByText('🌿 main')).toBeInTheDocument() // Default branch
    expect(screen.queryByText('No active pull request found')).not.toBeInTheDocument() // Should not show for main
    expect(screen.getByText('🚀 https://project-main.fly.dev')).toBeInTheDocument()
  })

  it('displays riff name as branch when riff is provided', () => {
    const app = {
      slug: 'test-app',
      github_url: 'https://github.com/user/test-app',
      github_status: {
        branch: 'main',
        tests_passing: true,
        last_commit: 'abc123'
      },
      deployment_status: {
        deploy_status: 'success',
        deployed: true
      }
    }

    const riff = {
      slug: 'my-test-riff',
      app_slug: 'test-app',
      created_at: '2025-09-14T01:30:00.000Z',
      created_by: 'test-user-123'
    }

    render(<AppStatus app={app} riff={riff} />)
    
    // Should display the riff name instead of the app branch
    expect(screen.getByText('🌿 my-test-riff')).toBeInTheDocument()
    expect(screen.queryByText('🌿 main')).not.toBeInTheDocument()
  })

  it('falls back to app branch when riff has no slug', () => {
    const app = {
      slug: 'test-app',
      github_status: {
        branch: 'main',
        tests_passing: true
      }
    }

    const riff = {
      app_slug: 'test-app',
      created_at: '2025-09-14T01:30:00.000Z',
      created_by: 'test-user-123'
      // slug is missing to test fallback
    }

    render(<AppStatus app={app} riff={riff} />)
    
    // Should fall back to app branch when riff slug is not available
    expect(screen.getByText('🌿 main')).toBeInTheDocument()
  })
})