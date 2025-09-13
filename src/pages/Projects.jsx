import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'
import { Card, Button, Input, LoadingSpinner, Alert, PageHeader } from '../components/ui'
import Layout from '../components/Layout'

function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

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
    <Layout>
      <PageHeader 
        title="Projects" 
        subtitle="Manage your OpenVibe projects"
      />

      {/* Create New Project Form */}
      <Card className="p-6 mb-8 rounded-lg">
        <h2 className="text-xl font-semibold text-white mb-4">Create New Project</h2>
        <form onSubmit={handleCreateProject} className="space-y-4">
          <Input
            label="Project Name"
            type="text"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            placeholder="Enter project name"
            disabled={creating}
            error={error}
          />
          
          {newProjectName && (
            <div className="text-sm text-gray-400">
              Slug: <code className="bg-gray-700 px-2 py-1 rounded text-primary-300">{createSlug(newProjectName)}</code>
            </div>
          )}
          
          <Button 
            type="submit" 
            disabled={creating || !newProjectName.trim()}
            loading={creating}
            className="w-full sm:w-auto"
          >
            Create Project
          </Button>
        </form>

        {success && (
          <Alert variant="success" className="mt-4">
            {success}
          </Alert>
        )}
      </Card>

      {/* Projects List */}
      <div>
        <h2 className="text-2xl font-semibold text-white mb-6">Your Projects</h2>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" text="Loading projects..." />
          </div>
        ) : projects.length === 0 ? (
          <Card className="p-8 text-center">
            <p className="text-gray-400 text-lg">No projects yet. Create your first project above!</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link 
                key={project.id} 
                to={`/projects/${project.slug}`}
                className="block"
              >
                <Card hover className="p-6 h-full">
                  <div className="mb-4">
                    <h3 className="text-xl font-semibold text-white mb-2">{project.name}</h3>
                    <span className="text-sm text-primary-300 bg-primary-300/10 px-2 py-1 rounded">
                      {project.slug}
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    <p className="text-sm text-gray-400">
                      Created: {new Date(project.created_at).toLocaleDateString()}
                    </p>
                    
                    {project.github_url && (
                      <div className="text-sm text-green-400">
                        ✓ GitHub repository available
                      </div>
                    )}
                    
                    <div className="pt-2">
                      <span className="text-primary-300 text-sm font-medium">
                        View Project →
                      </span>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}

export default Projects