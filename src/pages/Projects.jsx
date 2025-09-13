import { useState, useEffect } from 'react'
import { generateUUID } from '../utils/uuid'
import './Projects.css'

function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Get or create user UUID
  const getUserUUID = () => {
    let uuid = localStorage.getItem('user_uuid')
    if (!uuid) {
      uuid = generateUUID()
      localStorage.setItem('user_uuid', uuid)
    }
    return uuid
  }

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
    try {
      setLoading(true)
      const response = await fetch('/api/projects')
      
      if (!response.ok) {
        throw new Error('Failed to fetch projects')
      }
      
      const data = await response.json()
      setProjects(data.projects || [])
    } catch (err) {
      console.error('Error fetching projects:', err)
      setError('Failed to load projects. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Create new project
  const handleCreateProject = async (e) => {
    e.preventDefault()
    
    if (!newProjectName.trim()) {
      setError('Project name is required')
      return
    }

    const slug = createSlug(newProjectName.trim())
    if (!slug) {
      setError('Please enter a valid project name')
      return
    }

    try {
      setCreating(true)
      setError('')
      setSuccess('')

      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newProjectName.trim(),
          uuid: getUserUUID()
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create project')
      }

      setSuccess(`Project "${newProjectName}" created successfully!`)
      setNewProjectName('')
      
      // Refresh projects list
      await fetchProjects()
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(''), 5000)
      
    } catch (err) {
      console.error('Error creating project:', err)
      setError(err.message || 'Failed to create project. Please try again.')
    } finally {
      setCreating(false)
    }
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
    <div className="projects-page">
      <div className="projects-container">
        <header className="projects-header">
          <h1>Projects</h1>
          <p>Manage your OpenVibe projects</p>
        </header>

        {/* Create New Project Form */}
        <section className="create-project-section">
          <h2>Create New Project</h2>
          <form onSubmit={handleCreateProject} className="create-project-form">
            <div className="form-group">
              <label htmlFor="projectName">Project Name</label>
              <input
                type="text"
                id="projectName"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Enter project name"
                disabled={creating}
                className={error ? 'error' : ''}
              />
              {newProjectName && (
                <div className="slug-preview">
                  Slug: <code>{createSlug(newProjectName)}</code>
                </div>
              )}
            </div>
            
            <button 
              type="submit" 
              disabled={creating || !newProjectName.trim()}
              className="create-button"
            >
              {creating ? 'Creating...' : 'Create Project'}
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
        </section>

        {/* Projects List */}
        <section className="projects-list-section">
          <h2>Your Projects</h2>
          
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading projects...</p>
            </div>
          ) : projects.length === 0 ? (
            <div className="empty-state">
              <p>No projects yet. Create your first project above!</p>
            </div>
          ) : (
            <div className="projects-grid">
              {projects.map((project) => (
                <div key={project.id} className="project-card">
                  <div className="project-header">
                    <h3>{project.name}</h3>
                    <span className="project-slug">{project.slug}</span>
                  </div>
                  
                  <div className="project-details">
                    <p className="project-date">
                      Created: {new Date(project.created_at).toLocaleDateString()}
                    </p>
                    
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
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default Projects