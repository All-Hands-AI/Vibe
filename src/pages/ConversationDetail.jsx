import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import MessageList from '../components/MessageList'
import MessageInput from '../components/MessageInput'
import { useConversation } from '../hooks/useConversation'

function ConversationDetail() {
  const { slug: projectSlug, conversationSlug } = useParams()
  const [project, setProject] = useState(null)
  const [projectLoading, setProjectLoading] = useState(true)
  const [projectError, setProjectError] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [isDirectAccess, setIsDirectAccess] = useState(false)

  // Fetch project details to get project ID
  const fetchProject = useCallback(async () => {
    try {
      setProjectLoading(true)
      setProjectError('')
      
      if (projectSlug) {
        // Normal access via /projects/:slug/conversations/:conversationSlug
        console.log('🔄 Fetching project details:', projectSlug)
        setIsDirectAccess(false)
        
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
        
        // Now get the conversations for this project to find the conversation ID
        const conversationsResponse = await fetch(`/api/projects/${projectData.project.id}/conversations`)
        console.log('📡 Conversations response status:', conversationsResponse?.status)
        
        if (!conversationsResponse || !conversationsResponse.ok) {
          const errorText = await conversationsResponse?.text() || 'Unknown error'
          console.error('❌ Fetch conversations failed:', errorText)
          throw new Error(`Failed to fetch conversations: ${conversationsResponse?.status} ${errorText}`)
        }
        
        const conversationsData = await conversationsResponse.json()
        console.log('📊 Received conversations data:', conversationsData)
        
        // Find the specific conversation by slug or ID
        const foundConversation = conversationsData.conversations.find(
          c => c.slug === conversationSlug || c.id === conversationSlug
        )
        
        if (!foundConversation) {
          console.error('❌ Conversation not found:', conversationSlug)
          throw new Error('Conversation not found')
        }
        
        setConversationId(foundConversation.id)
        console.log('✅ Project data loaded successfully, conversation ID:', foundConversation.id)
      } else {
        // Direct access via /conversations/:conversationSlug
        console.log('🔄 Direct conversation access, searching across all projects:', conversationSlug)
        setIsDirectAccess(true)
        
        // First, get all projects
        const projectsResponse = await fetch('/api/projects')
        console.log('📡 Projects response status:', projectsResponse?.status)
        
        if (!projectsResponse || !projectsResponse.ok) {
          const errorText = await projectsResponse?.text() || 'Unknown error'
          console.error('❌ Fetch projects failed:', errorText)
          throw new Error(`Failed to fetch projects: ${projectsResponse?.status} ${errorText}`)
        }
        
        const projectsData = await projectsResponse.json()
        console.log('📊 Received projects data:', projectsData)
        
        // Search for the conversation across all projects
        let foundConversation = null
        let foundProject = null
        
        for (const proj of projectsData.projects || []) {
          try {
            const conversationsResponse = await fetch(`/api/projects/${proj.id}/conversations`)
            if (conversationsResponse.ok) {
              const conversationsData = await conversationsResponse.json()
              const conversation = conversationsData.conversations.find(
                c => c.slug === conversationSlug || c.id === conversationSlug
              )
              if (conversation) {
                foundConversation = conversation
                foundProject = proj
                break
              }
            }
          } catch (err) {
            console.warn(`⚠️ Failed to fetch conversations for project ${proj.id}:`, err)
            // Continue searching other projects
          }
        }
        
        if (!foundConversation || !foundProject) {
          console.error('❌ Conversation not found across all projects:', conversationSlug)
          throw new Error('Conversation not found')
        }
        
        setProject(foundProject)
        setConversationId(foundConversation.id)
        console.log('✅ Conversation found via direct access, project:', foundProject.name, 'conversation ID:', foundConversation.id)
      }
    } catch (err) {
      console.error('❌ Error fetching project data:', err)
      setProjectError(err.message || 'Failed to load project. Please try again.')
    } finally {
      setProjectLoading(false)
    }
  }, [projectSlug, conversationSlug])

  // Load project data on component mount
  useEffect(() => {
    fetchProject()
  }, [fetchProject])

  // Use the conversation hook once we have the project ID and conversation ID
  const {
    messages,
    events,
    conversation,
    loading: conversationLoading,
    error: conversationError,
    sending,
    sendMessage,
    refresh,
    pollingEnabled,
    setPollingEnabled,
    isPolling
  } = useConversation(project?.id, conversationId)

  const loading = projectLoading || conversationLoading
  const error = projectError || conversationError

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-10 h-10 border-4 border-gray-600 border-t-primary-300 rounded-full animate-spin mb-4"></div>
          <p className="text-gray-400">Loading conversation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4">Error</h2>
            <p className="text-gray-300 mb-8">{error}</p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link to="/" className="inline-flex items-center text-primary-300 hover:text-primary-400 font-medium transition-colors duration-200">
                ← Back to Projects
              </Link>
              {project && !isDirectAccess && (
                <Link to={`/projects/${project.slug}`} className="inline-flex items-center text-primary-300 hover:text-primary-400 font-medium transition-colors duration-200">
                  ← Back to {project.name}
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!project || !conversation) {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4">Not Found</h2>
            <p className="text-gray-300 mb-8">The conversation could not be found.</p>
            <Link to="/" className="inline-flex items-center text-primary-300 hover:text-primary-400 font-medium transition-colors duration-200">
              ← Back to Projects
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Navigation */}
        <nav className="mb-8">
          <div className="flex items-center space-x-2 text-sm">
            <Link to="/" className="text-primary-300 hover:text-primary-400 transition-colors duration-200">
              ← Projects
            </Link>
            {!isDirectAccess && (
              <>
                <span className="text-gray-500">/</span>
                <Link to={`/projects/${project.slug}`} className="text-primary-300 hover:text-primary-400 transition-colors duration-200">
                  {project.name}
                </Link>
              </>
            )}
            <span className="text-gray-500">/</span>
            <span className="text-gray-300">{conversation.name}</span>
            {isDirectAccess && (
              <span className="text-gray-500 ml-2">(from {project.name})</span>
            )}
          </div>
        </nav>

        {/* Conversation Header */}
        <header className="mb-8">
          <div className="mb-6">
            <h1 className="text-4xl font-bold text-white mb-2">
              {conversation?.name || conversation?.id || 'Conversation'}
            </h1>
            <span className="text-gray-400 font-mono text-lg">{conversationSlug}</span>
          </div>
          
          <div className="flex flex-wrap items-center gap-6 text-gray-300 mb-4">
            <p>Created: {conversation?.created_at ? new Date(conversation.created_at).toLocaleDateString() : 'Unknown'}</p>
            {conversation?.last_message_at && (
              <p>Last activity: {new Date(conversation.last_message_at).toLocaleDateString()}</p>
            )}
            <p>Messages: {messages?.length || 0}</p>
            <p>Events: {events?.length || 0}</p>
            {isPolling && <p className="text-primary-400 font-medium">🔄 Live updates enabled</p>}
          </div>
          
          <div className="flex flex-wrap gap-3">
            <button 
              onClick={refresh} 
              disabled={loading}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:opacity-50 text-white border border-gray-600 rounded-lg transition-colors duration-200 text-sm font-medium"
              title="Refresh conversation"
            >
              🔄 Refresh
            </button>
            <button 
              onClick={() => setPollingEnabled(!pollingEnabled)}
              className={`px-4 py-2 border rounded-lg transition-colors duration-200 text-sm font-medium ${
                pollingEnabled 
                  ? 'bg-primary-600 hover:bg-primary-700 text-white border-primary-500' 
                  : 'bg-gray-700 hover:bg-gray-600 text-gray-300 border-gray-600'
              }`}
              title={pollingEnabled ? 'Disable live updates' : 'Enable live updates'}
            >
              {pollingEnabled ? '⏸️ Pause' : '▶️ Resume'} Updates
            </button>
          </div>
        </header>

        {/* Message Interface */}
        <section className="mb-8">
          <div className="flex flex-col gap-4 min-h-[600px]">
            <MessageList 
              messages={messages} 
              loading={conversationLoading && !messages?.length} 
              error={conversationError}
            />
            <MessageInput 
              onSendMessage={sendMessage}
              disabled={!conversation || sending || conversationError}
              placeholder={
                conversationError 
                  ? "Cannot send messages due to error" 
                  : sending 
                    ? "Sending..." 
                    : "Type your message to the agent..."
              }
            />
          </div>
        </section>

        {/* Conversation Actions */}
        <section>
          <h2 className="text-2xl font-bold text-primary-300 mb-6">Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-white mb-2">Export Conversation</h4>
              <p className="text-gray-400 mb-4">Download this conversation as a file</p>
              <button className="w-full px-4 py-2 bg-gray-600 text-gray-400 rounded-md cursor-not-allowed" disabled>
                Export (Coming Soon)
              </button>
            </div>
            
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-white mb-2">Share Conversation</h4>
              <p className="text-gray-400 mb-4">Generate a shareable link</p>
              <button className="w-full px-4 py-2 bg-gray-600 text-gray-400 rounded-md cursor-not-allowed" disabled>
                Share (Coming Soon)
              </button>
            </div>
            
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-white mb-2">Archive Conversation</h4>
              <p className="text-gray-400 mb-4">Move to archived conversations</p>
              <button className="w-full px-4 py-2 bg-red-600/20 text-red-400 border border-red-500 rounded-md cursor-not-allowed" disabled>
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