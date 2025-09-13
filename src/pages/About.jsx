function About() {
  return (
    <div className="min-h-screen bg-black text-neon-green relative">
      <div className="max-w-6xl mx-auto px-8 py-16 relative z-10">
        <section className="text-center mb-16">
          <h1 className="text-5xl font-bold text-neon-green mb-4 font-mono neon-glow-strong glitch-text" data-text="About OpenVibe">
            <span className="text-neon-cyan">{'<'}</span> About OpenVibe <span className="text-neon-cyan">{'/>'}</span>
            <span className="animate-terminal-blink">_</span>
          </h1>
          <p className="text-xl text-neon-green/80 max-w-2xl mx-auto font-mono">
            🔍 Learn more about our cyberpunk mission and the hacker tech behind this project
          </p>
        </section>

        <section className="mb-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-neon-green mb-6 font-mono neon-glow">
                🎯 Our Mission
              </h2>
              <div className="terminal-window">
                <div className="terminal-header">
                  💻 MISSION.TXT
                </div>
                <div className="terminal-content text-left">
                  <p className="text-neon-green/90 leading-relaxed mb-4 font-mono">
                    <span className="text-neon-cyan">{'>'}</span> OpenVibe is a cyberpunk React application built with cutting-edge 
                    hacker technologies and best practices. Our goal is to provide a solid 
                    foundation for building scalable, maintainable, and performant web applications.
                  </p>
                  <p className="text-neon-green/90 leading-relaxed font-mono">
                    <span className="text-neon-cyan">{'>'}</span> We believe in the power of open source and community-driven development. 
                    This project serves as both a learning resource and a starting point for 
                    developers looking to build amazing cyberpunk user experiences.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex justify-center">
              <div className="w-64 h-64 bg-gradient-to-br from-neon-green to-neon-cyan rounded-full flex items-center justify-center neon-border animate-pulse-neon">
                <span className="text-8xl">🚀</span>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl font-bold text-neon-green mb-8 text-center font-mono neon-glow">
            <span className="text-neon-cyan">{'<'}</span> Technology Stack <span className="text-neon-cyan">{'/>'}</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-neon-green mb-3 font-mono neon-glow group-hover:animate-pulse-neon">
                ⚛️ React 19
              </h3>
              <p className="text-neon-green/80 font-mono">Latest version of React with modern hooks and cyberpunk features</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-neon-green mb-3 font-mono neon-glow group-hover:animate-pulse-neon">
                ⚡ Vite
              </h3>
              <p className="text-neon-green/80 font-mono">Matrix-speed build tool and development server</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-neon-green mb-3 font-mono neon-glow group-hover:animate-pulse-neon">
                🛣️ React Router
              </h3>
              <p className="text-neon-green/80 font-mono">Declarative routing for cyberpunk React applications</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-neon-green mb-3 font-mono neon-glow group-hover:animate-pulse-neon">
                🧪 Vitest
              </h3>
              <p className="text-neon-green/80 font-mono">Fast unit testing framework built for Vite hackers</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-neon-green mb-3 font-mono neon-glow group-hover:animate-pulse-neon">
                🔍 ESLint
              </h3>
              <p className="text-neon-green/80 font-mono">Code linting and formatting for consistent hacker code quality</p>
            </div>
            <div className="hacker-card group">
              <h3 className="text-xl font-semibold text-neon-green mb-3 font-mono neon-glow group-hover:animate-pulse-neon">
                🤖 GitHub Actions
              </h3>
              <p className="text-neon-green/80 font-mono">Automated CI/CD pipeline for testing and cyber deployment</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default About