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
              {project && (
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
            <span className="text-gray-500">/</span>
            <Link to={`/projects/${project.slug}`} className="text-primary-300 hover:text-primary-400 transition-colors duration-200">
              {project.name}
            </Link>
            <span className="text-gray-500">/</span>
            <span className="text-gray-300">{conversation.name}</span>
          </div>
        </nav>

        {/* Conversation Header */}
        <header className="mb-12">
          <div className="mb-6">
            <h1 className="text-4xl font-bold text-white mb-2">{conversation.name}</h1>
            <span className="text-gray-400 font-mono text-lg">{conversation.slug}</span>
          </div>
          
          <div className="flex flex-wrap items-center gap-6 text-gray-300">
            <p>Created: {new Date(conversation.created_at).toLocaleDateString()}</p>
            {conversation.last_message_at && (
              <p>Last activity: {new Date(conversation.last_message_at).toLocaleDateString()}</p>
            )}
            <p>Messages: {conversation.message_count || 0}</p>
          </div>
        </header>

        {/* Conversation Content */}
        <section className="mb-12">
          <div className="bg-gray-850 rounded-lg border border-gray-700 p-12 text-center">
            <div className="text-6xl mb-6">💬</div>
            <h3 className="text-2xl font-bold text-primary-300 mb-4">Conversation Interface</h3>
            <p className="text-gray-300 mb-6">This is where the conversation interface would be implemented.</p>
            <div className="text-left max-w-md mx-auto">
              <p className="text-gray-300 mb-4 font-semibold">Features to add:</p>
              <ul className="space-y-2 text-gray-400">
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-primary-300 rounded-full mr-3"></span>
                  Message history display
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-primary-300 rounded-full mr-3"></span>
                  Message input and sending
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-primary-300 rounded-full mr-3"></span>
                  Real-time updates
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-primary-300 rounded-full mr-3"></span>
                  File attachments
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-primary-300 rounded-full mr-3"></span>
                  Message search and filtering
                </li>
              </ul>
            </div>
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