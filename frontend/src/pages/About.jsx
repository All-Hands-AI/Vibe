function About() {
  return (
    <div className="min-h-screen bg-black text-cyber-text relative">
      <div className="max-w-6xl mx-auto px-8 py-16 relative z-10">
        <section className="text-center mb-16">
          <h1 className="text-5xl font-bold text-cyber-text mb-4 font-mono glitch-text" data-text="About OpenVibe">
            <span className="text-cyber-muted">{'<'}</span> About OpenVibe <span className="text-cyber-muted">{'/>'}</span>
          </h1>
          <p className="text-xl text-cyber-muted max-w-2xl mx-auto font-mono">
            🔍 Learn more about our cyberpunk mission and the hacker tech behind this project
          </p>
        </section>

        <section className="mb-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-cyber-text mb-6 font-mono">
                🎯 Our Mission
              </h2>
              <div className="terminal-window">
                <div className="terminal-header">
                  💻 MISSION.TXT
                </div>
                <div className="terminal-content text-left">
                  <p className="text-cyber-text leading-relaxed mb-4 font-mono">
                    <span className="text-cyber-muted">{'>'}</span> OpenVibe is a cyberpunk React application built with cutting-edge 
                    hacker technologies and best practices. Our goal is to provide a solid 
                    foundation for building scalable, maintainable, and performant web applications.
                  </p>
                  <p className="text-cyber-text leading-relaxed font-mono">
                    <span className="text-cyber-muted">{'>'}</span> We believe in the power of open source and community-driven development. 
                    This project serves as both a learning resource and a starting point for 
                    developers looking to build amazing cyberpunk user experiences.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex justify-center">
              <div className="w-64 h-64 bg-gradient-to-br from-cyber-accent to-cyber-border rounded-full flex items-center justify-center border-2 border-cyber-border hover:border-neon-green transition-colors duration-300">
                <span className="text-8xl">🚀</span>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl font-bold text-cyber-text mb-8 text-center font-mono">
            <span className="text-cyber-muted">{'<'}</span> Technology Stack <span className="text-cyber-muted">{'/>'}</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-cyber-text mb-3 font-mono">
                ⚛️ React 19
              </h3>
              <p className="text-cyber-muted font-mono">Latest version of React with modern hooks and cyberpunk features</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-cyber-text mb-3 font-mono">
                ⚡ Vite
              </h3>
              <p className="text-cyber-muted font-mono">Matrix-speed build tool and development server</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-cyber-text mb-3 font-mono">
                🛣️ React Router
              </h3>
              <p className="text-cyber-muted font-mono">Declarative routing for cyberpunk React applications</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-cyber-text mb-3 font-mono">
                🧪 Vitest
              </h3>
              <p className="text-cyber-muted font-mono">Fast unit testing framework built for Vite hackers</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-cyber-text mb-3 font-mono">
                🔍 ESLint
              </h3>
              <p className="text-cyber-muted font-mono">Code linting and formatting for consistent hacker code quality</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-cyber-text mb-3 font-mono">
                🤖 GitHub Actions
              </h3>
              <p className="text-cyber-muted font-mono">Automated CI/CD pipeline for testing and cyber deployment</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default About