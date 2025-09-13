import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'
import ConfirmationModal from '../components/ConfirmationModal'

function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Delete modal state
  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    project: null,
    isDeleting: false
  })

  // Create slug from project name for preview
  const createSlug = (name) => {
    return name
      .toLowerCase()
      .replace(/[^a-zA-Z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
  }

  // Fetch projects from backend
  const fetchProjects = async () => {
    console.log('🔄 Fetching projects from backend...')
    try {
      setLoading(true)
      
      const url = '/api/projects'
      console.log('📡 Making request to:', url)
      
      const response = await fetch(url)
      console.log('📡 Response status:', response?.status)
      console.log('📡 Response ok:', response?.ok)
      console.log('📡 Response headers:', response?.headers ? Object.fromEntries(response.headers.entries()) : 'N/A')
      
      if (!response || !response.ok) {
        const errorText = await response?.text() || 'Unknown error'
        console.error('❌ Fetch failed:', errorText)
        throw new Error(`Failed to fetch projects: ${response?.status} ${errorText}`)
      }
      
      const data = await response.json()
      console.log('📊 Received data:', data)
      console.log('📊 Projects count:', data.projects?.length || 0)
      
      setProjects(data.projects || [])
      console.log('✅ Projects loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching projects:', err)
      console.error('❌ Error stack:', err.stack)
      setError('Failed to load projects. Please try again.')
    } finally {
      setLoading(false)
      console.log('🔄 Fetch projects completed')
    }
  }

  // Create new project
  const handleCreateProject = async (e) => {
    e.preventDefault()
    console.log('🆕 Creating new project...')
    
    if (!newProjectName.trim()) {
      console.warn('❌ Project name is empty')
      setError('Project name is required')
      return
    }

    const slug = createSlug(newProjectName.trim())
    console.log('📝 Project details:', { name: newProjectName.trim(), slug })
    
    if (!slug) {
      console.warn('❌ Invalid slug generated')
      setError('Please enter a valid project name')
      return
    }

    try {
      setCreating(true)
      setError('')
      setSuccess('')

      const uuid = getUserUUID()
      console.log('🆔 User UUID:', uuid)

      const requestData = {
        name: newProjectName.trim()
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
      console.log('📡 Request body:', requestData)

      const response = await fetch('/api/projects', requestOptions)
      
      console.log('📡 Create response status:', response?.status)
      console.log('📡 Create response ok:', response?.ok)
      console.log('📡 Create response headers:', response?.headers ? Object.fromEntries(response.headers.entries()) : 'N/A')

      const data = await response.json()
      console.log('📊 Create response data:', data)

      if (!response.ok) {
        console.error('❌ Create project failed:', data)
        throw new Error(data.error || 'Failed to create project')
      }

      console.log('✅ Project created successfully:', data.project)
      setSuccess(`Project "${newProjectName}" created successfully!`)
      setNewProjectName('')
      
      // Refresh projects list
      console.log('🔄 Refreshing projects list...')
      await fetchProjects()
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(''), 5000)
      
    } catch (err) {
      console.error('❌ Error creating project:', err)
      console.error('❌ Error stack:', err.stack)
      setError(err.message || 'Failed to create project. Please try again.')
    } finally {
      setCreating(false)
      console.log('🆕 Create project completed')
    }
  }

  // Handle delete project button click
  const handleDeleteClick = (project, event) => {
    event.preventDefault() // Prevent navigation to project detail
    event.stopPropagation() // Stop event bubbling
    
    console.log('🗑️ Delete button clicked for project:', project.name)
    setDeleteModal({
      isOpen: true,
      project: project,
      isDeleting: false
    })
  }

  // Handle delete confirmation
  const handleDeleteConfirm = async () => {
    const project = deleteModal.project
    if (!project) return

    console.log('🗑️ Confirming deletion of project:', project.name)
    
    try {
      setDeleteModal(prev => ({ ...prev, isDeleting: true }))
      setError('')
      setSuccess('')

      const uuid = getUserUUID()
      console.log('🆔 User UUID:', uuid)

      const requestOptions = {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-User-UUID': uuid
        }
      }
      
      console.log('📡 Delete request options:', requestOptions)

      const response = await fetch(`/api/projects/${project.slug}`, requestOptions)
      
      console.log('📡 Delete response status:', response?.status)
      console.log('📡 Delete response ok:', response?.ok)

      const data = await response.json()
      console.log('📊 Delete response data:', data)

      if (!response.ok) {
        console.error('❌ Delete project failed:', data)
        throw new Error(data.error || 'Failed to delete project')
      }

      console.log('✅ Project deleted successfully:', data)
      
      // Show success message
      let successMessage = `Project "${project.name}" deleted successfully!`
      if (data.warnings && data.warnings.length > 0) {
        successMessage += ` (Note: ${data.warnings.join(', ')})`
      }
      setSuccess(successMessage)
      
      // Close modal
      setDeleteModal({
        isOpen: false,
        project: null,
        isDeleting: false
      })
      
      // Refresh projects list
      console.log('🔄 Refreshing projects list...')
      await fetchProjects()
      
      // Clear success message after 8 seconds (longer for delete confirmation)
      setTimeout(() => setSuccess(''), 8000)
      
    } catch (err) {
      console.error('❌ Error deleting project:', err)
      console.error('❌ Error stack:', err.stack)
      setError(err.message || 'Failed to delete project. Please try again.')
      
      // Keep modal open but stop loading state
      setDeleteModal(prev => ({ ...prev, isDeleting: false }))
    }
  }

  // Handle delete modal close
  const handleDeleteCancel = () => {
    if (deleteModal.isDeleting) return // Prevent closing while deleting
    
    console.log('❌ Delete cancelled')
    setDeleteModal({
      isOpen: false,
      project: null,
      isDeleting: false
    })
  }

  // Load projects on component mount
  useEffect(() => {
    fetchProjects()
  }, [])

  // Clear error when user starts typing
  useEffect(() => {
    if (error && newProjectName) {
      setError('')
    }
  }, [newProjectName, error])

  return (
    <div className="min-h-screen bg-black text-cyber-text">
      <div className="max-w-6xl mx-auto px-8 py-16">
        <header className="text-center mb-16">
          <h1 className="text-5xl font-bold text-cyber-text mb-4 font-mono">Projects</h1>
          <p className="text-xl text-cyber-muted font-mono">Manage your OpenVibe projects</p>
        </header>

        {/* Create New Project Form */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-cyber-text mb-8 font-mono">Create New Project</h2>
          <div className="hacker-card max-w-2xl">
            <form onSubmit={handleCreateProject} className="space-y-6">
              <div>
                <label htmlFor="projectName" className="block text-sm font-medium text-cyber-text mb-2 font-mono">
                  <span className="text-cyber-muted">{'>'}</span> Project Name:
                </label>
                <input
                  type="text"
                  id="projectName"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="Enter project name"
                  disabled={creating}
                  className={`w-full px-4 py-3 bg-black text-cyber-text font-mono border-2 transition-colors duration-200 focus:outline-none focus:border-neon-green ${
                    error ? 'border-red-500' : 'border-cyber-border'
                  }`}
                />
                {newProjectName && (
                  <div className="mt-2 text-sm text-cyber-muted font-mono">
                    Slug: <code className="bg-cyber-accent px-2 py-1 rounded text-cyber-text">{createSlug(newProjectName)}</code>
                  </div>
                )}
              </div>
              
              <button 
                type="submit" 
                disabled={creating || !newProjectName.trim()}
                className="btn-hacker-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? 'Creating...' : 'Create Project'}
              </button>
            </form>

            {error && (
              <div className="mt-4 p-4 bg-red-900/20 border border-red-500 rounded-md text-red-400 font-mono">
                {error}
              </div>
            )}

            {success && (
              <div className="mt-4 p-4 bg-green-900/20 border border-green-500 rounded-md text-green-400 font-mono">
                {success}
              </div>
            )}
          </div>
        </section>

        {/* Projects List */}
        <section>
          <h2 className="text-3xl font-bold text-cyber-text mb-8 font-mono">Your Projects</h2>
          
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-10 h-10 border-4 border-cyber-border border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-cyber-muted font-mono">Loading projects...</p>
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-cyber-muted text-lg font-mono">No projects yet. Create your first project above!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <div key={project.id} className="hacker-card transition-all duration-300 hover:transform hover:-translate-y-1">
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold text-cyber-text mb-1 font-mono">{project.name}</h3>
                        <span className="text-sm text-cyber-muted font-mono">{project.slug}</span>
                      </div>
                      <button 
                        className="text-red-400 hover:text-red-300 text-lg p-2 hover:bg-red-900/20 rounded transition-colors duration-200"
                        onClick={(e) => handleDeleteClick(project, e)}
                        title={`Delete project "${project.name}"`}
                        aria-label={`Delete project "${project.name}"`}
                      >
                        🗑️
                      </button>
                    </div>
                    
                    <div className="space-y-3">
                      <p className="text-sm text-cyber-muted font-mono">
                        Created: {new Date(project.created_at).toLocaleDateString()}
                      </p>
                      
                      {project.github_url && (
                        <div className="text-sm text-green-400 bg-green-900/20 px-3 py-1 rounded font-mono">
                          GitHub repository available
                        </div>
                      )}
                      
                      <div className="pt-2">
                        <Link 
                          to={`/projects/${project.slug}`}
                          className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono"
                        >
                          View Project →
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
      
      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete Project"
        message={
          deleteModal.project ? (
            <>
              Are you sure you want to delete the project <strong>&ldquo;{deleteModal.project.name}&rdquo;</strong>?
              <br /><br />
              <strong>This action will permanently delete:</strong>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                <li>The project from OpenVibe</li>
                {deleteModal.project.github_url && <li>The associated GitHub repository</li>}
                <li>The associated Fly.io application</li>
                <li>All project conversations and data</li>
              </ul>
              <br />
              <strong>This action cannot be undone.</strong>
            </>
          ) : ''
        }
        confirmText="Delete Project"
        cancelText="Cancel"
        isDestructive={true}
        isLoading={deleteModal.isDeleting}
      />
    </div>
  )
}

export default Projects