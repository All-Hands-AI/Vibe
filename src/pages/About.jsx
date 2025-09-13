import { Card, PageHeader } from '../components/ui'
import Layout from '../components/Layout'

function About() {
  return (
    <Layout>
      <PageHeader 
        title="About OpenVibe" 
        subtitle="Learn more about our mission and the technology behind this project"
      />

      <div className="space-y-12">
        {/* Mission Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div>
            <h2 className="text-2xl font-bold text-text-primary mb-4">Our Mission</h2>
            <div className="space-y-4 text-text-secondary">
              <p>
                OpenVibe is a modern React application built with the latest technologies 
                and best practices. Our goal is to provide a solid foundation for building 
                scalable, maintainable, and performant web applications.
              </p>
              <p>
                We believe in the power of open source and community-driven development. 
                This project serves as both a learning resource and a starting point for 
                developers looking to build amazing user experiences.
              </p>
            </div>
          </div>
          <div className="flex justify-center">
            <Card className="p-12 text-center">
              <span className="text-6xl">🚀</span>
            </Card>
          </div>
        </div>

        {/* Technology Stack */}
        <div>
          <h2 className="text-2xl font-bold text-text-primary mb-8 text-center">Technology Stack</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card hover className="p-6">
              <h3 className="text-lg font-semibold text-primary-300 mb-2">React 19</h3>
              <p className="text-text-secondary">Latest version of React with modern hooks and features</p>
            </Card>
            <Card hover className="p-6">
              <h3 className="text-lg font-semibold text-primary-300 mb-2">Vite</h3>
              <p className="text-text-secondary">Lightning-fast build tool and development server</p>
            </Card>
            <Card hover className="p-6">
              <h3 className="text-lg font-semibold text-primary-300 mb-2">React Router</h3>
              <p className="text-text-secondary">Declarative routing for React applications</p>
            </Card>
            <Card hover className="p-6">
              <h3 className="text-lg font-semibold text-primary-300 mb-2">Vitest</h3>
              <p className="text-text-secondary">Fast unit testing framework built for Vite</p>
            </Card>
            <Card hover className="p-6">
              <h3 className="text-lg font-semibold text-primary-300 mb-2">ESLint</h3>
              <p className="text-text-secondary">Code linting and formatting for consistent code quality</p>
            </Card>
            <Card hover className="p-6">
              <h3 className="text-lg font-semibold text-primary-300 mb-2">Tailwind CSS</h3>
              <p className="text-text-secondary">Utility-first CSS framework for rapid UI development</p>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default About