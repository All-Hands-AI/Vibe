import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'

function ConversationDetail() {
  const { slug: projectSlug, conversationSlug } = useParams()
  const [project, setProject] = useState(null)
  const [conversation, setConversation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Fetch project and conversation details
  const fetchData = useCallback(async () => {
    console.log('🔄 Fetching conversation details:', { projectSlug, conversationSlug })
    try {
      setLoading(true)
      
      // First, get the project to find its ID
      const projectResponse = await fetch(`/api/projects/${projectSlug}`)
      console.log('📡 Project response status:', projectResponse?.status)
      
      if (!projectResponse || !projectResponse.ok) {
        const errorText = await projectResponse?.text() || 'Unknown error'
        console.error('❌ Fetch project failed:', errorText)
        throw new Error(`Failed to fetch project: ${projectResponse?.status} ${errorText}`)
      }
      
      const projectData = await projectResponse.json()
      console.log('📊 Received project data:', projectData)
      setProject(projectData.project)
      
      // Now get the conversations for this project
      const conversationsResponse = await fetch(`/api/projects/${projectData.project.id}/conversations`)
      console.log('📡 Conversations response status:', conversationsResponse?.status)
      
      if (!conversationsResponse || !conversationsResponse.ok) {
        const errorText = await conversationsResponse?.text() || 'Unknown error'
        console.error('❌ Fetch conversations failed:', errorText)
        throw new Error(`Failed to fetch conversations: ${conversationsResponse?.status} ${errorText}`)
      }
      
      const conversationsData = await conversationsResponse.json()
      console.log('📊 Received conversations data:', conversationsData)
      
      // Find the specific conversation by slug
      const foundConversation = conversationsData.conversations.find(
        c => c.slug === conversationSlug
      )
      
      if (!foundConversation) {
        console.error('❌ Conversation not found:', conversationSlug)
        throw new Error('Conversation not found')
      }
      
      setConversation(foundConversation)
      console.log('✅ Data loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching data:', err)
      setError(err.message || 'Failed to load conversation. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [projectSlug, conversationSlug])

  // Load data on component mount
  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) {
    return (
      <div className="conversation-detail-page">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading conversation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="conversation-detail-page">
        <div className="error-state">
          <h2>Error</h2>
          <p>{error}</p>
          <div className="error-actions">
            <Link to="/" className="back-link">← Back to Projects</Link>
            {project && (
              <Link to={`/projects/${project.slug}`} className="back-link">
                ← Back to {project.name}
              </Link>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (!project || !conversation) {
    return (
      <div className="conversation-detail-page">
        <div className="error-state">
          <h2>Not Found</h2>
          <p>The conversation could not be found.</p>
          <Link to="/" className="back-link">← Back to Projects</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="conversation-detail-page">
      <div className="conversation-detail-container">
        {/* Navigation */}
        <nav className="conversation-nav">
          <Link to="/" className="back-link">← Projects</Link>
          <span className="nav-separator">/</span>
          <Link to={`/projects/${project.slug}`} className="back-link">
            {project.name}
          </Link>
          <span className="nav-separator">/</span>
          <span className="current-page">{conversation.name}</span>
        </nav>

        {/* Conversation Header */}
        <header className="conversation-header">
          <div className="conversation-title">
            <h1>{conversation.name}</h1>
            <span className="conversation-slug">{conversation.slug}</span>
          </div>
          
          <div className="conversation-meta">
            <p>Created: {new Date(conversation.created_at).toLocaleDateString()}</p>
            {conversation.last_message_at && (
              <p>Last activity: {new Date(conversation.last_message_at).toLocaleDateString()}</p>
            )}
            <p>Messages: {conversation.message_count || 0}</p>
          </div>
        </header>

        {/* Conversation Content */}
        <section className="conversation-content">
          <div className="conversation-placeholder">
            <div className="placeholder-icon">💬</div>
            <h3>Conversation Interface</h3>
            <p>This is where the conversation interface would be implemented.</p>
            <p>Features to add:</p>
            <ul>
              <li>Message history display</li>
              <li>Message input and sending</li>
              <li>Real-time updates</li>
              <li>File attachments</li>
              <li>Message search and filtering</li>
            </ul>
          </div>
        </section>

        {/* Conversation Actions */}
        <section className="conversation-actions">
          <div className="actions-grid">
            <div className="action-card">
              <h4>Export Conversation</h4>
              <p>Download this conversation as a file</p>
              <button className="action-button" disabled>
                Export (Coming Soon)
              </button>
            </div>
            
            <div className="action-card">
              <h4>Share Conversation</h4>
              <p>Generate a shareable link</p>
              <button className="action-button" disabled>
                Share (Coming Soon)
              </button>
            </div>
            
            <div className="action-card">
              <h4>Archive Conversation</h4>
              <p>Move to archived conversations</p>
              <button className="action-button danger" disabled>
                Archive (Coming Soon)
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default ConversationDetail