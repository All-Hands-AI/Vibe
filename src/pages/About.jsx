function About() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-6xl mx-auto px-8 py-16">
        <section className="text-center mb-16">
          <h1 className="text-5xl font-bold text-primary-300 mb-4">About OpenVibe</h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">Learn more about our mission and the technology behind this project</p>
        </section>

        <section className="mb-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-primary-300 mb-6">Our Mission</h2>
              <p className="text-gray-300 leading-relaxed mb-4">
                OpenVibe is a modern React application built with the latest technologies 
                and best practices. Our goal is to provide a solid foundation for building 
                scalable, maintainable, and performant web applications.
              </p>
              <p className="text-gray-300 leading-relaxed">
                We believe in the power of open source and community-driven development. 
                This project serves as both a learning resource and a starting point for 
                developers looking to build amazing user experiences.
              </p>
            </div>
            <div className="flex justify-center">
              <div className="w-64 h-64 bg-gradient-to-br from-primary-300 to-primary-500 rounded-full flex items-center justify-center">
                <span className="text-8xl">🚀</span>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl font-bold text-primary-300 mb-8 text-center">Technology Stack</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700 hover:border-primary-300 transition-colors duration-300">
              <h3 className="text-xl font-semibold text-primary-300 mb-3">React 19</h3>
              <p className="text-gray-300">Latest version of React with modern hooks and features</p>
            </div>
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700 hover:border-primary-300 transition-colors duration-300">
              <h3 className="text-xl font-semibold text-primary-300 mb-3">Vite</h3>
              <p className="text-gray-300">Lightning-fast build tool and development server</p>
            </div>
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700 hover:border-primary-300 transition-colors duration-300">
              <h3 className="text-xl font-semibold text-primary-300 mb-3">React Router</h3>
              <p className="text-gray-300">Declarative routing for React applications</p>
            </div>
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700 hover:border-primary-300 transition-colors duration-300">
              <h3 className="text-xl font-semibold text-primary-300 mb-3">Vitest</h3>
              <p className="text-gray-300">Fast unit testing framework built for Vite</p>
            </div>
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700 hover:border-primary-300 transition-colors duration-300">
              <h3 className="text-xl font-semibold text-primary-300 mb-3">ESLint</h3>
              <p className="text-gray-300">Code linting and formatting for consistent code quality</p>
            </div>
            <div className="bg-gray-850 p-6 rounded-lg border border-gray-700 hover:border-primary-300 transition-colors duration-300">
              <h3 className="text-xl font-semibold text-primary-300 mb-3">GitHub Actions</h3>
              <p className="text-gray-300">Automated CI/CD pipeline for testing and deployment</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default About