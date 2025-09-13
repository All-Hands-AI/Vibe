import './About.css'

function About() {
  return (
    <div className="about">
      <div className="container">
        <section className="about-hero">
          <h1>About OpenVibe</h1>
          <p>Learn more about our mission and the technology behind this project</p>
        </section>

        <section className="about-content">
          <div className="about-grid">
            <div className="about-text">
              <h2>Our Mission</h2>
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
            <div className="about-image">
              <div className="placeholder-image">
                <span>🚀</span>
              </div>
            </div>
          </div>
        </section>

        <section className="tech-stack">
          <h2>Technology Stack</h2>
          <div className="tech-grid">
            <div className="tech-item">
              <h3>React 19</h3>
              <p>Latest version of React with modern hooks and features</p>
            </div>
            <div className="tech-item">
              <h3>Vite</h3>
              <p>Lightning-fast build tool and development server</p>
            </div>
            <div className="tech-item">
              <h3>React Router</h3>
              <p>Declarative routing for React applications</p>
            </div>
            <div className="tech-item">
              <h3>Vitest</h3>
              <p>Fast unit testing framework built for Vite</p>
            </div>
            <div className="tech-item">
              <h3>ESLint</h3>
              <p>Code linting and formatting for consistent code quality</p>
            </div>
            <div className="tech-item">
              <h3>GitHub Actions</h3>
              <p>Automated CI/CD pipeline for testing and deployment</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default About