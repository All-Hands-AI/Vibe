import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'
import BranchStatus from '../components/BranchStatus'

function ProjectDetail() {
  const { slug } = useParams()
  const [project, setProject] = useState(null)
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [conversationsLoading, setConversationsLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newConversationName, setNewConversationName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Helper function to extract hostname from URL
  const getHostname = (url) => {
    if (!url) return null
    try {
      const urlObj = new URL(url)
      return urlObj.hostname
    } catch {
      return null
    }
  }

  // Helper function to extract repo name from GitHub URL
  const getRepoName = (githubUrl) => {
    if (!githubUrl) return null
    try {
      const urlObj = new URL(githubUrl)
      const pathParts = urlObj.pathname.split('/').filter(part => part)
      if (pathParts.length >= 2) {
        return `${pathParts[0]}/${pathParts[1]}`
      }
      return null
    } catch {
      return null
    }
  }

  // Helper function to get Fly.io dashboard URL
  const getFlyDashboardUrl = (appUrl) => {
    if (!appUrl) return null
    try {
      const urlObj = new URL(appUrl)
      const hostname = urlObj.hostname
      // Extract app name from hostname (e.g., "my-app.fly.dev" -> "my-app")
      const appName = hostname.replace('.fly.dev', '')
      return `https://fly.io/apps/${appName}`
    } catch {
      return null
    }
  }

  // Create slug from conversation name
  const createSlug = (name) => {
    return name
      .toLowerCase()
      .replace(/[^a-zA-Z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
  }

  // Fetch project details
  const fetchProject = useCallback(async () => {
    console.log('🔄 Fetching project details for slug:', slug)
    try {
      setLoading(true)
      
      const uuid = getUserUUID()
      const headers = {
        'X-User-UUID': uuid
      }
      
      const response = await fetch(`/api/projects/${slug}`, { headers })
      console.log('📡 Project response status:', response?.status)
      
      if (!response || !response.ok) {
        const errorText = await response?.text() || 'Unknown error'
        console.error('❌ Fetch project failed:', errorText)
        throw new Error(`Failed to fetch project: ${response?.status} ${errorText}`)
      }
      
      const data = await response.json()
      console.log('📊 Received project data:', data)
      
      setProject(data)
      console.log('✅ Project loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching project:', err)
      setError('Failed to load project. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [slug])

  // Fetch conversations for this project
  const fetchConversations = useCallback(async () => {
    if (!project) return
    
    console.log('🔄 Fetching conversations for project:', project.id)
    try {
      setConversationsLoading(true)
      
      const response = await fetch(`/api/projects/${project.id}/conversations`)
      console.log('📡 Conversations response status:', response?.status)
      
      if (!response || !response.ok) {
        const errorText = await response?.text() || 'Unknown error'
        console.error('❌ Fetch conversations failed:', errorText)
        throw new Error(`Failed to fetch conversations: ${response?.status} ${errorText}`)
      }
      
      const data = await response.json()
      console.log('📊 Received conversations data:', data)
      
      setConversations(data.conversations || [])
      console.log('✅ Conversations loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching conversations:', err)
      // Don't set error for conversations, just log it
    } finally {
      setConversationsLoading(false)
    }
  }, [project])

  // Create new conversation
  const handleCreateConversation = async (e) => {
    e.preventDefault()
    console.log('🆕 Creating new conversation...')
    
    if (!newConversationName.trim()) {
      console.warn('❌ Conversation name is empty')
      setError('Conversation name is required')
      return
    }

    const conversationSlug = createSlug(newConversationName.trim())
    console.log('📝 Conversation details:', { name: newConversationName.trim(), slug: conversationSlug })
    
    if (!conversationSlug) {
      console.warn('❌ Invalid conversation slug generated')
      setError('Please enter a valid conversation name')
      return
    }

    try {
      setCreating(true)
      setError('')
      setSuccess('')

      const uuid = getUserUUID()
      console.log('🆔 User UUID:', uuid)

      const requestData = {
        name: newConversationName.trim(),
        slug: conversationSlug
      }
      
      const requestOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-UUID': uuid
        },
        body: JSON.stringify(requestData),
      }
      
      console.log('📡 Request options:', requestOptions)

      const response = await fetch(`/api/projects/${project.id}/conversations`, requestOptions)
      
      console.log('📡 Create conversation response status:', response?.status)

      const data = await response.json()
      console.log('📊 Create conversation response data:', data)

      if (!response.ok) {
        console.error('❌ Create conversation failed:', data)
        throw new Error(data.error || 'Failed to create conversation')
      }

      console.log('✅ Conversation created successfully:', data.conversation)
      setSuccess(`Conversation "${newConversationName}" created successfully!`)
      setNewConversationName('')
      
      // Refresh conversations list
      console.log('🔄 Refreshing conversations list...')
      await fetchConversations()
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(''), 5000)
      
    } catch (err) {
      console.error('❌ Error creating conversation:', err)
      setError(err.message || 'Failed to create conversation. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  // Load project on component mount
  useEffect(() => {
    fetchProject()
  }, [fetchProject])

  // Load conversations when project is loaded
  useEffect(() => {
    if (project) {
      fetchConversations()
    }
  }, [project, fetchConversations])

  // Clear error when user starts typing
  useEffect(() => {
    if (error && newConversationName) {
      setError('')
    }
  }, [newConversationName, error])

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-10 h-10 border-4 border-cyber-border border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-cyber-muted font-mono">Loading project...</p>
        </div>
      </div>
    )
  }

  if (error && !project) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4 font-mono">Error</h2>
            <p className="text-cyber-muted mb-8 font-mono">{error}</p>
            <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono">
              ← Back to Projects
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4 font-mono">Project Not Found</h2>
            <p className="text-cyber-muted mb-8 font-mono">The project &quot;{slug}&quot; could not be found.</p>
            <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono">
              ← Back to Projects
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-cyber-text">
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Navigation */}
        <nav className="mb-8">
          <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono">
            ← Back to Projects
          </Link>
        </nav>

        {/* Project Header */}
        <header className="mb-12">
          <div className="flex flex-wrap items-baseline justify-between gap-4 mb-6">
            <div>
              <h1 className="text-4xl font-bold text-cyber-text mb-2 font-mono">{project.name}</h1>
              <span className="text-cyber-muted font-mono text-lg">{project.slug}</span>
            </div>
            <p className="text-cyber-muted font-mono text-sm">
              Created {new Date(project.created_at).toLocaleDateString()}
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-6">
            {project.github_url && (
              <a 
                href={project.github_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                {getRepoName(project.github_url) || 'GitHub'}
              </a>
            )}
            {project.fly_status?.app_url && (
              <a 
                href={getFlyDashboardUrl(project.fly_status.app_url)} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                Fly.io Dashboard
              </a>
            )}
          </div>
        </header>

        {/* Project Status */}
        <section className="mb-12">
          <h2 className="text-3xl font-bold text-cyber-text mb-8 font-mono">Project Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <BranchStatus project={project} />

            <div className="hacker-card">
              <h3 className="text-xl font-semibold text-cyber-text mb-4 font-mono">Deployment</h3>
              <div className="mb-4">
                {project.fly_status ? (
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium font-mono border ${
                    project.fly_status.deployed ? 'bg-green-900/20 text-green-400 border-green-500' : 'bg-red-900/20 text-red-400 border-red-500'
                  }`}>
                    {project.fly_status.deployed ? '✅ Deployed' : '❌ Failed'}
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-cyber-accent text-cyber-muted border border-cyber-border">
                    🔄 Checking...
                  </span>
                )}
              </div>
              {project.fly_status?.app_url && (
                <a 
                  href={project.fly_status.app_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                  </svg>
                  {getHostname(project.fly_status.app_url) || 'Visit App'}
                </a>
              )}
            </div>
          </div>
        </section>

        {/* Conversations Section */}
        <section>
          <h2 className="text-3xl font-bold text-cyber-muted mb-8">Conversations</h2>
          
          {/* Create New Conversation */}
          <div className="mb-12">
            <h3 className="text-2xl font-semibold text-cyber-text mb-6">Create New Conversation</h3>
            <div className="hacker-card p-6 rounded-lg border border-gray-700 max-w-2xl">
              <form onSubmit={handleCreateConversation} className="space-y-6">
                <div>
                  <input
                    type="text"
                    value={newConversationName}
                    onChange={(e) => setNewConversationName(e.target.value)}
                    placeholder="Enter conversation name"
                    disabled={creating}
                    className={`w-full px-4 py-3 bg-gray-700 text-cyber-text rounded-md border transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-cyber-muted focus:border-transparent ${
                      error ? 'border-red-500' : 'border-gray-600'
                    }`}
                  />
                  {newConversationName && (
                    <div className="mt-2 text-sm text-cyber-muted">
                      Slug: <code className="bg-gray-700 px-2 py-1 rounded text-cyber-muted">{createSlug(newConversationName)}</code>
                    </div>
                  )}
                </div>
                
                <button 
                  type="submit" 
                  disabled={creating || !newConversationName.trim()}
                  className="w-full px-6 py-3 bg-cyber-muted text-gray-900 rounded-md font-semibold hover:bg-neon-green disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:transform hover:-translate-y-0.5"
                >
                  {creating ? 'Creating...' : 'Create Conversation'}
                </button>
              </form>

              {error && (
                <div className="mt-4 p-4 bg-red-900/20 border border-red-500 rounded-md text-red-400">
                  {error}
                </div>
              )}

              {success && (
                <div className="mt-4 p-4 bg-green-900/20 border border-green-500 rounded-md text-green-400">
                  {success}
                </div>
              )}
            </div>
          </div>

          {/* Conversations List */}
          <div>
            <h3 className="text-2xl font-semibold text-cyber-text mb-6">All Conversations</h3>
            
            {conversationsLoading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="w-10 h-10 border-4 border-gray-600 border-t-cyber-muted rounded-full animate-spin mb-4"></div>
                <p className="text-cyber-muted">Loading conversations...</p>
              </div>
            ) : conversations.length === 0 ? (
              <div className="text-center py-16">
                <p className="text-cyber-muted text-lg">No conversations yet. Create your first conversation above!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {conversations.map((conversation) => (
                  <Link 
                    key={conversation.id} 
                    to={`/projects/${project.slug}/conversations/${conversation.slug}`}
                    className="block hacker-card rounded-lg border border-gray-700 hover:border-cyber-muted transition-all duration-300 hover:transform hover:-translate-y-1 p-6"
                  >
                    <div className="mb-4">
                      <h4 className="text-xl font-semibold text-cyber-text mb-1">{conversation.name}</h4>
                      <span className="text-sm text-cyber-muted font-mono">{conversation.slug}</span>
                    </div>
                    
                    <div className="space-y-2">
                      <p className="text-sm text-cyber-muted">
                        Created: {new Date(conversation.created_at).toLocaleDateString()}
                      </p>
                      {conversation.last_message_at && (
                        <p className="text-sm text-cyber-muted">
                          Last activity: {new Date(conversation.last_message_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default ProjectDetail