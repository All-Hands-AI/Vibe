import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'

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
      
      setProject(data.project)
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
          <div className="mb-6">
            <h1 className="text-4xl font-bold text-cyber-text mb-2 font-mono">{project.name}</h1>
            <span className="text-cyber-muted font-mono text-lg">{project.slug}</span>
          </div>
          
          <div className="flex flex-wrap items-center gap-6">
            <p className="text-cyber-muted font-mono">
              Created: {new Date(project.created_at).toLocaleDateString()}
            </p>
            {project.github_url && (
              <a 
                href={project.github_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono"
              >
                View on GitHub →
              </a>
            )}
          </div>
        </header>

        {/* Project Status */}
        <section className="mb-12">
          <h2 className="text-3xl font-bold text-cyber-text mb-8 font-mono">Project Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="hacker-card">
              <h3 className="text-xl font-semibold text-cyber-text mb-4 font-mono">CI/CD Tests</h3>
              <div className="mb-4">
                {project.github_status ? (
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium font-mono ${
                    project.github_status.tests_passing === true ? 'bg-green-900/20 text-green-400 border border-green-500' : 
                    project.github_status.tests_passing === false ? 'bg-red-900/20 text-red-400 border border-red-500' : 
                    'bg-yellow-900/20 text-yellow-400 border border-yellow-500'
                  }`}>
                    {project.github_status.tests_passing === true ? '✅ Passing' : 
                     project.github_status.tests_passing === false ? '❌ Failing' : 
                     '🔄 Running'}
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium font-mono bg-cyber-accent text-cyber-muted">
                    🔄 Checking...
                  </span>
                )}
              </div>
              {project.github_status?.last_commit && (
                <p className="text-cyber-muted text-sm font-mono">
                  Last commit: {project.github_status.last_commit.substring(0, 7)}
                </p>
              )}
            </div>

            <div className="hacker-card">
              <h3 className="text-xl font-semibold text-cyber-text mb-4">Deployment</h3>
              <div className="mb-4">
                {project.fly_status ? (
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    project.fly_status.deployed ? 'bg-green-900/20 text-green-400 border border-green-500' : 'bg-red-900/20 text-red-400 border border-red-500'
                  }`}>
                    {project.fly_status.deployed ? '✅ Deployed' : '❌ Failed'}
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-700 text-cyber-muted">
                    🔄 Checking...
                  </span>
                )}
              </div>
              {project.fly_status?.app_url && (
                <a 
                  href={project.fly_status.app_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200"
                >
                  Visit App →
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