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
      <div className="project-detail-page">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading project...</p>
        </div>
      </div>
    )
  }

  if (error && !project) {
    return (
      <div className="project-detail-page">
        <div className="error-state">
          <h2>Error</h2>
          <p>{error}</p>
          <Link to="/" className="back-link">← Back to Projects</Link>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="project-detail-page">
        <div className="error-state">
          <h2>Project Not Found</h2>
          <p>The project &quot;{slug}&quot; could not be found.</p>
          <Link to="/" className="back-link">← Back to Projects</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="project-detail-page">
      <div className="project-detail-container">
        {/* Navigation */}
        <nav className="project-nav">
          <Link to="/" className="back-link">← Back to Projects</Link>
        </nav>

        {/* Project Header */}
        <header className="project-header">
          <div className="project-title">
            <h1>{project.name}</h1>
            <span className="project-slug">{project.slug}</span>
          </div>
          
          <div className="project-meta">
            <p>Created: {new Date(project.created_at).toLocaleDateString()}</p>
            {project.github_url && (
              <a 
                href={project.github_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="github-link"
              >
                View on GitHub →
              </a>
            )}
          </div>
        </header>

        {/* Project Status */}
        <section className="project-status">
          <h2>Project Status</h2>
          <div className="status-grid">
            <div className="status-card">
              <h3>CI/CD Tests</h3>
              <div className="status-indicator">
                {project.github_status ? (
                  <span className={`status ${
                    project.github_status.tests_passing === true ? 'success' : 
                    project.github_status.tests_passing === false ? 'error' : 
                    'running'
                  }`}>
                    {project.github_status.tests_passing === true ? '✅ Passing' : 
                     project.github_status.tests_passing === false ? '❌ Failing' : 
                     '🔄 Running'}
                  </span>
                ) : (
                  <span className="status loading">🔄 Checking...</span>
                )}
              </div>
              {project.github_status?.last_commit && (
                <p className="status-detail">
                  Last commit: {project.github_status.last_commit.substring(0, 7)}
                </p>
              )}
            </div>

            <div className="status-card">
              <h3>Deployment</h3>
              <div className="status-indicator">
                {project.fly_status ? (
                  <span className={`status ${project.fly_status.deployed ? 'success' : 'error'}`}>
                    {project.fly_status.deployed ? '✅ Deployed' : '❌ Failed'}
                  </span>
                ) : (
                  <span className="status loading">🔄 Checking...</span>
                )}
              </div>
              {project.fly_status?.app_url && (
                <a 
                  href={project.fly_status.app_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="deployment-link"
                >
                  Visit App →
                </a>
              )}
            </div>
          </div>
        </section>

        {/* Conversations Section */}
        <section className="conversations-section">
          <h2>Conversations</h2>
          
          {/* Create New Conversation */}
          <div className="create-conversation">
            <h3>Create New Conversation</h3>
            <form onSubmit={handleCreateConversation} className="create-conversation-form">
              <div className="form-group">
                <input
                  type="text"
                  value={newConversationName}
                  onChange={(e) => setNewConversationName(e.target.value)}
                  placeholder="Enter conversation name"
                  disabled={creating}
                  className={error ? 'error' : ''}
                />
                {newConversationName && (
                  <div className="slug-preview">
                    Slug: <code>{createSlug(newConversationName)}</code>
                  </div>
                )}
              </div>
              
              <button 
                type="submit" 
                disabled={creating || !newConversationName.trim()}
                className="create-button"
              >
                {creating ? 'Creating...' : 'Create Conversation'}
              </button>
            </form>

            {error && (
              <div className="message error-message">
                {error}
              </div>
            )}

            {success && (
              <div className="message success-message">
                {success}
              </div>
            )}
          </div>

          {/* Conversations List */}
          <div className="conversations-list">
            <h3>All Conversations</h3>
            
            {conversationsLoading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>Loading conversations...</p>
              </div>
            ) : conversations.length === 0 ? (
              <div className="empty-state">
                <p>No conversations yet. Create your first conversation above!</p>
              </div>
            ) : (
              <div className="conversations-grid">
                {conversations.map((conversation) => (
                  <Link 
                    key={conversation.id} 
                    to={`/projects/${project.slug}/conversations/${conversation.slug}`}
                    className="conversation-card"
                  >
                    <div className="conversation-header">
                      <h4>{conversation.name}</h4>
                      <span className="conversation-slug">{conversation.slug}</span>
                    </div>
                    
                    <div className="conversation-details">
                      <p className="conversation-date">
                        Created: {new Date(conversation.created_at).toLocaleDateString()}
                      </p>
                      {conversation.last_message_at && (
                        <p className="conversation-activity">
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